# MAID - `M`arkdown `AI` `D`oc creator

`maid` is a Python script that aggregates content from directories and files into a single Markdown file. It supports various options for logging, blacklisting files, and reading local `.maidignore` files.

## Usage

```bash
./maid.py [OPTIONS] PATHS...
```

### Options

- `-o`, `--output` (required): Specify the output Markdown file.
- `--log`: Enable logging to stdout.
- `--blacklist`: Glob patterns for files or directories to skip (matched against filename only). This option can be used multiple times.
- `--blacklist-file`: File containing blacklist glob patterns.
- `--local-maidignore`: Enable reading of .maidignore files in directories.

### Arguments

- `PATHS`: One or more directories or files to process.

## Examples

### Basic Usage

To aggregate content from the `src` directory into `output.md`:

```bash
./maid.py -o output.md src
```

### Enable Logging

To enable logging:

```bash
./maid.py -o output.md --log src
```

### Using Blacklist Patterns

To skip certain files or directories:

```bash
./maid.py -o output.md --blacklist "*.log" --blacklist "__pycache__" src
```

### Using a Blacklist File

To use a blacklist file:

```bash
./maid.py -o output.md --blacklist-file blacklist.txt src
```

### Reading Local .maidignore Files

To enable reading of .maidignore files in directories:

```bash
./maid.py -o output.md --local-maidignore src
```

### Blacklist Patterns

Blacklist patterns can be specified directly via the `--blacklist` option or through a file using the `--blacklist-file` option. Patterns are matched against filenames only.

### Example Blacklist File

```bash
*.log
__pycache__
.DS_Store
```

## Logging

If the `--log` option is enabled, `maid` will log its actions to stdout, including which files are being processed and which are being skipped due to blacklist patterns.

### Local `.maidignore` Files

If the `--local-maidignore` option is enabled, `maid` will look for a `.maidignore` file in each directory it scans. The `.maidignore` file should contain glob patterns, one per line, for files or directories to skip.

### Example `.maidignore` File

```text
*.tmp
*.bak
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

Fabio Rotondo
