"""
	CS221 Project
	Class encapsulating all behavior of the tetris AI
"""
class AI:

	def __init__(self, state, maxDepth):
		#A set of weights for the features
		self.weights = {}

		self.maxDepth = maxDepth


	"""
	Given the sequence of all next known pieces, 
	return the best piece orientation for the current piece
	"""
	def getNextPieceOrientation(self, state, nextPieces):
		pass
		

	"""
	Given the current piece, return all possible 
	final positions it can end up in.
	"""
	def possibleOrientations(self, state, currentPiece):
		pass


	"""
	Evaluates the passed state based on the weights
	"""
	def evaluate(self, state):
		f = extractFeatures(state)
		s = 0
		for w in self.weights:
			if f[w] != None:
				s += self.weights[w] * f[w]
		return s


	"""
	Returns a dict of features representing the state
	"""
	def extractFeatures(self, state):
		features = {}
		#features["numHoles_"+str(extractNumHoles(state))] = 1
		features["numHoles"] = extractNumHoles(state)

		return features

	
	"""
	Returns the number of holes in the passed state
	"""
	def extractNumHoles(self, state):
		pass



	"""
	Returns the number of holes in the passed state
	"""
	def extractHeight(self, state):
		

