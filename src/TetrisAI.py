#!/usr/bin/env python
"""
HighScore: 35900

Tetris Tk - A tetris clone written in Python using the Tkinter GUI library.

Controls:
    Left Arrow      Move left
    Right Arrow     Move right
    Down Arrow      Move down
    Up Arrow        Drop Tetronimoe to the bottom
    'a'             Rotate anti-clockwise (to the left)
    'b'             Rotate clockwise (to the right)
    'p'             Pause the game.
"""
#Sebb was here
#Changed and commited with sublime
from Tkinter import *
import random

import time
import tkMessageBox
import sys
import collections
import numpy

from GlobalSettings import *
import GameLogic
import AI

scores = []
times = []

trainData = []

def trainDataStr():
    s = ""
    #Header
    (weights, avg, std) = trainData[0]
    for key in weights.keys():
        s += str(key) + "\t"
 
    s += " mean score" + "\t" + "std score" + "\n"

    #Data
    for weights, avg, std in trainData:
        for w in weights:
            s += "{:10.2f}".format(weights[w]) + "\t"
        s += "{:10.2f}".format(avg)
        s += "{:10.2f}".format(std)
        s += "\n"
    return s

def statsStr(samples):
    return "%0.1f"%min(samples)+"\t"\
            +"%0.1f"%max(samples)+"\t"\
            +"%0.1f"%numpy.mean(samples)+"\t"\
            +"%0.1f"%numpy.std(samples)

def printStats():
    print 
    print "\tmin\tmax\tavg\tstd"
    print "SCORES:\t",statsStr(scores)
    print " TIMES:\t",statsStr(times)
    print "AVG SCORE / AVG TIME: ", numpy.mean(scores)/numpy.mean(times)
    print 


def level_thresholds( first_level, no_of_levels ):
    """
    Calculates the score at which the level will change, for n levels.
    """
    thresholds =[]
    for x in xrange( no_of_levels ):
        multiplier = 2**x
        thresholds.append( first_level * multiplier )
    
    return thresholds

class status_bar( Frame ):
    """
    Status bar to display the score and level
    """
    def __init__(self, parent):
        Frame.__init__( self, parent )
        self.label = Label( self, bd=1, relief=SUNKEN, anchor=W )
        self.label.pack( fill=X )
        
    def set( self, format, *args):
        self.label.config( text = format % args)
        self.label.update_idletasks()
        
    def clear( self ):
        self.label.config(test="")
        self.label.update_idletasks()

class Board( Frame ):
    """
    The board represents the tetris playing area. A grid of x by y blocks.
    """
    def __init__(self, parent, scale=20, max_x=10, max_y=20, offset=3):
        """
        Init and config the tetris board, default configuration:
        Scale (block size in pixels) = 20
        max X (in blocks) = 10
        max Y (in blocks) = 20
        offset (in pixels) = 3
        """
        Frame.__init__(self, parent)
        # blocks are indexed by there corrdinates e.g. (4,5), these are
        self.state = GameLogic.State(max_x, max_y)

        self.parent = parent
        self.scale = scale
        self.offset = offset        

        self.canvas = Canvas(parent,
                             height=(max_y * scale)+offset,
                             width= (max_x * scale)+offset)
        self.canvas.pack()

    def add_block( self, (x, y), colour):
        """
        Create a block by drawing it on the canvas, return
        it's ID to the caller.
        """
        rx = (x * self.scale) + self.offset
        ry = (y * self.scale) + self.offset
        
        return self.canvas.create_rectangle(
            rx, ry, rx+self.scale, ry+self.scale, fill=colour
        )
        
    def move_block( self, id, coord):
        """
        Move the block, identified by 'id', by x and y. Note this is a
        relative movement, e.g. move 10, 10 means move 10 pixels right and
        10 pixels down NOT move to position 10,10. 
        """
        x, y = coord
        self.canvas.move(id, x*self.scale, y*self.scale)
        
    def delete_block(self, id):
        """
        Delete the identified block
        """
        self.canvas.delete( id )
        
