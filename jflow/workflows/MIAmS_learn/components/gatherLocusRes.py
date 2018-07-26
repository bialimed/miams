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

import os
from jflow.component import Component
from weaver.function import ShellFunction
from anacore.bed import getAreas


def two_dim_stack(elts, nb_col):
    """
    @summary: Returns 2D array from a 1D array. Each row contains nb_col columns.
    @param elts: [list] The 1D array to process.
    @param nb_col: [int] Number of columns in each rows of the 2D array.
    @return: [list] The 2D array.
    """
    two_dim = list()
    for elt_idx, curr_elt in enumerate(elts):
        col_idx = elt_idx % nb_col
        if col_idx == 0:
            two_dim.append([curr_elt])
        else:
            two_dim[-1].append(curr_elt)
    return two_dim


class GatherLocusRes (Component):

    def define_parameters(self, loci_reports, targets_design, samples_names, result_method, result_class_name="LocusResDistrib"):
        # Parameters
        self.add_parameter("result_method", "The name of the method storing locus metrics in LocusRes.", default=result_method)
        self.add_parameter("result_class_name", "The class used to store LocusRes.", choices=["LocusRes", "LocusResDistrib", "LocusResPairsCombi"], default=result_class_name)
        self.add_parameter_list("samples_names", "The samples names.", default=samples_names)

        # Inputs files
        self.add_input_file_list("loci_reports", 'Pathes to the file containing locus results (format: JSON). Each file contains the results for one locus of one sample. The list is ordered firstly by sample secondly by locus (locus are ordered by targets_design order).', default=loci_reports, required=True)
        self.add_input_file("targets_design", 'Path to the file containing targets positions and names (format: BED).', default=targets_design, required=True)

        # Outputs files
        self.add_output_file_list("out_report", 'Pathes to the output reports (format: MSIReport). One report by sample.', pattern='{basename}_report.json', items=self.samples_names)
        self.add_output_file_list("stderr", 'Pathes to the stderr files (format: txt).', pattern='{basename}.stderr', items=self.samples_names)


    def process(self):
        # Create combined lists
        targets = getAreas(self.targets_design)
        loci_reports_list_in_spl = list()
        reports_in_spl = two_dim_stack(self.loci_reports, len(targets))
        for spl_idx, reports in enumerate(reports_in_spl):
            list_filepath = os.path.join(self.output_directory, "spl_{}_comb_reports_list.tsv".format(spl_idx))
            loci_reports_list_in_spl.append(list_filepath)
            with open(list_filepath, "w") as FH_out:
                FH_out.write("#Locus_position\tLocus_name\tFilepath\n")
                for target_idx, curr_report in enumerate(reports):
                    target_id = "{}:{}-{}".format(targets[target_idx].chrom, targets[target_idx].start - 1, targets[target_idx].end)
                    FH_out.write(
                        "{}\t{}\t{}\n".format(target_id, targets[target_idx].name, curr_report)
                    )
        # Set commands
        cmd = self.get_exec_path("gatherLocusRes.py") + \
            " --method-name '{}'".format(self.result_method) + \
            " --method-class-name '{}'".format(self.result_class_name) + \
            " --result-keys 'nb_by_length=nb_by_length'" + \
            " --input-loci-metrics-list $1" + \
            " --output-report $2 " + \
            " 2> $3"
        report_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        for spl_idx, spl_name in enumerate(self.samples_names):
            report_fct(
                inputs=[loci_reports_list_in_spl[spl_idx]],
                outputs=[self.out_report[spl_idx], self.stderr[spl_idx]],
                includes=[reports_in_spl[spl_idx]]
            )
