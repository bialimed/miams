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


class MIAmSClassify (Component):

    def define_parameters(self, references_samples, evaluated_samples, method_name="MIAmS_combi", random_seed=None, min_voting_loci=3, min_support_fragments=150, consensus_method="ratio", instability_ratio=0.2, instability_count=3, undetermined_weight=0.5):
        # Parameters
        self.add_parameter("consensus_method", "Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable.", choices=['count', 'majority', 'ratio'], default=consensus_method)
        self.add_parameter("instability_count", "[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable.", default=instability_count, type=int)
        self.add_parameter("instability_ratio", "[Only with consensus-method = ratio] If the ratio of unstable/determined loci is upper or equal than this value the sample will be unstable otherwise it will be stable.", default=instability_ratio, type=float)
        self.add_parameter("method_name", "The name of the method storing locus metrics and where the status will be set.", default=method_name)
        self.add_parameter("min_support_fragments", "The minimum numbers of fragment (reads pairs) for determine the status.", default=min_support_fragments, type=int)
        self.add_parameter("min_voting_loci", "Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined.", default=min_voting_loci, type=int)
        self.add_parameter("random_seed", "The seed used by the random number generator in the classifier.", default=random_seed, type=int)
        self.add_parameter("undetermined_weight", "The weight of the undetermined loci in sample score calculation.", default=undetermined_weight, type=float)

        # Input Files
        self.add_input_file_list("evaluated_samples", "Pathes to the files containing the samples with loci to classify (format: MSIReport).", default=evaluated_samples, required=True)
        self.add_input_file("references_samples", "Path to the file containing the references samples used in learn step (format: MSIReport).", default=references_samples, required=True)

        # Output Files
        self.add_output_file_list("out_report", "Pathes to the output files (format: MSIReport).", pattern='{basename_woext}.json', items=self.evaluated_samples)
        self.add_output_file_list("stderr", "Pathes to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=self.evaluated_samples)

    def process(self):
        cmd = self.get_exec_path("miamsClassify.py") + \
            ("" if self.random_seed == None else " --random-seed " + str(self.random_seed)) + \
            " --consensus-method " + str(self.consensus_method) + \
            " --method-name " + str(self.method_name) + \
            " --min-voting-loci " + str(self.min_voting_loci) + \
            " --min-support-fragments " + str(self.min_support_fragments) + \
            " --undetermined-weight " + str(self.undetermined_weight) + \
            (" --instability-ratio " + str(self.instability_ratio) if self.consensus_method == "ratio" else "") + \
            (" --instability-count " + str(self.instability_count) if self.consensus_method == "count" else "") + \
            " --input-references " + self.references_samples + \
            " --input-evaluated $1 " + \
            " --output-report $2 " + \
            " 2> $3"
        classifier_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(classifier_fct, inputs=[self.evaluated_samples], outputs=[self.out_report, self.stderr], includes=[self.references_samples])