class Block(object):
    def __init__( self, id, (x, y)):
        self.id = id
        self.x = x
        self.y = y
        
    def coord( self ):
        return (self.x, self.y)


class shape(object):
    """
    Shape is the  Base class for the game pieces e.g. square, T, S, Z, L,
    reverse L and I. Shapes are constructed of blocks. 
    """
    @classmethod
    def check_and_create(cls, board, coords, colour, rots):
        """
        Check if the blocks that make the shape can be placed in empty coords
        before creating and returning the shape instance. Otherwise, return
        None.
        """
        for coord in coords:
            if not board.state.check_block( coord ):
                return None
        
        return cls( board, coords, colour, rots)
            
    def __init__(self, board, coords, colour, rots):
        """
        Initialise the shape base.
        """
        self.board = board
        self.blocks = []
        self.rots = rots
        
        for coord in coords:
            block = Block(self.board.add_block( coord, colour), coord)
            
            self.blocks.append( block )
            
    def move( self, direction ):
        """
        Move the blocks in the direction indicated by adding (dx, dy) to the
        current block coordinates
        """
        d_x, d_y = DIRECTIONS[direction]
        
        for block in self.blocks:

            x = block.x + d_x
            y = block.y + d_y
            
            if not self.board.state.check_block( (x, y) ):
                return False
            
        for block in self.blocks:
            
            x = block.x + d_x
            y = block.y + d_y
            
            self.board.move_block( block.id, (d_x, d_y) )
            
            block.x = x
            block.y = y
        
        return True
            
    def rotate(self, clockwise = True):
        """
        Rotate the blocks around the 'middle' block, 90-degrees. The
        middle block is always the index 0 block in the list of blocks
        that make up a shape.
        """
        # TO DO: Refactor for DRY
        middle = self.blocks[0]
        rel = []
        for block in self.blocks:
            rel.append( (block.x-middle.x, block.y-middle.y ) )
            
        # to rotate 90-degrees (x,y) = (-y, x)
        # First check that the there are no collisions or out of bounds moves.
        for idx in xrange(len(self.blocks)):
            rel_x, rel_y = rel[idx]
            if clockwise:
                x = middle.x-rel_y
                y = middle.y+rel_x
            else:    
                x = middle.x+rel_y
                y = middle.y-rel_x
            
            if not self.board.state.check_block( (x, y), includeRoof=False):
                return False
            
        for idx in xrange(len(self.blocks)):
            rel_x, rel_y = rel[idx]
            if clockwise:
                x = middle.x-rel_y
                y = middle.y+rel_x
            else:    
                x = middle.x+rel_y
                y = middle.y-rel_x
            
            
            diff_x = x - self.blocks[idx].x 
            diff_y = y - self.blocks[idx].y 
            
            self.board.move_block( self.blocks[idx].id, (diff_x, diff_y) )
            
            self.blocks[idx].x = x
            self.blocks[idx].y = y
       
        return True

    def setCoords(self,coords):
        for i in range(len(self.blocks)):
            x,y = coords[i]
            dx = x-self.blocks[i].x
            dy = y-self.blocks[i].y
            self.blocks[i].x = x;
            self.blocks[i].y = y;

            self.board.move_block( self.blocks[i].id, (dx, dy) )
        return True


class shape_limited_rotate( shape ):
    """
    This is a base class for the shapes like the S, Z and I that don't fully
    rotate (which would result in the shape moving *up* one block on a 180).
    Instead they toggle between 90 degrees clockwise and then back 90 degrees
    anti-clockwise.
    """
    def __init__( self, board, coords, colour, rots ):
        self.clockwise = True
        super(shape_limited_rotate, self).__init__(board, coords, colour, rots)
    
    def rotate(self, clockwise=True):
        """
        Clockwise, is used to indicate if the shape should rotate clockwise
        or back again anti-clockwise. It is toggled.
        """
        super(shape_limited_rotate, self).rotate(clockwise=self.clockwise)
        if self.clockwise:
            self.clockwise=False
        else:
            self.clockwise=True
        

class square_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(4,0),(5,0),(4,1),(5,1)]
        rots = []
        return super(square_shape, cls).check_and_create(board, coords, "red", rots)
        
    def rotate(self, clockwise=True):
        """
        Override the rotate method for the square shape to do exactly nothing!
        """
        pass
        
