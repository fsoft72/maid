#!/usr/bin/env python3

import argparse
import os
import mimetypes
import logging
import sys
from pathlib import Path
import fnmatch


def is_binary(file_path):
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, "tr") as check_file:
            check_file.read()
            return False
    except (IOError, OSError):
        return True


def process_file(file_path, markdown_content):
    """
    Process a single file and add its content to the markdown.
    """
    file_path = Path(file_path)
    if is_binary(file_path):
        file_type = mimetypes.guess_type(file_path)[0] or "Unknown"
        file_size = file_path.stat().st_size
        markdown_content.append(
            "---------------------------------------------------------------------\n"
        )
        markdown_content.append(f"## {file_path}\n")
        markdown_content.append(
            "---------------------------------------------------------------------\n"
        )
        markdown_content.append(f"- Type: {file_type}\n")
        markdown_content.append(f"- Size: {file_size} bytes\n\n")
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        markdown_content.append(
            "---------------------------------------------------------------------\n"
        )
        markdown_content.append(f"## {file_path}\n")
        markdown_content.append("```\n")
        markdown_content.append(content)
        markdown_content.append("\n```\n")
        markdown_content.append(
            "---------------------------------------------------------------------\n\n\n"
        )


def is_blacklisted(file_path, blacklist):
    """
    Check if a file matches any of the blacklist patterns.
    """
    filename = os.path.basename(file_path)
    return any(fnmatch.fnmatch(filename, pattern) for pattern in blacklist)


def load_maidignore(directory):
    """
    Load .maidignore file from a directory.
    """
    maidignore_path = os.path.join(directory, ".maidignore")
    if os.path.exists(maidignore_path):
        with open(maidignore_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


def scan_directory(directory, markdown_content, global_blacklist, use_local_maidignore):
    """
    Recursively scan a directory and process all files.
    """
    for root, dirs, files in os.walk(directory):
        local_blacklist = global_blacklist.copy()

        if use_local_maidignore:
            local_blacklist.extend(load_maidignore(root))

        # Filter out blacklisted directories
        dirs[:] = [d for d in dirs if not is_blacklisted(d, local_blacklist)]

        for file in files:
            file_path = os.path.join(root, file)
            if not is_blacklisted(file_path, local_blacklist):
                process_file(file_path, markdown_content)
            else:
                logging.info(f"Skipped blacklisted file: {file_path}")


def load_blacklist(blacklist_file):
    """
    Load blacklist from a file.
    """
    with open(blacklist_file, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def main():
    parser = argparse.ArgumentParser(
        description="Create an aggregated Markdown file from directories and files."
    )
    parser.add_argument("paths", nargs="+", help="Directories or files to process")
    parser.add_argument("-o", "--output", required=True, help="Output Markdown file")
    parser.add_argument("--log", action="store_true", help="Enable logging")
    parser.add_argument(
        "--blacklist",
        action="append",
        default=[".git", "__pycache__", "*.log", "LICENSE"],
        help="Glob patterns for files or directories to skip (matched against filename only)",
    )
    parser.add_argument(
        "--blacklist-file", help="File containing blacklist glob patterns"
    )
    parser.add_argument(
        "--local-maidignore",
        action="store_true",
        help="Enable reading of .maidignore files in directories",
    )
    args = parser.parse_args()

    if args.log:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    blacklist = args.blacklist

    if args.blacklist_file:
        blacklist.extend(load_blacklist(args.blacklist_file))

    logging.info(f"Using global blacklist patterns: {blacklist}")

    markdown_content = []

    for path in args.paths:
        if os.path.isdir(path):
            logging.info(f"Scanning directory: {path}")
            scan_directory(path, markdown_content, blacklist, args.local_maidignore)
        elif os.path.isfile(path):
            if not is_blacklisted(path, blacklist):
                logging.info(f"Processing file: {path}")
                process_file(path, markdown_content)
            else:
                logging.info(f"Skipped blacklisted file: {path}")
        else:
            logging.warning(f"Invalid path: {path}")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))

    logging.info(f"Markdown file created: {args.output}")


if __name__ == "__main__":
    main()
