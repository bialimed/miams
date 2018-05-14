#!/usr/bin/env python3
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
__version__ = '1.0.1'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import json
import argparse
from anacore.msings import CountMSI
from anacore.sv import HashedSVIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def process(args):
    """
    @summary: Merge metrics from msings and pairs combination by locus.
    @param args: [Namespace] The namespace extracted from the script arguments.
    """
    final_metrics = {
        "loci": {},
        "sample": {}
    }
    # Parse lengths metrics by loci
    with HashedSVIO(args.input_combined_list) as FH_loci_list:
        for record in FH_loci_list:
            with open(record["Filepath"]) as FH_locus:
                locus_metrics = json.load(FH_locus)
                final_metrics["loci"][record["Locus"]] = {
                    "name": record["Target"],
                    "position": record["Locus"],
                    "pairs_combination": {
                        "nb_by_lengths": locus_metrics["nb_by_lengths"],
                        "nb_pairs": locus_metrics["nb_combined_pairs"]
                    },
                    "nb_pairs": locus_metrics["nb_uncombined_pairs"] + locus_metrics["nb_combined_pairs"]
                }
    # Parse status metrics
    msings_report = CountMSI(args.input_msings_result)
    if len(msings_report.samples) != 1:
        raise Exception("Only one sample must be reported in {}.".format(args.input_msings_result))
    spl_name = list(msings_report.samples.keys())[0]
    msings_spl = msings_report.samples[spl_name]
    for curr_locus in final_metrics["loci"]:  # Add status unknown on loci without reads in msings_report (mSINGS does not write line in his report for this locus)
        if curr_locus not in msings_spl.loci:
            msings_spl.loci[curr_locus] = None
    if len(msings_report.loci) != len(final_metrics["loci"]):
        raise Exception('The number of loci in "{}" and in "{}" are inconsistent.'.format(args.input_msings_result, args.input_combined_list))
    final_metrics["sample"] = {
        "name": msings_spl.name,
        "score": msings_spl.score,
        "is_stable": msings_spl.is_stable
    }
    for locus_pos, is_stable in msings_spl.loci.items():
        final_metrics["loci"][locus_pos]["is_stable"] = is_stable
    # Write metrics
    with open(args.output_report, "w") as FH_out:
        json.dump(final_metrics, FH_out, sort_keys=True)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Merge metrics from msings and pairs combination by locus.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-c', '--input-combined-list', required=True, help='The path to the file containing the list of combination report path by locus (format: TSV).')
    group_input.add_argument('-m', '--input-msings-result', required=True, help='The path to the file containing status for the sample and the evaluated loci (format: TSV). This file is outputted by command "msi count_msi_samples" of mSINGS.')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the merged report (format: JSON).')
    args = parser.parse_args()

    # Process
    process(args)
