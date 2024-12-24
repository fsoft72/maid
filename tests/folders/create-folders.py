#!/usr/bin/env python3

import bz2
import os
import pathlib
import argparse


def create_structure(bz2_file, dest_path):
    # Create base destination directory
    pathlib.Path(dest_path).mkdir(parents=True, exist_ok=True)

    # Read and process bz2 file
    with bz2.open(bz2_file, "rt") as f:
        for line in f:
            # Clean path and join with destination
            rel_path = line.strip()
            full_path = os.path.join(dest_path, rel_path)

            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)

            # Create empty file
            pathlib.Path(full_path).touch()


def main():
    parser = argparse.ArgumentParser(
        description="Create folder structure from bz2 file"
    )
    parser.add_argument(
        "bz2_file", help="Path to the bz2 file containing folder structure"
    )
    parser.add_argument(
        "dest_path", help="Destination path where to create the structure"
    )

    args = parser.parse_args()
    create_structure(args.bz2_file, args.dest_path)


if __name__ == "__main__":
    main()
