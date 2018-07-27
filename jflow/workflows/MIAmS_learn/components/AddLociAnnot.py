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
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction


class AddLociAnnot (Component):

    def define_parameters(self, msi_files, annotations_file):
        # Input Files
        self.add_input_file_list("msi_files", "**********************.", default=msi_files, required=True)
        self.add_input_file("annotations_file", "**************.", default=info_file, required=True)

        # Output Files
        self.add_output_file_list("out_report", "**********************.", pattern='{basename_woext}.json', items=self.msi_files)
        self.add_output_file_list("stderr", "Pathes to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=self.msi_files)

    def process(self):
        cmd = self.get_exec_path("addLociAnnotations.py") + \
            " --input-loci-annot " + self.annotations_file + \
            " --input-report $1 " + \
            " --output-report $2" + \
            " 2> $3"
        add_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        MultiMap(
            add_fct,
            inputs=[self.annotations_file, self.msi_files],
            outputs=[self.out_report, self.stderr],
            includes=self.info_file
        )
