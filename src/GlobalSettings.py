#Playing field
SCALE = 30
OFFSET = 3
MAXX = 10
MAXY = 22

# Don't use levels
NO_OF_LEVELS = -1

SHOW_GHOST_PIECE = False

#Controls
LEFT = "left"
RIGHT = "right"
DOWN = "down"
UP = "up"

DIRECTIONS = { "left": (-1, 0), "right": (1, 0), "down": (0, 1), "up": (0, -1) }


#Random input tetrominoes

TETROMINOES = "ZSL" #Available: OTLJSZI
NUM_ITERATIONS = 10

# Randomly mutates feature weights after each generation
LEARN_WEIGHTS = False
NUM_GENERATIONS = 0


#Input tetrominoes from deterministic sequence
# OBS! Overrides random input. 
# Disable by setting TETROMINO_SEQUENCE = None

TETROMINO_SEQUENCE = "" #"SZ" #"OTLJSZILJL"
#with open('../sequences/seq1.txt', 'r') as f:
#	TETROMINO_SEQUENCE = f.read()

LOOP_SEQUENCE = True


#AI
USE_AI = True
MAX_BRANCHING = 3
LOOKAHEAD = 1

MINIMAX_ON_LEAF_NODES = False
MAXIMAX_ON_LEAF_NODES = True
EXPECTIMAX_ON_LEAF_NODE = False

WEIGHTS_FILE = '../features/OTLJSZI_15x8_lookahead1.txt'
OUTPUT_WEIGHTS = "../features/tmp.txt"
