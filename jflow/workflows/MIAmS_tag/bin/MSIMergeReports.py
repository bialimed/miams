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
__version__ = '2.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import argparse
from copy import deepcopy
from anacore.msi import LocusRes, MSIReport, Status


########################################################################
#
# FUNCTIONS
#
########################################################################
def completeLocus(ref_msi, fixed_msi, missing_status=None):
    """
    Creates in fixed_msi the locus present in ref_msi and missing in fixed_msi.

    :param ref_msi: The sample containing the list of loci used as reference.
    :type ref_msi: anacore.msi.MSISample
    :param fixed_msi: The sample with missing loci.
    :type fixed_msi: anacore.msi.MSISample
    :param missing_status: The status added in new locus result.
    :type missing_status: str
    """
    for locus_id, locus in ref_msi.loci.items():
        if locus_id not in fixed_msi.loci:
            for method_id in fixed_msi.results:
                fixed_msi.loci[locus_id].results[method_id] = LocusRes(missing_status)
        """
        else:
            for method_id in fixed_msi.results:
                if method_id not in fixed_msi.loci[locus_id].results:
                    fixed_msi.loci[locus_id].results[method_id] = LocusRes(missing_status)
        """


def process(args):
    """
    Merges two MSIReports.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    # Parse status metrics
    first_report = MSIReport.parse(args.inputs_reports[0])
    second_report = MSIReport.parse(args.inputs_reports[1])
    if sorted([spl.name for spl in first_report]) != sorted([spl.name for spl in second_report]):
        raise Exception(
            'The reports "{}" and "{}" cannot be merged because they do not contain the same samples.'.format(
                *args.inputs_reports
            )
        )
    # Merge data
    first_by_spl = {spl.name: spl for spl in first_report}
    second_by_spl = {spl.name: spl for spl in second_report}
    final_report = []
    for spl in first_by_spl:
        completeLocus(first_by_spl[spl], second_by_spl[spl], args.missing_status)
        completeLocus(second_by_spl[spl], first_by_spl[spl], args.missing_status)
        merged_spl = deepcopy(first_by_spl[spl])
        for method_id, result in second_by_spl[spl].results.items():
            merged_spl.results[method_id] = result
        for locus_id, locus in second_by_spl[spl].loci.items():
            for method_id, result in locus.results.items():
                merged_spl.loci[locus_id].results[method_id] = result
        final_report.append(merged_spl)
    # Write metrics
    MSIReport.write(final_report, args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Merge two MSIReports.')
    parser.add_argument('-m', '--missing-status', default=Status.undetermined, help='The status used for loci missing in report but present in analysis. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-i', '--inputs-reports', required=True, nargs=2, help='The path to the 2 inputs files to merge (format: JSON). Each file contains a list of JSON serialisation of anacore.msi.MSISAmple.')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the merged report (format: JSON).')
    args = parser.parse_args()

    # Process
    process(args)
