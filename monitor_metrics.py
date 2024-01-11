#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description="Monitor log and extract counter values.")
    parser.add_argument("process_id", type=int, help="The process ID to monitor.")
    parser.add_argument("log_path", type=str, help="The path to the log file.")
    parser.add_argument("output_log_path", type=str, help="The path to the output log file.")
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.output_log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    log_file = open(args.log_path, "r")
    counter_pattern = r"ysqlsh:.*?NOTICE:  \[.*?\] counter: (\d+)"

    while True:
        # Check if the process is still running
        if not os.path.exists("/proc/" + str(args.process_id)):
            logging.info(f"Process {args.process_id} has terminated.")
            break

        # Seek to the end of the log file
        log_file.seek(0, os.SEEK_END)

        while True:
            # Read a line from the end of the log file
            line = log_file.readline()
            if not line:
                time.sleep(0.1)  # Wait for more log output
                continue

            # Check if the line matches the counter pattern
            match = re.search(counter_pattern, line)
            if match:
                counter_value = int(match.group(1))
                logging.info(f"Counter value: {counter_value}")
                logging.info(f"Current timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                # Execute show_metrics.sh and pipe output to the log
                try:
                    subprocess.run(
                        ["./show_metrics.sh"],
                        check=True,
                        stdout=logging.getLogger().handlers[0].stream,
                        stderr=subprocess.STDOUT,
                    )
                except subprocess.CalledProcessError as exc:
                    logging.error(f"Error executing show_metrics.sh: {exc}")

                break

    log_file.close()


if __name__ == '__main__':
    main()