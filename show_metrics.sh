#!/usr/bin/env bash

set -euo pipefail 

set -x
iostat

set +x
METRICS_LIST=(
rocksdb_bloom_filter_useful
rocksdb_bloom_filter_checked
rocksdb_block_cache_data_hit
rocksdb_block_cache_data_miss
)

metrics_re=""
for metric in "${METRICS_LIST[@]}"; do
  if [[ -n ${metrics_re} ]]; then
    metrics_re+="|"
  fi
  metrics_re+=$metric
done

curl -s http://localhost:9000/prometheus-metrics |
  grep -E "test_table" |
  grep -wE "${metrics_re}" |
  sed 's/expo.*9000..//' |
  sed 's/[0-9]*$//' |
  tr " " "\n"

