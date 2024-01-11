#!/usr/bin/env bash

set -euo pipefail -x

METRICS_RE="\
rocksdb_bloom_filter_useful|\
rocksdb_bloom_filter_checked|\
rocksdb_block_cache_data_hit|\
rocksdb_block_cache_data_miss\
"
curl -s http://localhost:9000/prometheus-metrics |
  grep -E "test_table" |
  grep -wE "${METRICS_RE}" |
  sed 's/expo.*9000..//' |
  sed 's/[0-9]*$//' |
  tr " " "\n"
