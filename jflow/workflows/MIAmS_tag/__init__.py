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
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '0.4.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'dev'

import os
import sys
import json
import time
import shutil
from jflow.workflow import Workflow

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(CURRENT_DIR, "lib")
sys.path.append(LIB_DIR)

from anacore.illumina import getLibNameFromReadsPath


def commonSubStr(str_a, str_b):
    """Returns the longer common substring from the left of the two strings.

    :param str_a: The first string to process.
    :type str_a: str
    :param str_b: The second string to process.
    :type str_b: str
    :return: The longer common substring.
    :rtype: str
    """
    common = ""
    valid = True
    for char_a, char_b in zip(str_a, str_b):
        if char_a != char_b:
            valid = False
        if valid:
            common += char_a
    return common


def commonSubPathes(pathes_a, pathes_b, use_basename=False):
    """Returns the longer common substring from the left of the two strings.

    :param pathes_a: The first string to process.
    :type pathes_a: list
    :param pathes_b: The second string to process.
    :type pathes_b: list
    :param use_basename: With true the substrings are extracted from the
    basenames. Otherwise they are extracted from all the path.
    :type use_basename: bool
    :return: The longer common substring.
    :rtype: list
    """
    out_list = list()
    for path_a, path_b in zip(pathes_a, pathes_b):
        if use_basename:
            path_a = os.path.basename(path_a)
            path_b = os.path.basename(path_b)
        out_list.append(commonSubStr(path_a, path_b))
    return out_list


class MIAmSTag (Workflow):
    def get_description(self):
        return "Workflow for detecting microsatellite instability by next-generation sequencing on amplicons."


    def write_log(self, log_path, version):
        """Writes a tiny log for user.

        :param log_path: Path to the log file.
        :type log_path: str
        :param version: Version of the workflow.
        :type version: str
        """
        with open(log_path, "w") as FH_log:
            FH_log.write(
                "Workflow={}\n".format(self.__class__.__name__) + \
                "Version={}\n".format(version) + \
                "Parameters={}\n".format(" ".join(sys.argv)) + \
                "Start_time={}\n".format(self.start_time) + \
                "End_time={}\n".format(time.time())
            )


    def define_parameters(self, parameters_section=None):
        # Cleaning
        self.add_input_file("R1_end_adapter", "Path to sequence file containing the start of Illumina P7 adapter (format: fasta). This sequence is trimmed from the end of R1 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        self.add_input_file("R2_end_adapter", "Path to sequence file containing the start of reverse complemented Illumina P5 adapter ((format: fasta). This sequence is trimmed from the end of R2 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")

        # Inputs data
        self.add_input_file_list("R1", "Pathes to R1 (format: fastq).", required=True, group="Inputs data")
        self.add_input_file_list("R2", "Pathes to R2 (format: fastq).", required=True, group="Inputs data")

        # Inputs design
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", required=True, group="Inputs design")
        self.add_input_file("intervals", "MSI intervals file (format: TSV). See mSINGS create_intervals script.", required=True, group="Inputs design")
        self.add_input_file("baseline", "Path to the MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.", required=True, group="Inputs design")
        self.add_input_file("genome_seq", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", required=True, file_format="fasta", group="Inputs design")

        # Outputs data
        self.add_parameter("output_dir", "Path to the output folder.", required=True, group="Output data")


    def pre_restart(self):
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = os.environ['PYTHONPATH'] + os.pathsep + LIB_DIR
        else:
            os.environ["PYTHONPATH"] = LIB_DIR


    def pre_process(self):
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = os.environ['PYTHONPATH'] + os.pathsep + LIB_DIR
        else:
            os.environ["PYTHONPATH"] = LIB_DIR
        try:
            self.samples_names = [getLibNameFromReadsPath(str(elt)) for elt in self.R1]
        except:
            self.samples_names = commonSubPathes(self.R1, self.R2, True)


    def process(self):
        # Clean reads
        cleaned_R1 = self.R1
        if self.R1_end_adapter != None:
            clean_R1 = self.add_component("Cutadapt", ["a", self.R1_end_adapter, self.R1, None, 0.01, 10], component_prefix="R1")
            cleaned_R1 = clean_R1.out_R1
        cleaned_R2 = self.R2
        if self.R2_end_adapter != None:
            clean_R2 = self.add_component("Cutadapt", ["a", self.R2_end_adapter, self.R2, None, 0.01, 10], component_prefix="R2")
            cleaned_R2 = clean_R2.out_R1

        # Align reads
        bwa = self.add_component("BWAmem", [self.genome_seq, cleaned_R1, cleaned_R2, self.samples_names])
        idx_aln = self.add_component("BAMIndex", [bwa.aln_files])

        # Call MSI with run_msings.py
        msings = self.add_component("MSINGS", [idx_aln.out_aln, self.targets, self.intervals, self.baseline, self.genome_seq])

        # Retrieve size profile for each MSI
        on_targets = self.add_component("BamAreasToFastq", [idx_aln.out_aln, self.targets, 20, True, cleaned_R1, cleaned_R2])
        combine = self.add_component("CombinePairs", [on_targets.out_R1, on_targets.out_R2, None, 0.25, 20])

        # Report
        self.reports_cmpt = self.add_component("MSIMergeReports", [combine.out_report, msings.report, self.targets])


    def post_process(self):
        if not os.path.exists(self.output_dir): os.mkdir(self.output_dir)

        # User log
        log_file = os.path.join(self.output_dir, self.__class__.__name__ + "_log.txt")
        self.write_log(log_file, __version__)

        # Copy data
        data_folder = os.path.join(self.output_dir, "data")
        if not os.path.exists(data_folder): os.mkdir(data_folder)
        for curr_res in self.reports_cmpt.out_report:
            filename = os.path.basename(curr_res)
            shutil.copy(curr_res, os.path.join(data_folder, filename))

        # Copy lib
        wf_src_path = os.path.dirname(os.path.realpath(__file__))
        web_lib_path = os.path.join(wf_src_path, "resources", "lib")
        out_lib = os.path.join(self.output_dir, "lib")
        if os.path.exists(out_lib): shutil.rmtree(out_lib)
        shutil.copytree(web_lib_path, out_lib)

        # Get results
        results_by_sample = {}
        for curr_spl, curr_res in zip(self.samples_names, self.reports_cmpt.out_report):
            with open(curr_res) as FH_in:
                results_by_sample[curr_spl] = json.load(FH_in)

        # Write report
        template_path = os.path.join(wf_src_path, "resources", "report.html")
        report_path = os.path.join(self.output_dir, "report.html")
        with open(report_path, "w") as FH_output:
            with open(template_path) as FH_template:
                for line in FH_template:
                    if "= ##DATA##" in line:
                        line = line.replace("##DATA##", json.dumps(results_by_sample))
                    FH_output.write(line)
