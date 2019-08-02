  #!/bin/bash
  unset PYTHONPATH

  data_dir=`dirname $0`
  assessment_dir=`dirname ${data_dir}`
  doc_dir=`dirname ${assessment_dir}`
  app_dir=`dirname ${doc_dir}`
  res_dir=${data_dir}/results

  mkdir -p ${res_dir}

  source ${app_dir}/doc/assessment/venv/bin/activate
  ${app_dir}/doc/assessment/processAccuracy.py \
    --instability-ratio 0.21 \
    --process-balanced-metrics \
    --add-algorithm-consensus \
    --input-datasets ${res_dir}/datasets.tsv \
    --input-results ${res_dir}/results.tsv \
    --output-folder ${res_dir}/accuracy
