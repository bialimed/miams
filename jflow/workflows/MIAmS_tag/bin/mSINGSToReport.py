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
__version__ = '1.3.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import argparse
from anacore.msi import Status, LocusResDistrib, MSIReport
from anacore.msings import MSINGSAnalysis, MSINGSReport


########################################################################
#
# FUNCTIONS
#
########################################################################
def process(args):
    """
    Aggregate report and analysis information coming from mSINGS in serialisation of anacore.msi.MSISAmple object.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    # Aggregate data
    msi_spl = list(MSINGSReport(args.input_report).samples.values())[0]
    with MSINGSAnalysis(args.input_analysis) as FH_analysis:
        for record in FH_analysis:
            if record.position in msi_spl.loci:
                msi_spl.loci[record.position].name = record.name
                if "MSINGS" not in msi_spl.loci[record.position].results:
                    msi_spl.loci[record.position].results["MSINGS"] = LocusResDistrib(Status.none)
                else:
                    msi_spl.loci[record.position].results["MSINGS"]._class = "LocusResDistrib"
                msi_spl.loci[record.position].results["MSINGS"].data = record.results["MSINGS"].data
            else:
                msi_spl.addLocus(record)
    # Write report
    MSIReport.write([msi_spl], args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Aggregates report and analysis information coming from mSINGS in serialisation of anacore.msi.MSISAmple object.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--input-report', required=True, help='The path to the file containing status for one sample and the evaluated loci (format: TSV). This file is outputted by command "msi count_msi_samples" of mSINGS.')
    group_input.add_argument('-a', '--input-analysis', required=True, help='The path to the file containing the profiles of evaluated loci for one sample (format: TSV). This file is outputted by command "msi analyzer" of mSINGS.')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: JSON).')
    args = parser.parse_args()

    # Process
    process(args)
