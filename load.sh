#!/usr/bin/env bash
set -euo pipefail

print_usage() {
  cat >&2 <<-EOT
Usage: ${0##*/} <options>
Options:
  -h, --help
    Print usage

  -n, --num_rows <num_rows>
    Number of rows to load.

  -r, --yb_root
    YugabyteDB source root directory or YugabyteDB binary distribution directory.
EOT
}

cleanup() {
  rm -f "$tmp_sql_script"
}

num_rows=1000000
yb_root=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_usage
      exit
    ;;
    -n|--num_rows)
      num_rows=$2
      shift
    ;;
    -r|--yb_root)
      yb_root=$2
      shift
    ;;
    *)
      echo >&2 "Invalid option: $1"
      exit 1
    ;;
  esac
  shift
done
if [[ ! $num_rows =~ ^[0-9]+$ ]]; then
  echo >&2 "Invalid number of rows: $num_rows"
  exit 1
fi
if [[ -z $yb_root ]]; then
  echo >&2 "--yb_root not specified" >&2
  exit 1
fi
if [[ ! -f $yb_root/bin/yb-ctl ]]; then
  echo >&2 "$yb_root does not seem like a valid YugabyteDB source or installation directory."
  exit 1
fi

rows_per_group=10000
num_groups=$(( num_rows / rows_per_group ))
effective_num_rows=$(( num_groups * rows_per_group ))
echo "Number of rows: $effective_num_rows"
if [[ $effective_num_rows -ne $num_rows ]]; then
  echo >&2 "Warning: --num_rows specified as $num_rows"
fi
log_dir=~/logs/ysql_bulk_load
mkdir -p "$log_dir"
timestamp=$( date +%Y-%m-%dT%H_%M_%S )
log_path=$log_dir/ysql_bulk_load_${num_rows}_${timestamp}.log
script_dir=$( cd "$( dirname "$0" )" && pwd )
tmp_sql_script=/tmp/bulk_load_tmp_${timestamp}_${RANDOM}_${RANDOM}_${RANDOM}.sql
trap cleanup EXIT
sed "s/NUM_GROUPS/$num_groups/" "$script_dir/bulk_load.sql" >"$tmp_sql_script"
echo "Logging to $log_path"
(
set -x
cd "$yb_root"
bin/yb-ctl wipe_restart
git log -n 1
bin/ysqlsh -f "$tmp_sql_script"
) |& tee "$log_path"

echo "Saved log to $log_path"
