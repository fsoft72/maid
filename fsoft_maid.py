#!/usr/bin/env python3

# flake8: noqa: E203

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

try:
    from fsoft_maid.lib.pattern_matcher import PatternMatcher
except ImportError:
    from lib.pattern_matcher import PatternMatcher

VERSION = "0.4.6"

# default patterns
PATTERNS = [
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
_files_excluded = []

_files_binaries = []  # Files treated as binaries
_binaries = set(
    [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "ico",
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "zip",
        "rar",
        "7z",
        "gz",
        "tar",
        "tgz",
        "bz2",
        "xz",
        "mp3",
        "wav",
        "mp4",
        "avi",
        "mov",
        "mkv",
        "flv",
        "swf",
        "exe",
        "dll",
        "svg",
    ]
)  # This is a list of extensions that are considered binary files

PROFILES = {
    "c#": {
        "patterns": [
            "*.csproj",
            "*.user",
            "*.xaml",
            "*.xml",
            "*.css",
            "*.xslt",
            "*.json",
            "*.dll",
            "*.csproj.*",
            "*.png",
            "*.trdp",
            "*.targets",
            "*.props",
            "*.jpg",
            "*.jpeg",
            "*.cache",
            "*.editorconfig",
            "Debug",
            "obj",
            "*.vsidx",
            "*.lock",
            "*.v2",
            "*.suo",
            "Release",
            "*.ico",
            "*.licx",
        ]
    },
    "no-images": {"patterns": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico"]},
}


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


# ==================================
# GLOBAL VARIABLES
# ==================================

matcher = PatternMatcher(PATTERNS)


def is_binary(file_path):
    """
    Check if a file is binary, handling UTF-16 files with BOM.
    """

    #  get the file extension (lowercase, without the dot)
    ext = os.path.splitext(file_path)[1]
    ext = ext.lower().replace(".", "")
    if ext in _binaries:
        _files_binaries.append(file_path)
        return True

    try:
        # Check first few bytes for UTF-16 BOM
        with open(file_path, "rb") as check_file:
            header = check_file.read(2)
            if header.startswith(b"\xfe\xff") or header.startswith(b"\xff\xfe"):
                return False

        # Try reading as regular text
        with open(file_path, "rt") as check_file:
            check_file.read()
            return False
    except (IOError, OSError, UnicodeDecodeError):
        _files_binaries.append(file_path)
        return True


def _apply_rules(file_name, content, rules):
    import logging

    do_debug = False

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

        # Try reading with UTF-16 first if it has BOM
        try:
            with open(file_path, "rb") as f:
                header = f.read(2)
                f.seek(0)
                if header.startswith(b"\xfe\xff") or header.startswith(b"\xff\xfe"):
                    content = open(file_path, "r", encoding="utf-16").readlines()
                else:
                    content = open(
                        file_path, "r", encoding="utf-8", errors="ignore"
                    ).readlines()
        except Exception as e:
            logging.warning(f"Error reading file {file_path}: {e}")
            content = []

        content = _apply_rules(file_path, content, rules)

        ext = _ext2markdown(file_path)
        markdown_content.append(("-" * 40) + "\n\n")
        markdown_content.append(f"## FILE: `{file_path}`\n\n")
        markdown_content.append("```%s\n" % ext)
        if ext == "markdown":
            content = content.replace("```", "'''")

        markdown_content.append(content)
        markdown_content.append("```\n\n")


def _extend_unique(target_list, new_items, key_func=None):
    """
    Extend a list with new items, avoiding duplicates.
    For rules, key_func should return the rule's unique identifier (name).
    For patterns, key_func is None and items are compared directly.
    """
    if not new_items:
        return

    if key_func is None:
        # For simple items like patterns
        existing = set(target_list)
        for item in new_items:
            if item not in existing:
                target_list.append(item)
                existing.add(item)
    else:
        # For complex items like rules
        existing = {key_func(item) for item in target_list}
        for item in new_items:
            key = key_func(item)
            if key not in existing:
                target_list.append(item)
                existing.add(key)


def load_maid_conf(directory, patterns, rules):
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
        _extend_unique(patterns, dct["patterns"])
    if "rules" in dct:
        _extend_unique(rules, dct["rules"], lambda x: x["name"])


def scan_directory(directory, markdown_content, global_patterns, global_rules):
    """
    Recursively scan a directory and process all files.
    """
    import os
    import logging

    # Copy global patterns and rules to local variables
    patterns = global_patterns.copy()
    rules = global_rules.copy()

    # Load local configuration
    load_maid_conf(directory, patterns, rules)
    matcher.clear_patterns()
    matcher.add_patterns(PATTERNS)
    matcher.add_patterns(patterns)

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
        if not matcher.matches(file_path):
            process_file(file_path, markdown_content, rules)
        else:
            _files_excluded.append(file_path)
            logging.info(f"Skipped ignored file: {file_path}")

    # Recursively process subdirectories
    for subdir in subdirs:
        subdir_path = os.path.join(directory, subdir)
        if not matcher.matches(subdir_path):
            scan_directory(subdir_path, markdown_content, patterns, rules)
        else:
            _files_excluded.append(subdir_path)
            logging.info(f"Skipped ignored directory: {subdir_path}")


def _maid_init(args):
    rules = []
    patterns = args.pattern

    # Handle profiles first
    if args.profile:
        for profile_name in args.profile:
            if profile_name in PROFILES:
                profile = PROFILES[profile_name]
                if "patterns" in profile:
                    _extend_unique(patterns, profile["patterns"])
                if "rules" in profile:
                    _extend_unique(rules, profile["rules"], lambda x: x["name"])
            else:
                logging.warning(f"Profile '{profile_name}' not found")

    if args.maid_file:
        load_maid_conf(args.maid_file, patterns, rules)

    # load global patterns from home directory '.maid.json' if exists
    home = str(Path.home())
    dirs = [home, os.path.join(home, ".local", "share"), os.path.join(home, ".config")]

    for d in dirs:
        load_maid_conf(d, patterns, rules)

    if args.binary:
        _binaries.update([ext.replace(".", "").lower() for ext in args.binary])

    if args.no_binary:
        # remove from binaries
        for ext in args.no_binary:
            _binaries.discard(ext.replace(".", "").lower())

    return patterns, rules


def _dump_conf(patterns, rules):
    print("\n=== Active Patterns ===")
    for pattern in matcher.patterns:
        print(f"- {pattern}")

    print("\n=== Active Rules ===")
    for rule in rules:
        print(f"- {rule['name']}")
        print(f"  Pattern: {rule['pattern']}")
        print(f"  Start: {rule['start']}")
        print(f"  Delete: {rule['delete']}")
        if "keep_start" in rule:
            print(f"  Keep Start: {rule['keep_start']}")
        print()


def main():
    global matcher

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
        "--pattern",
        action="append",
        default=PATTERNS,
        help="Glob patterns for files or directories to skip (matched against filename only)",
    )
    parser.add_argument(
        "--maid-file",
        help="File containing Maid configuration (maid.json)",
        default="maid.json",
    )
    parser.add_argument(
        "--profile",
        action="append",
        help="Load settings from predefined profile (can be used multiple times)",
    )

    parser.add_argument(
        "--binary", action="append", help="File extensions to treat as binary"
    )

    parser.add_argument(
        "--no-binary", action="append", help="File extensions to treat as non-binary"
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    if args.log:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    patterns = []
    rules = []

    patterns, rules = _maid_init(args)

    if args.verbose:
        _dump_conf(patterns, rules)

    logging.info(f"Ignored patterns: {patterns}")

    markdown_content = [
        "# Content\n\nThis file was generated by [Maid](https://github.com/fsoft72/maid) v%s - by [Fabio Rotondo](https://github.com/fsoft72)\n\n"
        % VERSION
    ]

    for path in args.paths:
        if os.path.isdir(path):
            logging.info(f"Scanning directory: {path}")

            scan_directory(path, markdown_content, patterns, rules)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))

    logging.info(f"Markdown file created: {args.output}")

    if args.verbose:
        print("\n=== Included files: ")
        for f in _files_included:
            print(f)

        print("\n=== Excluded files: ")
        for f in _files_excluded:
            print(f)

        print("\n=== Binary files: ")
        for f in _files_binaries:
            print(f)


if __name__ == "__main__":
    main()
