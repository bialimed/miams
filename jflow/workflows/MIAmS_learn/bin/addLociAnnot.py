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
from anacore.msi import MSIReport
from anacore.msiannot import getLocusAnnotDict, addLociResToSpl


########################################################################
#
# FUNCTIONS
#
########################################################################
def process(args):
    """
    ********************************************************.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """

    data_by_spl = getLocusAnnotDict(args.input_loci_annotations)
    msi_samples = MSIReport.parse(args.input_report)
    for curr_spl in msi_samples:
        addLociResToSpl(curr_spl, data_by_spl[curr_spl.name])
    MSIReport.write(msi_samples, args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='****************************.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--input-report', required=True, nargs='+', help='******************************************************** (format: MSIReport).')
    group_input.add_argument('-l', '--input-loci-annot', required=True, help='******************************************************** (format: LocusAnnot).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: JSON).')
    args = parser.parse_args()

    # Process
    process(args)
