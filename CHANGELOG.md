# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1] - 2024-10-07

- Fixed issue with reading global `maid.json` file.
- Removed some linter warnings.

## [0.3.0] - 2024-10-07

- Breaking: removed support for '.maidignore' files, now use 'maid.json' instead.
- Added support for reading 'maid.json' file.
- Added support for rules in 'maid.json' file.
- Updated README.md with new usage instructions.

## [0.2.1] - 2024-10-07

- Enhanced markdown output with better formatting for filenames.
- Enhanced markdown output for binary files.
- Fixed issue with reading global `.maidignore` file.
- Fixed issue with reading local `.maidignore` file.
- Fixed is_binary() exception on special files.

## [0.2.0] - 2024-10-05

- Added support for reading local `.maidignore` files.
- Added support for reading global `.maidignore` file from:
  - Home directory.
  - `.maid` directory in home directory.
  - `.local/share/maid` directory in home directory.
  - `.config/maid` directory in home directory.
- Added generating markdown content with type from file extension.
- Added new option `--version` to display the version.
- Enhanced logging in various parts of the script.
- Enhanced markdown output with better formatting.
- Removed `--local-maidignore` option.
- Updated README.md with new usage instructions.

## [0.1.0] - 2024-10-04

- Initial release.