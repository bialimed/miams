#!/usr/bin/env python2.7
#
# Copyright (C) 2018 IUCT-O
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


__author__ = 'Charles Van Goethem and Frederic Escudie'
__copyright__ = 'Copyright (C) 2018'
__license__ = 'Academic License Agreement'
__version__ = '1.2.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import csv
import logging
import argparse
import subprocess
from shutil import copyfile


########################################################################
#
# FUNCTIONS
#
########################################################################
def getLociWithoutStatus(sample_name, in_annot, expected_status="MSS"):
    """
    @summary: Returns loci with a status different of expected_status.
    @param sample_name: [str] The name of the sample selected in annotations file.
    @param in_annot: [str] Path to the MSIAnnot file containing for each sample for each targeted locus the stability status (format: TSV). This file allows to filter loci used in each samples. First line must be: sample<tab>locus_position<tab>method_id<tab>key<tab>value<tab>type. An example of line content is: H2291-1_S15<tab>4:55598140-55598290<tab>model<tab>status<tab>MSS<tab>str.
    @param expected_status: [str] The loci without this status are returned.
    @return: [list] The list of selected loci.
    """
    selected_loci = set()
    with open(in_annot) as FH_annot:
        reader = csv.DictReader(FH_annot, delimiter="\t")
        for row in reader:
            if row["sample"] == sample_name and row["locus_position"] != "":
                if row["key"] == "status" and row["value"] != expected_status:
                    selected_loci.add(row["locus_position"])
    return list(selected_loci)


def invalidateLoci(filtered_loci, in_analyzer, out_anlyzer):
    """
    @summary: Sets support of selected loci to 0. This action allows to prevent usage of these loci of this sample in building of baseline.
    @filtered_loci: [list] The positions (chr:start-end with start 0-based) of the loci to discard.
    @in_analyzer: [str] The path of the mSINGS analyze file.
    @out_anlyzer: [str] The path of the mSINGS analyze file after modification.
    """
    dict_filtered_loci = {locus: 1 for locus in filtered_loci}
    with open(out_anlyzer, "w") as FH_out:
        writer = csv.DictWriter(FH_out, fieldnames=["Position", "Name", "Average_Depth", "Number_of_Peaks", "Standard_Deviation", "IndelLength:AlleleFraction:SupportingCalls"], delimiter="\t")
        writer.writeheader()
        with open(in_analyzer) as FH_in:
            reader = csv.DictReader(FH_in, delimiter="\t")
            for row in reader:
                if row["Position"] in dict_filtered_loci:
                    row["Average_Depth"] = 0  # Set Average_Depth to 0 for eliminate this locus in create_baseline script
                writer.writerow(row)


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
    for current_folder in reversed(PATH.split(os.pathsep)):  # Reverse PATH elements to kept only the first valid folder
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
        log.info("[{}] Start samtools mpileup".format(sample_name))
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

        log.debug("[{}] Sub-command: {}".format(sample_name, " ".join(cmd)))
        with open(mpileup_output, 'w') as FH_out:
            subprocess.check_call(cmd, stdout=FH_out)
        filtered_mpileup_output = os.path.join(working_directory, sample_name + ".filtered_mpileup.txt")
        cmd = [
            "awk",
            '{if($4 >= 6) print $0}',
            mpileup_output
        ]
        log.debug("[{}] Sub-command: {}".format(sample_name, " ".join(cmd)))
        with open(filtered_mpileup_output, 'w') as FH_out:
            subprocess.check_call(cmd, stdout=FH_out)
        log.info("[{}] End samtools mpileup".format(sample_name))

        # Varscan
        log.info("[{}] Start Varscan readcounts".format(sample_name))
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
        log.debug("[{}] Sub-command: {}".format(sample_name, " ".join(cmd)))
        subprocess.check_call(cmd)
        log.info("[{}] End Varscan readcounts".format(sample_name))

        # MSI analyzer
        log.info("[{}] Start MSI analyzer".format(sample_name))
        analyzer_output = os.path.join(working_directory, sample_name + ".msi.txt")
        cmd = [
            msi_path,
            "analyzer",
            varscan_output,
            args.input_targets,
            "-o", analyzer_output
        ]
        log.debug("[{}] Sub-command: {}".format(sample_name, " ".join(cmd)))
        subprocess.check_call(cmd)
        log.info("[{}] End MSI analyzer".format(sample_name))

        # Filter targets
        if args.input_annotations is not None:
            log.info("[{}] Start filter targets".format(sample_name))
            invalid_loci = getLociWithoutStatus(sample_name, args.input_annotations, "MSS")
            if len(invalid_loci) > 0:
                log.info("[{}] Loci filtered in sample: {}".format(sample_name, sorted(invalid_loci)))
                filter_output = os.path.join(working_directory, sample_name + ".filtered.txt")
                invalidateLoci(invalid_loci, analyzer_output, filter_output)
                copyfile(filter_output, analyzer_output)
            log.info("[{}] End filter targets".format(sample_name))

    # MSI call
    log.info("Start MSI create baseline")
    cmd = [
        msi_path,
        "create_baseline",
        working_directory,
        "-o", args.output_baseline
    ]
    log.debug("Sub-command: " + " ".join(cmd))
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
    group_input_exclusive = group_input.add_mutually_exclusive_group(required=True)
    group_input_exclusive.add_argument('-a', '--inputs-aln', nargs='+', help="The pathes of alignment file to evaluate (format: BAM). All BAMs must be ordered by coordinates and indexed.")
    group_input_exclusive.add_argument('-f', '--input-list', help="The path of the file listing the alignment files pathes (format: txt). All BAMs must be ordered by coordinates and indexed.")
    group_input.add_argument('-g', '--input-genome', required=True, help="Reference used to generate alignment file.(format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.")
    group_input.add_argument('-i', '--input-intervals', required=True, help="MSI interval file (format: TSV). See mSINGS create_intervals script.")
    group_input.add_argument('-t', '--input-targets', required=True, help="The locations of the microsatellite tracts of interest (format: BED). This file must be sorted numerically and must not have a header line.")
    group_input.add_argument('-n', '--input-annotations', help='Path to the MSIAnnot file containing for each sample for each targeted locus the stability status (format: TSV). This file allows to filter loci used in each samples. First line must be: sample<tab>locus_position<tab>method_id<tab>key<tab>value<tab>type. An example of line content is: H2291-1_S15<tab>4:55598140-55598290<tab>model<tab>status<tab>MSS<tab>str.')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-baseline', required=True, help="MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.")
    args = parser.parse_args()

    # Process
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger("run_mSINGS")
    log.setLevel(args.logging_level)
    log.info("Start mSINGS")
    log.info("Command: " + " ".join(sys.argv))
    if args.input_list is not None:
        with open(args.input_list) as FH_in:
            args.inputs_aln = [elt.strip() for elt in FH_in.readlines() if elt != ""]
    process(args, log)
    log.info("End mSINGS")
