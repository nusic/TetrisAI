import copy
import time

from Globals import *



"""
	CS221 Project
	Class encapsulating all behavior of the tetris AI
"""
class SimpleAI:

	def __init__(self, state, maxDepth):

		#A set of weights for the features
		self.weights = {\
			"tetrominoY" : 0.3, \
			"numHoles" : -1, \
			"linesCleared" : 5, \
			"aggregateHeight" : -1,\
			"bumpiness" : -0.3}

		#max recursion depth - currently not used
		self.maxDepth = maxDepth


	"""
	Given the sequence of all next known pieces, 
	return the best piece orientation for the current pieces
	"""
	def getNextPieceOrientation(self, state, tetrominoes):
		
		possibleActions = self.possibleActions(state, tetrominoes[0])
		worstScore = float("inf")
		sumScore = 0
		bestScore = float("-inf")
		bestTetromino = None

		possibleActions
		for pos in possibleActions:
			#succState = state.copy()
			addedCoords = pos.coords
			state.setCoordsAsLanded(pos.coords)

			#print pos
			#state.output()
			#print

			score = self.localEval(state, pos)
			if len(tetrominoes) > 1 and self.maxDepth > 0:
				score += self.eval(state, tetrominoes, 0, 1)
			sumScore += score
			if score < worstScore:
				worstScore = score
			if score > bestScore:
				bestScore = score
				bestTetromino = pos

			state.removeCoords(addedCoords)
			#print score
			#print

		#raise Exception("debug")
		#print "scores: [",worstScore,",",bestScore,"]", 
		#print "\tmean:",sumScore/len(possibleActions)
		bestActionScores.append(bestScore)
		return bestTetromino

	def eval(self, state, tetrominoes, score, d):

		#Base case / leaf node
		maxScore = float("-inf")
		actions = self.possibleActions(state, tetrominoes[d])
		for actions in actions:

			addedCoords = list(actions.coords)
			state.setCoordsAsLanded(actions.coords)

			futureScore = self.localEval(state, actions)

			if d < self.maxDepth and d < len(tetrominoes):
				futureScore += self.eval(state, tetrominoes, futureScore, d+1)
				
			maxScore = max( maxScore, score + futureScore)
			state.removeCoords(addedCoords)

		return maxScore

	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleActions(self, state, tetromino):

		choices = []
		t = tetromino.copy()
		checked = []
		for rot in range(4):

			for coord in t.coords:
				if coord not in checked:
					continue

			checked.append(list(t.coords))

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
	def localEval(self, state, tetromino):
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
		features["tetrominoY"] = tetromino.upperMostY()
		features["numHoles"] = self.extractNumHoles(state, tetromino)
		features["linesCleared"] = self.extractLinesCleared(state, tetromino)
		features["aggregateHeight"] = self.extractAggregateHeight(state, tetromino)
		features["bumpiness"] = self.extractBumpiness(state, tetromino)

		return features

	
	"""
	Returns the number of holes in the passed state
	"""
	#Holes = each empty space with blocks above in same column
	def extractNumHoles(self, state, tetromino):
		holes = 0
		for x in range(state.width):
			y0 = 0
			while not state.landed.has_key( (x,y0) ) and y0 < state.height:
				y0 += 1

			for y in range(y0+1,state.height):
				if not state.landed.has_key( (x,y) ):
					holes += 1

		return holes

	def extractLinesCleared(self, state, tetromino):
		completeRows = 0
		y_range = range(tetromino.upperMostY(), tetromino.lowerMostY()+1)
		for row in y_range:
			if state.checkRowIsComplete(row):
				completeRows += 1
		return completeRows

	def extractAggregateHeight(self, state, tetromino):
		return sum(self.extractColumnHeights(state, tetromino))

	def extractColumnHeights(self, state, tetromino):
		columnHeights = []
		for x in range(state.width):
			y = 0
			while not state.landed.has_key( (x,y) ) and y < state.height:
				y += 1
			columnHeights.append(state.height - y)
		return columnHeights

	def extractBumpiness(self, state, tetromino):
		bumpiness = 0
		columnHeights = self.extractColumnHeights(state, tetromino)
		for i in range(1,state.width):
			bumpiness += abs(columnHeights[i] - columnHeights[i-1])
		return bumpiness

	def moveTetrominoToLeftWall(self, tetromino):
		tetromino.skip(LEFT, tetromino.leftMostX())



