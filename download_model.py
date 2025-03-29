from pathlib import Path
download_path = Path(__file__).parent / 'models'

if __name__ == '__main__':
    from docling.utils.model_downloader import download_models
    download_models(download_path, progress=True)
    
    from huggingface_hub import snapshot_download
    print("Downloading RapidOCR models")
    from tqdm import tqdm
    snapshot_download(repo_id="SWHL/RapidOCR", local_dir=download_path, tqdm_class=tqdm)