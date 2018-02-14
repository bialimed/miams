#
# Copyright (C) 2018 
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
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'c-vangoethem@chu-montpellier.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap

from weaver.function import ShellFunction



class MSINGS (Component):

    def define_parameters(self, bam, bed, intervals, baseline, ref_genome, multiplier=2.0, msi_min_threshold=0.60, msi_max_threshold=0.60, java_mem=4):
        # Parameters
        self.add_parameter("multiplier", "", default=multiplier, type=float)
        self.add_parameter("msi_min_threshold", "", default=msi_min_threshold, type=float)
        self.add_parameter("msi_max_threshold", "", default=msi_max_threshold, type=float)
        self.add_parameter("java_mem", "", default=java_mem, type=int)

        # Input Files
        self.add_input_file_list("bam", "Path to the bam files (format: bam).", default=bam, required=True)
        self.add_input_file("bed", "Path to the bed file (format: bed).", default=bed, required=True)
        self.add_input_file("intervals", "Path to the intervals file (format: intervals).", default=intervals, required=True)
        self.add_input_file("baseline", "Path to the baseline file (format: tsv).", default=baseline, required=True)
        self.add_input_file("ref_genome", "Path to the ref_genome file (format: fasta).", default=ref_genome, required=True)

        # Output Files
        self.add_output_file_list("report", "report msi", pattern='{basename_woext}_report.txt', items=self.bam)
        self.add_output_file_list("analyzer", "msi analyzer output", pattern='{basename_woext}_analyzer.txt', items=self.bam)
        self.add_output_file_list("stderr", "Path to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=self.bam)

    def process(self):
        cmd = self.get_exec_path("run_msings") + \
            " -a $1 " + \
            " -b " + self.baseline + \
            " -g " + self.ref_genome + \
            " -i " + self.intervals + \
            " -t " + self.bed + \
            " -oa $2 " + \
            " -or $3 " + \
            " -m " + str(self.java_mem) + \
            " --multiplier " + str(self.multiplier) + \
            " --msi-min-threshold " + str(self.msi_min_threshold) + \
            " --msi-max-threshold " + str(self.msi_max_threshold) + \
            " 2> $4"
        msings_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(msings_fct, inputs=[self.bam],
            outputs=[self.analyzer, self.report, self.stderr], includes=[self.ref_genome, self.intervals, self.baseline, self.bed])
