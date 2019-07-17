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
__version__ = '1.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import json
import shutil
import fnmatch
import argparse

from workflows.src.miamsWorkflows import MIAmSWf

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "lib")
sys.path.insert(0, LIB_DIR)

from anacore.illumina import getLibNameFromReadsPath
from anacore.msi import MSIReport, Status


def getHigherPeakByLocus(models, min_support_reads):
    """
    Return length of the higher peak of each model by locus.

    :param models: The list of MSIReport representing the models (status known and stored in Expected result).
    :type models: list
    :param min_support_reads: The minimum number of reads on locus to use the stability status of the current model.
    :type min_support_reads: int
    :return: By locus the list of higher peak length.
    :rtype: dict
    """
    higher_by_locus = {}
    models_samples = MSIReport.parse(models)
    for curr_spl in models_samples:
        for locus_id, curr_locus in curr_spl.loci.items():
            if locus_id not in higher_by_locus:
                higher_by_locus[locus_id] = []
            if "model" in curr_locus.results:
                if curr_locus.results["model"].status == Status.stable and curr_locus.results["model"].getNbFrag() > (min_support_reads / 2):
                    max_peak = None
                    max_count = -1
                    for length, count in curr_locus.results["model"].data["nb_by_length"].items():
                        if count >= max_count:  # "=" for select the tallest
                            max_count = count
                            max_peak = int(length)
                    higher_by_locus[locus_id].append(max_peak)
    return higher_by_locus


def commonSubStr(str_a, str_b):
    """
    Return the longer common substring from the left of the two strings.

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
    """
    Return the longer common substring from the left of the two strings.

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


