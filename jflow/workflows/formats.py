#
# Copyright (C) 2015 INRA
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

import jflow
from jflow import seqio
from jflow.featureiolib.gff3 import GFF3IO
from jflow.exceptions import InvalidFormatError
import os
import sys


def any(ifile): pass
def bam(ifile): pass

def fastq(ifile):
    try:
        reader = seqio.FastqReader(ifile)
        nb_seq = 0
        for id, desc, seq, qualities in reader:
            nb_seq += 1
            # only check the first 10 sequences
            if nb_seq == 10: break
    except:
        raise InvalidFormatError("The provided file '" + ifile + "' is not a fastq file!")
    
def fasta(ifile):
    try:
        reader = seqio.FastaReader(ifile)
        nb_seq = 0
        for id, desc, seq, qualities in reader:
            nb_seq += 1
             # only check the first 3 sequences
            if nb_seq == 3: break
    except:
        raise InvalidFormatError("The provided file '" + ifile + "' is not a fasta file!")
    
def sff(ifile):
    try:
        reader = seqio.SFFReader(ifile)
        nb_seq = 0
        for id, desc, seq, qualities in reader:
            nb_seq += 1
            # only check the first 10 sequences
            if nb_seq == 10: break
    except:
        raise InvalidFormatError("The provided file '" + ifile + "' is not a sff file!")

def gff3(ifile):
    #try:
        reader = GFF3IO(ifile,"r")
        nb_line = 0
        for record in reader:
            nb_line += 1
            # only check the first 10 sequences
            if nb_line == 10: break
    #except:
    #    raise InvalidFormatError("The provided file '" + ifile + "' is not a gff3 file!")