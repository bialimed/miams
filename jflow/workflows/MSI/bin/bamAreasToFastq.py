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

import pysam
import argparse
from anacore.lib.bed import BEDIO
from anacore.lib.region import RegionList
from anacore.lib.sequenceIO import Sequence, FastqIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def bam2PairedFastq(aln_path, R1_path, R2_path, selected_areas, min_len_on_area=20, qual_offset=33):
    """
    @summary: Writes in fastq files the reads pairs overlapping the provided regions.
    @param aln_path: [str] The path to the alignment file (format: BAM)
    @param R1_path: [str] The path to the outputted R1 file (format: fastq).
    @param R2_path: [str] The path to the outputted R2 file (format: fastq).
    @param selected_areas: [RegionList] The selected regions.
    @param min_len_on_area: [int] A reads pair is written on fastq only if this number of nucleotides of the target are covered by the each read.
    @param qual_offset: [int] The quality offset.
    """
    with FastqIO(R1_path, "w") as FH_R1:
        with FastqIO(R2_path, "w") as FH_R2:
            with pysam.AlignmentFile(aln_path, "rb") as FH_sam:
                already_selected = dict()
                for area_idx, curr_area in enumerate(selected_areas):
                    selected_in_area = dict()
                    for read in FH_sam.fetch(curr_area.reference.name, curr_area.start, curr_area.end):
                        len_on_area = min(read.reference_end, curr_area.end) - max(read.reference_start, curr_area.start)  # Deletions decrease this value
                        if len_on_area > min_len_on_area:
                            read_id = read.query_name
                            if read_id not in selected_in_area:
                                selected_in_area[read_id] = {"R1": False, "R2": False}
                            if read.is_read2:
                                selected_in_area[read_id]["R2"] = True
                                if selected_in_area[read_id]["R1"] and not read_id in already_selected:
                                    R1 = getSeqFromAlnSeq(FH_sam.mate(read), qual_offset)
                                    R2 = getSeqFromAlnSeq(read, qual_offset)
                                    FH_R1.write(R1)
                                    FH_R2.write(R2)
                                    already_selected[read_id] = 1
                            else:
                                selected_in_area[read_id]["R1"] = True
                                if selected_in_area[read_id]["R2"] and not read_id in already_selected:
                                    R1 = getSeqFromAlnSeq(read, qual_offset)
                                    R2 = getSeqFromAlnSeq(FH_sam.mate(read), qual_offset)
                                    FH_R1.write(R1)
                                    FH_R2.write(R2)
                                    already_selected[read_id] = 1

def getAreas(input_areas):
    """
    @summary: Returns the list of areas from a BED file.
    @param input_areas: [str] The path to the areas description (format: BED).
    @returns: [RegionList] The list of areas.
    """
    areas = RegionList()
    with BEDIO(input_areas) as FH_panel:
        areas = RegionList(FH_panel.read())
    return areas

def getSeqFromAlnSeq(read, qual_offset):
    """
    @summary: Returns the Sequence instance corresponding to the read.
    @param read: [pysam.AlignedSegment] The read to convert.
    @param qual_offset: [int] The quality offset.
    @return: [Sequence] The sequence corresponding to the read.
    """
    read_seq = read.query_sequence
    read_qual = "".join([chr(qual + qual_offset) for qual in read.query_qualities])
    if read.is_reverse:
        read_seq = revcom(read_seq)
        read_qual = read_qual[::-1]
    return Sequence(read.query_name, read_seq, None, read_qual)

def revcom(seq):
    """
    @summary: Returns the reverse complement the sequence.
    @param seq: [str] The sequence.
    @return: [str] The reverse complement of the sequence.
    """
    complement_rules = {'A':'T','T':'A','G':'C','C':'G','U':'A','N':'N','W':'W','S':'S','M':'K','K':'M','R':'Y','Y':'R','B':'V','V':'B','D':'H','H':'D',
                        'a':'t','t':'a','g':'c','c':'g','u':'a','n':'n','w':'w','s':'s','m':'k','k':'m','r':'y','y':'r','b':'v','v':'b','d':'h','h':'d'}
    return("".join([complement_rules[base] for base in seq[::-1]]))


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Extract reads pairs overlapping the specified regions from a BAM file.')
    parser.add_argument('-m', '--min-overlap', default=20, type=int, help='A reads pair is selected only if this number of nucleotides of the target are covered by the each read. [Default: %(default)s]')
    parser.add_argument('-q', '--qual-offset', default=33, type=int, help='The quality offset of the reads in alignment file. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-a', '--input-aln', required=True, help='The path to the alignment file (format: BAM).')
    group_input.add_argument('-t', '--input-targets', required=True, help='The path to the targets file (format: BED).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-R1', '--output-R1', required=True, help='The path to the outputted reads file (format: fastq).')
    group_output.add_argument('-R2', '--output-R2', required=True, help='The path to the outputted reads file (format: fastq).')
    args = parser.parse_args()

    # Process
    selected_areas = getAreas(args.input_targets)
    bam2PairedFastq(args.input_aln, args.output_R1, args.output_R2, selected_areas, args.min_overlap)
