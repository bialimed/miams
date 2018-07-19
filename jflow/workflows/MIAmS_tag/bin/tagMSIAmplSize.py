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
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import json
import argparse
from anacore.msi import Status, MSILocus, MSISample, PairsCombiProcessor, MSIReport
from anacore.sv import HashedSVIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def process(args):
    """
    Tag stability for loci and sample from length distribution on loci.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    spl_name = args.sample_name
    if args.sample_name is None:
        spl_name = os.path.basename(args.output_report).split(".")[0]
        if spl_name.endswith("_report"):
            spl_name = spl_name[:-7]
    msi_spl = MSISample(spl_name)
    # Parse lengths metrics by loci
    with HashedSVIO(args.input_combined_list) as FH_loci_list:
        for record in FH_loci_list:
            with open(record["Filepath"]) as FH_locus:
                locus_metrics = json.load(FH_locus)
            msi_locus = MSILocus.fromDict({
                "name": record["Locus_name"],
                "position": record["Locus_position"],
                "results": {
                    "PairsCombi": {
                        "_class": "LocusResPairsCombi",
                        "status": Status.none,
                        "data": {
                            "nb_by_length": locus_metrics["nb_by_length"],
                            "nb_pairs_aligned": locus_metrics["nb_uncombined_pairs"] + locus_metrics["nb_combined_pairs"]
                        }
                    }
                }
            })
            msi_spl.addLocus(msi_locus)
    # Process status
    msi_models = MSIReport.parse(args.input_models)
    for locus_id in msi_spl.loci:
        processor = PairsCombiProcessor(locus_id, msi_models, [msi_spl], args.min_support)
        processor.setLocusStatus()
    msi_spl.setStatus("PairsCombi")
    # Write report
    MSIReport.write([msi_spl], args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Tag stability for loci and sample from length distribution on loci.')
    parser.add_argument('-n', '--sample-name', type=int, help='The name of the sample. [Default: output-report basename]')
    parser.add_argument('-s', '--min-support', default=200, type=int, help='The minimum numbers of fragment (reads pairs) for determine the status. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-c', '--input-combined-list', required=True, help='The path to the file containing the list of combination report path by locus (format: TSV).')
    group_input.add_argument('-m', '--input-models', required=True, help='The path to the file containing the models sample: MSI and MSS with PairsCombi result already setted (format: JSON).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: JSON).')
    args = parser.parse_args()

    # Process
    process(args)
