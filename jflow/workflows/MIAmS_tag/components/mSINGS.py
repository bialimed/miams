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
__license__ = 'GNU General Public License'
__version__ = '1.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction


class MSINGS (Component):

    def define_parameters(self, aln, targets, intervals, baseline, genome, multiplier=2.0, msi_min_threshold=0.60, msi_max_threshold=0.60, java_mem=4):
        # Parameters
        self.add_parameter("multiplier", "The number of standard deviations from the baseline that is required to call instability.", default=multiplier, type=float)
        self.add_parameter("msi_min_threshold", "The maximum fraction of unstable sites allowed to call a specimen MSI negative.", default=msi_min_threshold, type=float)
        self.add_parameter("msi_max_threshold", "The minimum fraction of unstable sites allowed to call a specimen MSI positive.", default=msi_max_threshold, type=float)
        self.add_parameter("java_mem", "", default=java_mem, type=int)

        # Input Files
        self.add_input_file_list("aln", "Pathes to alignment files for the samples to evaluate (format: BAM). These BAM must be ordered by coordinates and indexed.", default=aln, required=True)
        self.add_input_file("baseline", "Path to the MSI baseline file generated for your analytic process on data generated using the same protocols (format: TSV). This file describes the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors). See mSINGS create_baseline script.", default=baseline, required=True)
        self.add_input_file("genome", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", default=genome, required=True)
        self.add_input_file("intervals", "Path to the MSI intervals file (format: TSV). See mSINGS create_intervals script.", default=intervals, required=True)
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", default=targets, required=True)

        # Output Files
        self.add_output_file_list("report", "Pathes to the output files containing status for the sample and the evaluated loci (format: TSV).", pattern='{basename_woext}_report.txt', items=self.aln)
        self.add_output_file_list("analysis", "Pathes to the output files containing the profiles of evaluated loci (format: TSV).", pattern='{basename_woext}_analysis.txt', items=self.aln)
        self.add_output_file_list("aggreg_report", "Pathes to the output files containing status for the sample and the evaluated loci and the data used (format: JSON).", pattern='{basename_woext}_report.json', items=self.aln)
        self.add_output_file_list("msings_stderr", "Pathes to the stderr files of mSINGS (format: txt).", pattern='{basename_woext}_msings.stderr', items=self.aln)
        self.add_output_file_list("rename_stderr", "Pathes to the stderr files of the rename step (format: txt).", pattern='{basename_woext}_rename.stderr', items=self.aln)
        self.add_output_file_list("aggreg_stderr", "Pathes to the stderr files of the aggregation step (format: txt).", pattern='{basename_woext}_aggreg.stderr', items=self.aln)

    def process(self):
        tmp_report = [curr_path + ".tmp" for curr_path in self.report]

        # Process mSINGS
        cmd = self.get_exec_path("msings_venv") + " " + self.get_exec_path("run_msings.py") + \
            " --java-path " + self.get_exec_path("java") + \
            " --java-mem " + str(self.java_mem) + \
            " --multiplier " + str(self.multiplier) + \
            " --msi-min-threshold " + str(self.msi_min_threshold) + \
            " --msi-max-threshold " + str(self.msi_max_threshold) + \
            " --input-baseline " + self.baseline + \
            " --input-genome " + self.genome + \
            " --input-intervals " + self.intervals + \
            " --input-targets " + self.targets + \
            " --input-aln $1 " + \
            " --output-analyzer $2 " + \
            " --output-report $3 " + \
            " 2> $4"
        msings_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(msings_fct, inputs=[self.aln], outputs=[self.analysis, tmp_report, self.msings_stderr], includes=[self.genome, self.intervals, self.baseline, self.targets])

        # Remove suffix in samples names
        cmd = self.get_exec_path("sed") + \
            " -e 's/_analysis//'" + \
            " $1" + \
            " > $2" + \
            " 2> $3"
        rename_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(rename_fct, inputs=[tmp_report], outputs=[self.report, self.rename_stderr])

        # Aggregate report and analysis
        cmd = self.get_exec_path("mSINGSToReport.py") + \
            " --input-report $1 " + \
            " --input-analysis $2 " + \
            " --output $3 " + \
            " 2> $4"
        convert_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(convert_fct, inputs=[self.report, self.analysis], outputs=[self.aggreg_report, self.aggreg_stderr])
