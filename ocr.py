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

_log = logging.getLogger(__name__)

IMAGE_RESOLUTION_SCALE = 2.0


def ocr_docling(doc_path = "./test/1-20.pdf", output_path = 'result', *, image=True, latex=False, code=True):
    logging.basicConfig(level=logging.INFO)
    input_doc_path = Path(doc_path)
    output_dir = "output" / Path(output_path)
    
    det_model_path = os.path.join(
        download_path, "PP-OCRv4", "en_PP-OCRv3_det_infer.onnx"
    )
    rec_model_path = os.path.join(
        download_path, "PP-OCRv4", "ch_PP-OCRv4_rec_server_infer.onnx"
    )
    cls_model_path = os.path.join(
        download_path, "PP-OCRv3", "ch_ppocr_mobile_v2.0_cls_train.onnx"
    )
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
    pipeline_options.generate_page_images = False
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

    # # Save page images
    # for page_no, page in conv_res.document.pages.items():
    #     page_no = page.page_no
    #     page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
    #     with page_image_filename.open("wb") as fp:
    #         page.image.pil_image.save(fp, format="PNG")

    # Save images of figures and tables
    table_counter = 0
    picture_counter = 0
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            element_image_filename = (
                output_dir / f"{doc_filename}-table-{table_counter}.png"
            )
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")

        if isinstance(element, PictureItem):
            picture_counter += 1
            element_image_filename = (
                output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            )
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")

    # Save markdown with embedded pictures
    md_filename = output_dir / f"{doc_filename}-with-images.md"
    conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.EMBEDDED)

    # Save markdown with externally referenced pictures
    md_filename = output_dir / f"{doc_filename}-with-image-refs.md"
    conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)

    # Save HTML with externally referenced pictures
    html_filename = output_dir / f"{doc_filename}-with-image-refs.html"
    conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)

    end_time = time.time() - start_time

    _log.info(f"Document converted and figures exported in {end_time:.2f} seconds.")


if __name__ == "__main__":
    ocr_docling()