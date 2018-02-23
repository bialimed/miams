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
__email__ = 'frederic.escudie@iuct-oncopole.fr'
__status__ = 'prod'

import gzip


def isGzip(path):
    """
    @return: [bool] True if the file is gziped.
    @param path: [str] Path to processed file.
    """
    is_gzip = None
    FH_input = gzip.open(path)
    try:
        FH_input.readline()
        is_gzip = True
    except:
        is_gzip = False
    finally:
        FH_input.close()
    return is_gzip


class MsingsRecord:
    def __init__(self, sample, score, status, loci=None):
        self.sample = sample
        self.score = score
        self.status = status
        self.loci = dict() if loci is None else loci


    def getNbUnstable(self):
        nb_unstable = 0
        for locus, is_stable in self.loci.items():
            if is_stable is not None and not is_stable:
                nb_unstable += 1
        return nb_unstable


    def getNbStable(self):
        nb_stable = 0
        for locus, is_stable in self.loci.items():
            if is_stable is not None and is_stable:
                nb_stable += 1
        return nb_stable


    def getNbEvaluated(self):
        nb_evaluated = 0
        for locus, is_stable in self.loci.items():
            if is_stable is not None:
                nb_evaluated += 1
        return nb_evaluated


    def getNbLoci(self):
        return len(self.loci)


class Report(object):
    def __init__(self, filepath):
        """
        @param filepath: [str] The filepath.
        """
        self.filepath = filepath
        self.records = dict()
        self.loci = list()
        self.parse()


    def _parseFileHandle(self, FH):
        samples = [elt.strip() for elt in FH.readline.split("\t")][1:]
        nb_unstable = [elt.strip() for elt in FH.readline.split("\t")][1:]
        nb_evaluated = [elt.strip() for elt in FH.readline.split("\t")][1:]
        scores = [elt.strip() for elt in FH.readline.split("\t")][1:]
        status = [elt.strip() for elt in FH.readline.split("\t")][1:]
        for spl_idx, curr_spl in enumerate(samples):
            self.records[curr_spl] = MsingsRecord(curr_spl, scores[spl_idx], status[spl_idx])
        for curr_line in enumerate(FH):
            fields = [elt.strip() for elt in curr_line.split("\t")]
            curr_locus = fields[0]
            self.loci.append(curr_locus)
            for idx, curr_val in fields[1:]:
                curr_spl = samples[idx]
                if curr_val == "":
                    self.records[curr_spl].loci[curr_locus] = None
                elif curr_val == "1":
                    self.records[curr_spl].loci[curr_locus] = True
                else:
                    self.records[curr_spl].loci[curr_locus] = False


    def parse(self):
        if isGzip(self.filepath):
            with gzip.open(self.filepath, "rt") as FH:
                self._parseFileHandle(FH)
        else:
            with open(self.filepath, "r") as FH:
                self._parseFileHandle(FH)
