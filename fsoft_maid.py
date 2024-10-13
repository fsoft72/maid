#!/usr/bin/env python3

"""
Program Name: Maid
Usage: Aggregates Markdown files from directories and files.
Author: Fabio Rotondo
License: MIT License
"""

"""
Example of rules:

    "rules": [
        {
            "pattern": "*.tscn",
            "name": "subres RectangleShape",
            "match": ".sub_resource.*type=.RectangleShape",
            "delete": "::empty::"
        }
    ]

The rule above will apply only on files with extension '.tscn' and will remove all lines
from the content from the one starting with RegEx '.sub_resource.*type=.RectangleShape',
up to the first empty line.
"""


import argparse
import json
import os
import mimetypes
import logging
import re
import sys
from pathlib import Path
import fnmatch

VERSION = "0.3.6"

# default blacklist
BLACKLIST = [
    ".git",
    ".gitignore",
    ".gitattributes",
    ".gitsubmodules",
    "maid.json",
    "__pycache__",
    "*.log",
    "LICENSE",
    "node_modules",
    "*.bak",
    "*.old",
]

_loaded_confs = {}
_files_included = []


def _ext2markdown(fname):
    ext = os.path.splitext(fname)[1]
    ext = ext.lower()
    return {
        ".py": "python",
        ".sh": "bash",
        ".js": "javascript",
        ".json": "json",
        ".svelte": "svelte",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".txt": "text",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".xml": "xml",
        ".csv": "csv",
        ".ts": "typescript",
        ".sql": "sql",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".kt": "kotlin",
        ".swift": "swift",
        ".m": "objectivec",
        ".pl": "perl",
        ".r": "r",
        ".lua": "lua",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".psm1": "powershell",
        ".psd1": "powershell",
        ".ps1xml": "powershell",
        ".pssc": "powershell",
        ".psrc": "powershell",
        ".gd": "gdscript",
        ".tscn": "gdscript",
    }.get(ext, "text")


def is_binary(file_path):
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, "rt") as check_file:
            check_file.read()
            return False
    except (IOError, OSError, UnicodeDecodeError):
        return True


def _apply_rules(file_name, content, rules):
    import fnmatch
    import logging

    do_debug = False
    """
    if str(file_name).endswith("theme.ts"):
        print("=== FILE: ", file_name, rules)
        do_debug = True
    """

    for rule in rules:
        if do_debug:
            print(
                "=== RULE: ",
                file_name,
                rule["name"],
                rule["pattern"],
                fnmatch.fnmatch(file_name, rule["pattern"]),
            )
        if fnmatch.fnmatch(file_name, rule["pattern"]):
            logging.info(f"Applying rule: {rule['name']} to {file_name}")

            match_regex = re.compile(rule["start"])
            delete_pattern = rule["delete"]
            delete_regex = re.compile(delete_pattern)
            keep_match = rule.get("keep_start", False)
            indices_to_delete = []

            i = 0
            while i < len(content):
                line = content[i]
                if match_regex.search(line):
                    # print("=== START MATCH: ", line)
                    if keep_match:
                        start = i + 1
                    else:
                        start = i

                    end = None
                    j = start

                    if delete_pattern == "::line::":
                        end = start
                    else:
                        while j < len(content):
                            delete_line = content[j]
                            if (
                                delete_pattern == "::empty::"
                                and not delete_line.strip()
                            ):
                                end = j
                                break
                            if delete_regex.search(delete_line):
                                # print("=== END MATCH: ", delete_line)
                                end = j
                                break
                            j += 1
                    if end is None:
                        end = len(content) - 1
                    indices_to_delete.append((start, end))
                    i = end + 1
                else:
                    i += 1

            for start, end in reversed(indices_to_delete):
                # logging.info(f"Deleting lines {start} to {end} in {file_name}")
                del content[start : end + 1]

            # open(f"/ramdisk/step-{rule['name']}.txt", "w").write("".join(content))

    return "".join(content)


def process_file(file_path, markdown_content, rules):
    """
    Process a single file and add its content to the markdown.
    """
    _files_included.append(file_path)
    file_path = Path(file_path)
    if is_binary(file_path):
        file_type = mimetypes.guess_type(file_path)[0] or "Unknown"
        file_size = file_path.stat().st_size
        markdown_content.append(("-" * 40) + "\n")
        markdown_content.append(
            f"## FILE: `{file_path}` - Type: {file_type} - Size: {file_size} bytes\n"
        )
    else:
        logging.info(f"Processing file: {file_path}")

        content = open(file_path, "r", encoding="utf-8", errors="ignore").readlines()

        content = _apply_rules(file_path, content, rules)

        ext = _ext2markdown(file_path)
        markdown_content.append(("-" * 40) + "\n\n")
        markdown_content.append(f"## FILE: `{file_path}`\n\n")
        markdown_content.append("```%s\n" % ext)
        if ext == "markdown":
            content = content.replace("```", "'''")

        markdown_content.append(content)
        markdown_content.append("```\n\n")


