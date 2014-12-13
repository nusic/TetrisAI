import copy

from GlobalSettings import *

class State:
    """
    This class is a complete representation of the current game state.
    """

    def __init__(self, width=10, height=20):
        self.landed = {}
        self.width = width
        self.height = height

    """
    Copy a state
    """
    def copy(self):
        return copy.deepcopy(self)

    def setAsLanded(self, blocks):
        """
        Adds the blocks to those in the grid that have already 'landed'
        """
        for block in blocks:
            self.landed[ block.coord() ] = block.id

    def setCoordsAsLanded(self, coords):
        for coord in coords:
            self.landed[ coord ] = 1337

    def removeCoords(self, coords):
        for coord in coords:
            #self.landed[ coord ] = None
            del self.landed[ coord ]

    def findFirstEmptyRow(self):
        """
        Returns the row index of the first empty row, starting from bottom
        """
        for y in xrange(self.height -1, -1, -1):
            row_is_empty = True
            for x in xrange(self.width):
                if self.landed.get((x,y), None):
                    row_is_empty = False
                    break;
            if row_is_empty:
                #print y
                return y
        return -1

    def currentHeight(self):
        return self.height - self.findFirstEmptyRow()

    def findCompleteRowsBelow(self, rowLimit):
        """
        Scans from bottom row, up until rowLimit, and finds any complete rows. 
        """
        completeRows = []
        y = self.height - 1 #Bottom row
        while y > rowLimit:

            if self.checkRowIsComplete(y):
                completeRows.append(y)
            y -= 1
        return completeRows

    def checkRowIsComplete(self, y):
        for x in xrange(self.width):
            if self.landed.get((x,y), None) is None:
                return False
        return True

    def addAndGetCompleteRows(self, blocks):
        """
        Adds the blocks and returns a list of rows that now are completed.
        """

        self.setAsLanded(blocks)
        empty_row = self.findFirstEmptyRow()
        return self.findCompleteRowsBelow(empty_row)


    def check_tetromino(self, tetromino):
        for coord in tetromino.coords:
            if not self.check_block(coord):
                return False
        return True

    def check_block( self, (x, y), includeRoof=True):
        """
        Check if the x, y coordinate can have a block placed there.
        That is; if there is a 'landed' block there or it is outside the
        board boundary, then return False, otherwise return true.
        """

        #if x < 0 or x >= self.width or y < 0 or y >= self.height:
        if x < 0 or x >= self.width or y >= self.height:
            return False
        if includeRoof and y < 0:
            return False

        elif self.landed.has_key( (x, y) ):
            return False
        else:
            return True

    def rotate(self, tetromino, clockwise = True):
        """
        Rotate the blocks around the 'middle' block, 90-degrees. The
        middle block is always the index 0 block in the list of blocks
        that make up a shape.
        """

        middle = tetromino.coords[0]
        rel = []
        for block in tetromino.coords:
            rel.append( (block.x-middle.x, block.y-middle.y ) )
            
        # to rotate 90-degrees (x,y) = (-y, x)
        # First check that the there are no collisions or out of bounds moves.
        for idx in xrange(len(tetromino.coords)):
            rel_x, rel_y = rel[idx]
            if clockwise:
                x = middle.x-rel_y
                y = middle.y+rel_x
            else:    
                x = middle.x+rel_y
                y = middle.y-rel_x
            
            if not self.state.check_block( (x, y), includeRoof=False):
                return False
            
        for idx in xrange(len(tetromino.coords)):
            rel_x, rel_y = rel[idx]
            if clockwise:
                x = middle.x-rel_y
                y = middle.y+rel_x
            else:    
                x = middle.x+rel_y
                y = middle.y-rel_x
            
            
            diff_x = x - tetromino.coords[idx].x 
            diff_y = y - tetromino.coords[idx].y 
        
            tetromino.coords[idx].x = x
            tetromino.coords[idx].y = y
       
        return True

    def output( self ):
        for y in xrange(self.height):
            line = []
            for x in xrange(self.width):
                if self.landed.get((x,y), None):
                    line.append("X")
                else:
                    line.append(".")
            print "".join(line)



    def deleteRows(self, rows, empty_row=0):
        #delete the completed row
        for y in rows:
            for x in xrange(self.width):
                self.landed.pop((x,y))

            # move all the rows above it down
            for ay in xrange(y-1, empty_row, -1):
                for x in xrange(self.width):
                    block = self.landed.get((x,ay), None)
                    if block:
                        dx,dy = DIRECTIONS[DOWN]
                        block = self.landed.pop((x,ay))
                        self.landed[(x+dx, ay+dy)] = block


