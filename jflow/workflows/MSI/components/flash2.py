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
__status__ = 'dev'

import os
from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction
from weaver.function import PythonFunction


def writeReport(combined, uncombined_R1, out_report):
    """
    @summary: Writes report file for combination results.
    @param combined: [str] Path to the file containing the combined reads (format: fastq).
    @param uncombined_R1: [str] Path to the file containing the uncombined R1 (format: fastq).
    @param out_report: [str] Path to the outputted report file (format: json).
    """
    import json
    from anacore.lib.sequenceIO import FastqIO
    report = {
        "nb_combined_pairs": 0,
        "nb_uncombined_pairs": 0,
        "nb_by_lengths": dict()
    }
    # Get nb combined and lengths distribution
    with FastqIO(combined) as FH_comb:
        for record in FH_comb:
            report["nb_combined_pairs"] += 1
            curr_len = len(record.string)
            if curr_len not in report["nb_by_lengths"]:
                report["nb_by_lengths"][curr_len] = 1
            else:
                report["nb_by_lengths"][curr_len] += 1
    # Get nb uncombined
    with FastqIO(uncombined_R1) as FH_not_comb:
        for record in FH_not_comb:
            report["nb_uncombined_pairs"] += 1
    # Write report
    with open(out_report, "w") as FH_report:
        json.dump(report, FH_report, sort_keys=True)


class Flash2 (Component):

    def define_parameters(self, R1, R2, names=None, mismatch_ratio=0.25, min_overlap=20, max_overlap=None, phred_offset=33, nb_threads=1):
        # Parameters
        self.add_parameter("max_overlap", 'Maximum overlap length expected in approximately 90% of read pairs.', default=max_overlap, type=int)
        self.add_parameter("min_overlap", "The minimum required overlap length between two reads to provide a confident overlap.", default=min_overlap, type=int)
        self.add_parameter("mismatch_ratio", "Maximum allowed ratio between the number of mismatched base pairs and the overlap length. Two reads will not be combined with a given overlap if that overlap results in a mismatched base density higher than this value.", default=mismatch_ratio, type=float)
        self.add_parameter("nb_threads", "Set the number of worker threads", default=nb_threads, type=int)
        self.add_parameter("phred_offset", "phred_offset", default=phred_offset, type=int)
        self.add_parameter_list("names", "", default=names)
        if len(self.names) == 0:
            self.prefixes = self.get_outputs('{basename_woext}', [R1, R2])
        else:
            self.prefixes = self.get_outputs('{basename_woext}', names)

        # Inputs files
        self.add_input_file_list("R1", "fastq read R1", default=R1, required=True)
        self.add_input_file_list("R2", "fastq read R2", default=R2, required=True)

        # Outputs files
        self.add_output_file_list("out_histogram", "", pattern='{basename_woext}.histogram', items=self.prefixes)
        self.add_output_file_list("out_hist", "", pattern='{basename_woext}.hist', items=self.prefixes)
        self.add_output_file_list("out_report", "", pattern='{basename_woext}_report.json', items=self.prefixes)
        self.add_output_file_list("out_combined", "", pattern='{basename_woext}.extendedFrags.fastq.gz', items=self.prefixes, file_format='fastq')
        self.add_output_file_list("out_not_combined_R1", "", pattern='{basename_woext}.notCombined_1.fastq.gz', items=self.prefixes, file_format='fastq')
        self.add_output_file_list("out_not_combined_R2", "", pattern='{basename_woext}.notCombined_2.fastq.gz', items=self.prefixes, file_format='fastq')
        self.add_output_file_list("stderr", "", pattern='{basename_woext}.stderr', items=self.prefixes)


    def process(self):
        # Combine reads
        for idx, curr_prefix in enumerate(self.prefixes):
            flash2 = ShellFunction(
                self.get_exec_path("flash2") +
                " --compress " +
                " --threads " + str(self.nb_threads) +
                " --min-overlap " + str(self.min_overlap) +
                ("" if self.min_overlap == None else " --min-overlap " + str(self.min_overlap)) +
                " --max-mismatch-density " + str(self.mismatch_ratio) +
                " --phred-offset " + str(self.phred_offset) +
                " --output-prefix " + os.path.basename(curr_prefix) +
                " --output-directory " + self.output_directory +
                " $1 " +
                " $2 " +
                " 2> $3",
                cmd_format='{EXE} {IN} {OUT}'
            )
            flash2(
                inputs=[self.R1[idx], self.R2[idx]],
                outputs=[self.stderr[idx], self.out_hist[idx], self.out_combined[idx], self.out_histogram[idx], self.out_not_combined_R1[idx], self.out_not_combined_R2[idx]]
            )
        # Write report
        report_fct = PythonFunction(writeReport, cmd_format="{EXE} {IN} {OUT}")
        MultiMap(report_fct, inputs=[self.out_combined, self.out_not_combined_R1], outputs=[self.out_report])
