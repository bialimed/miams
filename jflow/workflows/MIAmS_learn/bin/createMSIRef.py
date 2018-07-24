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
from copy import deepcopy
from anacore.bed import BEDIO
from anacore.msi import Status, LocusResPairsCombi, MSILocus, MSIReport
from anacore.msiannot import getLocusAnnotDict, addLociResToSpl, MSIAnnot


########################################################################
#
# FUNCTIONS
#
########################################################################
def getAggregatedSpl(in_reports):
    """
    Return one list of MSISample from several MSReport.

    :param in_reports: Pathes to the MSIReport files.
    :type in_reports: list of MSIReport
    :return: List of MSISample.
    :rtype: list
    """
    aggregated_spl = []
    for curr_report in in_reports:
        msi_samples = MSIReport.parse(curr_report)
        for curr_spl in msi_samples:
            aggregated_spl.append(curr_spl)
    return aggregated_spl


def writeStatusMetrics(msi_samples, result_id, out_summary):
    """
    Write the statistics of status by loci in population of samples.

    :param msi_samples: The samples processed.
    :type msi_samples: list of MSISample
    :param result_id: Only the results of this methd are processed.
    :type result_id: str
    :param out_summary: Path to the output file.
    :type out_summary: str
    """
    status_by_locus = dict()
    locus_name_by_id = dict()
    authorized_status = Status.authorizedValues()
    # Get number of samples by status for each locus
    for spl in msi_samples:
        for locus_id, locus in spl.loci.items():
            locus_name_by_id[locus_id] = locus.name
            if locus_id not in status_by_locus:
                status_by_locus[locus_id] = {status: 0 for status in authorized_status}  # init each status for the current locus
            if result_id in locus.results:
                status = locus.results[result_id].status
                status_by_locus[locus_id][status] += 1
    # Write results
    with open(out_summary, "w") as FH_out:
        FH_out.write("Nb retained samples: {}\n".format(len(msi_samples)))
        print(
            "Locus_position", "Locus_name", "\t".join([str(status) for status in authorized_status]),
            sep="\t",
            file=FH_out
        )
        for locus_id, locus_name in locus_name_by_id.items():
            print(
                locus_id,
                locus_name,
                "\t".join(
                    [str(status_by_locus[locus_id][status]) for status in authorized_status]
                ),
                sep="\t",
                file=FH_out
            )


def populateLoci(msi_samples, ref_loci):
    """
    Add loci if they are missing in sample.

    :param msi_samples: The samples to populate.
    :type msi_samples: list of MSISample
    :param ref_loci: The loci to add if they are missing in samples.
    :type ref_loci: str
    """
    for spl in msi_samples:
        for ref_locus in ref_loci:
            if ref_locus.position not in spl.loci:
                spl.addLocus(deepcopy(ref_locus))


def pruneResults(msi_samples, result_id, min_support_fragments):
    """
    Remove LocusRes where the status is not determined (none or undetermined)
    and/or where the number of fragment used to determine status is lower than
    min_support_fragments.

    :param msi_samples: The pruned samples.
    :type msi_samples: list of MSISample
    :param result_id: The method on which the filters are applied.
    :type result_id: str
    :param min_support_fragments: The minimum number of fragments to keep a LocusRes in data.
    :type min_support_fragments: int
    """
    removed_spl_idx = list()
    for spl_idx, spl in enumerate(msi_samples):
        nb_results = 0
        for locus_id, msi_locus in spl.loci.items():
            if result_id in msi_locus.results:
                if msi_locus.results[result_id].status not in [Status.stable, Status.instable]:
                    msi_locus.delMethod(result_id)
                elif msi_locus.results[result_id].getNbFrag() < min_support_fragments:
                    msi_locus.delMethod(result_id)
                else:
                    nb_results += 1
        if nb_results == 0:
            removed_spl_idx.append(spl_idx)
    for spl_idx in sorted(removed_spl_idx)[::-1]:
        del(msi_samples[spl_idx])


def process(args):
    """
    Create training data for MSI classifiers. These references are stored in
    MSIReport format.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    # Get method name from annotations file
    method_names = set()
    for record in MSIAnnot(args.input_locus_annot):
        method_names.add(record["method_id"])
    if len(method_names) != 1:
        raise ValueError('The annotation file must contain only one value for method_id. The file "{}" contains {}.'.format(args.input_reports, method_names))
    result_id = list(method_names)[0]
    # Get reference loci from targets file
    ref_loci = []
    with BEDIO(args.input_targets) as FH_in:
        for record in FH_in:
            ref_loci.append(
                MSILocus(
                    "{}:{}-{}".format(record.chrom, record.start - 1, record.end),
                    record.name
                )
            )
    # Aggregate samples
    msi_samples = getAggregatedSpl(args.inputs_reports)
    # Add locus result info
    data_by_spl = getLocusAnnotDict(args.input_locus_annot)
    for curr_spl in msi_samples:
        addLociResToSpl(curr_spl, data_by_spl[curr_spl.name], LocusResPairsCombi)
    # Filter locus results
    populateLoci(msi_samples, ref_loci)
    pruneResults(msi_samples, result_id, args.min_support_fragments)
    # Display metrics
    writeStatusMetrics(msi_samples, result_id, args.output_info)
    # Write output
    MSIReport.write(msi_samples, args.output_references)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Create training data for MSI classifiers. These references are stored in MSIReport format. All the loci are represented in all samples but all the loci does not have a result (if the data does not fit filters criteria).')
    parser.add_argument('-s', '--min-support-fragments', type=int, default=200, help='Minimum number of fragment in size distribution to keep the result. The distribution must contains a sufficient amount of data to be representative of length distribution profile for the current locus. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--inputs-reports', required=True, nargs='+', help='Path(es) to the MSIReport file(s) evaluated in references creation process (format: JSON).')
    group_input.add_argument('-l', '--input-locus-annot', required=True, help='Path to the MSIAnnot file containing for each sample for each targeted locus the stability status (format: TSV). First line must be: sample<tab>locus_position<tab>method_id<tab>key<tab>value<tab>type. The method_id should be "model" and an example of line content is: H2291-1_S15<tab>4:55598140-55598290<tab>model<tab>status<tab>MSS<tab>str.')
    group_input.add_argument('-t', '--input-targets', required=True, help='The locations of the microsatellite of interest (format: BED).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-references', required=True, help='The path to the MSIReport containing the references distribution for each locus (format: JSON).')
    group_output.add_argument('-i', '--output-info', required=True, help='The path to the file describing the number of references by status for each locus (format: TSV).')
    args = parser.parse_args()

    # Process
    process(args)
