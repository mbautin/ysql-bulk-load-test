#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import time

from datetime import datetime


TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def main():
    parser = argparse.ArgumentParser(description="Monitor log and extract counter values.")
    parser.add_argument(
            "--process_id", type=int, help="The process ID to monitor.", required=True)
    parser.add_argument(
            "--log_path", type=str, help="The path to the log file.", required=True)
    parser.add_argument(
            "--output_log_path", type=str, help="The path to the output log file.", required=True)
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.output_log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    log_file = open(args.log_path, "r")

    # Example:
    # NOTICE:  [2024-01-11 07:41:43.767624+00s] counter: 740000
    counter_pattern = r"ysqlsh:.*?NOTICE:  \[(.*)\] counter: (\d+)"

    metrics_script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'show_metrics.sh')

    first_ts = None
    prev_counter = None
    prev_ts = None

    while True:
        # Check if the process is still running
        if not os.path.exists("/proc/" + str(args.process_id)):
            logging.info(f"Process {args.process_id} has terminated.")
            break

        line = log_file.readline()
        if not line:
            time.sleep(0.1)  # Wait for more log output
            continue

        # Check if the line matches the counter pattern
        match = re.search(counter_pattern, line)
        if match:
            timestamp_from_log_str = match.group(1)
            if timestamp_from_log_str.endswith('+00s'):
                timestamp_from_log_str = timestamp_from_log_str[:-4]
            parsed_ts_from_log = datetime.strptime(timestamp_from_log_str, TIME_FORMAT)
            current_ts = datetime.now()
            if first_ts is None:
                first_ts = parsed_ts_from_log

            delta_sec = abs((current_ts - parsed_ts_from_log).total_seconds())

            counter_value = int(match.group(2))
            logging.info(f"Counter value: {counter_value}")
            actual_time_str = current_ts.strftime(TIME_FORMAT)
            logging.info(f"Current timestamp: {actual_time_str}")
            logging.info(f"Timestamp from bulk load log: {timestamp_from_log_str}")
            elapsed_time_sec = (parsed_ts_from_log - first_ts).total_seconds()
            logging.info("Elapsed time since first batch: %.3f sec", elapsed_time_sec)
            if prev_ts is not None:
                time_since_last_batch = (parsed_ts_from_log - prev_ts).total_seconds()
                logging.info("Time since previous batch: %.3f sec", time_since_last_batch)
                if time_since_last_batch > 0:
                    logging.info(
                        "Rows inserted per second: %.3f",
                        (counter_value - prev_counter) / time_since_last_batch)

            prev_ts = parsed_ts_from_log
            prev_counter = counter_value

            if delta_sec >= 2:
                logging.warning(
                    "LARGE DELTA BETWEEN CURRENT TIMESTAMP AND TIMESTAMP FROM LOG: %.3f sec",
                    delta_sec)
            else:
                logging.info("Acceptable delta between timestamps: %.3f sec", delta_sec)

            # Execute show_metrics.sh and pipe output to the log
            try:
                subprocess.run(
                    [metrics_script_path],
                    check=True,
                    stdout=logging.getLogger().handlers[0].stream,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as exc:
                logging.error(f"Error executing show_metrics.sh: {exc}")

    log_file.close()


if __name__ == '__main__':
    main()
