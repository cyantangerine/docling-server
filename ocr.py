import logging
import time
from pathlib import Path
from download_model import download_path
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import (
    DocumentConverter,
    InputFormat,
    PdfFormatOption,
)
import os
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import shutil

_log = logging.getLogger(__name__)
det_model_path = os.path.join(
    download_path, "PP-OCRv4", "en_PP-OCRv3_det_infer.onnx"
)
rec_model_path = os.path.join(
    download_path, "PP-OCRv4", "ch_PP-OCRv4_rec_server_infer.onnx"
)
cls_model_path = os.path.join(
    download_path, "PP-OCRv3", "ch_ppocr_mobile_v2.0_cls_train.onnx"
)
IMAGE_RESOLUTION_SCALE = 2.0


def ocr_docling(
    server_path_prefix = "/static/",
    doc_path = "./test/1-20.pdf", 
    output_path = 'output/result', 
    *, 
    image=True, 
    latex=True, 
    code=True
):
    result_obj = {}    
    if not server_path_prefix.endswith("/"):
        server_path_prefix += '/'
    
    logging.basicConfig(level=logging.INFO)
    input_doc_path = Path(doc_path)
    output_dir = Path(output_path)
    
    ocr_options = RapidOcrOptions(
        det_model_path=det_model_path,
        rec_model_path=rec_model_path,
        cls_model_path=cls_model_path,
    )
    pipeline_options = PdfPipelineOptions(
        ocr_options=ocr_options,
        artifacts_path=download_path,
        #accelerator_options=AcceleratorOptions(device='cuda:4')
    )
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = image
    pipeline_options.do_formula_enrichment = latex
    pipeline_options.do_code_enrichment = code
    
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    start_time = time.time()
    conv_res = doc_converter.convert(input_doc_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = conv_res.input.file.stem

    # Save page images
    result_obj['pages'] = []
    os.makedirs(output_dir / 'pages', exist_ok=True)
    for page_no, page in conv_res.document.pages.items():
        if page.image and page.image.pil_image:
            page_no = page.page_no
            filename = f"pages/{page_no}.png"
            page_image_filename = output_dir / filename
            result_obj['pages'].append(server_path_prefix + filename)
            with page_image_filename.open("wb") as fp:
                page.image.pil_image.save(fp, format="PNG")
            
    # Save images of figures and tables
    table_counter = 0
    picture_counter = 0
    result_obj['tables'] = []
    result_obj['pictures'] = []
    os.makedirs(output_dir / 'pictures', exist_ok=True)
    os.makedirs(output_dir / 'tables', exist_ok=True)
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            img = element.get_image(conv_res.document) 
            if img:
                table_counter += 1
                filename = f"tables/{table_counter}.png"
                element_image_filename = output_dir / filename 
                result_obj['tables'].append(server_path_prefix + filename)
                with element_image_filename.open("wb") as fp:
                    img.save(fp, "PNG")

        if isinstance(element, PictureItem):
            img = element.get_image(conv_res.document)
            if img:
                picture_counter += 1
                filename = f"pictures/{picture_counter}.png"
                element_image_filename = output_dir / filename
                result_obj['pictures'].append(server_path_prefix + filename)
                with element_image_filename.open("wb") as fp:                
                    img.save(fp, "PNG")

    # Save markdown with embedded pictures
    filename = f"preview_embedded.md"
    md_filename = output_dir / filename
    result_obj["markdown_with_image"] = server_path_prefix + filename
    conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.EMBEDDED)

    # Save markdown with externally referenced pictures
    filename = f"preview.md"
    md_filename = output_dir / filename
    result_obj["markdown"] = server_path_prefix + filename
    conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
    # data = ''
    # with open(md_filename, 'r') as f:
    #     data = f.read()
    # with open(md_filename, 'w') as f:
    #     f.write(data.replace('![Image](preview_artifacts/image_', f'![Image]({server_path_prefix}preview_artifacts/image_'))

    # Save HTML with externally referenced pictures
    filename = f"preview.html"
    html_filename = output_dir / filename
    result_obj["preview"] = server_path_prefix + filename
    conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)
    data = ''
    with open(html_filename, 'r') as f:
        data = f.read()
    data = data.replace('https://raw.githubusercontent.com/docling-project/docling/refs/heads/main/docs/assets/logo.svg', '')
    data = data.replace("Powered by Docling", '')
    with open(html_filename, 'w') as f:
        f.write(data)
        # f.write(data.replace('<img src="preview_artifacts/image_', f'<img src="{server_path_prefix}preview_artifacts/image_'))

    
    filename = f"original" + os.path.splitext(doc_path)[-1]
    result_obj["origin"] = server_path_prefix + filename
    shutil.move(input_doc_path,  output_dir / filename)

    end_time = time.time() - start_time

    _log.info(f"Document converted and figures exported in {end_time:.2f} seconds.")
    result_obj["process_time"] = end_time
    return result_obj


if __name__ == "__main__":
    ocr_docling()