import chess
import chess.pgn
import chess.svg
import io
import os
import sys
import argparse
from graphviz import Digraph

# This script relies on the 'cairosvg' library to convert SVG images
# to the PNG format, which is required for Graphviz integration.
# To install, run: pip install cairosvg
try:
    import cairosvg
except ImportError:
    print("Error: The 'cairosvg' library is not installed. Please install it with 'pip install cairosvg'")
    sys.exit(1)


class MoveNode:
    """
    Represents a single node within the chess move tree, corresponding to a
    unique board position.
    """
    def __init__(self, board, move=None, parent=None):
        self.board = board.copy()      # The chess.Board state for this node.
        self.move = move               # The move that resulted in this board state.
        self.parent = parent           # The parent MoveNode.
        self.children = {}             # A dictionary of child nodes, keyed by move UCI.
        self.fen = board.fen()         # The FEN representation of the board state.

    def add_child(self, move):
        """
        Applies a given move to the current board and generates a new child
        node. If a child node for this move already exists, it is returned
        instead of creating a new one.
        """
        uci = move.uci()
        if uci not in self.children:
            board_after_move = self.board.copy()
            board_after_move.push(move)
            self.children[uci] = MoveNode(board_after_move, move, self)
        return self.children[uci]


def _add_pgn_nodes_to_tree(current_treenode, pgn_node):
    """
    Recursively iterates through game nodes from a `chess.pgn` object and
    constructs the corresponding MoveNode tree structure.
    """
    # The .variations attribute includes the main line and all alternatives.
    for variation in pgn_node.variations:
        move = variation.move
        # Create a child for the move and descend recursively.
        child_treenode = current_treenode.add_child(move)
        _add_pgn_nodes_to_tree(child_treenode, variation)


def build_tree_from_pgn(pgn_text):
    """
    Constructs a unified MoveNode tree from a PGN string. The string can
    contain multiple games or studies; their move sequences will be merged
    into a single tree.
    """
    root = MoveNode(chess.Board())
    pgn_file = io.StringIO(pgn_text)

    # Process all games within the PGN data.
    while True:
        game = chess.pgn.read_game(pgn_file)
        if game is None:
            break  # End of PGN data.

        # The recursive function merges moves into the existing tree,
        # ensuring shared lines are not duplicated.
        _add_pgn_nodes_to_tree(root, game)
        
    return root


def find_first_divergence_node(root_node):
    """
    Traverses the tree from the root to locate the first node with more than
    one child. This identifies the first move where variations appear.

    This is useful for omitting a long, shared opening sequence from the
    final visualization, focusing instead on the branching points.
    """
    current_node = root_node
    # Follow the main line as long as there are no alternative moves.
    while len(current_node.children) == 1:
        # Get the only child node to continue traversal.
        current_node = list(current_node.children.values())[0]

    # Returns the node where branching begins, or the root if no moves exist
    # or if branching starts immediately.
    return current_node


def prune_end_nodes(node):
    """
    Recursively removes terminal nodes that are part of a non-branching,
    linear sequence. This cleans up the visualization by ensuring that every
    leaf in the final graph originates from a node with at least two
    children.
    """
    # Create a list from children to allow modification of the dictionary
    # during iteration.
    children_to_process = list(node.children.values())
    for child in children_to_process:
        prune_end_nodes(child)

    # Post-recursion check: if this node has a single child, and that child
    # has become a leaf node through pruning, remove the child. This action
    # effectively shortens the linear "tail".
    if len(node.children) == 1:
        child = list(node.children.values())[0]
        if not child.children:
            node.children.clear()


def generate_tree_image(root_node, output_filename='chess_tree.png'):
    """
    Renders a high-resolution visual graph of the chess move tree using
    Graphviz and saves it to a file.
    """
    # A directory is needed to hold temporary board images.
    img_dir = 'board_images'
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    dot = Digraph(comment='Chess Opening Tree',
                  graph_attr={'splines': 'ortho', 'ranksep': '2.0', 'nodesep': '0.8', 'overlap': 'false'},
                  node_attr={'shape': 'box', 'style': 'rounded'},
                  edge_attr={'arrowsize': '0.7'})

    # Board color theme.
    colors = {
        "square light": "#F0D9B5",
        "square dark": "#B58863",
        "margin": "#333333",
    }
    
    queue = [root_node]
    processed_fens = set()

    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='filled', color='lightgrey')
        c.node_attr.update(style='filled', color='white')
        c.attr(label='Chess Study Tree')

        while queue:
            current_node = queue.pop(0)
            if current_node.fen in processed_fens:
                continue
            
            processed_fens.add(current_node.fen)

            # Generate the SVG image for the current board position.
            arrows = []
            if current_node.move:
                # Highlight the last move with a colored arrow.
                arrow = chess.svg.Arrow(current_node.move.from_square, current_node.move.to_square, color="#15781B")
                arrows.append(arrow)

            board_svg = chess.svg.board(
                board=current_node.board,
                size=350,
                arrows=arrows,
                colors=colors,
            ).encode('utf-8')

            # Sanitize the FEN string to create a valid filename.
            safe_fen = current_node.fen.replace('/', '_').replace(' ', '_')
            
            # Convert the SVG data to a PNG file.
            png_image_path = os.path.abspath(os.path.join(img_dir, f'{safe_fen}.png'))
            cairosvg.svg2png(bytestring=board_svg, write_to=png_image_path)
            
            # Define a graph node using the generated board image.
            dot.node(current_node.fen, label='', image=png_image_path, shape='none')

            # Create edges to connect this node to its children.
            for uci, child_node in current_node.children.items():
                # Get the Standard Algebraic Notation for the edge label.
                edge_label = current_node.board.san(child_node.move)
                # Use 'xlabel' to prevent interference with orthogonal line routing.
                dot.edge(current_node.fen, child_node.fen, xlabel=edge_label)
                queue.append(child_node)

    # Render the final graph to the specified output file.
    output_base = os.path.splitext(output_filename)[0]
    dot.render(output_base, format='png', view=False, cleanup=True)
    print(f"Generated chess tree image: {output_base}.png")


def main():
    """
    Main execution function. Parses command-line arguments, reads the PGN,
    builds the tree, and generates the final image.
    """
    parser = argparse.ArgumentParser(
        description="Generate a visual tree of chess variations from a PGN study file.",
        epilog="Requires Graphviz to be installed and in the system's PATH."
    )
    parser.add_argument("pgn_file", help="The path to the input PGN file.")
    parser.add_argument("output_file", help="The name of the output image file (e.g., 'study_tree.png').")
    args = parser.parse_args()

    # Check for Graphviz installation.
    # This is a simple check; a more robust solution might use shutil.which.
    if os.system('dot -V') != 0:
        print("Error: Graphviz does not appear to be installed or is not in the system's PATH.")
        print("Please install it from https://graphviz.org/download/")
        sys.exit(1)

    # Read the PGN data from the specified file.
    try:
        with open(args.pgn_file, 'r', encoding='utf-8') as f:
            pgn_data = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{args.pgn_file}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

    # Build the complete tree from the PGN data.
    full_tree_root = build_tree_from_pgn(pgn_data)

    # Locate the first branching point to serve as the visual root of the graph.
    graph_start_node = find_first_divergence_node(full_tree_root)

    # Prune the tree to clean up terminal, non-branching paths.
    if graph_start_node:
        prune_end_nodes(graph_start_node)

    # Generate the final image from the processed tree structure.
    generate_tree_image(graph_start_node, output_filename=args.output_file)


if __name__ == '__main__':
    main()