class MIAmSTag (MIAmSWf):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lib_dir = LIB_DIR


    def get_description(self):
        return "Workflow for detecting microsatellite instability by next-generation sequencing on amplicons."


    def define_parameters(self, parameters_section=None):
        # Sample classifier
        self.add_parameter("loci_consensus_method", "Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-threshold the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-threshold the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable.", choices=['count', 'majority', 'ratio'], default='ratio', group="Sample classification parameters")
        self.add_parameter("instability_count", 'Only if consensus-method is equal to "count". The threshold to determine if the sample is stable or unstable. If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable.', default=3, type=int, group="Sample classification parameters")
        self.add_parameter("instability_ratio", 'Only if consensus-method is equal to "ratio". The threshold to determine if the sample is stable or unstable. If the ratio of unstable/determined loci is upper or equal than this value the sample will be unstable otherwise it will be stable.', default=0.5, type=float, group="Sample classification parameters")
        self.add_parameter("min_voting_loci", "Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined.", default=3, type=int, group="Sample classification parameters")

        # Sample classification score
        self.add_parameter("undetermined_weight", "[Used only for the sklearn classifier] The weight of undetermined loci in sample prediction score calculation.", default=0.0, type=float, group="Sample classification score")
        self.add_parameter("locus_weight_is_score", "[Used only for the sklearn classifier] Use the prediction score of each locus as wheight of this locus in sample prediction score calculation.", type="bool", default=False, group="Sample classification score")

        # Locus classifier
        self.add_parameter("min_support_reads", "The minimum number of reads on locus for analyse the stability status of this locus in this sample.", default=300, type=int, group="Locus classification parameters")
        self.add_parameter("classifier", "The classifier used to predict loci status.", choices=["DecisionTree", "KNeighbors", "LogisticRegression", "RandomForest", "SVC"], default="SVC", group="Locus classification parameters")
        self.add_parameter("classifier_params", 'By default the MIAmSClassifier is used with these default parameters defined in scikit-learn. If you want change these parameters you use this option to provide them as json string. Example: {"n_estimators": 1000, "criterion": "entropy"} for RandmForest.', group="Locus classification parameters")
        self.add_parameter("random_seed", "The seed used by the random number generator in MIAmSClassifier.", type=int, group="Locus classification parameters")

        # Combine reads method
        self.add_parameter("max_mismatch_ratio", "Maximum allowed ratio between the number of mismatched base pairs and the overlap length. Two reads will not be combined with a given overlap if that overlap results in a mismatched base density higher than this value.", default=0.25, type=float, group="Combine reads method")
        self.add_parameter("min_pair_overlap", "The minimum required overlap length between two reads in pair to provide a confident overlap.", default=20, type=int, group="Combine reads method")
        self.add_parameter("min_zoi_overlap", "A reads pair is selected for combine method only if this number of nucleotides of the target are covered by the each read.", default=12, type=int, group="Combine reads method")

        # Cleaning
        self.add_input_file("R1_end_adapter", "Path to sequence file containing the start of Illumina P7 adapter (format: fasta). This sequence is trimmed from the end of R1 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        self.add_input_file("R2_end_adapter", "Path to sequence file containing the start of reverse complemented Illumina P5 adapter ((format: fasta). This sequence is trimmed from the end of R2 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")

        # Inputs data
        self.add_input_file_list("R1", "Pathes to R1 (format: fastq).", rules="Exclude=R1_pattern,R2_pattern,exclusion_pattern;ToBeRequired=R2;RequiredIf?ALL[R1_pattern=None]", group="Inputs data")
        self.add_input_file_list("R2", "Pathes to R2 (format: fastq).", rules="Exclude=R1_pattern,R2_pattern,exclusion_pattern;ToBeRequired=R1;RequiredIf?ALL[R1_pattern=None]", group="Inputs data")
        self.add_input_file_list("R1_pattern", "Pattern to find R1 files (format: fastq). This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", type="regexpfiles", rules="Exclude=R1,R2;ToBeRequired=R2_pattern;RequiredIf?ALL[R1=None]", group="Inputs data by pattern")
        self.add_input_file_list("R2_pattern", "Pattern to find R2 files (format: fastq). This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", type="regexpfiles", rules="Exclude=R1,R2;ToBeRequired=R1_pattern;RequiredIf?ALL[R1=None]", group="Inputs data by pattern")
        self.add_parameter("exclusion_pattern", "Pattern to exclude files from files retrieved by R1_pattern and R2_pattern. This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", rules="Exclude=R1,R2", group="Inputs data by pattern")

        # Inputs design
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", required=True, group="Inputs design")
        self.add_input_file("intervals", "MSI intervals file (format: TSV). See mSINGS create_intervals script.", required=True, group="Inputs design")
        self.add_input_file("baseline", "Path to the MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.", required=True, group="Inputs design")
        self.add_input_file("models", "Path to the file generated for your analytic process on data generated using the same protocols (format: JSON). This file describes the lengths distribution for each locus for samples tagged as MSI and samples tagged as MSS. See MIAmSLearn.", required=True, group="Inputs design")
        self.add_input_file("genome_seq", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", required=True, file_format="fasta", group="Inputs design")

        # Outputs data
        self.add_parameter("output_dir", "Path to the output folder.", required=True, group="Output data")


    def pre_process(self):
        super().pre_process()

        # Get R1 and R2
        if len(self.R1) == 0 and len(self.R1_pattern) == 0:
            raise argparse.ArgumentTypeError("the following arguments are required: --R1, --R2 or --R1-pattern --R2-pattern")
        if len(self.R1_pattern) != 0:
            self.R1 = sorted(self.R1_pattern)
            self.R2 = sorted(self.R2_pattern)
            if self.exclusion_pattern != None:
                self.R1 = [path for path in self.R1 if not fnmatch.fnmatch(path, self.exclusion_pattern)]
                self.R2 = [path for path in self.R2 if not fnmatch.fnmatch(path, self.exclusion_pattern)]

        # Get samples names
        try:
            self.samples_names = [getLibNameFromReadsPath(str(elt)) for elt in self.R1]
        except:
            self.samples_names = commonSubPathes(self.R1, self.R2, True)


    def process(self):
        # Clean reads
        cleaned_R1 = self.R1
        if self.R1_end_adapter != None:
            clean_R1 = self.add_component("Cutadapt", ["a", self.R1_end_adapter, self.R1, None, 0.1, 11], component_prefix="R1")
            cleaned_R1 = clean_R1.out_R1
        cleaned_R2 = self.R2
        if self.R2_end_adapter != None:
            clean_R2 = self.add_component("Cutadapt", ["a", self.R2_end_adapter, self.R2, None, 0.1, 11], component_prefix="R2")
            cleaned_R2 = clean_R2.out_R1

        # Align reads
        bwa = self.add_component("BWAmem", [self.genome_seq, cleaned_R1, cleaned_R2, self.samples_names])
        idx_aln = self.add_component("BAMIndex", [bwa.aln_files])

        # Call MSI with run_msings.py
        msings = self.add_component("MSINGS", [idx_aln.out_aln, self.targets, self.intervals, self.baseline, self.genome_seq])
        filtered_msings = self.add_component("MSIFilter", kwargs={
            "in_reports": msings.aggreg_report,
            "method_name": "MSINGS",
            "min_distrib_support": self.min_support_reads,
            "consensus_method": self.loci_consensus_method,
            "instability_count": self.instability_count,
            "instability_ratio": self.instability_ratio,
            "min_voting_loci": self.min_voting_loci,
            "undetermined_weight": 0,
            "locus_weight_is_score": False
        })

        # Retrieve size profile for each MSI
        on_targets = self.add_component("BamAreasToFastq", [idx_aln.out_aln, self.targets, self.min_zoi_overlap, True, cleaned_R1, cleaned_R2])
        combine = self.add_component("CombinePairs", [on_targets.out_R1, on_targets.out_R2, None, self.max_mismatch_ratio, self.min_pair_overlap])
        gather = self.add_component("GatherLocusRes", [combine.out_report, self.targets, self.samples_names, self.classifier + "Pairs", "LocusResPairsCombi"])
        classif = self.add_component("MIAmSClassify", kwargs={
            "references_samples": self.models,
            "evaluated_samples": gather.out_report,
            "method_name": self.classifier + "Pairs",
            "classifier": self.classifier,
            "classifier_params": self.classifier_params,
            "min_support_fragments": self.min_support_reads / 2,
            "consensus_method": self.loci_consensus_method,
            "instability_count": self.instability_count,
            "instability_ratio": self.instability_ratio,
            "min_voting_loci": self.min_voting_loci,
            "random_seed": self.random_seed,
            "undetermined_weight": self.undetermined_weight,
            "locus_weight_is_score": self.locus_weight_is_score
        })

        # Report
        self.reports_cmpt = self.add_component("MSIMergeReports", [classif.out_report, filtered_msings.out_report])


    def post_process(self):
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        # User log
        log_file = os.path.join(self.output_dir, self.__class__.__name__ + "_log.txt")
        self.write_log(log_file, __version__)

        # Copy data
        data_folder = os.path.join(self.output_dir, "data")
        if not os.path.exists(data_folder):
            os.mkdir(data_folder)
        for curr_res in self.reports_cmpt.out_report:
            filename = os.path.basename(curr_res)
            shutil.copy(curr_res, os.path.join(data_folder, filename))

        # Copy lib
        wf_src_path = os.path.dirname(os.path.realpath(__file__))
        web_lib_path = os.path.join(wf_src_path, "resources", "lib")
        out_lib = os.path.join(self.output_dir, "lib")
        if os.path.exists(out_lib):
            shutil.rmtree(out_lib)
        shutil.copytree(web_lib_path, out_lib)

        # Get results
        results_by_sample = {}
        for curr_spl, curr_res in zip(self.samples_names, self.reports_cmpt.out_report):
            with open(curr_res) as FH_in:
                results_by_sample[curr_spl] = json.load(FH_in)[0]

        # Write report
        higher_peak_by_locus = getHigherPeakByLocus(self.models, self.min_support_reads)
        template_path = os.path.join(wf_src_path, "resources", "report.html")
        report_path = os.path.join(self.output_dir, "report.html")
        with open(report_path, "w") as FH_output:
            with open(template_path) as FH_template:
                for line in FH_template:
                    if "= ##DATA##" in line:
                        line = line.replace("##DATA##", json.dumps(results_by_sample))
                    elif "= ##MODELS_HIGHER_PEAK##" in line:
                        line = line.replace("##MODELS_HIGHER_PEAK##", json.dumps(higher_peak_by_locus))
                    FH_output.write(line)
