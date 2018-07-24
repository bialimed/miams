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

import os
from jflow.component import Component
from weaver.function import PythonFunction


def createMSIRef_wrapper(exec_path, min_support_fragments, in_report_list, in_targets, in_annot, out_references, out_info, out_stderr):
    """This wrapper is used to prevent the limit of command line length."""
    import subprocess
    # Init command
    cmd = [
        exec_path,
        "--min-support-fragments", min_support_fragments,
        "--output-references", out_references,
        "--output-info", out_info,
        "--input-targets", in_targets,
        "--input-locus-annot", in_annot,
        "--inputs-reports"
    ]
    # Add list of reports
    in_reports = []
    with open(in_report_list) as FH_in:
        for line in FH_in:
            in_reports.append(line.strip())
    cmd.extend(in_reports)
    # Submit
    str_cmd = " ".join([str(elt) for elt in cmd])
    subprocess.check_call(str_cmd + " 2> " + out_stderr, shell=True)


class CreateMSIRef (Component):

    def define_parameters(self, msi_reports, msi_targets, expected_status, min_support_fragments=200):
        # Parameters
        self.add_parameter("min_support_fragments", "Minimum number of fragment in size distribution to keep the locus result of a sample in reference distributions.", default=min_support_fragments, type=int)

        # Input Files
        self.add_input_file_list("msi_reports", "Pathes to the MSIReport files evaluated in references creation process (format: JSON).", default=msi_reports, required=True)
        self.add_input_file("msi_targets", "Locations of the microsatellite of interest (format: BED).", default=msi_targets, required=True)
        self.add_input_file("expected_status", 'Path to the MSIAnnot file containing for each sample for each targeted locus the stability status (format: TSV). First line must be: sample<tab>locus_position<tab>method_id<tab>key<tab>value<tab>type. The method_id should be "model" and an example of line content is: H2291-1_S15<tab>4:55598140-55598290<tab>model<tab>status<tab>MSS<tab>str', default=expected_status, required=True)

        # Output Files
        self.add_output_file("out_references", "Path to the MSIReport containing the references distribution for each locus (format: JSON).", filename='msiRef_references.json')
        self.add_output_file("out_info", "Path to the file describing the number of references by status for each locus (format: TSV).", filename='msiRef_info.tsv')
        self.add_output_file("stderr", "Pathes to the stderr files (format: txt).", filename='msiRef.stderr')

    def process(self):
        # List the input files
        msi_reports_list = os.path.join(self.output_directory, "msi_reports_list.txt")
        with open(msi_reports_list, "w") as FH_list:
            for curr_path in self.msi_reports:
                FH_list.write(curr_path + "\n")
        # Submit
        cmd = "{EXE}" + \
            " " + self.get_exec_path("createMSIRef.py") + \
            " " + str(self.min_support_fragments) + \
            " {IN}" + \
            " {OUT}"
        add_fct = PythonFunction(
            createMSIRef_wrapper,
            cmd_format=cmd
        )
        add_fct(
            inputs=[msi_reports_list, self.msi_targets, self.expected_status],
            outputs=[self.out_references, self.out_info, self.stderr],
            includes=[self.msi_reports]
        )
