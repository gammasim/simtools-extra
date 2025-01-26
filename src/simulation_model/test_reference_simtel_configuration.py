#!/usr/bin/python3
r"""
     Test reference sim_telarray configurations against configurations generated sim_telarray.

     Reference configuration files are in `tests/resources/sim_telarray_configurations/`.
     This test compares these files with model version 5.0.0 (prod5) and 6.0.0 (prod6) configuration
     generated by sim_telarray.

     Note:

    - Modifies configuration directory of your sim_telarray 'cfg' directory (!).
    - Highly adapted to prod5 / prod6 configurations.

"""

import logging
import os
import shutil
import subprocess
import tarfile
import warnings
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


configuration = {
    "prod6-north": {
        "site": "North",
        "model_version": "6.0.0",
        "cfg_name": "CTA-PROD6-LaPalma.cfg",
        "mst_option": "-DNECTARCAM",
        "n_telescopes": 30,
        "cfg_replace": {
            "CTA-PROD6-LST-prototype.cfg": "CTA-North-LSTN-01-6.0.0_test.cfg",
            "CTA-PROD6-LST.cfg": "CTA-North-LSTN-02-6.0.0_test.cfg",
            "CTA-PROD6-MST-NectarCam.cfg": "CTA-North-MSTN-01-6.0.0_test.cfg",
        },
        "telescopes_to_test": ["CT1\t", "CT2\t", "CT3\t", "CT4\t", "CT5\t"],
    },
    "prod6-south": {
        "site": "South",
        "model_version": "6.0.0",
        "cfg_name": "CTA-PROD6-Paranal.cfg",
        "mst_option": "-DFLASHCAM",
        "n_telescopes": 87,
        "cfg_replace": {
            "CTA-PROD6-LST-prototype.cfg": "CTA-South-LSTS-01-6.0.0_test.cfg",
            "CTA-PROD6-MST-FlashCam.cfg": "CTA-South-MSTS-01-6.0.0_test.cfg",
            "CTA-PROD6-MST-NectarCam.cfg": "CTA-South-MSTS-01-6.0.0_test.cfg",
            "CTA-PROD6-SST.cfg": "CTA-South-SSTS-01-6.0.0_test.cfg",
            "CTA-PROD6-SCT.cfg": "CTA-South-SCTS-01-6.0.0_test.cfg",
        },
        "telescopes_to_test": ["CT1\t", "CT2\t", "CT3\t", "CT4\t", "CT5\t", "CT30\t"],
    },
    "prod5-north": {
        "site": "North",
        "model_version": "5.0.0",
        "cfg_name": "CTA-PROD5-LaPalma-baseline.cfg",
        "mst_option": "-DNECTARCAM",
        "n_telescopes": 30,
        "cfg_replace": {
            "CTA-PROD4-LST-prototype.cfg": "CTA-North-LSTN-01-5.0.0_test.cfg",
            "CTA-PROD4-LST.cfg": "CTA-North-LSTN-02-5.0.0_test.cfg",
            "CTA-PROD4-MST-NectarCam.cfg": "CTA-North-MSTN-01-5.0.0_test.cfg",
        },
        "telescopes_to_test": ["CT1\t", "CT2\t", "CT3\t", "CT4\t", "CT5\t"],
    },
    "prod5-south": {
        "site": "South",
        "model_version": "5.0.0",
        "cfg_name": "CTA-PROD5-Paranal-Alpha.cfg",
        "mst_option": "-DFLASHCAM",
        "n_telescopes": 100,
        "cfg_replace": {
            "CTA-PROD4-LST.cfg": "CTA-South-LSTS-01-5.0.0_test.cfg",
            "CTA-PROD4-MST-FlashCam.cfg": "CTA-South-MSTS-01-5.0.0_test.cfg",
            "CTA-PROD4-MST-NectarCam.cfg": "CTA-South-MSTS-01-5.0.0_test.cfg",
            "CTA-PROD5-SST.cfg": "CTA-South-SSTS-01-5.0.0_test.cfg",
        },
        "telescopes_to_test": ["CT1\t", "CT2\t", "CT3\t", "CT4\t", "CT5\t", "CT79\t"],
    },
}


def _generate_config(production, new_cfg_name=None):
    """
    Generate a sim_telarray configuration file.

    Parameters
    ----------
    cfg_name: str
        Configuration file name.

    Returns
    -------
    list
        List of lines from the generated configuration file.

    """
    cfg_name = configuration[production]["cfg_name"] if new_cfg_name is None else new_cfg_name
    command = [
        "./sim_telarray/bin/sim_telarray",
        "-c",
        f"sim_telarray/cfg/CTA/{cfg_name}",
        "-C",
        "limits=no-internal",
        "-C",
        "initlist=no-internal",
        "-C",
        "list=no-internal",
        "-C",
        "typelist=no-internal",
        "-C",
        f"maximum_telescopes={configuration[production]['n_telescopes']}",
        "-DNSB_AUTOSCALE",
        f"{configuration[production]['mst_option']}",
        "-DHYPER_LAYOUT",
        f"-DNUM_TELESCOPES={configuration[production]['n_telescopes']}",
        "/dev/null",
    ]
    logger.info(f"Command to generate sim_telarray configuration: {(' ').join(command)}")
    with subprocess.Popen(
        command,
        cwd=os.getenv("SIMTOOLS_SIMTEL_PATH"),
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    ) as process:
        stdout, _ = process.communicate()

    # make sure that all telescopes are found
    for telescope in configuration[production]["telescopes_to_test"]:
        if telescope not in stdout:
            raise ValueError(f"Telescope {telescope} not found in configuration")
    return [
        line
        for line in stdout.splitlines()
        if any(telescope in line for telescope in configuration[production]["telescopes_to_test"])
    ]


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


