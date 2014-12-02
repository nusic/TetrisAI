import copy
import time
from collections import Counter

from Globals import *



"""
	CS221 Project
	Class encapsulating all behavior of the tetris AI
"""
class SimpleAI:

	def __init__(self, state, maxDepth):

		#A set of weights for the features
		self.weights = {
			"tetrominoY" : 0.1, \
			"numHoles" : -0.46, 
			"linesCleared" : 1, 
			"aggregateHeight" : -0.66,
			"bumpiness" : -0.24}

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

		actionAndLocalScore = []
		for action in possibleActions:

			state.setCoordsAsLanded(action.coords)
			localScore = self.localEval(state, action)
			actionAndLocalScore.append( (action, localScore) )
			state.removeCoords(action.coords)

		actionAndLocalScore.sort(key=lambda tup: tup[1], reverse = True)  # sorts in place

		for i in xrange(min(10, len(actionAndLocalScore))):

			(action, localScore) = actionAndLocalScore[i]
			score = localScore
			if len(tetrominoes) > 1 and self.maxDepth > 0:
				state.setCoordsAsLanded(action.coords)
				score += self.eval(state, tetrominoes, 1)
				state.removeCoords(action.coords)

			if score < worstScore:
				worstScore = score
			if score > bestScore:
				bestScore = score
				bestTetromino = action

		#raise Exception("debug")
		#print "scores: [",worstScore,",",bestScore,"]", 
		#print "\tmean:",sumScore/len(possibleActions)
		bestActionScores.append(bestScore)
		return bestTetromino

	def eval(self, state, tetrominoes, d):
		#Base case / leaf node
		maxScore = float("-inf")
		actions = self.possibleActions(state, tetrominoes[d])
		actionAndLocalScore = []
		for action in actions:
			

			#addedCoords = list(action.coords)
			state.setCoordsAsLanded(action.coords)
			
			localScore = self.localEval(state, action)

			actionAndLocalScore.append( (action, localScore) )
				
			state.removeCoords(action.coords)
		#raise Exception("ASD")
		actionAndLocalScore.sort(key=lambda tup: tup[1], reverse = True)  # sorts in place

		for i in xrange(min(3, len(actionAndLocalScore))):
			(action, localScore) = actionAndLocalScore[i]

			state.setCoordsAsLanded(action.coords)
			if d < self.maxDepth and d < len(tetrominoes):
				localScore += self.eval(state, tetrominoes, d+1)
			state.removeCoords(action.coords)
			maxScore = max( maxScore, 100*d + localScore)

		return maxScore

	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleActions(self, state, tetromino):

		choices = []
		t = tetromino.copy()
		checked = Counter()
		for rot in range(4):
			t.rotate()
			self.moveTetrominoToLeftWall(t)
			self.moveTetrominoToRoof(t)
			right = t.rightMostX()


			#Checking if already has tested this rotation
			#if there is a coordinate that haven't seen before
			#eg. it is not in checked, we have to explore this rotation
			alreadyTested = True
			for coord in t.coords:
				if checked[coord] == 0:
					alreadyTested = False
					break
			if alreadyTested:
				continue

			for coord in t.coords:
				checked[coord] += 1


			#Drop the piece at all possible x locations
			while right <= state.width:

				if state.check_tetromino(t):
					dropped = t.copy()

					dropped.hardDrop(state)
					choices.append(dropped)

				right += 1
				t.move(RIGHT)
		#for choice in choices:
			#print choice.coords
		#raise Exception("possible actions")
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

	def moveTetrominoToRoof(self, tetromino):
		tetromino.skip(UP, tetromino.upperMostY())


