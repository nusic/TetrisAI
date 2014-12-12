#Playing field
SCALE = 30
OFFSET = 3
MAXX = 10
MAXY = 22

# Don't use levels
NO_OF_LEVELS = -1

#Controls
LEFT = "left"
RIGHT = "right"
DOWN = "down"
UP = "up"

DIRECTIONS = { "left": (-1, 0), "right": (1, 0), "down": (0, 1), "up": (0, -1) }


#Random input tetrominoes
TETROMINOES = "SZL" #Available: O T L J S Z I
NUM_ITERATIONS = 10

#Input tetrominoes from sequence
TETROMINO_SEQUENCE = None
#with open('../sequences/seq1.txt', 'r') as f:
#	TETROMINO_SEQUENCE = f.read()

LOOP_SEQUENCE = False


#AI
USE_AI = True
MAX_BRANCHING = 3
LOOKAHEAD = 2
MINIMAX_ON_LEAF_NODES = True

SHOW_GHOST_PIECE = True