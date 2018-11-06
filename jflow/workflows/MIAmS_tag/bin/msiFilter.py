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

import argparse
from anacore.msi import Status, MSIReport


########################################################################
#
# FUNCTIONS
#
########################################################################
def process(args):
    """
    Filter loci usable for instability status prediction.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    reports = MSIReport.parse(args.input_reports)
    for spl in reports:
        # Filter loci status
        for locus_id, locus in spl.loci.items():
            res_locus = locus.results[args.method_name]
            if len(res_locus.data) != 0 and res_locus.getCount() < args.min_distrib_support:
                res_locus.status = Status.undetermined
                res_locus.score = None
        # Re-repocess sample status
        if args.consensus_method == "majority":
            spl.setStatusByMajority(args.method_name, args.min_voting_loci)
        elif args.consensus_method == "ratio":
            spl.setStatusByInstabilityRatio(args.method_name, args.min_voting_loci, args.instability_ratio)
        elif args.consensus_method == "count":
            spl.setStatusByInstabilityCount(args.method_name, args.min_voting_loci, args.instability_count)
        spl.setScore(args.method_name, args.undetermined_weight)
    # Write report
    MSIReport.write(reports, args.output_reports)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Filter loci usable for instability status prediction. Loci do not fitting criteria are set to undetermined and the score and the status of the sample are re-processed.')
    parser.add_argument('-l', '--min-voting-loci', default=3, type=int, help='The minimum numbers of loci to determine a sample status. [Default: %(default)s]')
    parser.add_argument('-m', '--consensus-method', default='ratio', choices=['count', 'majority', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/stable loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    parser.add_argument('-n', '--method-name', required=True, help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-r', '--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio of unstable/determined loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    parser.add_argument('-s', '--min-distrib-support', default=100, type=int, help='The minimum numbers of reads (mSINGS) or reads pairs (classifiers based on pairs) to determine a locus status. [Default: %(default)s]')
    parser.add_argument('-u', '--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument('-w', '--undetermined-weight', default=0.5, type=float, help='The weight of the undetermined loci in sample score calculation. [Default: %(default)s]')
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-i', '--input-reports', required=True, help='The path to the input file containing samples reports (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-reports', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    if args.consensus_method != "ratio" and args.instability_ratio != parser.get_default('instability_ratio'):
        raise Exception('The parameter "instability-ratio" can only used with consensus-ratio set to "ratio".')
    if args.consensus_method != "count" and args.instability_count != parser.get_default('instability_count'):
        raise Exception('The parameter "instability-count" can only used with consensus-ratio set to "count".')

    # Process
    process(args)
