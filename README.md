# MAID - `M`arkdown `AI` `D`oc creator

`maid` is a Python script that aggregates content from directories and files into a single Markdown file, especially useful for creating documentation for augmenting Artificial Intelligence services like [Claude3](https://claude.ai), [ChatGPT](https://chatgpt.com), and [Github Copilot](https://github.com/features/copilot).

The creation of special _rules_ helps developer to filter text files and remove unwanted content from the output, reducing the need for manual editing and the total size of the output file (less tokens, less cost).

It is very powerful and flexible, with support for:

- blacklisting files and directories
- filtering text files using special `rules` (see below)
- logging

Configuration can be keept in a `maid.json` file in the root directory of the project and even modified in subdirectories using a `maid.json` file that is only applied to that directory and its subdirectories.

## Usage

```bash
./maid.py [OPTIONS] PATHS...
```

### Options

- `-o`, `--output`: Specify the output Markdown file (default: `_content.md` in the current directory).
- `--log`: Enable logging to stdout.
- `--blacklist`: Glob patterns for files or directories to skip (matched against filename only). This option can be used multiple times.
- `--maid-file`: File containing `maid` configuration (default: `maid.json` in the current directory).
- `--version`: Display the version.

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

### Using a Maid configuration File

To use a blacklist file:

```bash
./maid.py -o output.md --maid-file maid-special.json src
```

### Reading Global and Local maid.json Files

Every directory scanned by `maid` will be checked for a `maid.json` file. If found, the patterns and rules in the file will be used to skip files or directories.
Patterns are added to the current blacklist, so they can be combined with other blacklist patterns.

At startup, `maid` will look for a global `maid.json` file in the following locations:

- current directory.
- Home directory.
- `.maid` directory in the home directory.
- `.local/share/maid` directory in the home directory.
- `.config/maid` directory in the home directory.

### Blacklist Patterns

Blacklist patterns can be specified directly via the `--blacklist` option or through a file using the `patterns` section in `--maid-file` option. Patterns are matched against filenames only.

### Example `maid.json` File

```json
{
  "patterns": ["*.log", "__pycache__", ".DS_Store"],
  "rules": []
}
```

## Rules definition

Rules are a powerful way to filter text files. They are defined in the `rules` section of the `maid.json` file and are applied to text files only.

A rule is some special text manipulation that can be applied to a range of lines in a text file.
The range is defined by a start pattern (the `start` key in the `rule` definition).
At the moment, the only supported end of the range is the rule inside the `delete` key.

Let's see an example of a rule that deletes all lines in a Godot `.tscn` file

Original godot `.tscn` file section:

```ini
[gd_scene load_steps=98 format=3 uid="uid://clmi4pv7vlgn1"]

[ext_resource type="Script" path="res://player/player_graphics.gd" id="1_ayi7m"]
[ext_resource type="Texture2D" uid="uid://dhq5k7y6mo74e" path="res://player/assets/spritesheet.png" id="2_bmcav"]

[sub_resource type="AtlasTexture" id="AtlasTexture_nbjsh"]
atlas = ExtResource("2_bmcav")
region = Rect2(48, 128, 48, 64)

[sub_resource type="AtlasTexture" id="AtlasTexture_ktvfe"]
atlas = ExtResource("2_bmcav")
region = Rect2(48, 128, 48, 64)

[node name="torso" type="AnimatedSprite2D" parent="."]
position = Vector2(1, -30)
sprite_frames = SubResource("SpriteFrames_w0qkt")
animation = &"run"
frame_progress = 0.410062
```

Suppose you want to remove all sub resources of type `AtlasTexture`, you can write a rule similar to this:

```json
"rules": [
        {
            "pattern": "*.tscn",
            "name": "subres AtlasTexture",
            "start": ".sub_resource.*type=.AtlasTexture",
            "delete": "::empty::",
            "keep_start": false
        }
]
```

This rule will delete all lines, starting from the line containing the `sub_resource` declaration with `type="AtlasTexture"` until the first empty line in the file.

### Rule definition

A rule is defined by a dictionary with the following keys:

- `pattern`: A glob pattern to match the file name.
- `name`: A name for the rule.
- `start`: A Regular Expression pattern to match the start of the range.
- `delete`: A Regular Expression pattern to match the end of the range or the special values:
  - `::empty::`: The first empty line after the start of the range.
  - `::line::`: the same line as the start of the range.
- `keep_start`: A boolean value to keep the start line matched in the output.

Rules are applied only if the pattern matches the file name and they are applied in the order they are defined in the `rules` section.

### Useful Rules

Here are some useful rules that can be used to filter text files:

- Remove all single line comments from files

  ```json
  {
    "name": "Remove single line comments",
    "pattern": "*.*",
    "start": "^\\s*//.*",
    "delete": "::line::"
  }
  ```

- Remove all `<style>` blocks from Svelte files

  ```json
  {
    "name": "Remove style blocks",
    "pattern": "*.svelte",
    "start": "<style>",
    "delete": "</style>"
  }
  ```

- Remove all empty lines from the file (run this as the latest rule)

  ```json
  {
    "name": "Remove empty lines",
    "pattern": "*.*",
    "start": "^\\s*$",
    "delete": "::line::"
  }
  ```

## Logging

If the `--log` option is enabled, `maid` will log its actions to stdout, including which files are being processed and which are being skipped due to blacklist patterns.

### Local `maid.json` Files

`maid` will look for a `maid.json` file in each directory it scans. The `maid.json` file should contain glob patterns in the `patterns` section and text manipultation rules in the `rules` section.
Patterns and rules in local `maid.json` files are only applied to the directory and its subdirectories.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

Fabio Rotondo
