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
__version__ = '0.0.1'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'dev'


from jflow.workflow import Workflow

class MSI (Workflow):
    def get_description(self):
        return "Microsatellites instability detection."

    def define_parameters(self, parameters_section=None):
        # Inputs data
        self.add_input_file_list("R1", "Fastq R1", required=True, group="Inputs data")
        self.add_input_file_list("R2", "Fastq R2", required=True, group="Inputs data")

        self.add_input_file("R1_end_adapter", "Path to sequence file containing the start of Illumina P7 adapter (format: fasta). This sequence is trimmed from the end of R1 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")
        self.add_input_file("R2_end_adapter", "Path to sequence file containing the start of reverse complemented Illumina P5 adapter ((format: fasta). This sequence is trimmed from the end of R2 of the amplicons with a size lower than read length.", file_format="fasta", required=False, group="Cleaning")

        self.add_input_file("bed", "Bed with msi regions", required=True, group="Inputs design")
        self.add_input_file("intervals", "Intervals with msi regions (generated previously)", required=True, group="Inputs design")
        self.add_input_file("baseline", "Baseline of stability", required=True, group="Inputs design")
        self.add_input_file("genome_seq", "Reference genome (fasta)", required=True, file_format="fasta", group="Inputs design")

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
        # lib_names = [spl["Library_Name"] for spl in self.samples]
        bwa = self.add_component("BWAmem", [self.genome_seq, cleaned_R1, cleaned_R2])
        idx_aln = self.add_component("BAMIndex", [bwa.aln_files])

        # Call MSI with run_msings.py
        msings = self.add_component("MSINGS", [idx_aln.out_aln, self.bed, self.intervals, self.baseline, self.genome_seq])