def is_blacklisted(file_path, blacklist):
    """
    Check if a file matches any of the blacklist patterns.
    """
    filename = os.path.basename(file_path)
    return any(fnmatch.fnmatch(filename, pattern) for pattern in blacklist)


def load_maid_conf(directory, blacklist, rules):
    """
    Load maid.json file from a directory.
    """
    maid_conf_path = os.path.join(directory, "maid.json")
    hidden_conf_path = os.path.join(directory, ".maid.json")
    p = None

    if os.path.exists(maid_conf_path):
        logging.info(f"Found maid.json in {directory}")
        p = maid_conf_path

    elif os.path.exists(hidden_conf_path):
        logging.info(f"Found .maid.json in {directory}")
        p = hidden_conf_path

    if not p:
        return

    if maid_conf_path in _loaded_confs:
        return

    _loaded_confs[maid_conf_path] = True

    dct = json.loads(open(p, "r").read())
    if "patterns" in dct:
        blacklist.extend(dct["patterns"])
    if "rules" in dct:
        rules.extend(dct["rules"])


def scan_directory(directory, markdown_content, global_blacklist, global_rules):
    """
    Recursively scan a directory and process all files.
    """
    import os
    import logging

    # Copy global blacklist and rules to local variables
    blacklist = global_blacklist.copy()
    rules = global_rules.copy()

    # Load local configuration
    load_maid_conf(directory, blacklist, rules)

    logging.info(f"Scanning directory: {directory}")

    try:
        entries = os.listdir(directory)
    except PermissionError:
        logging.warning(f"Permission denied: {directory}")
        return

    files = []
    subdirs = []

    # Separate files and directories
    for entry in entries:
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path):
            files.append(entry)
        elif os.path.isdir(full_path):
            subdirs.append(entry)

    # Process files in the current directory
    for file in files:
        file_path = os.path.join(directory, file)
        if not is_blacklisted(file_path, blacklist):
            process_file(file_path, markdown_content, rules)
        else:
            logging.info(f"Skipped blacklisted file: {file_path}")

    # Recursively process subdirectories
    for subdir in subdirs:
        subdir_path = os.path.join(directory, subdir)
        if not is_blacklisted(subdir_path, blacklist):
            scan_directory(subdir_path, markdown_content, blacklist, rules)
        else:
            logging.info(f"Skipped blacklisted directory: {subdir_path}")


def _maid_init(args):
    rules = []
    blacklist = args.blacklist

    if args.maid_file:
        load_maid_conf(args.maid_file, blacklist, rules)

    # load global blacklist from home directory '.maid.json' if exists
    home = str(Path.home())
    dirs = [home, os.path.join(home, ".local", "share"), os.path.join(home, ".config")]

    for d in dirs:
        load_maid_conf(d, blacklist, rules)

    return blacklist, rules


def main():
    parser = argparse.ArgumentParser(
        description="Create an aggregated Markdown file from directories and files."
    )
    parser.add_argument("paths", nargs="+", help="Directories or files to process")
    parser.add_argument(
        "-o",
        "--output",
        help="Output Markdown file full path (default: _content.md)",
        default="_content.md",
    )
    parser.add_argument("--log", action="store_true", help="Enable logging")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--blacklist",
        action="append",
        default=BLACKLIST,
        help="Glob patterns for files or directories to skip (matched against filename only)",
    )
    parser.add_argument(
        "--maid-file",
        help="File containing Maid configuration (maid.json)",
        default="maid.json",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    if args.log:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    blacklist = []
    rules = []

    blacklist, rules = _maid_init(args)

    logging.info(f"Blacklist patterns: {blacklist}")

    markdown_content = [
        "# Content\n\nThis file was generated by [Maid](https://github.com/fsoft72/maid) v%s - by [Fabio Rotondo](https://github.com/fsoft72)\n\n"
        % VERSION
    ]

    for path in args.paths:
        if os.path.isdir(path):
            logging.info(f"Scanning directory: {path}")
            _blacklist = blacklist.copy()
            _rules = rules.copy()

            load_maid_conf(path, _blacklist, _rules)

            scan_directory(path, markdown_content, _blacklist, _rules)
        elif os.path.isfile(path):
            if not is_blacklisted(path, blacklist):
                logging.info(f"Processing file: {path}")
                process_file(path, markdown_content, rules)
            else:
                logging.info(f"Skipped blacklisted file: {path}")
        else:
            logging.warning(f"Invalid path: {path}")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))

    logging.info(f"Markdown file created: {args.output}")

    if args.verbose:
        print("=== Included files: ")
        for f in _files_included:
            print(f)


if __name__ == "__main__":
    main()
