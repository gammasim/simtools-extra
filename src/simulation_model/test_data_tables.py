#!/usr/bin/python3
r"""
    Test data tables for prod5/prod6 from 'Files' collection.

    Requires first do download the reference configurations for prod5/prod6 from Zenodo
    using the script 'download_configuration_from_zenodo.py'.

    List of files ignored fine-tuned and might need updates in future.

    To test all files run e.g.,:

    ```bash
    python ./test_data_tables.py ../../../simulation-models/simulation-models/model_parameters/Files
    ```

"""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def compare_file(file: Path, simtel_path: Path):
    """Compare two files."""

    with open(file, "r", encoding="utf-8") as file1, open(
        simtel_path, "r", encoding="utf-8"
    ) as file2:
        lines1 = file1.readlines()
        lines2 = file2.readlines()
        # remove empty lines
        lines1 = [line for line in lines1 if line.strip()]
        lines2 = [line for line in lines2 if line.strip()]
        # remove trailing spaces
        lines1 = [line.strip() for line in lines1]
        lines2 = [line.strip() for line in lines2]

        if len(lines1) != len(lines2):
            logger.error(f"Files {file} and {simtel_path} have different number of lines")
            return

        for line1, line2 in zip(lines1, lines2):
            if line1 != line2:
                logger.error(f"Files {file} and {simtel_path} differ")
                logger.error(f"Line1: {line1}")
                logger.error(f"Line2: {line2}")

        logger.info(f"Files {file} and {simtel_path} are identical")


def test_simtel_files(file_directory: str, simtel_path: str):
    """Compare all data tables (files) found in 'file_directory'"""

    exclude_list = [
        "ray-tracing-North-LST-1-d10.0-za20.0_validate_optics.ecsv",  # simtools-derived
        "ray-tracing-North-MST-NectarCam-D-d10.0-za20.0_validate_optics.ecsv",  # simtools-derived
        "ray-tracing-South-MST-FlashCam-D-d10.0-za20.0_validate_optics.ecsv",  # simtools-derived
        "ray-tracing-South-SST-D-d10.0-za20.0_validate_optics.ecsv",  # simtools-derived
        "ray-tracing-South-LST-D-d10.0-za20.0_validate_optics.ecsv",  # simtools-derived
        "array_coordinates_LaPalma_alpha.dat",
        "array_coordinates_Paranal_alpha.dat",
        "LaPalma_coords.lis",
        "Paranal_coords.lis",
        "sct_photon_incidence_angle_focal_surface.ecsv",  # simtools-derived
        "sst_photon_incidence_angle_secondary_mirror.ecsv",  # simtools-derived
        "sst_photon_incidence_angle_camera_window.ecsv",  # simtools-derived
        "sst_photon_incidence_angle_primary_mirror.ecsv",  # simtools-derived
        "Benn_LaPalma_sky_converted.lis",  # needed for testeff and not for nominal simulations
        "atm_trans_2200_1_3_0_0_0.dat",  # needed for testeff and not for nominal simulations
    ]
    common_list = [
        "atm_trans_2158_1_3_2_0_0_0.1_0.1.dat",
        "atm_trans_2156_1_3_2_0_0_0.1_0.1.dat",
        "atm_trans_2147_1_10_2_0_2147.dat",
        "funnel_perfect.dat",
        "ref_AlSiO2HfO2.dat",
    ]

    files = list(Path(file_directory).rglob("*"))
    for file in files:
        if file.name in exclude_list:
            logger.info(f"Skipping {file}")
            continue
        if file.name in common_list:
            simtel_file = simtel_path / "common" / file.name
        else:
            simtel_file = simtel_path / "CTA" / file.name

        logger.info(f"Comparing {file} with {simtel_file}")
        compare_file(file, simtel_file)


def main():
    """Main function."""
    load_dotenv(".env")

    parser = argparse.ArgumentParser(description="Directory with files to be tested.")
    parser.add_argument("file_directory", type=str, help="Directory with files to be tested.")
    args = parser.parse_args()

    simtel_path = os.getenv("SIMTOOLS_SIMTEL_PATH") or "/workdir/sim_telarray"

    test_simtel_files(
        file_directory=args.file_directory,
        simtel_path=Path(simtel_path) / "sim_telarray/cfg/",
    )


if __name__ == "__main__":
    main()
