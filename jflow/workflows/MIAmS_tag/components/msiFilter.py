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

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction


class MSIFilter (Component):

    def define_parameters(self, in_reports, method_name, min_voting_loci=3, min_distrib_support=100, consensus_method="ratio", instability_ratio=0.2, instability_count=3, undetermined_weight=0.5):
        # Parameters
        self.add_parameter("consensus_method", "Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/stable loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable.", choices=['count', 'majority', 'ratio'], default=consensus_method)
        self.add_parameter("instability_count", "[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable.", default=instability_count, type=int)
        self.add_parameter("instability_ratio", "[Only with consensus-method = ratio] If the ratio of unstable/determined loci is upper or equal than this value the sample will be unstable otherwise it will be stable.", default=instability_ratio, type=float)
        self.add_parameter("method_name", "The name of the method storing locus metrics and where the status will be set.", default=method_name)
        self.add_parameter("min_distrib_support", "The minimum numbers of reads (mSINGS) or reads pairs (classifiers based on pairs) to determine a locus status.", default=min_distrib_support, type=int)
        self.add_parameter("min_voting_loci", "The minimum numbers of loci to determine a sample status.", default=min_voting_loci, type=int)
        self.add_parameter("undetermined_weight", "The weight of the undetermined loci in sample score calculation.", default=undetermined_weight, type=float)

        # Inputs files
        self.add_input_file_list("in_reports", 'The path to the input file containing samples reports (format: MSIReport).', default=in_reports, required=True)

        # Outputs files
        self.add_output_file_list("out_report", 'Pathes to the merged reports (format: JSON).', pattern='{basename_woext}.json', items=self.in_reports)
        self.add_output_file_list("stderr", 'Pathes to the stderr files (format: txt).', pattern='{basename_woext}.stderr', items=self.in_reports)

    def process(self):
        cmd = self.get_exec_path("msiFilter.py") + \
            " --consensus-method " + str(self.consensus_method) + \
            " --method-name " + str(self.method_name) + \
            " --min-voting-loci " + str(self.min_voting_loci) + \
            " --min-distrib-support " + str(self.min_distrib_support) + \
            " --undetermined-weight " + str(self.undetermined_weight) + \
            (" --instability-ratio " + str(self.instability_ratio) if self.consensus_method == "ratio" else "") + \
            (" --instability-count " + str(self.instability_count) if self.consensus_method == "count" else "") + \
            " --input-reports $1" + \
            " --output-reports $2" + \
            " 2> $3"
        filter_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(
            filter_fct,
            inputs=[self.in_reports],
            outputs=[self.out_report, self.stderr]
        )
