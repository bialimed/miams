#!/bin/bash
unset PYTHONPATH

data_dir=`dirname $0`
assessment_dir=`dirname ${data_dir}`
doc_dir=`dirname ${assessment_dir}`
app_dir=`dirname ${doc_dir}`
res_dir=${data_dir}/results

mkdir -p ${res_dir}

source ${app_dir}/doc/assessment/venv/bin/activate
${app_dir}/doc/assessment/processAssessment.py \
  --nb-tests 10 \
  --instability-ratio 0.3 \
  --add-classifiers DecisionTree KNeighbors LogisticRegression RandomForest RandomForest:50 \
  --data-folder ${data_dir} \
  --work-folder ${data_dir}/work \
  --results-path ${res_dir}/results.tsv \
  --datasets-path ${res_dir}/datasets.tsv
sed -i 's/SVCPairs/SVM/' ${res_dir}/results.tsv