def _modify_cfg(production):
    """
    Modify configuration file `cfg_name` and use simtools tel-type dependent cfg files.

    """
    simtel_cfg_path = Path(os.getenv("SIMTOOLS_SIMTEL_PATH")) / "sim_telarray/cfg/CTA/"

    # modify main cfg file
    cfg_name = configuration[production]["cfg_name"]
    replacements = configuration[production]["cfg_replace"]
    new_cfg_name = f"new_{cfg_name}"
    with open(simtel_cfg_path / cfg_name, encoding="utf-8") as file:
        lines = file.readlines()
    new_cfg_name = f"new_{cfg_name}"
    with open(simtel_cfg_path / new_cfg_name, "w", encoding="utf-8") as file:
        for line in lines:
            for old, new in replacements.items():
                if old in line:
                    line = line.replace(old, new)
            file.write(line)

    # copy simtools-generated cfg files
    files_to_copy = Path("./tests/resources/sim_telarray_configurations").glob("*.cfg")
    for file in files_to_copy:
        logger.info(f"Copying {file} to {simtel_cfg_path}")
        shutil.copy(file, simtel_cfg_path)

    return new_cfg_name


def test_reference_simtel_configuration(production):
    """Test reference sim_telarray configuration files."""

    cfg_name = configuration[production]["cfg_name"]
    mst_option = configuration[production]["mst_option"]
    n_telescopes = configuration[production]["n_telescopes"]
    model_version = configuration[production]["model_version"]

    logger.info(
        "Testing reference sim_telarray configuration files for "
        f"{cfg_name} with {n_telescopes} telescopes and "
        f"model version {model_version} (MST option: {mst_option})"
    )

    simtel_cfg = _generate_config(production)
    simtools_cfg = _generate_config(production, _modify_cfg(production))
    print(simtools_cfg)

    _compare_configuration_files(simtel_cfg, simtools_cfg)


def _compare_configuration_files(simtel_cfg, simtools_cfg):
    """
    Compare sim_telarray and simtools configuration files.

    Includes a list of lines to be ignored as they are process dependent.
    """

    if len(simtel_cfg) == 0 or len(simtools_cfg) == 0:
        raise ValueError(
            "No configuration file found "
            f"(simtel: {len(simtel_cfg)}; simtools: {len(simtools_cfg)})."
        )

    if len(simtel_cfg) != len(simtools_cfg):
        raise ValueError(
            "Number of telescopes in sim_telarray and simtools configuration files do not match."
        )

    ignore_keywords = {
        "CONFIG_RELEASE",
        "CONFIG_VERSION",
        "OPTICS_CONFIG_NAME",
        "OPTICS_CONFIG_VARIANT",
        "CAMERA_CONFIG_NAME",
        "CAMERA_CONFIG_VARIANT",
        "TAILCUT_SCALE",
    }

    n_par_differ = 0
    for simtel_line, simtools_line in zip(simtel_cfg, simtools_cfg):
        if any(keyword in simtel_line for keyword in ignore_keywords):
            continue
        if simtel_line != simtools_line:
            print("Lines differ:")
            print("\t SIMTEL  :", simtel_line)
            print("\t SIMTOOLS:", simtools_line)
            n_par_differ += 1

    # Test site parameter (one-by-one; as cfg files are different in structure for sites)
    site_parameters = {
        "atmospheric_transmission",
    }
    for par in site_parameters:
        simtel_par = [line for line in simtel_cfg if par.upper() in line.upper()]
        simtools_par = [line for line in simtools_cfg if par.upper() in line.upper()]
        if simtel_par != simtools_par:
            print("Site parameter differ:")
            print("\t SIMTEL  :", simtel_par)
            print("\t SIMTOOLS:", simtools_par)
            n_par_differ += 1

    print(f"Number of differing parameters: {n_par_differ}")


def main():
    """Main function."""
    load_dotenv(".env")

    download_configuration = False
    if download_configuration:
        download_and_unpack(
            url="https://syncandshare.desy.de/index.php/s/H9zbdK7MyJnafTm/download",
            target_directory=os.getenv("SIMTOOLS_SIMTEL_PATH"),
            filename="download",
        )

    for key in configuration:
        if key != "prod5-south":
            continue
        test_reference_simtel_configuration(key)

    # test_reference_simtel_configuration(
    #    "CTA-PROD6-LaPalma.cfg", "-DNECTARCAM", 30, "North", "6.0.0")
    # test_reference_simtel_configuration(
    #    "CTA-PROD6-Paranal.cfg", "-DFLASHCAM", 87, "South", "6.0.0")
    # test_reference_simtel_configuration(
    #    "CTA-PROD5-LaPalma-baseline.cfg", "-DNECTARCAM", 30, "North", "5.0.0")
    # test_reference_simtel_configuration(
    #    "CTA-PROD5-Paranal-baseline.cfg", "-DFLASHCAM", 150, "South", "5.0.0"
    # )


if __name__ == "__main__":
    main()
