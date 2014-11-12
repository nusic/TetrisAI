#!/usr/bin/env python
"""
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
from time import sleep
from random import randint
import tkMessageBox
import sys
import copy

#True to use the AI, False to play the game
AI = True

SCALE = 30
OFFSET = 3
MAXX = 10
MAXY = 22

NO_OF_LEVELS = 10

LEFT = "left"
RIGHT = "right"
DOWN = "down"

direction_d = { "left": (-1, 0), "right": (1, 0), "down": (0, 1) }

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

class State:
    """
    This class is a complete representation of the current game state.
    """

    def __init__(self, width=10, height=20):
        self.landed = {}
        self.width = width
        self.height = height
        self.savedLanded = []

    def setAsLanded(self, blocks):
        """
        Adds the blocks to those in the grid that have already 'landed'
        """
        for block in blocks:
            self.landed[ block.coord() ] = block.id

    def findFirstEmptyRow(self):
        """
        Returns the row index of the first empty row
        """
        empty_row = -1
        for y in xrange(self.height -1, -1, -1):
            row_is_empty = True
            for x in xrange(self.width):
                if self.landed.get((x,y), None):
                    row_is_empty = False
                    break;
            if row_is_empty:
                empty_row = y
                break
        return empty_row

    def findCompleteRowsBelow(self, rowLimit):
        """
        Scans from bottom row, up until rowLimit, and finds any complete rows. 
        """
        completeRows = []
        y = self.height - 1 #Bottom row
        while y > rowLimit:

            complete_row = True
            for x in xrange(self.width):
                if self.landed.get((x,y), None) is None:
                    complete_row = False
                    break;

            if complete_row:
                completeRows.append(y)
            y -= 1
        return completeRows

    def addAndGetCompleteRows(self, blocks):
        """
        Adds the blocks and returns a list of rows that now are completed.
        """

        self.setAsLanded(blocks)
        empty_row = self.findFirstEmptyRow()
        return self.findCompleteRowsBelow(empty_row)

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

    def output( self ):
        for y in xrange(self.height):
            line = []
            for x in xrange(self.width):
                if self.landed.get((x,y), None):
                    line.append("X")
                else:
                    line.append(".")
            print "".join(line)

    def reward(self, dropedShapes):
        currShape = dropedShapes[0]

        holes = 0
        radius = 1
        checked = []
        totHeight = 0
       
        #deletedRows,dropedShapes2 = self.handleCompleteRows(copy.copy(dropedShapes))

        #if deletedRows:
        #   print [block.coord() for block in dropedShapes[0].blocks]
        #   print [block.coord() for block in dropedShapes2[0].blocks]
        #   print 
        #validate on droped shapes
        #coords = [(block.coord()) for block in currShape.blocks]
        #for i in range(1,len(dropedShapes)):
        #    coords += [(block.coord()) for block in dropedShapes[i].blocks]
        for block in currShape.blocks:
            totHeight += self.height-block.y
            for x in xrange(block.x-1,block.x+2):
                for y in xrange(block.y,block.y+2):
                    if x in range(0,self.width) and y in range(0,self.height):
                        if (x,y) not in checked and (x,y) not in self.landed:
                            holes += 1
                        checked.append((x,y))

        return holes + (totHeight/4)

    def pushLanded(self):
        self.savedLanded.append(copy.copy(self.landed))

    def popLanded(self):
        self.landed = self.savedLanded.pop(len(self.savedLanded)-1)

    #FUNKAR lINTE N
    def handleCompleteRows(self,dropedShapes):
        firstEmptyRow = state.findFirstEmptyRow()
        completeRows = state.findCompleteRowsBelow(firstEmptyRow)
        return [len(completeRows) > 0,self.deleteRows(completeRows, dropedShapes, firstEmptyRow)]

    def deleteRows(self, rows, dropedShapes, empty_row=0):
        #delete the completed row
        for y in rows:
            for x in xrange(self.width):
                self.landed.pop((x,y))
                for shape in dropedShapes:
                    if (x,y) in shape.blocks:
                        shape.pop((x,y))

            # move all the rows above it down
            for ay in xrange(y-1, empty_row, -1):
                for x in xrange(self.width):
                    block = self.landed.get((x,ay), None)
                    if block:
                        block = self.landed.pop((x,ay))
                        self.landed[(x+dx, ay+dy)] = block
                    for shape in dropedShapes:
                        if (x,y) in shape.blocks:
                            block = self.landed.pop((x,ay))
                            shape.append((x+dx, ay+dy))
        return dropedShapes 


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
        self.state = State(max_x, max_y)

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
    def check_and_create(cls, board, coords, colour ):
        """
        Check if the blocks that make the shape can be placed in empty coords
        before creating and returning the shape instance. Otherwise, return
        None.
        """
        for coord in coords:
            if not board.state.check_block( coord ):
                return None
        
        return cls( board, coords, colour)
            
    def __init__(self, board, coords, colour ):
        """
        Initialise the shape base.
        """
        self.board = board
        self.blocks = []
        
        for coord in coords:
            block = Block(self.board.add_block( coord, colour), coord)
            
            self.blocks.append( block )
            
    def move( self, direction ):
        """
        Move the blocks in the direction indicated by adding (dx, dy) to the
        current block coordinates
        """
        d_x, d_y = direction_d[direction]
        
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
    def __init__( self, board, coords, colour ):
        self.clockwise = True
        super(shape_limited_rotate, self).__init__(board, coords, colour)
    
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
        return super(square_shape, cls).check_and_create(board, coords, "red")
        
    def rotate(self, clockwise=True):
        """
        Override the rotate method for the square shape to do exactly nothing!
        """
        pass
        
class t_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(4,0),(3,0),(5,0),(4,1)]
        return super(t_shape, cls).check_and_create(board, coords, "yellow" )
        
class l_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(4,0),(3,0),(5,0),(3,1)]
        return super(l_shape, cls).check_and_create(board, coords, "orange")
    

        #  0 1 2 3 4 5 6
        #0         X X X
        #1             X
        #2
class reverse_l_shape( shape ):
    @classmethod
    def check_and_create( cls, board ):
        coords = [(5,0),(4,0),(6,0),(6,1)]
        return super(reverse_l_shape, cls).check_and_create(
            board, coords, "green")

class z_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(5,0),(4,0),(5,1),(6,1)]
        return super(z_shape, cls).check_and_create(board, coords, "purple")
        
class s_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(5,1),(4,1),(5,0),(6,0)]
        return super(s_shape, cls).check_and_create(board, coords, "magenta")
        
class i_shape( shape_limited_rotate ):
    @classmethod
    def check_and_create( cls, board ):
        coords =[(4,0),(3,0),(5,0),(6,0)]
        return super(i_shape, cls).check_and_create(board, coords, "blue")
        
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
        self.numNextShapes = 1
        self.moves = []
        
        #lookup table
        self.shapes = [square_shape,
                      t_shape,
                      l_shape,
                      reverse_l_shape,
                      z_shape,
                      s_shape,
                      i_shape ]
        
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
        
        if self.numNextShapes != 0:
            self.nextShapes += self.get_next_shapes(self.numNextShapes)
            self.shape = self.create_shape(self.nextShapes.pop(0))
        else:
            self.shape = self.create_shape(self.get_next_shapes(1)[0])
        self.nextShapes += self.get_next_shapes(1)

        self.ghostPiece = None
        self.updateGhostPiece()

        #self.board.output()

        self.after_id = self.parent.after( self.delay, self.move_my_shape )
    
    def updateGhostPiece(self):
        if not AI:
            if self.ghostPiece != None:
                for block in self.ghostPiece.blocks:
                    self.board.delete_block(block.id)
                    del block

            coords = []
            for block in self.shape.blocks:
                coords.append( (block.x, block.y) )

            gp = shape(self.board, coords, "black")

            while gp.move( DOWN ):
                pass
            
            self.ghostPiece = gp

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

                #Find the first empty row. One could call this the "tetris-height".
                #Find all complete rows below first empty row, and remove them
                firstEmptyRow = state.findFirstEmptyRow()
                completeRows = state.findCompleteRowsBelow(firstEmptyRow)
                self.deleteRows(completeRows, firstEmptyRow)

                #Update score based on # removed rows
                self.score += (100 * len(completeRows)) * len(completeRows)

                #Delete last shape and get a new one
                del self.shape
                self.shape = self.create_shape(self.nextShapes.pop(0))
                self.nextShapes += self.get_next_shapes(1)
                # If the shape returned is None, then this indicates that
                # that the check before creating it failed and the
                # game is over!
                if self.shape is None:
                    tkMessageBox.showwarning(
                        title="GAME OVER",
                        message ="Score: %7d\tLevel: %d\t" % (
                            self.score, self.level),
                        parent=self.parent
                        )
                    Toplevel().destroy()
                    self.parent.destroy()
                    #self.__init__(root)
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
                        dx,dy = direction_d[DOWN]
                        
                        self.board.move_block(block, direction_d[DOWN])
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

    def move_my_shape( self ):
        if self.shape:
            
            if AI:
                self.moves = []
                self.board.state.pushLanded()
                self.recursiveMove(self.shape,[],0,0)
                coords = min(self.moves)[1]
                self.board.state.popLanded()

                self.shape.setCoords(coords)
                self.handle_move(DOWN)
                
                self.after_id = self.parent.after( 1 , self.move_my_shape )

            else:
                self.handle_move( DOWN )
                self.after_id = self.parent.after( self.delay, self.move_my_shape )


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

    def recursiveMove(self,newShape,dropedShapes,n,reward):
        if newShape != None:
            if n <= self.numNextShapes:
                shape = self.create_shape(newShape)
                if shape != None:
                    for _ in range(10):
                        self.shape.move(LEFT)
                    self.moveRightReward(shape,dropedShapes,n,reward)
                    self.moveLeftRotate(shape)
                    self.moveRightReward(shape,dropedShapes,n,reward)
                    self.moveLeftRotate(shape)
                    self.moveRightReward(shape,dropedShapes,n,reward)
                    self.moveLeftRotate(shape)
                    self.moveRightReward(shape,dropedShapes,n,reward)
                    self.delShape(shape)
                else:
                    self.recursiveMove(newShape,dropedShapes,self.numNextShapes+1,reward)
            else:
                self.moves += [(reward + self.board.state.reward(dropedShapes), self.shapeCoords(dropedShapes[0]))] 

    def moveRightReward(self,shape,dropedShapes,n,reward):
        for _ in range(10):
            if shape != None:
                dropedShape = self.dropShape(shape)
                dropedShapes.append(dropedShape)
                self.board.state.pushLanded()
                #reward += self.board.state.reward(dropedShapes)
                for dshape in dropedShapes:
                    if dshape != None:
                        self.board.state.setAsLanded(dshape.blocks)
                self.recursiveMove(self.nextShapes[n-1],dropedShapes,n+1,reward)
                shape.move(RIGHT)
                dropedShapes.pop(len(dropedShapes)-1)
                self.board.state.popLanded()
                if dropedShape != None:
                    self.delShape(dropedShape)

    def moveLeftRotate(self, shape):
        for _ in range(5):
            shape.move(LEFT)
        shape.rotate(clockwise=True)
        for _ in range(5):
            shape.move(LEFT)

    def get_next_shapes( self, num ):
        """
        Randomly select which tetrominoe will be used next.
        """
        shapes = []
        for _ in range(num):
            shapes.append(self.shapes[randint(0,len(self.shapes)-1)])
        return shapes

    def create_shape( self, the_shape):
        shape = the_shape.check_and_create(self.board)
        if shape is not None:
            shape.move("down")
            shape.move("down")
        return shape
        
if __name__ == "__main__":
    root = Tk()
    root.title("Tetris Tk")
    theGame = GameController( root )
    
    root.mainloop()
