import bisect
import itertools
import random
import sys
from collections import deque

from constants import *


class Line:
    def __init__(self, coordinates, clues, orientation):
        self.coordinates = coordinates
        self.clues = clues
        self.orientation = orientation

    def __lt__(self, other):
        return sum(self.clues) < sum(other.clues)

    def __hash__(self):
        return hash(self.coordinates)


class Nonogram:
    def __init__(self, clues=None, n=15, m=15, density=.5, seed=None):
        if clues is None:
            if seed:
                random.seed(seed)
            else:
                seed = random.randrange(sys.maxsize)
                random.seed(seed)
                print(f"Seed is: {seed}")
            self.vertical_clues, self.horizontal_clues = self.generate_random_clues(n, m, density)
        else:
            self.vertical_clues = clues[0]
            self.horizontal_clues = clues[1]
        self.x_size = len(self.vertical_clues)
        self.y_size = len(self.horizontal_clues)
        self.grid = [[UNKNOWN for _ in range(self.y_size)] for _ in range(self.x_size)]
        self.lines_to_solve = deque()
        self.lines_to_solve_set = set()
        self.horizontal_lines = []
        self.vertical_lines = []
        for x in range(self.x_size):
            line = Line(tuple((x, y) for y in range(self.y_size)), self.vertical_clues[x], 'vertical')
            self._enqueue_line_to_solve(line)
            self.vertical_lines.append(line)
        for y in range(self.y_size):
            line = Line(tuple((x, y) for x in range(self.x_size)), self.horizontal_clues[y], 'horizontal')
            self._enqueue_line_to_solve(line)
            self.horizontal_lines.append(line)
        self.gui = None

    @staticmethod
    def generate_random_clues(n, m, density):
        filled_indices = set(random.sample(range(n * m), round(density * n * m)))
        grid = [[EMPTY if i * n + j not in filled_indices else FILLED for i in range(n)] for j in range(m)]
        horizontal_clues = []
        for i in range(m):
            count_filled = 0
            clues = []
            for j in range(n):
                if grid[i][j] == FILLED:
                    count_filled += 1
                else:
                    if count_filled != 0:
                        clues.append(count_filled)
                    count_filled = 0
            if count_filled:
                clues.append(count_filled)
            horizontal_clues.append(clues)

        vertical_clues = []
        for i in range(n):
            count_filled = 0
            clues = []
            for j in range(m):
                if grid[j][i] == FILLED:
                    count_filled += 1
                else:
                    if count_filled != 0:
                        clues.append(count_filled)
                    count_filled = 0
            if count_filled:
                clues.append(count_filled)
            vertical_clues.append(clues)
        return vertical_clues, horizontal_clues

    def set_gui(self, gui):
        self.gui = gui
        self.gui.draw()

    def _enqueue_line_to_solve(self, line):
        self.lines_to_solve.appendleft(line)
        self.lines_to_solve_set.add(line)

    def _get_next_line_to_solve(self):
        line = self.lines_to_solve.pop()
        self.lines_to_solve_set.remove(line)
        return line

    @staticmethod
    def _get_value_from_placement(position, placement):
        for cell_index, length in placement:
            if cell_index <= position < cell_index + length:
                return 1
        return 0

    @staticmethod
    def solve_for_values(clues, values):
        if sum(1 for value in values if value == FILLED) == sum(clues):
            return [EMPTY if value == UNKNOWN else value for value in values]

        # Find all possible placements
        already_filled_cells = [i for i, value in enumerate(values) if value == FILLED]
        possible_placements = []
        init_cell_indexes = [0]
        while values[init_cell_indexes[0]] == EMPTY:
            init_cell_indexes[0] += 1
        clue_index = 0
        cur_placement = []
        while init_cell_indexes[0] < len(values):
            if (all(init_cell_indexes[clue_index] + i < len(values) and values[init_cell_indexes[clue_index] + i] in {FILLED, UNKNOWN} for i in range(clues[clue_index]))
                    and (init_cell_indexes[clue_index] + clues[clue_index] >= len(values) or values[init_cell_indexes[clue_index] + clues[clue_index]] in {UNKNOWN, EMPTY})):
                cur_placement.append((init_cell_indexes[clue_index], clues[clue_index]))
                if clue_index < len(clues) - 1:
                    init_cell_indexes.append(init_cell_indexes[clue_index] + clues[clue_index] + 1)
                    clue_index += 1
                else:
                    if all(Nonogram._get_value_from_placement(i, cur_placement) == FILLED for i in already_filled_cells):
                        possible_placements.append(cur_placement[:])
                    init_cell_indexes[clue_index] += 1
                    cur_placement.pop()
            else:
                if init_cell_indexes[clue_index] >= len(values):
                    clue_index -= 1
                    init_cell_indexes.pop()
                    cur_placement = cur_placement[:-1]
                init_cell_indexes[clue_index] += 1

        # Find values common to all placements
        if possible_placements:
            new_values = []
            for i in range(len(values)):
                new_value = Nonogram._get_value_from_placement(i, possible_placements[0])
                if all(Nonogram._get_value_from_placement(i, placement) == new_value for placement in possible_placements):
                    new_values.append(new_value)
                else:
                    new_values.append(UNKNOWN)
            if new_values != values:
                return new_values
        return False

    @staticmethod
    def optimized_solve_for_values(clues, values):
        # Generate all possible ranges
        margin = len(values) - sum(clues) - len(clues) + 1
        clues_ranges = []
        i = 0
        for clue in clues:
            clues_ranges.append([i + j for j in range(margin + 1)])
            i += clue + 1

        # Filter based on empty cells
        empty_cells = [i for i, value in enumerate(values) if value == EMPTY]
        clues_search_start_i = 0
        for empty_cell_i in empty_cells:
            first_match_found = False
            for clue_range, clue in zip(clues_ranges[clues_search_start_i:], clues[clues_search_start_i:]):
                if clue_range[0] > empty_cell_i:
                    break
                elif empty_cell_i < clue_range[-1] + clue:
                    first_match_found = True
                    for i in (i + empty_cell_i - clue + 1 for i in range(clue)):
                        try:
                            clue_range.remove(i)
                        except ValueError:
                            pass
                elif not first_match_found:
                    clues_search_start_i += 1

        # Filter based on ranges start
        for (clue_range, clue), (other_clues_range, other_clue) in zip(zip(clues_ranges[:-1], clues[:-1]), zip(clues_ranges[1:], clues[1:])):
            other_clues_range[:] = other_clues_range[bisect.bisect_right(other_clues_range, clue_range[0] + clue):]
            clue_range[:] = clue_range[:bisect.bisect_left(clue_range, other_clues_range[-1] - clue)]

        # Filter based on filled cells
        for clue_range, clue in zip(clues_ranges, clues):
            values_to_remove = []
            for clue_start_i in clue_range:
                if (clue_start_i > 0 and values[clue_start_i - 1] == FILLED) or (clue_start_i + clue < len(values) and values[clue_start_i + clue] == FILLED):
                    values_to_remove.append(clue_start_i)
            for value in values_to_remove:
                clue_range.remove(value)

        new_values = [EMPTY if value != FILLED else FILLED for value in values]
        for clue_range, clue in zip(clues_ranges, clues):
            filled_cells_length = clue_range[0] + clue - clue_range[-1]
            for i in range(clue_range[-1] - clue_range[0] + clue):
                if values[clue_range[0] + i] == UNKNOWN:
                    new_values[clue_range[0] + i] = UNKNOWN
            for i in range(filled_cells_length):
                new_values[clue_range[0] + clue - filled_cells_length + i] = FILLED

        if sum(clues) == new_values.count(FILLED):
            return [EMPTY if value == UNKNOWN else value for value in new_values]

        return new_values

    def _update_grid_from_values(self, line, values):
        for i, (x, y) in enumerate(line.coordinates):
            if values[i] != UNKNOWN and self.grid[x][y] != values[i]:
                new_line_to_solve = self.horizontal_lines[i] if line.orientation == 'vertical' else self.vertical_lines[i]
                if new_line_to_solve not in self.lines_to_solve_set and any(self.grid[x][y] == UNKNOWN for x, y in new_line_to_solve.coordinates):
                    self._enqueue_line_to_solve(new_line_to_solve)
                self.grid[x][y] = values[i]

    def solve(self):
        while self.lines_to_solve:
            line = self._get_next_line_to_solve()
            values = self.optimized_solve_for_values(line.clues, [self.grid[x][y] for x, y in line.coordinates])
            self._update_grid_from_values(line, values)
            if self.gui:
                self.gui.draw()

        for line in itertools.chain(self.horizontal_lines, self.vertical_lines):
            if any(self.grid[x][y] == UNKNOWN for x, y in line.coordinates):
                self._enqueue_line_to_solve(line)

        while self.lines_to_solve:
            line = self._get_next_line_to_solve()
            values = self.solve_for_values(line.clues, [self.grid[x][y] for x, y in line.coordinates])
            if values:
                self._update_grid_from_values(line, values)
            if self.gui:
                self.gui.draw()
        return tuple(tuple(self.grid[x][y] for x in range(self.x_size)) for y in range(self.y_size))

    def __str__(self):
        s = ""
        max_length_vertical = max(len(clues) for clues in self.vertical_clues)
        max_length_horizontal = max(len(clues) for clues in self.horizontal_clues)
        for i in range(max_length_vertical):
            s += f'  ' * max_length_horizontal
            for clues in self.vertical_clues:
                index = i - max_length_vertical + len(clues)
                s += f'|{clues[index] if index >= 0 else " ":>2} '
            s += '|\n'

        dash_line = '-' * (2 * max_length_horizontal + 4 * self.x_size + 1) + '\n'
        for y, clues in enumerate(self.horizontal_clues):
            s += dash_line
            s += f'{" ".join(str(clue) for clue in clues):>{2 * max_length_horizontal - 1}} '
            for x in range(self.x_size):
                s += f'| {"#" if self.grid[x][y] == FILLED else " " if self.grid[x][y] == EMPTY else "?"} '
            s += '|\n'
        s += dash_line
        return s