"""
Class for handling non GUI parts of tetrominoes
"""
class Tetromino:
    def __init__(self, coords, rots = -1):
        self.coords = coords
        self.rots = rots

    def copy(self):
        return copy.deepcopy(self)

    def leftMostX(self):
        return min( x for (x,y) in self.coords )

    def rightMostX(self):
        return max( x for (x,y) in self.coords )

    def lowerMostY(self):
        return max( y for (x,y) in self.coords )

    def upperMostY(self):
        return min( y for (x,y) in self.coords )

    def move(self, direction):
        d_x, d_y = DIRECTIONS[direction]
        for i in range(len(self.coords)):
            self.coords[i] = (self.coords[i][0] + d_x, self.coords[i][1] + d_y)

    def skip(self, direction, n):
        d_x, d_y = DIRECTIONS[direction]
        for i in range(len(self.coords)):
            self.coords[i] = (self.coords[i][0] + d_x * n, self.coords[i][1] + d_y * n)

    def rotate(self, clockwise = True):
        (cx, cy) = self.coords[0]
        rel = []
        for (x,y) in self.coords:
            rel.append( (x-cx, y-cy ) )
            
        # to rotate 90-degrees (x,y) = (-y, x)
        for idx in xrange(len(self.coords)):
            rel_x, rel_y = rel[idx]
            x,y = 0,0
            if clockwise:
                x = cx-rel_y
                y = cy+rel_x
            else:    
                x = cx+rel_y
                y = cy-rel_x
            
            self.coords[idx] = (x, y)
    
    #Can be optimized!
    def hardDrop(self, state):
        while state.check_tetromino(self):
            self.move(DOWN)
        self.move(UP)
        #for i in range(self.leftMostX(), self.rightMostX()):



def letterToTetromino(letter):
    if letter.upper() == "O": return Tetromino([(4,0),(5,0),(4,1),(5,1)] , [] )
    if letter.upper() == "T": return Tetromino([(4,0),(3,0),(5,0),(4,1)] , [1, 1, 1] )
    if letter.upper() == "L": return Tetromino([(4,0),(3,0),(5,0),(3,1)] , [1, 1, 1] )
    if letter.upper() == "J": return Tetromino([(5,0),(4,0),(6,0),(6,1)] , [1, 1, 1] )
    if letter.upper() == "Z": return Tetromino([(5,0),(4,0),(5,1),(6,1)] , [1] )
    if letter.upper() == "S": return Tetromino([(5,1),(4,1),(5,0),(6,0)] , [1] )
    if letter.upper() == "I": return Tetromino([(4,0),(3,0),(5,0),(6,0)] , [1] )
    raise Exception("Cannot parse " + letter + " to Tetromino")

NullTetromino = Tetromino([(5,2), (5,1), (5,0), (5,-1)] , [] )




Tetrominoes = []
if TETROMINO_SEQUENCE is not None:
    Tetrominoes.append( Tetromino([(4,0),(5,0),(4,1),(5,1)] , [] ) ) # square
    Tetrominoes.append( Tetromino([(4,0),(3,0),(5,0),(4,1)] , [1, 1, 1] ) ) # T
    Tetrominoes.append( Tetromino([(4,0),(3,0),(5,0),(3,1)] , [1, 1, 1] ) ) # L
    Tetrominoes.append( Tetromino([(5,0),(4,0),(6,0),(6,1)] , [1, 1, 1] ) ) # J
    Tetrominoes.append( Tetromino([(5,0),(4,0),(5,1),(6,1)] , [1] ) ) # Z
    Tetrominoes.append( Tetromino([(5,1),(4,1),(5,0),(6,0)] , [1] ) ) # S
    Tetrominoes.append( Tetromino([(4,0),(3,0),(5,0),(6,0)] , [1] ) ) # I
else:   
    Tetrominoes = [letterToTetromino(l) for l in TETROMINOES]
