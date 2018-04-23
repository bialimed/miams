#!/usr/bin/env python2.7
#
# Copyright (C) 2018
#


__author__ = 'Charles Van Goethem and Frederic Escudie'
__copyright__ = 'Copyright (C) 2018'
__license__ = 'Academic License Agreement'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import logging
import argparse
import subprocess


########################################################################
#
# FUNCTIONS
#
########################################################################
def getSoftwarePath(software, expected_folder):
    """
    @summary: Returns the path to the software from the expected_folder if it is present or from the PATH environment variable.
    @param software: [str] Name of the software.
    @param expected_folder: [str] The folder where the software it is supposed to be in mSINGS.
    @return: [str] The path of the software.
    """
    path = os.path.join(expected_folder, software)  # Expected path in mSINGS directory
    if not os.path.exists(path):
        path = wich(software)  # Search in PATH
        if path is None:
            raise Exception("The software {} cannot be found in environment.".format(software))
    return path


def wich(software):
    """
    @summary: Returns the path to the software from the PATH environment variable.
    @param software: [str] Name of the software.
    @return: [str/None] The path of the software or None if it is not found.
    """
    soft_path = None
    PATH = os.environ.get('PATH')
    for current_folder in reversed(PATH.split(os.pathsep)):  # Reverse PATh elements to kept only the first valid folder
        evel_path = os.path.join(current_folder, software)
        if os.path.exists(eval_path):
            soft_path = evel_path
    return soft_path


def process(args, log):
    """
    @summary: Create intervals file from bed file containing microsatellite of interest.
    param args: [Namespace] The namespace extract from the script arguments.
    param log: [Logger] The logger of the script.
    """
    # Softwares pathes
    msi_path = getSoftwarePath("msi", os.path.join(args.msings_directory, "msings-env", "bin"))

    # Init
    working_directory = os.path.join(os.path.dirname(args.output), os.path.basename(args.output) + "_work")
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)

    # sort bed file
    log.info("Start sort bed file")
    sort_output = os.path.join(working_directory, "sorted.bed")
    fout = open(sort_output,'w')
    cmd = [
        "sort",
        "-V",
        "-k1,1",
        "-k2,2n",
        args.input_bed
    ]
    log.debug("sub-command: " + " ".join(map(str, cmd)))
    subprocess.check_call(cmd, stdout=fout)
    fout.close()

    # Making MSI intervals file
    log.info("Making MSI intervals file")
    cmd = [
        msi_path,
        "formatter",
        sort_output,
        args.output
    ]
    log.debug("sub-command: " + " ".join(map(str, cmd)))
    subprocess.check_call(cmd)
    log.info("End Making MSI intervals file")

    # Clean temporaries
    for tmp_file in [sort_output]:
        os.remove(tmp_file)
    os.rmdir(working_directory)


class LoggerAction(argparse.Action):
    """
    @summary: Manages logger level parameters (The value "INFO" becomes logging.info and so on).
    """
    def __call__(self, parser, namespace, values, option_string=None):
        log_level = None
        if values == "DEBUG":
            log_level = logging.DEBUG
        elif values == "INFO":
            log_level = logging.INFO
        elif values == "WARNING":
            log_level = logging.WARNING
        elif values == "ERROR":
            log_level = logging.ERROR
        elif values == "CRITICAL":
            log_level = logging.CRITICAL
        setattr(namespace, self.dest, log_level)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Create intervals file from bed file containing microsatellite of interest.")
    parser.add_argument('-d', '--msings-directory', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), help='The path to the mSINGS installation folder. [Default: %(default)s]')
    parser.add_argument('-l', '--logging-level', default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], action=LoggerAction, help='The logger level. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-b', '--input-bed', required=True, help="Bed file contains microsatellite of interset (format: BED)")
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output', required=True, help="Output intervals file (format : intervals)")
    args = parser.parse_args()

    # Process
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger("create_intervals")
    log.setLevel(args.logging_level)
    log.info("Start create intervals")
    log.info("Command: " + " ".join(sys.argv))
    process(args, log)
    log.info("End create intervals")