class t_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(4,0),(3,0),(5,0),(4,1)]
        rots = [1, 1, 1]
        return super(t_shape, cls).check_and_create(board, coords, "yellow" , rots)
        
class l_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(4,0),(3,0),(5,0),(3,1)]
        rots = [1, 1, 1]
        return super(l_shape, cls).check_and_create(board, coords, "orange", rots)
    

        #  0 1 2 3 4 5 6 7 8 9 
        #0         X X X
        #1             X
        #2
        #:
class reverse_l_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(5,0),(4,0),(6,0),(6,1)]
        rots = [1, 1, 1]
        return super(reverse_l_shape, cls).check_and_create(
            board, coords, "green", rots)

class z_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(5,0),(4,0),(5,1),(6,1)]
        rots = [1]
        return super(z_shape, cls).check_and_create(board, coords, "purple", rots)
        
class s_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(5,1),(4,1),(5,0),(6,0)]
        rots = [1]
        return super(s_shape, cls).check_and_create(board, coords, "magenta", rots)
        
class i_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(4,0),(3,0),(5,0),(6,0)]
        rots = [1]
        return super(i_shape, cls).check_and_create(board, coords, "blue", rots)


class GameController(object):
    """
    Main game loop and receives GUI callback events for keypresses etc...
    """
    def __init__(self, parent):
        """
        Intialise the game...
        """
        self.parent = parent
        self.score = 0
        self.level = 0
        self.delay = 1000    #ms
        self.nextShapes = []
        

        #lookup table
        self.shapes = []
        self.shapes = [self.letterToTetromino(l) for l in TETROMINOES]

        
        self.thresholds = level_thresholds( 500, NO_OF_LEVELS )
        
        self.status_bar = status_bar( parent )
        self.status_bar.pack(side=TOP,fill=X)
        #print "Status bar width",self.status_bar.cget("width")

        self.status_bar.set("Score: %-7d\t Level: %d " % (
            self.score, self.level+1)
        )
        
        self.board = Board(
            parent,
            scale=SCALE,
            max_x=MAXX,
            max_y=MAXY,
            offset=OFFSET
            )
        
        self.board.pack(side=BOTTOM)
        
        self.parent.bind("<Left>", self.left_callback)
        self.parent.bind("<Right>", self.right_callback)
        self.parent.bind("<Up>", self.rot_clockwise_callback)
        self.parent.bind("<Down>", self.down_callback)
        self.parent.bind("<space>", self.hard_drop_callback)
        #self.parent.bind("s", self.rot_anticlockwise_callback)
        self.parent.bind("p", self.pause_callback)
        

        self.ghostPiece = None
        self.showGhostPiece = not USE_AI and SHOW_GHOST_PIECE
        

        self.numNextShapes = LOOKAHEAD
        self.maxRuns = NUM_ITERATIONS

        self.generation = 0
        self.maxGeneration = NUM_GENERATIONS

        self.runs = 0
        self.userPickShape = False

        self.seq_index = 0
        self.seq_loop = LOOP_SEQUENCE


        if self.userPickShape:
            self.shape = self.create_shape(shapeFromInput())
        else:
            self.initNextShapes()
            


        self.ai = AI.SimpleAI()
        self.t0 = time.clock()
        self.after_id = self.parent.after( self.delay, self.move_my_shape )

    def initNextShapes(self):
        if self.numNextShapes != 0:
            self.nextShapes = self.get_next_shapes(self.numNextShapes+1)
            self.shape = self.create_shape(self.nextShapes.pop(0))
        else:
            self.shape = self.create_shape(self.get_next_shapes(1)[0])

    def letterToTetromino(self, letter):
        if letter.upper() == "O": return square_shape
        if letter.upper() == "T": return t_shape
        if letter.upper() == "L": return l_shape
        if letter.upper() == "J": return reverse_l_shape
        if letter.upper() == "Z": return z_shape
        if letter.upper() == "S": return s_shape
        if letter.upper() == "I": return i_shape
        raise Exception("Cannot parse " + letter + " to Tetromino")
    
    def updateGhostPiece(self):
        if self.showGhostPiece:
            if self.ghostPiece != None:
                for block in self.ghostPiece.blocks:
                    self.board.delete_block(block.id)
                    del block

            coords = []
            for block in self.shape.blocks:
                coords.append( (block.x, block.y) )

            gp = shape(self.board, coords, [], "black")

            while gp.move( DOWN ):
                pass
            
            self.ghostPiece = gp

    def restart(self):
        self.board.state.landed.clear()
        self.board.canvas.delete(ALL)
        self.seq_index = 0
        self.score = 0
        self.level = 0
        self.initNextShapes()
        #self.shape = self.create_shape(self.nextShapes.pop(0))

    def handle_move(self, direction):

        #if you can't move then you've hit something
        playerPieceMoved = self.shape.move( direction )
        if not playerPieceMoved:
            # Being here means we couldn't move the current shape.

            # If we tried to move down but couldn't move, that means 
            # the current shape has "landed" on the ground.
            if direction == DOWN:
                #Shortcut for accessing the game state
                state = self.board.state

                #Set the current shape as "landed"
                state.setAsLanded(self.shape.blocks)

                #print "shape rots:", self.shape.rots

                #Find the first empty row. One could call this the "tetris-height".
                #Find all complete rows below first empty row, and remove them
                firstEmptyRow = state.findFirstEmptyRow()
                completeRows = state.findCompleteRowsBelow(firstEmptyRow)
                self.deleteRows(completeRows, firstEmptyRow)

                #Update score based on # removed rows
                self.score += (100 * len(completeRows)) * len(completeRows)

                #Delete last shape and get a new one
                del self.shape
                self.nextShapes += self.get_next_shapes(1)
                if self.userPickShape:
                    self.shape = self.create_shape(shapeFromInput())
                else:
                    self.shape = self.create_shape(self.nextShapes.pop(0))
                
                
                # If the shape returned is None, then this indicates that
                # that the check before creating it failed and the
                # game is over!
                if self.shape is None:
                    #END GAME
                    self.runs += 1
                    t = time.clock() - self.t0
                    self.t0 = time.clock()

                    print self.generation,":",self.runs,":", "score:", self.score, "time:",t

                    scores.append(self.score)
                    times.append(t)

                    #f = open('bestScores', 'r+')

                    #f.write(",".join( str(scr) for scr in bestActionScores))
                    #f.close()

                    if USE_AI == None:
                        tkMessageBox.showwarning(
                            title="GAME OVER",
                            message ="Score: %7d\tLevel: %d\t" % (
                                self.score, self.level),
                            parent=self.parent
                            )
                        self.restart()
                        #Toplevel().destroy()
                    elif self.runs < self.maxRuns:
                        self.restart()
                    else:
                        printStats()
                        if self.generation < self.maxGeneration:

                            meanScore = numpy.mean(scores)
                            stdScore = numpy.std(scores)
                            trainData.append( (dict(self.ai.weights), meanScore, stdScore) )
                            del scores[:]
                            self.ai.mutate()
                            self.ai.mutate()
                            self.ai.mutate()

                            self.generation += 1
                            self.runs = 0
                            self.restart()
                        else:
                            if trainData:
                                print trainDataStr()
                            sys.exit(0)

                # do we go up a level?
                if (self.level < NO_OF_LEVELS and 
                    self.score >= self.thresholds[ self.level]):
                    self.level+=1
                    self.delay-=100
                    
                self.status_bar.set("Score: %-7d\t Level: %d " % (
                    self.score, self.level+1)
                )
                
                # Signal that the shape has 'landed'
                self.updateGhostPiece()
                return False
        self.updateGhostPiece()
        return True
        


    def deleteRows(self, rows, empty_row=0):
        #delete the completed row
        deletes = 0
        for y in rows:
            y += deletes
            for x in xrange(self.board.state.width):
                block = self.board.state.landed.pop((x,y))
                self.board.delete_block(block)
                del block

            # move all the rows above it down
            for ay in xrange(y-1, empty_row, -1):
                for x in xrange(self.board.state.width):
                    block = self.board.state.landed.get((x,ay), None)
                    if block:
                        block = self.board.state.landed.pop((x,ay))
                        dx,dy = DIRECTIONS[DOWN]
                        
                        self.board.move_block(block, DIRECTIONS[DOWN])
                        self.board.state.landed[(x+dx, ay+dy)] = block
            deletes += 1


    def left_callback( self, event ):
        if self.shape:
            self.handle_move( LEFT )
        
    def right_callback( self, event ):
        if self.shape:
            self.handle_move( RIGHT )

    def hard_drop_callback( self, event ):
        if self.shape:
            # drop the tetrominoe to the bottom
            while self.handle_move( DOWN ):
                pass

    def down_callback( self, event ):
        if self.shape:
            self.handle_move( DOWN )
            
    def rot_clockwise_callback( self, event):
        if self.shape:
            self.shape.rotate(clockwise=True)
            self.updateGhostPiece()
            
    def rot_anticlockwise_callback( self, event):
        if self.shape:
            self.shape.rotate(clockwise=False)
            self.updateGhostPiece()
        
    def pause_callback(self, event):
        self.parent.after_cancel( self.after_id )
        tkMessageBox.askquestion(
            title = "Paused!",
            message="Continue?",
            type=tkMessageBox.OK)
        self.after_id = self.parent.after( self.delay, self.move_my_shape )

    def getNextTetrominoes(self):
        tetrominoes = []
        for shape in self.nextShapes:
            s = shape.check_and_create(self.board)
            if s != None:
                tetrominoes.append(GameLogic.Tetromino( [b.coord() for b in s.blocks] , s.rots))
                self.delShape(s)
        return tetrominoes

    def move_my_shape( self ):
        if self.shape:
            
            if USE_AI:
                shapeCoords = [ (b.x, b.y) for b in self.shape.blocks ]

                t = [GameLogic.Tetromino(shapeCoords, self.shape.rots)]
                t += self.getNextTetrominoes()
                
                #t0 = time.clock()
                tetromino = self.ai.getNextPieceOrientation(self.board.state, t)

                #print time.clock()-t0
                self.shape.setCoords(tetromino.coords)

                self.handle_move(DOWN)
                self.after_id = self.parent.after( 0 , self.move_my_shape )

            else:
                self.handle_move( DOWN )
                self.after_id = self.parent.after( self.delay, self.move_my_shape )


    def get_next_shapes( self, num ):
        """
        Randomly select which tetrominoe will be used next.
        """
        shapes = []
        for _ in range(num):
            if TETROMINO_SEQUENCE:
                if self.seq_index == -1:
                    raise Exception("End of sequence!")
                
                shapes.append(self.letterToTetromino(TETROMINO_SEQUENCE[self.seq_index]))
                self.seq_index += 1
                self.seq_index %= len(TETROMINO_SEQUENCE)

                if not self.seq_loop and self.seq_index == 0 :
                    self.seq_index = -1

            else:
                shapes.append(self.shapes[random.randint(0,len(self.shapes)-1)])
        return shapes

    def dropShape(self,dropShape):
        dropedShape = shape(self.board, self.shapeCoords(dropShape), "black")

        while dropedShape.move( DOWN ):
            pass

        return dropedShape

    def shapeCoords(self, shape):
        coords = []
        for block in shape.blocks:
            coords.append((block.coord()))
        return coords

    def delShape(self, shape):
        for block in shape.blocks:
            self.board.delete_block(block.id)
            del block
        del shape

    def create_shape( self, the_shape):
        shape = the_shape.check_and_create(self.board)
        if shape is not None:
            pass#shape.move("down")
        return shape

def shapeFromInput():
    while True:
        s = raw_input("Enter shape [ O, T, L, J, Z, S, I ]: ").upper()
        try:
            return letterToTetromino(s)
        except Exception, e:
            print "invalid shape"
        
if __name__ == "__main__":
    root = Tk()
    root.title("Tetris Tk")
    #root.withdraw()

    theGame = GameController( root )
    
    root.mainloop()
