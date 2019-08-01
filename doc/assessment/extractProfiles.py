#!/usr/bin/env python3
#
# Copyright (C) 2019 IUCT-O
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
__copyright__ = 'Copyright (C) 2019 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import logging
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
sns.set_style("whitegrid")

APP_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LIB_DIR = os.path.join(APP_FOLDER, "jflow", "workflows", "lib")
sys.path.insert(0, LIB_DIR)

from anacore.msi import MSIReport
from anacore.sv import HashedSVIO


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Write lengths distributions profiles from the MIAmS_tag outputs.')
    parser.add_argument('-r', '--reference-method', default="SVCPairs", help='The method used to store locus results. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Inputs
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-s', '--input-status', required=True, help='Path to the file containing by sample the status for each locus (format: TSV).')
    group_input.add_argument('-d', '--input-data', required=True, help='Path to the data folder outputted by MIAmS_tag.')
    # Outputs
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-f', '--output-folder', default=".", help='Path to the output folder. [Default: %(default)s]')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Get status by locus
    status_by_spl = {}
    with HashedSVIO(args.input_status, title_starter="") as FH_in:
        for record in FH_in:
            status_by_spl[record["sample"]] = {locus: status for locus, status in record.items() if locus not in ["sample", "sample_status"]}

    # Get min and max amplicon size by locus
    range_by_locus = {}
    for filename in os.listdir(args.input_data):
        filepath = os.path.join(args.input_data, filename)
        report = MSIReport.parse(filepath)
        for spl in report:
            for locus_id, locus in spl.loci.items():
                if locus_id not in range_by_locus:
                    range_by_locus[locus_id] = {"min": 300, "max": 0}
                range_by_locus[locus_id]["min"] = min(locus.results[args.reference_method].getMinLength(), range_by_locus[locus_id]["min"])
                range_by_locus[locus_id]["max"] = max(locus.results[args.reference_method].getMaxLength(), range_by_locus[locus_id]["max"])

    # Write lengths distributions
    for filename in os.listdir(args.input_data):
        filepath = os.path.join(args.input_data, filename)
        report = MSIReport.parse(filepath)
        for spl in report:
            log.info("Process sample {}".format(spl.name))
            for locus_id, locus in spl.loci.items():
                start = range_by_locus[locus_id]["min"]
                end = range_by_locus[locus_id]["max"]
                if not os.path.exists(os.path.join(args.output_folder, locus.name)):
                    os.makedirs(os.path.join(args.output_folder, locus.name))
                data = [{"length": idx + start, "abundance": val} for idx, val in enumerate(locus.results[args.reference_method].getDensePrct(start, end))]
                second_peak_prct = 0
                if len(data) > 1:
                    rvs_ordered_prct = sorted([elt["abundance"] for elt in data], reverse=True)
                    second_peak_prct = rvs_ordered_prct[1]  # abundancy of the second most abundant
                df = pd.DataFrame(data)
                plt.figure(figsize=(18, 5))
                sns.barplot(data=df, x="length", y="abundance")
                plt.suptitle("{} {} {}".format(spl.name, locus.name, status_by_spl[spl.name][locus.name]))
                plt.title(
                    "nb elements: {}; second peak: {:.1f}%".format(locus.results[args.reference_method].getCount(), second_peak_prct),
                    fontstyle="italic"
                )
                plt.ylim(0, 100)
                plt.yticks(range(0, 101, 10))
                plt.xticks(rotation=90)
                plt.savefig(os.path.join(args.output_folder, locus.name, status_by_spl[spl.name][locus.name] + "_" + spl.name + ".png"))
                plt.close()

    log.info("End of job")
