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

import pysam
import argparse
from anacore.bed import getAreas
from anacore.region import RegionList
from anacore.sequenceIO import FastqIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def pickSeq(in_path, out_path, kept_ids):
    """
    Filter fastq by sequences IDs.

    :param in_path: The path to the initial sequences file (format: fastq).
    :type in_path: str
    :param out_path: The path to the outputted sequences file (format: fastq).
    :type out_path: str
    :param kept_ids: IDs of kept sequences.
    :type kept_ids: set
    """
    with FastqIO(in_path) as FH_in:
        with FastqIO(out_path, "w") as FH_out:
            for record in FH_in:
                if record.id in kept_ids:
                    FH_out.write(record)


def getReadsFromBAM(aln_path, selected_areas, min_len_on_area=20):
    """
    Retrun the ids of the reads pairs overlapping the provided regions.

    :param aln_path: Path to the alignments file (format: BAM).
    :type aln_path: str
    :param R1_path: Path to the outputted R1 file (format: fastq).
    :type R1_path: str
    :param R2_path: Path to the outputted R2 file (format: fastq).
    :type R2_path: str
    :param selected_areas: The selected regions.
    :type selected_areas: anacore.region.RegionList
    :param min_len_on_area: A reads pair is written on fastq only if this number of nucleotides of the target are covered by the each read.
    :type min_len_on_area: int
    :return: List of ids of the reads pairs overlapping the provided regions.
    :rtype: set
    """
    selected_reads = set()
    with pysam.AlignmentFile(aln_path, "rb") as FH_sam:
        already_selected = dict()
        for area_idx, curr_area in enumerate(selected_areas):
            selected_in_area = dict()
            for read in FH_sam.fetch(curr_area.reference.name, curr_area.start, curr_area.end):
                if read.reference_start and read.reference_end:  # Skip reads with a mapping score but no information on alignment (CIGAR=*)
                    len_on_area = None
                    if curr_area.thickStart is None or curr_area.thickEnd is None:
                        len_on_area = read.get_overlap(curr_area.start, curr_area.end)
                    else:
                        len_on_area = read.get_overlap(curr_area.thickStart, curr_area.thickEnd)
                    if len_on_area > min_len_on_area:
                        read_id = read.query_name
                        read_phase = "R2" if read.is_read2 else "R1"
                        if read_id not in already_selected:
                            if read_id not in selected_in_area:
                                selected_in_area[read_id] = {"R1": None, "R2": None}
                            selected_in_area[read_id][read_phase] = True
                            if selected_in_area[read_id]["R1"] is not None and selected_in_area[read_id]["R2"] is not None:
                                selected_reads.add(read_id)
                                already_selected[read_id] = 1
    return selected_reads


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Extract reads pairs overlapping the specified regions from a BAM file.')
    parser.add_argument('-m', '--min-overlap', default=20, type=int, help='A reads pair is selected only if this number of nucleotides of the target are covered by the each read. [Default: %(default)s]')
    parser.add_argument('-s', '--split-targets', action='store_true', help='With this parameter each region has his own pair of outputted fastq. In this configuration --output-R1 and --output-R2 must contain the placeholder "##TARGET##" dynamically replaced by the region name.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-a', '--input-aln', required=True, help='The path to the alignment file (format: BAM).')
    group_input.add_argument('-t', '--input-targets', required=True, help='The path to the targets file (format: BED). The position of the interests areas are extracted from column 7 (thickStart) and column 8 (thickEnd) if they exist otherwise they are extracted from column 2 (Start) and column 3 (End).')
    group_input.add_argument('-i1', '--input-R1', required=True, help='The path to the inputted reads file (format: fastq).')
    group_input.add_argument('-i2', '--input-R2', required=True, help='The path to the inputted reads file (format: fastq).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o1', '--output-R1', required=True, help='The path to the outputted reads file (format: fastq).')
    group_output.add_argument('-o2', '--output-R2', required=True, help='The path to the outputted reads file (format: fastq).')
    args = parser.parse_args()
    if args.split_targets:
        if "##TARGET##" not in args.output_R1 or "##TARGET##" not in args.output_R2:
            raise Exception('With {} the parameters {} and {} must contains "##TARGET##" as placeholder.'.format(args.split_targets.flag, args.output_R1.flag, args.output_R2.flag))

    # Process
    selected_areas = getAreas(args.input_targets)
    if not args.split_targets:
        reads_id = getReadsFromBAM(args.input_aln, selected_areas, args.min_overlap)
        pickSeq(args.input_R1, args.output_R1, reads_id)
        pickSeq(args.input_R2, args.output_R2, reads_id)
    else:
        uniq_names = set([elt.name for elt in selected_areas if elt.name is not None])
        if len(selected_areas) != len(uniq_names):
            raise Exception('With {} all the regions in {} must have an uniq name.'.format(args.split_targets.flag, args.input_targets))
        for curr_area in selected_areas:
            curr_output_R1 = args.output_R1
            curr_output_R1.replace("##TARGET##", curr_area.name)
            curr_output_R2 = args.output_R2
            curr_output_R2.replace("##TARGET##", curr_area.name)
            reads_id = getReadsFromBAM(args.input_aln, RegionList([curr_area]), args.min_overlap)
            pickSeq(args.input_R1, curr_output_R1, reads_id)
            pickSeq(args.input_R2, curr_output_R2, reads_id)
