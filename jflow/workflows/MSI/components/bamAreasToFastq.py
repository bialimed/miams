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
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap

from weaver.function import ShellFunction


class BamAreasToFastq (Component):

    def define_parameters(self, aln, targets, min_overlap=20):
        # Parameters
        self.add_parameter("min_overlap", "A reads pair is selected only if this number of nucleotides of the target are covered by the each read.", default=min_overlap, type=int)

        # Input Files
        self.add_input_file_list("aln", "Pathes to alignment files (format: BAM).", default=aln, required=True)
        self.add_input_file("targets", "The locations of areas to extract (format: BED).", default=targets, required=True)

        # Output Files
        self.add_output_file_list("out_R1", "Pathes to the outputted R1 file (format: fastq).", pattern='{basename_woext}_R1.fastq.gz', items=self.aln)
        self.add_output_file_list("out_R2", "Pathes to the outputted R2 file (format: fastq).", pattern='{basename_woext}_R2.fastq.gz', items=self.aln)
        self.add_output_file_list("stderr", "Pathes to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=self.aln)

    def process(self):
        cmd = self.get_exec_path("bamAreasToFastq.py") + \
            " --min-overlap " + str(self.min_overlap) + \
            " --input-targets " + self.targets + \
            " --input-aln $1 " + \
            " --output-R1 $2 " + \
            " --output-R2 $3 " + \
            " 2> $4"
        bam2fastq_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(bam2fastq_fct, inputs=[self.aln], outputs=[self.out_R1, self.out_R2, self.stderr], includes=[self.targets])
