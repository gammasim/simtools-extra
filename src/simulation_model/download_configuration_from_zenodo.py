#!/usr/bin/python3
r"""
    Download reference configurations for prod5/prod6 from Zenodo.

"""

import logging
import os
import tarfile
import warnings
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def download_and_unpack(url, target_directory, filename):
    """Download and unpack tarball with sim_telarray configuration."""

    tar_path = Path(target_directory) / filename
    logger.info(f"Downloading sim_telarray configuration from {url}")
    response = requests.get(url, stream=True, timeout=10)
    response.raise_for_status()

    with open(tar_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    logger.info(f"Extracting {tar_path} to {target_directory}")
    with warnings.catch_warnings():  # warnings; should go away with python 3.12
        warnings.simplefilter("ignore", category=RuntimeWarning)
        with tarfile.open(tar_path, "r:*") as tar:
            tar.extractall(path=target_directory)
    tar_path.unlink()


def download_configuration_from_zenodo():
    """Download reference configurations for prod5/prod6 from Zenodo."""

    load_dotenv(".env")
    urls = [
        "https://zenodo.org/records/6218687/files/sim_telarray_config_prod5b.tar.gz?download=1",
        "https://zenodo.org/records/14198379/files/sim_telarray_config_prod6.tar.gz?download=1",
    ]
    target_directory = os.getenv("SIMTOOLS_SIMTEL_PATH") or "/workdir/sim_telarray"
    for url in urls:
        download_and_unpack(
            url=url,
            target_directory=target_directory,
            filename="download",
        )


if __name__ == "__main__":
    download_configuration_from_zenodo()
