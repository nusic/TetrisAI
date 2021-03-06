import copy
import time
import GameLogic
import random
import os
import numpy

from collections import Counter
from GlobalSettings import *


"""
	CS221 Project
	Class encapsulating all behavior of the tetris AI
"""
class SimpleAI:

	def __init__(self):

		self.weights = { }
		self.readWeights(WEIGHTS_FILE)

		self.maxDepth = LOOKAHEAD
		self.minimax = MINIMAX_ON_LEAF_NODES
		self.maximax = MAXIMAX_ON_LEAF_NODES
		self.expectimax = EXPECTIMAX_ON_LEAF_NODE
		self.k = MAX_BRANCHING

		self.sumScore = 0




	"""
	Given the sequence of all next known pieces, 
	return the best piece orientation for the current pieces
	"""
	def getNextPieceOrientation(self, state, tetrominoes):
		return self.evalWithClearedLinesRemoved(state, tetrominoes, 0)[0]



	def evalWithClearedLinesRemoved(self, state, tetrominoes, d):

		#Base case - leaf node of max depth
		if d >= len(tetrominoes):
			return ([GameLogic.NullTetromino], 0)

		actionsAndLocalScores = self.actionsAndLocalScoresSorted(state, tetrominoes[d])

		bestScore = float("-inf")
		bestAction = GameLogic.NullTetromino
		for i in xrange(min(self.k, len(actionsAndLocalScores))):
			action, score = actionsAndLocalScores[i]

			state.setCoordsAsLanded(action.coords)
			linesCleared = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))

			#base case, leaf state
			if d >= self.maxDepth or d >= len(tetrominoes):
				if self.minimax:
					score += self.minimaxOneDepth(state)
				if self.maximax:
					score += self.maximaxOneDepth(state)
				if self.expectimax:
					score += self.expectimaxOnDepth(state)


			#if not leaf
			else:
				if linesCleared:
					tmpState = state.copy()
					tmpState.deleteRows(linesCleared)
					score += self.evalWithClearedLinesRemoved(tmpState, tetrominoes, d+1)[1]
					del tmpState
				else:
					score += self.evalWithClearedLinesRemoved(state, tetrominoes, d+1)[1]

			state.removeCoords(action.coords)

			if score > bestScore:
				bestScore = score
				bestAction = action

		return (bestAction, bestScore)


	def getBestLocalActionAndScore(self, state, tetromino):
		bestScore = float("-inf")
		bestAction = None

		possibleActions = self.possibleActions(state, tetromino)
		for action in possibleActions:
			localScore = self.localEval(state, action)

			if localScore > bestScore:
				bestScore = localScore
				bestAction = action

		return (bestAction, bestScore)


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


	def localEval(self, state, action):
		state.setCoordsAsLanded(action.coords)

		linesCleared = self.extractLinesCleared(state, GameLogic.Tetromino(action.coords))
		localScore = self.weights["linesCleared"]*len(linesCleared)
		localScore += self.localEval(state, action)

		state.removeCoords(action.coords)

		return localScore



	def minimaxOneDepth(self, state):
		minimizingScore = float('inf')
		for t in GameLogic.Tetrominoes:

			maximizingScore = float('-inf')
			for a in self.possibleActions(state, t):
				localScore = self.localEval(state, a)
				maximizingScore = max(maximizingScore, localScore)

			minimizingScore = min(minimizingScore, maximizingScore)

		return minimizingScore

	def maximaxOneDepth(self, state):
		maximizingScoreOuter = float('-inf')
		for t in GameLogic.Tetrominoes:

			maximizingScoreInner = float('-inf')
			for a in self.possibleActions(state, t):
				localScore = self.localEval(state, a)
				maximizingScoreInner = max(maximizingScoreInner, localScore)

			maximizingScoreOuter = max(maximizingScoreOuter, maximizingScoreInner)
		
		return maximizingScoreOuter

	def expectimaxOnDepth(self, state):
		maxScore = []
		for t in GameLogic.Tetrominoes:
			possibleActions = self.possibleActions(state,t)
			if len(possibleActions)>0:
				maxScore.append(max([self.localEval(state,a) for a in possibleActions]))
		if len(maxScore)>0:
			return numpy.mean(maxScore)
		else:
			return 0

	def actionsAndLocalScoresSorted(self, state, tetromino):
		actionAndLocalScore = []
		possibleActions = self.possibleActions(state, tetromino)
		for action in possibleActions:
			localScore = self.localEvalWithClearedLinesRemoved(state, action)

			actionAndLocalScore.append( (action, localScore) )
		# sorts in place
		actionAndLocalScore.sort(key=lambda tup: tup[1], reverse = True) 
		return actionAndLocalScore


	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleActions(self, state, tetromino):
		choices = []
		t = tetromino.copy()
		rot = 0
		while True:
			#print rot
			self.moveTetrominoToLeftWall(t)
			self.moveTetrominoToRoof(t)
			right = t.rightMostX()

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
		f = self.extractFeatures(state, tetromino)
		s = 0

		#if game over
		if f["tetrominoY"] <= 2:
			s = -1000000
		
		for w in self.weights:
			if f[w] != None:
				s += self.weights[w] * f[w]
		return s


	"""
	Returns a dict of features representing the state
	"""
	def extractFeatures(self, state, tetromino):
		features = {}
		yMax = tetromino.upperMostY()
		features["linesCleared"] = 0 
		features["tetrominoY"] = yMax
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



	"""
	Returns the number of holes in the passed state
	"""
	#Holes = each empty space with blocks above in same column
	def extractNumHoles2(self, state, tetromino):
		holes = 0
		for x in range(state.width):
			y0 = 0

			while True:
				while not state.landed.has_key( (x,y0) ) and y0 < state.height:
					y0 += 1

				while state.landed.has_key( (x,y0) ) and y0 < state.height:
					y0 += 1

				if y0 >= state.height:
					break

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


	def mutate(self):
		f = random.choice(self.weights.keys())
		delta = random.sample( [-0.1, 0.1], 1)[0]
		#print "Mutating",f,"with",delta
		self.weights[f] += delta

	def readWeights(self, filename):
		with open(filename, 'r') as f:
			lines = f.readlines()

			fName = lines[0].split()
			fWeight = lines[1].split()
			print "Loading feature weights ..."
			for i in range(len(fName)):
				print fName[i], ":",fWeight[i]
				self.weights[fName[i].strip()] = float(fWeight[i])

