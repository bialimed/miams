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
import shutil
import fnmatch
import argparse
import subprocess

from workflows.src.miamsWorkflows import MIAmSWf

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "lib")
sys.path.insert(0, LIB_DIR)

from anacore.msiannot import MSIAnnot


class MIAmSLearn (MIAmSWf):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lib_dir = LIB_DIR

    def get_description(self):
        return "Build distribution model for stable microsatellites used as reference for MIAmS Tag workflow."

    def define_parameters(self, parameters_section=None):
        self.add_parameter("min_support_reads", "Minimum number of reads in size distribution to keep the locus result of a sample in reference distributions.", default=400, type=int)

        # Combine reads method
        self.add_parameter("max_mismatch_ratio", "Maximum allowed ratio between the number of mismatched base pairs and the overlap length. Two reads will not be combined with a given overlap if that overlap results in a mismatched base density higher than this value.", default=0.25, type=float, group="Combine reads method")
        self.add_parameter("min_pair_overlap", "The minimum required overlap length between two reads in pair to provide a confident overlap.", default=20, type=int, group="Combine reads method")
        self.add_parameter("min_zoi_overlap", "A reads pair is selected for combine method only if this number of nucleotides of the target are covered by the each read.", default=12, type=int, group="Combine reads method")

        # Cleaning
        self.add_input_file("R1_end_adapter", "Path to sequence file containing the start of Illumina P7 adapter (format: fasta). This sequence is trimmed from the end of R1 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        self.add_input_file("R2_end_adapter", "Path to sequence file containing the start of reverse complemented Illumina P5 adapter ((format: fasta). This sequence is trimmed from the end of R2 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")

        # Inputs data
        self.add_input_file("annotations", 'Path to the file containing for each sample the status for each locus (format: TSV). The title line must contain "sample<tab>loci_1_name...<tab>loci_n_name". Each row defined one sample with the format: "spl_name<tab>loci_1_status<tab>...<tab>loci_n_status<tab>". The status must be "MSS", "MSI" or "Undetermined".', required=True, group="Inputs data")
        self.add_input_file_list("R1", "Pathes to R1 (format: fastq).", rules="Exclude=R1_pattern,R2_pattern,exclusion_pattern;ToBeRequired=R2;RequiredIf?ALL[R1_pattern=None]", group="Inputs data")
        self.add_input_file_list("R2", "Pathes to R2 (format: fastq).", rules="Exclude=R1_pattern,R2_pattern,exclusion_pattern;ToBeRequired=R1;RequiredIf?ALL[R1_pattern=None]", group="Inputs data")
        self.add_input_file_list("R1_pattern", "Pattern to find R1 files (format: fastq). This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", type="regexpfiles", rules="Exclude=R1,R2;ToBeRequired=R2_pattern;RequiredIf?ALL[R1=None]", group="Inputs data by pattern")
        self.add_input_file_list("R2_pattern", "Pattern to find R2 files (format: fastq). This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", type="regexpfiles", rules="Exclude=R1,R2;ToBeRequired=R1_pattern;RequiredIf?ALL[R1=None]", group="Inputs data by pattern")
        self.add_parameter("exclusion_pattern", "Pattern to exclude files from files retrieved by R1_pattern and R2_pattern. This pattern use Unix shell-style wildcards (see https://docs.python.org/3/library/fnmatch.html).", rules="Exclude=R1,R2", group="Inputs data by pattern")

        # Inputs design
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", required=True, group="Inputs design")
        self.add_input_file("intervals", "MSI intervals file (format: TSV). See mSINGS create_intervals script.", required=True, group="Inputs design")
        self.add_input_file("genome_seq", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", required=True, file_format="fasta", group="Inputs design")

        # Outputs data
        self.add_parameter("output_baseline", "Path to the mSINGS model file (format: TSV).", required=True, group="Output data")
        self.add_parameter("output_training", "Path to the training samples file (format: JSON).", required=True, group="Output data")
        self.add_parameter("output_log", "Path to the log file (format: txt).", required=True, group="Output data")

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

        # Convert targets status to MSIAnnot
        self.converted_annotations = os.path.join(self.directory, "loci_annotations.tsv")
        converter_path = os.path.join(CURRENT_DIR, "bin", "statusToAnnot.py")
        subprocess.check_call([
            converter_path,
            "--logging-level", "ERROR",
            "--input-targets", self.targets,
            "--input-status", self.annotations,
            "--output-annotations", self.converted_annotations
        ])

        # Get status by sample
        unordered_spl_names = list()
        self.with_MSS = dict()
        for record in MSIAnnot(self.converted_annotations):
            if record["key"] == "status":
                spl_name = record["sample"]
                unordered_spl_names.append(spl_name)
                if record["value"] == "MSS":
                    self.with_MSS[spl_name] = 1

        # Sort samples names by R1 and R2 order
        self.samples_names = list()
        for curr_R1, curr_R2 in zip(self.R1, self.R2):
            selected_name = ""
            selected_idx = None
            for searched_idx, searched_spl in enumerate(unordered_spl_names):
                if(os.path.basename(curr_R1).startswith(searched_spl) and os.path.basename(curr_R2).startswith(searched_spl)) and len(selected_name) < len(searched_spl):
                    selected_name = searched_spl
                    selected_idx = searched_idx
            if selected_name == "":
                raise Exception(
                    'The annotation for the sample corresponding to the fastq "{}" and "{}" cannot be found in annotation file {}.'.format(
                        os.path.basename(curr_R1), os.path.basename(curr_R2), self.annotations
                    )
                )
            self.samples_names.append(selected_name)
            del(unordered_spl_names[selected_idx])

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

        # Create baseline for mSINGS with create_baseline.py
        MSS_aln = [idx_aln.out_aln[spl_idx] for spl_idx, spl_name in enumerate(self.samples_names) if spl_name in self.with_MSS]
        self.baseline_cmpt = self.add_component("MSINGSBaseline", [MSS_aln, self.targets, self.intervals, self.genome_seq, self.converted_annotations])

        # Create models from pairs combination
        on_targets = self.add_component("BamAreasToFastq", [idx_aln.out_aln, self.targets, self.min_zoi_overlap, True, cleaned_R1, cleaned_R2])
        combine = self.add_component("CombinePairs", [on_targets.out_R1, on_targets.out_R2, None, self.max_mismatch_ratio, self.min_pair_overlap])
        gather_locus = self.add_component("GatherLocusRes", [combine.out_report, self.targets, self.samples_names, "model", "LocusResPairsCombi"])
        self.training_cmpt = self.add_component("CreateMSIRef", [gather_locus.out_report, self.targets, self.converted_annotations, self.min_support_reads/2])

    def post_process(self):
        self.write_log(self.output_log, __version__)
        shutil.copy(self.baseline_cmpt.baseline, self.output_baseline)
        shutil.copy(self.training_cmpt.out_references, self.output_training)
