#!/bin/bash
data_folder=`dirname $0`
results_folder=${data_folder}/results_1.0.0
mkdir -p ${results_folder}


################################################################################
#
# Process assessment
#
################################################################################
../processAssessment.py \
  --data-folder ${data_folder} \
  --work-folder ${data_folder}/work \
  --add-classifiers DecisionTree KNeighbors LogisticRegression RandomForest RandomForest:50 RandomForest:500 \
  --tag-min-support-reads 100 \
  --learn-min-support-reads 400 \
  --consensus-method count \
  --instability-count 3 \
  --results-path ${results_folder}/results.tsv \
  --datasets-path ${results_folder}/datasets.tsv \
  --start-dataset-id 0 \
  --nb-test 50


################################################################################
#
# Process accuracy
#
################################################################################
# MIAmS classifiers
grep -v "DecisionTree" ${results_folder}/results.tsv | grep -v "KNeighbors" - | grep -v "LogisticRegression" - | grep -v "RandomForest" - > ${results_folder}/results_miams.tsv
sed -i 's/SVCPairs/SVM/' ${results_folder}/results_miams.tsv

../processAccuracy.py \
    --add-algorithm-consensus \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --input-datasets ${results_folder}/datasets.tsv \
    --input-results ${results_folder}/results_miams.tsv \
    --output-folder ${results_folder}/miamsClf_cCount_s300

rm ${results_folder}/results_miams.tsv


Sklearn classifiers
grep -v "MSINGS" ${results_folder}/results.tsv > ${results_folder}/results_sklearnClf.tsv
sed -i 's/SVCPairs/SVM/' ${results_folder}/results_sklearnClf.tsv

../processAccuracy.py \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --input-datasets ${results_folder}/datasets.tsv \
    --input-results ${results_folder}/results_sklearnClf.tsv \
    --output-folder ${results_folder}/sklearnClf_cCount_s300

rm ${results_folder}/results_sklearnClf.tsv
