#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import argparse
from anacore.msi import LocusClassifier, MSIReport, Status
from sklearn.svm import SVC


########################################################################
#
# FUNCTIONS
#
########################################################################
class MIAmSClassifier(LocusClassifier):
    def __init__(self, locus_id, method_name="MIamS_combi_SVC", model_method_name="model", random_state=None):
        classifier = SVC(random_state=random_state, probability=True)
        super().__init__(locus_id, method_name, classifier, model_method_name)


def process(args):
    """
    Predict classification (status and score) for all samples loci.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    train_dataset = MSIReport.parse(args.input_references)
    test_dataset = MSIReport.parse(args.input_evaluated)

    # Classification by locus
    loci_ids = sorted(train_dataset[0].loci.keys())
    for locus_id in loci_ids:
        evaluated_test_dataset = []
        for spl in test_dataset:
            if spl.loci[locus_id].results[args.method_name].getNbFrag() < args.min_support_fragments:
                spl.loci[locus_id].results[args.method_name].status = Status.undetermined
            else:
                evaluated_test_dataset.append(spl)
        clf = MIAmSClassifier(locus_id, args.method_name, "model", args.random_seed)
        clf.fit(train_dataset)
        clf.set_status(evaluated_test_dataset)

    # Classification by sample
    for spl in test_dataset:
        spl.setStatusByMajority(args.method_name)

    MSIReport.write(test_dataset, args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Predict classification (status and score) for all samples loci.')
    parser.add_argument('-m', '--method-name', default="MIAmS_combi", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-f', '--min-support-fragments', default=150, type=int, help='The minimum numbers of fragment (reads pairs) for determine the status. [Default: %(default)s]')
    parser.add_argument('-s', '--random-seed', default=None, type=int, help='The seed used by the random number generator in the classifier.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--input-references', required=True, help='Path to the file containing the references samples used in learn step (format: MSIReport).')
    group_input.add_argument('-e', '--input-evaluated', required=True, help='Path to the file containing the samples with loci to classify (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    # Process
    process(args)
