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

import json
from anacore.sv import HashedSVIO
from anacore.msi import Status, LocusRes, MSILocus


class MSIAnnot(HashedSVIO):
    def __init__(self, filepath, mode="r"):
        """
        Build and return an instance of HashedSVIO.

        :param filepath: The filepath.
        :type filepath: str.
        :param mode: Mode to open the file ('r', 'w', 'a').
        :type mode: str.
        :param separator: Separator used between values.
        :type separator: str.
        :param title_starter: The string used to introduce the title line.
        :type title_starter: str.
        :return: The new instance.
        :rtype: HashedSVIO
        """
        super().__init__(filepath, mode, separator="\t", title_starter="")
        valid_titles = ["sample", "locus_position", "method_id", "key", "value", "type"]
        if self.titles != valid_titles:
            raise Exception('The column present in "{}" are invalid they must be: {}.'.format(filepath, valid_titles))

    def _parseLine(self):
        """
        Return a structured record from the current line.

        :return: The record defined by the current line.
        :rtype: dict
        """
        record = super()._parseLine()
        record["value"] = getCastedValue(record["value"], record["type"])
        return record

    def recordToLine(self, record):
        """
        Return the record in SV format.

        :param record: The record to process.
        :type record: dict.
        :return: The SV line corresponding to the record.
        :rtype: str
        """

        fields = []
        for curr_title in self.titles:
            val = record[curr_title]
            if curr_title == "value" and record["type"] == "json":
                val = json.dump(val)
            else:
                val = str(val)
            fields.append(val)
        line = self.separator.join(fields)
        return(line)


def getCastedValue(value, type_name):
    casted_value = value
    if type_name != "" and type_name != "str":
        if type_name == "int":
            casted_value = int(value)
        elif type_name == "float":
            casted_value = float(value)
        elif type_name == "bool":
            casted_value = (value.lower() in ["1", "true"])
        elif type_name == "json":
            casted_value = json.loads(value)
        else:
            raise ValueError('The type "{}" cannot be used in getCastedValue.'.format(type_name))
    return casted_value


def getLocusAnnotDict(in_annot):
    data_by_spl = dict()
    with MSIAnnot(in_annot) as FH_in:
        for record in FH_in:
            # Add sample
            if record["sample"] not in data_by_spl:
                data_by_spl[record["sample"]] = dict()
            data_by_locus = data_by_spl[record["sample"]]
            # Add locus
            if record["locus_position"] not in data_by_locus:
                data_by_locus[record["locus_position"]] = dict()
            data_by_res = data_by_locus[record["locus_position"]]
            # Add result method
            if record["method_id"] not in data_by_res:
                data_by_res[record["method_id"]] = dict()
            data_by_key = data_by_res[record["method_id"]]
            # Add data
            data_by_key[record["key"]] = record["value"]
    return data_by_spl


def addLociResToSpl(msi_spl, data_by_locus, res_cls=LocusRes):
    for locus_id, data_by_res in data_by_locus.items():
        # Add locus
        if locus_id not in msi_spl.loci:
            msi_spl.addLocus(
                MSILocus(locus_id)
            )
        msi_locus = msi_spl.loci[locus_id]
        # Add result and data
        addLociResult(msi_locus, data_by_res, res_cls)


def addLociResult(msi_locus, data_by_res, res_cls):
    for result_id, data_by_key in data_by_res.items():
        # Add result
        if result_id not in msi_locus.results:
            msi_locus.results[result_id] = res_cls(Status.none)
        locus_res = msi_locus.results[result_id]
        # Add data
        for key, value in data_by_key.items():
            if key != "result_id":
                if key in locus_res.__dict__ and key != "data":  # The key correspond to an attibute
                    setattr(locus_res, key, value)
                else:  # The key correspond to a data
                    locus_res.data[key] = value
