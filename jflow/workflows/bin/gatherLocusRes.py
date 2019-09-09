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
from anacore.msi import LocusRes, LocusResDistrib, LocusResPairsCombi, MSILocus, MSISample, MSIReport, Status
from anacore.sv import HashedSVIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def addLociDataFromFiles(msi_spl, in_loci_list, method_name, keys, res_cls):
    """
    Get selected data for loci of a sample and add them as data in LocusRes.

    :param msi_spl: The sample where the results are added.
    :type msi_spl: MSISample
    :param in_loci_list: The path to the file containing the list of metrics files by locus (format: TSV). The header must be: #Locus_position<tab>Locus_name<tab>Filepath. Each file referenced in "Filepath" must be in JSON format and must contain a dictionary of metrics for one locus of the sample.
    :type in_loci_list: str
    :param method_name: The name of the method storing locus results in LocusRes.
    :type method_name: str
    :param keys: The keys extracted from in_locus_data and stored in LocusRes.
    :type keys: dict (keys are name in in_locus_data and values are names in LocusRes.data)
    :param res_cls: The class used to store LocusRes in msi_locus.
    :type res_cls: LocusRes or one of its subclasses
    """
    with HashedSVIO(in_loci_list) as FH_loci_list:
        for record in FH_loci_list:  # One file by locus
            # Add locus
            if record["Locus_position"] not in msi_spl.loci:
                msi_spl.addLocus(
                    MSILocus(record["Locus_position"], record["Locus_name"])
                )
            msi_locus = msi_spl.loci[record["Locus_position"]]
            # Add result and data
            addLociResult(msi_locus, record["Filepath"], method_name, keys, res_cls)


def addLociResult(msi_locus, in_locus_data, method_name, keys, res_cls):
    """
    Get selected data from a JSON file and add them as data in a LocusRes.

    :param msi_locus: The locus where the results are added.
    :type msi_locus: MSILocus
    :param in_locus_data: The path to the file containing the results for the locus (format: JSON).
    :type in_locus_data: str
    :param method_name: The name of the method storing locus results in LocusRes.
    :type method_name: str
    :param keys: The keys extracted from in_locus_data and stored in LocusRes.
    :type keys: dict (keys are name in in_locus_data and values are names in LocusRes.data)
    :param res_cls: The class used to store LocusRes in msi_locus.
    :type res_cls: LocusRes or one of its subclasses
    """
    # Get data
    with open(in_locus_data) as FH_locus:
        locus_metrics = json.load(FH_locus)
    # Add result
    if method_name not in msi_locus.results:
        msi_locus.results[method_name] = res_cls(Status.none)
    locus_res = msi_locus.results[method_name]
    # Add data
    if keys is not None:  # Add selected keys
        for metrics_key, result_key in keys.items():
            locus_res.data[result_key] = locus_metrics[metrics_key]
    else:  # Add all keys
        for metrics_key, metrics_val in locus_metrics.items():
            locus_res.data[metrics_key] = metrics_val


def process(args):
    """
    Create MSISample from loci metrics.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    spl_name = args.sample_name
    if args.sample_name is None:
        spl_name = os.path.basename(args.output_report).split(".")[0]
        if spl_name.endswith("_report"):
            spl_name = spl_name[:-7]
    msi_spl = MSISample(spl_name)
    # Add result data by loci
    addLociDataFromFiles(msi_spl, args.input_loci_metrics_list, args.method_name, args.result_keys, args.method_class_name)
    # Write report
    MSIReport.write([msi_spl], args.output_report)


class ResultKeysAction(argparse.Action):
    """Manages results keys parameters."""

    def __call__(self, parser, namespace, values, option_string=None):
        res_by_metrics = dict()
        for curr in values:
            metrics_key, result_key = curr.rsplit("=", 1)
            res_by_metrics[metrics_key] = result_key
        setattr(namespace, self.dest, res_by_metrics)


class ResultClassName(argparse.Action):
    """Manages result class name parameters."""

    def __call__(self, parser, namespace, value, option_string=None):
        new_value = eval(value)
        setattr(namespace, self.dest, new_value)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Gather results about several locus in a MSISample object and write them in MSIReport.')
    parser.add_argument('-s', '--sample-name', type=int, help='The name of the sample. [Default: output-report basename without extension]')
    parser.add_argument('-n', '--method-name', default="model", help='The name of the method storing locus metrics in LocusRes. [Default: %(default)s]')
    parser.add_argument('-c', '--method-class-name', default="LocusResDistrib", choices=["LocusRes", "LocusResDistrib", "LocusResPairsCombi"], action=ResultClassName, help='The class used to store LocusRes. [Default: %(default)s]')
    parser.add_argument('-r', '--result-keys', nargs='+', action=ResultKeysAction, help='The keys retrieved from loci metrics and stored in LocusRes. Each key is couple with format "name_in_metrics=name_in_LocusRes_data". [Default: all tags in loci metrics]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-i', '--input-loci-metrics-list', required=True, help='The path to the file containing the list of metrics files by locus (format: TSV). The header must be: #Locus_position<tab>Locus_name<tab>Filepath. Each file referenced in "Filepath" must be in JSON format and must contain a dictionary of metrics for one locus of the sample.')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    # Process
    process(args)
