import copy

from Globals import *

"""
	CS221 Project
	Class encapsulating all behavior of the tetris AI
"""
class SimpleAI:

	def __init__(self, state, maxDepth):

		#A set of weights for the features
		self.weights = {\
			"currentHeight" : -1, \
			"numHoles" : -1, \
			"linesCleared" : 5}

		#data to keep track of during algorithm
		self.state = state.copy()

		#max recursion depth - currently not used
		self.maxDepth = maxDepth


	"""
	Given the sequence of all next known pieces, 
	return the best piece orientation for the current pieces
	"""
	def getNextPieceOrientation(self, state, tetromino):
		
		possibleTetrominoes = self.possibleTetrominoes(state, tetromino)
		worstScore = float("inf")
		sumScore = 0
		bestScore = float("-inf")
		bestTetromino = None

		for tetromino in possibleTetrominoes:
			succState = state.copy()
			succState.setCoordsAsLanded(tetromino.coords)

			score = self.evaluate(succState, tetromino)
			sumScore += score
			if score < worstScore:
				worstScore = score
			if score > bestScore:
				bestScore = score
				bestTetromino = tetromino

		#print "scores: [",worstScore,",",bestScore,"]", 
		#print "\tmean:",sumScore/len(possibleTetrominoes)
		return bestTetromino


	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleTetrominoes(self, state, tetromino):
		choices = []
		t = tetromino.copy()
		for rot in range(4):
			t.rotate()
			self.moveTetrominoToLeftWall(t)
			right = t.rightMostX()
			while right <= state.width:

				if state.check_tetromino(t):
					dropped = t.copy()
					dropped.hardDrop(state)
					choices.append(dropped)

				right += 1
				t.move(RIGHT)

		return choices


	"""
	Evaluates the passed state based on the weights
	"""
	def evaluate(self, state, tetromino):
		f = self.extractFeatures(state, tetromino)
		s = 0
		for w in self.weights:
			if f[w] != None:
				s += self.weights[w] * f[w]
		return s


	"""
	Returns a dict of features representing the state
	"""
	def extractFeatures(self, state, tetromino):
		features = {}
		#features["numHoles_"+str(extractNumHoles(state))] = 1
		features["currentHeight"] = state.currentHeight()
		features["numHoles"] = self.extractNumHoles(state, tetromino)
		features["linesCleared"] = self.extractLinesCleared(state, tetromino)

		return features

	
	"""
	Returns the number of holes in the passed state
	"""
	def extractNumHoles(self, state, tetromino):
		#center
		holes = 0
		x_range = xrange(tetromino.leftMostX()-1, tetromino.rightMostX()+2)
		y_range = xrange(tetromino.upperMostY(), tetromino.lowerMostY()+2)
		#print tetromino.coords,"--> check holes in", x_range, y_range
		for x in x_range:
			for y in y_range:
				#not interested in holes outside play field
				if x < 0 or x >= state.width or y < 0 or y >= state.height:
					"hole cannot be outside playing field"
					continue

				if state.landed.has_key( (x,y) ) == None:
					holes += 1

		return holes

	def extractLinesCleared(self, state, tetromino):
		completeRows = 0
		y_range = range(tetromino.upperMostY()-1, tetromino.lowerMostY()+1)
		for row in y_range:
			if state.checkRowIsComplete(row):
				completeRows += 1
		return completeRows

	def moveTetrominoToLeftWall(self, tetromino):
		tetromino.skip(LEFT, tetromino.leftMostX())


