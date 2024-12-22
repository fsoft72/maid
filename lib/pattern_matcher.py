#!/usr/bin/env python3

# flake8: noqa: E203

import re
from pathlib import Path
from typing import Union, Sequence


class PatternMatcher:
    """
    A class to match file paths against a set of glob patterns and exclusion patterns.

    This class allows you to add glob patterns and exclusion patterns to match file paths.
    Patterns can be added individually or as a sequence. The class supports checking if
    a given file path matches any of the added patterns.

    Internal Attributes:
        _patterns (list[str]): A list of patterns to match against.
        _optimized (bool): A flag indicating whether the patterns have been optimized.

    Public properties:
        patterns (list[str]): A list of optimized patterns.

    Internal Methods:
        __init__(patterns: Sequence[str] = None):
            Initialize a new PatternMatcher instance.
        _ensure_optimized() -> None:
            Ensure the patterns are optimized for matching.
        _normalize_path(path: str) -> str:
            Normalize a file path by stripping leading "./" or "/".
        _convert_to_regex(pattern: str) -> str:
            Convert a glob pattern to a regular expression.

    Public Methods:
        add_pattern(pattern: str) -> None:
            Add a single pattern to the matcher.
        add_patterns(patterns: Sequence[str]) -> None:
            Add multiple patterns to the matcher.
        matches(filepath: Union[str, Path]) -> bool:
            Check if a filepath matches any of the patterns.
    """

    def __init__(self, patterns: Sequence[str] = None):
        """Initialize a new PatternMatcher instance.

        Args:
            patterns (Sequence[str], optional): A sequence of patterns to add.
                Each pattern can be a glob pattern or an exclusion pattern starting
                with "!". Defaults to None.

        Examples:
            >>> matcher = PatternMatcher(["*.py", "!test_*.py"])
        """
        self._patterns: list[str] = []
        self._optimized = False
        if patterns:
            self.add_patterns(patterns)

    def _ensure_optimized(self) -> None:
        if not self._optimized:
            self._patterns.sort(key=lambda x: not x.startswith("!"))
            self._patterns = [
                f"{p}**" if p.endswith("/") else p
                for p in dict.fromkeys(p.strip() for p in self._patterns)
            ]
            self._optimized = True

    def _normalize_path(self, path: str) -> str:
        path = path.strip()
        return (
            path[2:]
            if path.startswith("./")
            else path[1:] if path.startswith("/") else path
        )

    def _convert_to_regex(self, pattern: str) -> str:
        parts = []
        i = 0
        while i < len(pattern):
            if pattern[i] == "*":
                parts.append(
                    ".*" if i + 1 < len(pattern) and pattern[i + 1] == "*" else "[^/]*"
                )
                i += 1 + (pattern[i : i + 2] == "**")
            elif pattern[i] == "?":
                parts.append("[^/]")
                i += 1
            elif pattern[i] == "[":
                j = pattern.find("]", i + 1)
                parts.append(pattern[i : j + 1] if j != -1 else re.escape(pattern[i]))
                i = j + 1 if j != -1 else i + 1
            else:
                parts.append(re.escape(pattern[i]))
                i += 1
        return f"^{''.join(parts)}$"

    def add_pattern(self, pattern: str) -> None:
        """Add a single pattern to the matcher.

        Args:
            pattern (str): The pattern to add. Can be a glob pattern (e.g. "*.py")
                or an exclusion pattern starting with "!" (e.g. "!*.pyc").

        Examples:
            >>> matcher = PatternMatcher()
            >>> matcher.add_pattern("*.py")
            >>> matcher.add_pattern("!test_*.py")
        """
        self._patterns.append(pattern)
        self._optimized = False

    def add_patterns(self, patterns: Sequence[str]) -> None:
        """Add multiple patterns to the matcher.

        Args:
            patterns (Sequence[str]): A sequence of patterns to add. Each pattern can be
                a glob pattern or an exclusion pattern starting with "!".

        Examples:
            >>> matcher = PatternMatcher()
            >>> matcher.add_patterns(["*.py", "!test_*.py", "src/**/*.py"])
        """
        self._patterns.extend(patterns)
        self._optimized = False

    def clear_patterns(self) -> None:
        """Clear all patterns from the matcher.

        Examples:
            >>> matcher = PatternMatcher(["*.py", "!test_*.py"])
            >>> matcher.clear_patterns()
            >>> matcher.patterns
            []
        """
        self._patterns.clear()
        self._optimized = False

    def matches(self, filepath: Union[str, Path]) -> bool:
        """Check if a filepath matches any of the patterns.

        Args:
            filepath (Union[str, Path]): The path to check against the patterns.
                Can be either a string or a Path object.

        Returns:
            bool: True if the path matches any of the inclusion patterns and none
                of the exclusion patterns, False otherwise.

        Examples:
            >>> matcher = PatternMatcher(["*.py", "!test_*.py"])
            >>> matcher.matches("foo.py")
            True
            >>> matcher.matches("test_foo.py")
            False
        """
        self._ensure_optimized()
        filepath = self._normalize_path(str(filepath))

        for pattern in self._patterns:
            if not pattern or pattern.startswith("#"):
                continue

            is_negation = pattern.startswith("!")
            pattern = self._normalize_path(pattern[1:] if is_negation else pattern)
            regex = self._convert_to_regex(pattern)

            path_parts = filepath.split("/")
            if any(
                re.match(regex, "/".join(path_parts[i:]))
                for i in range(len(path_parts))
            ):
                return not is_negation

        return False

    @property
    def patterns(self) -> list[str]:
        self._ensure_optimized()
        return self._patterns.copy()


if __name__ == "__main__":
    matcher = PatternMatcher(
        [
            "!important.pyc",
            "./*.py",
            "*.py[cod]",
            "temp/",
            "!./temp/important.txt",
            "/root_only.txt",
        ]
    )

    # Add new patterns
    matcher.add_pattern("*.json")
    matcher.add_patterns(["!test/*.log", "docs/"])

    def test_file(filepath: str, expected_result: bool):
        res = matcher.matches(filepath)

        if res != expected_result:
            print(f"Test failed for {filepath}: expected {expected_result}, got {res}")

    test_file("./file.py", True)
    test_file("./temp/test.txt", True)
    test_file("temp/test.txt", True)
    test_file("./temp/important.txt", False)
    test_file("file.py", True)
    test_file("temp/important.txt", False)
    test_file("file.pyc", True)
    test_file("important.pyc", False)
    test_file("temp/file.txt", True)
    test_file("root_only.txt", True)
    test_file("important.json", True)
    test_file("test/file.log", False)
    test_file("docs/file.txt", True)

    print(matcher.patterns)
