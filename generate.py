import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for each in self.domains:
            our_words = self.domains[each].copy()
            for word in our_words:
                if len(word) != each.length:
                    self.domains[each].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        intersection = self.crossword.overlaps[x, y]

        if intersection is None:
            return revised
        else:
            a, b = intersection
            x_vals = self.domains[x].copy()

            for x_val in x_vals:
                x_let = x_val[a]
                counter = 0

                for y_val in self.domains[y]:
                    y_let = y_val[b]
                    if x_let == y_let:
                        counter += 1
                if counter == 0:
                    self.domains[x].remove(x_val)
                    revised = True
        return revised




    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            arcs = []
            for each in self.crossword.variables:
                neighbors = self.crossword.neighbors(each)
                for neighbor in neighbors:
                    arc = (each, neighbor)
                    if arc not in arcs:
                        arcs.append(arc)
        for arc in arcs:
            x, y = arc
            update = self.revise(x, y)

            if update:
                if len(self.domains[x]) == 0:
                    return False
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(assignment) == len(self.crossword.variables):
            return True
        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for i in assignment:
            word = assignment[i]
            for j in assignment:
                if i == j:
                    continue
                elif word == assignment[j]:
                    return False
            if len(word) != i.length:
                return False
            neighbors = self.crossword.neighbors(i)
            for neighbor in neighbors:
                if neighbor in assignment:
                    a, b = self.crossword.overlaps[i, neighbor]
                    if word[a] != assignment[neighbor][b]:
                        return False
        return True


    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        if var not in assignment:
            neighbors = self.crossword.neighbors(var)
            if len(neighbors) is None:
                return self.domains[var]
            else:
                order = []
                for each in self.domains[var]:
                    counter = 0
                    for neighbor in neighbors:
                        a, b = self.crossword.overlaps[var, neighbor]
                        for each_neighb in self.domains[neighbor]:
                            if each[a] != each_neighb[b]:
                                counter += 1
                    order.append((each, counter))
                order.sort(key=by_second_value)
                lis = []
                for x in range(len(order)):
                    lis.append(order[x][0])
                return lis


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        order = []
        for each in self.domains:
            if each not in assignment:
                remain_val = len(self.domains[each])
                order.append((each, remain_val))
        order.sort(key=by_second_value)
        var = order[0][0]
        min_len = order[0][1]
        neighbiors_num = len(self.crossword.neighbors(var))
        for x in range(len(order)):
            if order[x][1] == min_len:
                x_neighbors = len(self.crossword.neighbors(order[x][0]))
                if x_neighbors > neighbiors_num:
                    neighbiors_num = x_neighbors
                    var = order[x][0]
        return var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        val_list = self.order_domain_values(var, assignment)
        for val in val_list:
            assignment[var] = val
            if self.consistent(assignment):
                solution = self.backtrack(assignment)
                if solution is not None:
                    return solution
                else:
                    assignment.pop(var)
        return None

def by_second_value(val):
    return val[1]  

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
