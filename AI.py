import copy
import time
import GameLogic

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
			"tetrominoY" : 0.1, 
			"numHoles" : -0.46, 
			"linesCleared" : 1, 
			"aggregateHeight" : -0.66,
			"bumpiness" : -0.24}

		#max recursion depth - currently not used
		self.maxDepth = maxDepth
		self.statesExplored = 0


	"""
	Given the sequence of all next known pieces, 
	return the best piece orientation for the current pieces
	"""
	##clearedLines = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))
	def getNextPieceOrientation(self, state, tetrominoes):
		self.statesExplored = 0
		bestScore = float("-inf")
		bestTetromino = None

		actionsAndLocalScores = self.actionsAndLocalScoresSorted(state, tetrominoes[0])


		#If only one known tetromino or if max recursion depth
		#is 0, just return the best action based on local score
		if len(tetrominoes) == 1 or self.maxDepth == 0:
			#print "states explored:", self.statesExplored
			return actionsAndLocalScores[0][0]


		#Else, recursevely evaluate each successor state
		for i in xrange(min(4, len(actionsAndLocalScores))):
			action, score = actionsAndLocalScores[i]
			
			state.setCoordsAsLanded(action.coords)
			linesCleared = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))
			score += self.weights["linesCleared"]*len(linesCleared)

			if linesCleared:
				tmpState = state.copy()
				tmpState.deleteRows(linesCleared)
				score += self.evalWithClearedLinesRemoved(tmpState, tetrominoes, 0)
				del tmpState
			else:
				score += self.evalWithClearedLinesRemoved(state, tetrominoes, 0)

			state.removeCoords(action.coords)

			if score > bestScore:
				bestScore = score
				bestTetromino = action

		#bestActionScores.append(bestScore)
		#print "states explored:", self.statesExplored
		return bestTetromino



	def actionsAndLocalScoresSorted(self, state, tetromino):
		actionAndLocalScore = []
		possibleActions = self.possibleActions(state, tetromino)
		for action in possibleActions:
			localScore = self.localEvalWithClearedLinesRemoved(state, action)

			actionAndLocalScore.append( (action, localScore) )
		# sorts in place
		actionAndLocalScore.sort(key=lambda tup: tup[1], reverse = True) 
		return actionAndLocalScore



	def eval(self, state, tetrominoes, d):
		bestScore = float("-inf")
		actionsAndLocalScores = self.actionsAndLocalScoresSorted(state, tetrominoes[d])
		
		for i in xrange(min(2, len(actionsAndLocalScores))):
			action, localScore = actionsAndLocalScores[i]

			if d < self.maxDepth and d < len(tetrominoes):
				state.setCoordsAsLanded(action.coords)
				localScore += self.eval(state, tetrominoes, d+1)
				state.removeCoords(action.coords)
			bestScore = max( bestScore, localScore)

		return bestScore



	def evalWithClearedLinesRemoved(self, state, tetrominoes, d):
		actionsAndLocalScores = self.actionsAndLocalScoresSorted(state, tetrominoes[d])

		#Base case - leaf node of max depth
		if d >= self.maxDepth or d >= len(tetrominoes):
			if not actionsAndLocalScores:
				return 0
			return actionsAndLocalScores[0][1]


		bestScore = float("-inf")
		for i in xrange(min(2, len(actionsAndLocalScores))):
			action, localScore = actionsAndLocalScores[i]
			state.setCoordsAsLanded(action.coords)
			linesCleared = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))
			localScore = self.weights["linesCleared"]*len(linesCleared)

			if linesCleared:
				tmpState = state.copy()
				tmpState.deleteRows(linesCleared)
				localScore += self.evalWithClearedLinesRemoved(tmpState, tetrominoes, d+1)
				del tmpState
			else:
				localScore += self.evalWithClearedLinesRemoved(state, tetrominoes, d+1)

			state.removeCoords(action.coords)

			bestScore = max( bestScore, localScore)

		return bestScore





	def localEvalWithClearedLinesRemoved(self, state, action):
		state.setCoordsAsLanded(action.coords)

		linesCleared = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))
		localScore = self.weights["linesCleared"]*len(linesCleared)

		if linesCleared:
			tmpState = state.copy()
			tmpState.deleteRows(linesCleared)
			localScore += self.localEval(tmpState, action)
			del tmpState
		else:
			localScore += self.localEval(state, action)

		state.removeCoords(action.coords)

		return localScore




	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleActions(self, state, tetromino):
		choices = []
		t = tetromino.copy()
		checked = Counter()
		rot = 0
		while True:
			#print rot
			self.moveTetrominoToLeftWall(t)
			self.moveTetrominoToRoof(t)
			right = t.rightMostX()

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

			if tetromino.rots and rot < len(tetromino.rots):
				for _ in xrange(tetromino.rots[rot]):
					t.rotate()
					rot += 1
			else:
				break
			
		#for choice in choices:
			#print choice.coords
		#raise Exception("possible actions")
		return choices



	"""
	Evaluates the passed state based on the weights
	"""
	def localEval(self, state, tetromino):
		self.statesExplored += 1
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
		features["linesCleared"] = 0 
		features["tetrominoY"] = tetromino.upperMostY()
		features["numHoles"] = self.extractNumHoles(state, tetromino)
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
		y_range = range(tetromino.upperMostY(), tetromino.lowerMostY()+1)
		clearedLines = []
		for row in y_range:
			if state.checkRowIsComplete(row):
				clearedLines.append(row)
		return clearedLines

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


