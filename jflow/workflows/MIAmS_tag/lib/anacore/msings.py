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
__version__ = '1.1.1'
__email__ = 'frederic.escudie@iuct-oncopole.fr'
__status__ = 'prod'

import gzip
from copy import deepcopy
from anacore.abstractFile import isGzip
from anacore.sv import HashedSVIO
from anacore.msi import MSILocus, LocusRes, MSISample, MSISplRes, Status


def locusResToAnalysisRecord(locus_id, locus_name, locus_res):
    """
    Return a dict corresponding to a MSINGSAnalysis record.

    :param locus_id: The position of the locus chr:start-end (start is 0-based).
    :type locus_id: str
    :param locus_name: The name of the locus.
    :type locus_id: str
    :param locus_res: The result of mSINGS analysis for the locus.
    :type locus_res: LocusRes
    """
    analysis_record = {
        "Position": locus_id,
        "Name": locus_name,
        "Average_Depth": sum([curr_peak["DP"] for curr_peak in locus_res.data["peaks"]]),
        "Number_of_Peaks": locus_res.data["nb_peaks"],
        "Standard_Deviation": locus_res.data["std_dev"],
        "peaks": locus_res.data["peaks"],
    }
    return analysis_record


class MSINGSAnalysis(HashedSVIO):
    """Manage output file produced by the command "msi analyzer" of mSINGS (https://bitbucket.org/uwlabmed/msings)."""

    def __init__(self, filepath, mode="r"):
        """
        Return the new instance of MSINGSAnalysis.

        :param filepath: The filepath.
        :type filepath: str
        :param mode: Mode to open the file ('r', 'w', 'a').
        :type mode: str
        """
        super().__init__(filepath, mode, "\t", "")
        if mode == "w":
            self.titles = ["Position", "Name", "Average_Depth", "Number_of_Peaks", "Standard_Deviation", "IndelLength:AlleleFraction:SupportingCalls"]

    def _parseLine(self):
        """
        Return a structured record from the current line.

        :return: The record described by the current line.
        :rtype: dict
        """
        record = super()._parseLine()
        peaks = record["IndelLength:AlleleFraction:SupportingCalls"].split(" ")
        if len(peaks) == 1 and peaks[0] == "0:0.0:0":
            peaks = []
        else:
            for idx, curr_peak in enumerate(peaks):
                indel_length, AF, DP = curr_peak.split(":")
                peaks[idx] = {
                    "indel_length": int(indel_length),
                    "AF": float(AF),
                    "DP": int(DP)
                }
        record.pop("IndelLength:AlleleFraction:SupportingCalls", None)
        record["peaks"] = peaks
        return record

    def recordToLine(self, record):
        """
        Return the record in SV format.

        :param record: The record to process.
        :type record: dict or MSILocus
        :return: The SV line corresponding to the record.
        :rtype: str
        """
        formatted_record = None
        if issubclass(record.__class__, MSILocus):
            formatted_record = locusResToAnalysisRecord(record.position, record.name, record.results["MSINGS"])
        else:
            formatted_record = deepcopy(record)
        formatted_record["IndelLength:AlleleFraction:SupportingCalls"] = " ".join(
            ["{}:{}:{}".format(curr_peak["indel_length"], curr_peak["AF"], curr_peak["DP"]) for curr_peak in formatted_record["peaks"]]
        )
        formatted_record.pop("peaks", None)
        return super().recordToLine(formatted_record)


class MSINGSReport(object):
    """Manage output file produced by the command "msi count_msi_samples" of mSINGS (https://bitbucket.org/uwlabmed/msings)."""

    def __init__(self, filepath):
        """
        Return the new instance of MSINGSReport.

        :param filepath: The filepath.
        :type filepath: str
        """
        self.filepath = filepath
        self.samples = dict()
        self.loci = list()
        self.method_name = "MSINGS"
        self.parse()

    def _parseFileHandle(self, FH):
        """
        Parse file referenced by the file handle FH and store information in self.

        :param FH: The file handle for the filepath.
        :type FH: TextIOWrapper
        """
        # Parse general information
        samples = [elt.strip() for elt in FH.readline().split("\t")[1:]]
        nb_unstable = [int(elt.strip()) for elt in FH.readline().split("\t")[1:]]
        nb_evaluated = [int(elt.strip()) for elt in FH.readline().split("\t")[1:]]
        line = FH.readline()
        if not line.startswith("msing_score"):
            scores = [None for curr_spl in samples]
        else:
            scores = [elt.strip() for elt in line.split("\t")][1:]
            for idx, elt in enumerate(scores):
                curr_score = None
                if elt != "":
                    curr_score = float(elt)
                scores[idx] = curr_score
            line = FH.readline()  # To next line
        status = [elt.strip() for elt in line.split("\t")][1:]
        for idx, elt in enumerate(status):
            curr_status = Status.undetermined
            if nb_evaluated[idx] > 0:
                if elt == "NEG":
                    curr_status = Status.stable
                elif elt == "POS":
                    curr_status = Status.instable
            status[idx] = curr_status
        for spl_idx, curr_spl in enumerate(samples):
            spl_res = MSISplRes(status[spl_idx], self.method_name, scores[spl_idx])
            self.samples[curr_spl] = MSISample(curr_spl, None, {self.method_name: spl_res})
        # Parse loci information
        for curr_line in FH:
            fields = [elt.strip() for elt in curr_line.split("\t")]
            curr_locus = fields[0]
            self.loci.append(curr_locus)
            for idx, curr_val in enumerate(fields[1:]):
                curr_spl = samples[idx]
                loci_res = None
                if curr_val == "":
                    loci_res = LocusRes(Status.undetermined)
                elif curr_val == "1":
                    loci_res = LocusRes(Status.instable)
                else:
                    loci_res = LocusRes(Status.stable)
                self.samples[curr_spl].addLocus(
                    MSILocus(curr_locus, None, {self.method_name: loci_res})
                )

    def parse(self):
        """Parse file and store information in self."""
        if isGzip(self.filepath):
            with gzip.open(self.filepath, "rt") as FH:
                self._parseFileHandle(FH)
        else:
            with open(self.filepath, "r") as FH:
                self._parseFileHandle(FH)
