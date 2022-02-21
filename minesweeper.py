from contextlib import nullcontext
from ctypes import sizeof
from glob import glob
import itertools
import random
import re
from tkinter.messagebox import NO

from django.forms import SelectDateWidget
from sklearn import neighbors


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"
    
    def is_subset(self, sentence):
        if(self.cells.issubset(sentence.cells)):
            inf = Sentence (sentence.cells.difference(self.cells), sentence.count - self.count)
            return inf
        return None

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if(len(self.cells) == self.count):
            return self.cells
        return None

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if(self.count == 0):
            return self.cells
        return None


    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if(self.cells.__contains__(cell)):
            self.cells.remove(cell)
            self.count -=1
        if(len(self.cells) == 0):
            self = None   

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if(self.cells.__contains__(cell)):
            self.cells.remove(cell)
        if(len(self.cells) == 0):
            self = None

class MinesweeperAI():
    """
    Minesweeper game player
    """
    
    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width
        # Initialize an empty field with no mines
        self.board = set()
        for i in range(self.height):
            for j in range(self.width):
                self.board.add((i,j))


        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []
    def neighbors(self,cell):
        neighbors = set()
        mines = 0
        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if(((i,j) not in self.moves_made)):
                        if((i,j) not in self.mines):
                            neighbors.add((i,j))
                        else:
                            mines+=1
                        
        return neighbors,mines
    
    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)
            if(sentence is None):
                self.knowledge.remove(sentence)
            
    

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)
            if(sentence is None):
                self.knowledge.remove(sentence)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        
       
        # 1) mark the cell as a move that has been made
        self.moves_made.add(cell)
        # 2) mark the cell as safe
        self.mark_safe(cell) 
        # 3) add a new sentence to the AI's knowledge base based on the value of `cell` and `count`
        neighbors, mines = self.neighbors(cell)
        sentence = Sentence (neighbors,count -mines)
        self.knowledge.append(sentence) 
        changed = True
        while(changed):
            changed = False
            # 4) mark any additional cells as safe or as mines if it can be concluded based on the AI's knowledge base
            for sentence in self.knowledge.copy():
                if(sentence.known_mines()):
                    changed = True
                    for cell in sentence.known_mines().copy():
                        self.mark_mine(cell)
                    self.knowledge.remove(sentence)
                elif(sentence.known_safes()):
                    changed = True
                    for cell in sentence.known_safes().copy():
                        self.mark_safe(cell)        
                    self.knowledge.remove(sentence)
            # 5) add any new sentences to the AI's knowledge base if they can be inferred from existing knowledge
            for sentence1 in self.knowledge.copy():
                for sentence2 in self.knowledge.copy():
                    if sentence1 != sentence2:
                        inf = sentence1.is_subset(sentence2)
                        if(inf):
                            if(inf not in self.knowledge):
                                self.knowledge.append(inf)
                                if(inf.known_safes() or inf.known_mines()):
                                    changed= True
                        else:
                            inf = sentence2.is_subset(sentence1)
                            if(inf):
                                if(inf not in self.knowledge):
                                    self.knowledge.append(inf)
                                    if(inf.known_safes() or inf.known_mines()):
                                        changed= True

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        
        cells = list()
        for cell in self.safes:
            if (cell not in self.mines and cell not in self.moves_made):
                cells.append(cell)
        if(cells):
            return cells.pop(-1)
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        cells = list()
        for cell in self.board:
            if (cell not in self.mines and cell not in self.moves_made):
                cells.append(cell)
        if(cells):
            return cells.pop(random.randrange(len(cells)))
        return None