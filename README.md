Of course. Here is a comprehensive README file for the script.

-----

# PGN Variation Tree Generator

This script generates a visual tree diagram of chess variations from a PGN (Portable Game Notation) study file. It reads multiple game lines, merges them into a single branching tree, and uses Graphviz to create a high-quality PNG image showing the board state at each position.

This tool is ideal for visualizing opening repertoires or analyzing complex variations from a Lichess study or other PGN source.

## Example Output

The script produces a graph where each node is a board position and each edge is the move that connects them. An example generated from the included `study.pgn` file is shown below:

## Requirements

To use this script, you will need the following installed:

1.  **Python 3**

2.  **Python Libraries**: `python-chess`, `graphviz`, and `cairosvg`. You can install them all with pip:

    ```bash
    pip install python-chess graphviz cairosvg
    ```

3.  **Graphviz Software**: This is a separate program that the Python script uses to render the graph. You must install it and ensure it's available in your system's PATH.

      * **Windows**: Download an installer from the [official Graphviz download page](https://graphviz.org/download/). During installation, make sure to select the option "Add Graphviz to the system PATH".
      * **macOS** (using Homebrew):
        ```bash
        brew install graphviz
        ```
      * **Linux** (Debian/Ubuntu):
        ```bash
        sudo apt-get update
        sudo apt-get install graphviz
        ```

## Usage

Run the script from your command line, providing the path to your PGN file as the first argument and the desired name for the output image as the second.

**Syntax:**

```bash
python <script_name>.py <path_to_pgn_file> <output_image_name>
```

**Example:**
To generate a tree from the provided `study.pgn` and save it as `philidor_tree.png`:

```bash
python generate_tree.py study.pgn philidor_tree.png
```

The script will create a temporary directory (`board_images/`) to store board snapshots and then produce the final PNG image in your current directory.

## PGN File Format

> **⚠️ Important:** For the script to correctly identify and merge variations, **each individual line must be saved as a separate "game" or "study chapter"** within the PGN file.
>
> Most chess software allows you to export a study as a single PGN where each chapter is treated as a separate game, which is the required format.

The PGN file should look like this, with distinct `[Event "..."]` headers for each line:

```pgn
[Event "Line 1: Queen's Gambit Declined"]
[Site "?"]
...
1. d4 d5 2. c4 e6 *

[Event "Line 2: Slav Defense"]
[Site "?"]
...
1. d4 d5 2. c4 c6 *

[Event "Line 3: Queen's Gambit Accepted"]
[Site "?"]
...
1. d4 d5 2. c4 dxc4 *
```

The script will correctly merge these three lines starting from the common `1. d4 d5 2. c4` sequence.

## How It Works

The script processes the PGN data in several steps:

1.  **Parse PGN**: It reads the input `.pgn` file and iterates through each game/study defined within it.
2.  **Build Tree**: The moves from all games are added to a single tree data structure. Common moves are merged automatically, and variations create new branches.
3.  **Find Divergence**: To keep the graph focused and clean, the script automatically finds the first move where the lines diverge and sets that position as the root of the visual graph. This avoids cluttering the image with a long, shared opening sequence.
4.  **Prune End-Nodes**: Any terminal line that doesn't stem from a branching point is pruned. This ensures every leaf on the final diagram is a meaningful end to a variation.
5.  **Render Image**: Finally, it traverses the processed tree and uses Graphviz to generate nodes (as board images) and edges (as move labels), rendering the final `.png` file.

## License

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
