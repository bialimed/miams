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
__copyright__ = 'Copyright (C) 2019 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import csv
import argparse
import numpy as np
from scipy import interp
from sklearn import metrics
import matplotlib.pyplot as plt


########################################################################
#
# FUNCTIONS
#
########################################################################
def getClassifierRes(in_results, classifier):
    res = {}
    with open(in_results) as FH_in:
        reader = csv.DictReader(FH_in, delimiter='\t')
        for rec in reader:
            if rec["method_name"] == classifier:
                if rec["dataset_id"] not in res:
                    res[rec["dataset_id"]] = {"cls": [], "score": []}
                if rec["spl_expected_status"] != "Undetermined":
                    res[rec["dataset_id"]]["cls"].append(0 if rec["spl_expected_status"] == "MSS" else 1)
                    score = float(rec["spl_pred_score"])
                    res[rec["dataset_id"]]["score"].append(score)
    return res


def getMIAmSClassifierRes(in_results, classifier):
    res = {}
    with open(in_results) as FH_in:
        reader = csv.DictReader(FH_in, delimiter='\t')
        for rec in reader:
            if rec["method_name"] == classifier:
                if rec["dataset_id"] not in res:
                    res[rec["dataset_id"]] = {"cls": [], "score": []}
                if rec["spl_expected_status"] != "Undetermined":
                    res[rec["dataset_id"]]["cls"].append(0 if rec["spl_expected_status"] == "MSS" else 1)
                    score = float(rec["spl_pred_score"])
                    if rec["spl_observed_status"] == "MSS":
                        score = 1 - score
                    res[rec["dataset_id"]]["score"].append(score)
    return res

def getROCRes(datasets_res):
    tprs = []
    auc = []
    mean_fpr = np.linspace(0, 1, 100)
    for dataset_id, dataset_res in datasets_res.items():
        fpr, tpr, thresholds = metrics.roc_curve(
            dataset_res["cls"],
            dataset_res["score"]
        )
        tprs.append(interp(mean_fpr, fpr, tpr))
        tprs[-1][0] = 0.0
        auc.append(getAUCRes(dataset_res))
    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    return mean_fpr, mean_tpr, np.mean(auc)

def getROCResOneDataset(dataset_res):
    fpr, tpr, thresholds = metrics.roc_curve(
        dataset_res["cls"],
        dataset_res["score"]
    )
    return fpr, tpr, getAUCRes(dataset_res)

def getAUCRes(dataset_res):
    auc = 1
    if len(set(dataset_res["cls"])) == 2:
        auc = metrics.roc_auc_score(
            dataset_res["cls"],
            dataset_res["score"]
        )
    return auc


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Display ROC curves for MIAmS sklearn, MIAmS mSINGS and MSISensor.')
    parser.add_argument('-d', '--dataset-name', required=True, help='Name of the dataset.')
    parser.add_argument('-c', '--classifier', default="SVM", help='MIAmS sklearn classifier to evaluate. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Inputs
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-i', '--input-miams-results', required=True, help='Path to result file of MIAmS (format: TSV).')
    group_input.add_argument('-m', '--input-msisensor-results', required=True, help='Path to result file of MSISensor (format: TSV).')
    args = parser.parse_args()

    # Get results
    cls_res = getMIAmSClassifierRes(args.input_miams_results, args.classifier)
    msings_res = getMIAmSClassifierRes(args.input_miams_results, "mSINGS")
    msisensor_res = getClassifierRes(args.input_msisensor_results, "MSISensor")

    # Datasets
    lw = 2
    plt.figure()
    fpr, tpr, auc = getROCRes(msings_res)
    plt.plot(fpr, tpr, lw=lw, label='Mean {} (auc = {:0.2f})'.format("mSINGS", auc))
    fpr, tpr, auc = getROCResOneDataset(msisensor_res["0"])
    plt.plot(fpr, tpr, lw=lw, label='{} (auc = {:0.2f})'.format("MSISensor", auc))
    fpr, tpr, auc = getROCRes(cls_res)
    plt.plot(fpr, tpr, lw=lw, label='Mean {} (auc = {:0.2f})'.format(args.classifier, auc))
    # Figure
    plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic on {}'.format(args.dataset_name))
    plt.legend(loc="lower right")
    plt.show()
