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
__version__ = '2.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction


class MSIMergeReports (Component):

    def define_parameters(self, first_report, second_report):
        # Inputs files
        self.add_input_file_list("first_report", 'Pathes to the first file to merge (format: JSON). It contains a list of JSON serialisation of anacore.msi.MSISAmple.', default=first_report, required=True)
        self.add_input_file_list("second_report", 'Pathes to the second file to merge (format: JSON). It contains a list of JSON serialisation of anacore.msi.MSISAmple.', default=second_report, required=True)

        # Outputs files
        self.add_output_file_list("out_report", 'Pathes to the merged reports (format: JSON).', pattern='{basename_woext}.json', items=self.first_report)
        self.add_output_file_list("stderr", 'Pathes to the stderr files (format: txt).', pattern='{basename_woext}.stderr', items=self.first_report)

    def process(self):
        cmd = self.get_exec_path("MSIMergeReports.py") + \
            " --inputs-reports $1 $2" + \
            " --output-report $3" + \
            " 2> $4"
        merges_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(
            merges_fct,
            inputs=[self.first_report, self.second_report],
            outputs=[self.out_report, self.stderr]
        )
