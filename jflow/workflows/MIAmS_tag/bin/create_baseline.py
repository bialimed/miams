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
        path = which(software)  # Search in PATH
        if path is None:
            raise Exception("The software {} cannot be found in environment.".format(software))
    return path


def which(software):
    """
    @summary: Returns the path to the software from the PATH environment variable.
    @param software: [str] Name of the software.
    @return: [str/None] The path of the software or None if it is not found.
    """
    soft_path = None
    PATH = os.environ.get('PATH')
    for current_folder in reversed(PATH.split(os.pathsep)):  # Reverse PATh elements to kept only the first valid folder
        eval_path = os.path.join(current_folder, software)
        if os.path.exists(eval_path):
            soft_path = eval_path
    return soft_path


def process(args, log):
    """
    @summary: Launch mSINGS analysis from one BAM file.
    param args: [Namespace] The namespace extract from the script arguments.
    param log: [Logger] The logger of the script.
    """
    # Softwares pathes
    samtools_path = getSoftwarePath("samtools", os.path.join(args.msings_directory, "msings-env", "bin"))
    varscan_path = getSoftwarePath("VarScan.v2.3.7.jar", os.path.join(args.msings_directory, "msings-env", "bin"))
    msi_path = getSoftwarePath("msi", os.path.join(args.msings_directory, "msings-env", "bin"))

    # Init
    working_directory = os.path.join(os.path.dirname(args.output_baseline), os.path.basename(args.output_baseline) + "_work")
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)

    for curr_aln_path in args.inputs_aln:
        sample_name = os.path.basename(curr_aln_path).rsplit(".", 1)[0]

        # Mpileup
        log.info("Start samtools mpileup")
        mpileup_output = os.path.join(working_directory, sample_name + ".mpileup.txt")
        cmd = [
            samtools_path,
            "mpileup",
            "-f", args.input_genome,
            "-d", "100000",
            "-A",
            "-E", curr_aln_path,
            "-l", args.input_intervals
        ]

        log.debug("sub-command: " + " ".join(cmd))
        with open(mpileup_output, 'w') as FH_out:
            subprocess.check_call(cmd, stdout=FH_out)
        filtered_mpileup_output = os.path.join(working_directory, sample_name + ".filtered_mpileup.txt")
        cmd = [
            "awk",
            '{if($4 >= 6) print $0}',
            mpileup_output
        ]
        log.debug("sub-command: " + " ".join(cmd))
        with open(filtered_mpileup_output, 'w') as FH_out:
            subprocess.check_call(cmd, stdout=FH_out)
        log.info("End samtools mpileup")

        # Varscan
        log.info("Start Varscan readcounts")
        varscan_output = os.path.join(working_directory, sample_name + ".varscan.txt")
        cmd = [
            args.java_path,
            "-Xmx{}g".format(args.java_mem),
            "-jar", varscan_path,
            "readcounts",
            filtered_mpileup_output,
            "--variants-file", args.input_intervals,
            "--min-base-qual", "10",
            "--output-file", varscan_output
        ]
        log.debug("sub-command: " + " ".join(cmd))
        subprocess.check_call(cmd)
        log.info("End Varscan readcounts")

        # MSI analyzer
        log.info("Start MSI analyzer")
        tmp_output_analyzer = os.path.join(working_directory, sample_name + ".msi.txt")
        cmd = [
            msi_path,
            "analyzer",
            varscan_output,
            args.input_targets,
            "-o", tmp_output_analyzer
        ]
        log.debug("sub-command: " + " ".join(cmd))
        subprocess.check_call(cmd)
        log.info("End MSI analyzer")

    # MSI call
    log.info("Start MSI create baseline")
    cmd = [
        msi_path,
        "create_baseline",
        working_directory,
        "-o", args.output_baseline
    ]
    log.debug("sub-command: " + " ".join(cmd))
    subprocess.check_call(cmd)
    log.info("End MSI create baseline")

    # Clean temporaries
    for tmp_file in os.listdir(working_directory):
        os.remove(os.path.join(working_directory, tmp_file))
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
    parser = argparse.ArgumentParser(description="Launch mSINGS analysis from one BAM file. The virtual environment of mSINGS must be activated.")
    parser.add_argument('-j', '--java-path', default=which("java"), help='The path to the java runtime. [Default: %(default)s]')
    parser.add_argument('-m', '--java-mem', default=4, type=int, help='The memory allowed to java virtual machine in giga bytes. [Default: %(default)s]')
    parser.add_argument('-d', '--msings-directory', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), help='The path to the mSINGS installation folder. [Default: %(default)s]')
    parser.add_argument('-l', '--logging-level', default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], action=LoggerAction, help='The logger level. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-a', '--inputs-aln', required=True, nargs='+', help="The pathes of alignment file to evaluate (format: BAM). All BAMs must be ordered by coordinates and indexed.")
    group_input.add_argument('-g', '--input-genome', required=True, help="Reference used to generate alignment file.(format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.")
    group_input.add_argument('-i', '--input-intervals', required=True, help="MSI interval file (format: TSV). See mSINGS create_intervals script.")
    group_input.add_argument('-t', '--input-targets', required=True, help="The locations of the microsatellite tracts of interest (format: BED). This file must be sorted numerically and must not have a header line.")
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-baseline', required=True, help="MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.")
    args = parser.parse_args()

    # Process
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger("run_mSINGS")
    log.setLevel(args.logging_level)
    log.info("Start mSINGS")
    log.info("Command: " + " ".join(sys.argv))
    process(args, log)
    log.info("End mSINGS")
