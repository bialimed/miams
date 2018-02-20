#
# Copyright (C) 2017 IUCT-O
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
__copyright__ = 'Copyright (C) 2017 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '0.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'dev'


from jflow.workflow import Workflow

class MSI (Workflow):
    def get_description(self):
        return "Microsatellites instability detection."

    def define_parameters(self, parameters_section=None):
        # Inputs data
        self.add_input_file_list("R1", "Pathes to R1 (format: fastq).", required=True, group="Inputs data")
        self.add_input_file_list("R2", "Pathes to R2 (format: fastq).", required=True, group="Inputs data")

        # Cleaning
        self.add_input_file("R1_end_adapter", "Path to sequence file containing the start of Illumina P7 adapter (format: fasta). This sequence is trimmed from the end of R1 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        self.add_input_file("R2_end_adapter", "Path to sequence file containing the start of reverse complemented Illumina P5 adapter ((format: fasta). This sequence is trimmed from the end of R2 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        # Inputs design
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", required=True, group="Inputs design")
        self.add_input_file("intervals", "MSI intervals file (format: TSV). See mSINGS create_intervals script.", required=True, group="Inputs design")
        self.add_input_file("baseline", "Path to the MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.", required=True, group="Inputs design")
        self.add_input_file("genome_seq", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", required=True, file_format="fasta", group="Inputs design")

        # Parameters
        # Modify script/run_msings to edit parameters (multiplier, min threshold, max threshold)

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
        bwa = self.add_component("BWAmem", [self.genome_seq, cleaned_R1, cleaned_R2])
        idx_aln = self.add_component("BAMIndex", [bwa.aln_files])

        # Call MSI with run_msings.py
        msings = self.add_component("MSINGS", [idx_aln.out_aln, self.targets, self.intervals, self.baseline, self.genome_seq])
