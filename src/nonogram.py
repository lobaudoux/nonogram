import bisect
import itertools
import random
import sys
from contextlib import suppress

from constants import *


class Line:
    def __init__(self, coordinates, clues, orientation):
        self.coordinates = coordinates
        self.clues = clues
        self.clues_length = len(clues)
        self.clues_sum = sum(clues)
        self.unknown_count = len(coordinates)
        self.orientation = orientation
        self.score = 0.0
        self.compute_score()

    def compute_score(self):
        self.score = (
            0.75 * self.clues_sum
            - 1.5 * self.clues_length
            - self.unknown_count
        )

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
        self.size_x = len(self.vertical_clues)
        self.size_y = len(self.horizontal_clues)
        self.grid = [[UNKNOWN for _ in range(self.size_y)] for _ in range(self.size_x)]
        self.lines_to_solve = []
        self.lines_to_solve_set = set()
        self.cache = {}
        self.horizontal_lines = []
        self.vertical_lines = []
        for x in range(self.size_x):
            line = Line(tuple((x, y) for y in range(self.size_y)), self.vertical_clues[x], 'vertical')
            self.add_line_to_solve(line)
            self.vertical_lines.append(line)
        for y in range(self.size_y):
            line = Line(tuple((x, y) for x in range(self.size_x)), self.horizontal_clues[y], 'horizontal')
            self.add_line_to_solve(line)
            self.horizontal_lines.append(line)
        self.gui = None

    @staticmethod
    def generate_random_clues(n, m, density):
        filled_indices = set(random.sample(range(n * m), round(density * n * m)))
        grid = [[EMPTY if j * n + i not in filled_indices else FILLED for i in range(n)] for j in range(m)]
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

    def add_line_to_solve(self, line):
        if line not in self.lines_to_solve_set:
            self.lines_to_solve.append(line)
            self.lines_to_solve_set.add(line)

    def get_next_line_to_solve(self):
        self.lines_to_solve.sort(key=lambda l: l.score)
        line = self.lines_to_solve.pop()
        self.lines_to_solve_set.remove(line)
        return line

    @staticmethod
    def get_unsolved_part(clues, values):
        if UNKNOWN not in values:
            return clues, values, (len(clues), 0), (len(values), 0)

        if sum(1 for value in values if value == FILLED) == sum(clues):
            return clues, [EMPTY if value == UNKNOWN else value for value in values], (len(clues), 0), (len(values), 0)

        values_copy = values[:]

        values_start = next(i for i in range(len(values)) if values[i] != EMPTY)
        clues_start = 0
        while (
            clues_start < len(clues)
            and all(value == FILLED for value in values_copy[values_start:values_start + clues[clues_start]])
        ):
            with suppress(IndexError):
                assert values_copy[values_start + clues[clues_start]] != FILLED
                values_copy[values_start + clues[clues_start]] = EMPTY
            values_start += clues[clues_start] + 1
            clues_start += 1
            while values_copy[values_start] == EMPTY:
                values_start += 1

        values_end = len(values_copy)
        clues_end = len(clues)
        while (
            clues_end >= 0
            and all(value == FILLED for value in values_copy[values_end - clues[clues_end - 1]:values_end])
        ):
            with suppress(IndexError):
                values_copy[values_end - clues[clues_end - 1] - 1] = EMPTY
            values_end -= clues[clues_end - 1] + 1
            clues_end -= 1

        return clues, values_copy, (clues_start, clues_end), (values_start, values_end)

    @staticmethod
    def get_placements(clues, values):
        already_filled_cells = [i for i, value in enumerate(values) if value == FILLED]
        possible_placements = []
        clues_start = [0]
        clue_index = 0
        cur_placement = [EMPTY] * len(values)

        values_length = len(values)
        clues_length = len(clues)
        clues_start_limits = [values_length - sum(clues[i:]) - clues_length + i + 1 for i in range(clues_length + 1)]

        while clues_start[0] <= clues_start_limits[0]:
            clue_start = clues_start[clue_index]
            clue_end = clue_start + clues[clue_index]
            if (
                clue_end <= values_length
                and EMPTY not in values[clue_start:clue_end]
                and (
                    clue_end == values_length
                    or values[clue_end] in {UNKNOWN, EMPTY}
                )
            ):
                cur_placement[clue_start:clue_end] = [FILLED] * clues[clue_index]
                if clue_index < clues_length - 1:
                    clues_start.append(clue_end + 1)
                    clue_index += 1
                else:
                    if all(cur_placement[i] == FILLED for i in already_filled_cells):
                        possible_placements.append(cur_placement[:])
                    cur_placement[clue_start:clue_end] = [EMPTY] * clues[clue_index]
                    clues_start[clue_index] += 1
            else:
                if clue_start > clues_start_limits[clue_index]:
                    clue_index -= 1
                    cur_placement[clues_start[clue_index]:clues_start[clue_index] + clues[clue_index]] = [EMPTY] * clues[clue_index]
                    clues_start.pop()
                clues_start[clue_index] += 1
        return possible_placements

    def solve_for_values(self, clues, values):
        if not values:
            return values

        values = tuple(values)
        clues = tuple(clues)
        if (clues, values) in self.cache:
            return self.cache[(clues, values)]

        # Find all possible placements
        possible_placements = self.get_placements(clues, values)

        # Find values common to all placements
        if possible_placements:
            new_values = []
            for i in range(len(values)):
                new_value = possible_placements[0][i]
                if all(placement[i] == new_value for placement in possible_placements):
                    new_values.append(new_value)
                else:
                    new_values.append(UNKNOWN)

            self.cache[(clues, values)] = new_values[:]
            return new_values
        else:
            raise AssertionError

    @staticmethod
    def optimized_solve_for_values(clues, values):
        if not values:
            return values

        # Solve values based on first filled cells
        for i, value in enumerate(values[:clues[0] + 1]):
            if value == FILLED:
                if i == clues[0]:
                    values[0] = EMPTY
                else:
                    for j in range(clues[0] - i):
                        values[i + j] = FILLED
                    if i == 0:
                        with suppress(IndexError):
                            values[clues[0]] = EMPTY
                break

        # Solve values based on last filled cells
        for i, value in enumerate(reversed(values[-clues[-1] - 1:])):
            if value == FILLED:
                if i == clues[-1]:
                    values[-1] = EMPTY
                else:
                    for j in range(clues[-1] - i):
                        values[-i - j - 1] = FILLED
                    if i == 0:
                        with suppress(IndexError):
                            values[-clues[-1] - 1] = EMPTY
                break

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
                        with suppress(ValueError):
                            clue_range.remove(i)
                elif not first_match_found:
                    clues_search_start_i += 1

        # Filter based on ranges start
        for (clue_range, clue), (other_clues_range, other_clue) in zip(
            zip(clues_ranges[:-1], clues[:-1]),
            zip(clues_ranges[1:], clues[1:]),
        ):
            other_clues_range[:] = other_clues_range[bisect.bisect_right(other_clues_range, clue_range[0] + clue):]
            clue_range[:] = clue_range[:bisect.bisect_left(clue_range, other_clues_range[-1] - clue)]

        # Filter based on filled cells
        for clue_range, clue in zip(clues_ranges, clues):
            values_to_remove = []
            for clue_start_i in clue_range:
                if (
                    (clue_start_i > 0 and values[clue_start_i - 1] == FILLED)
                    or (clue_start_i + clue < len(values) and values[clue_start_i + clue] == FILLED)
                ):
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
            new_values = [EMPTY if value == UNKNOWN else value for value in new_values]

        return new_values

    def is_unsolved(self, line):
        return any(self.grid[x][y] == UNKNOWN for x, y in line.coordinates)

    def update_grid_from_values(self, line, values):
        for i, (x, y) in enumerate(line.coordinates):
            if values[i] != UNKNOWN and self.grid[x][y] != values[i]:
                line.unknown_count -= 1
                new_line_to_solve = self.horizontal_lines[i] if line.orientation == 'vertical' else self.vertical_lines[i]
                new_line_to_solve.unknown_count -= 1
                new_line_to_solve.compute_score()
                if self.is_unsolved(new_line_to_solve):
                    self.add_line_to_solve(new_line_to_solve)
                self.grid[x][y] = values[i]
        line.compute_score()
        if self.gui:
            self.gui.draw()

    def solve(self):
        for solve_function in (self.optimized_solve_for_values, self.solve_for_values):
            while self.lines_to_solve:
                line = self.get_next_line_to_solve()

                clues = line.clues
                values = [self.grid[x][y] for x, y in line.coordinates]

                _clues, _values, (clues_start, clues_end), (values_start, values_end) = Nonogram.get_unsolved_part(clues, values)
                new_values = (
                    *_values[:values_start],
                    *solve_function(_clues[clues_start:clues_end], _values[values_start:values_end]),
                    *_values[values_end:],
                )
                if new_values != values:
                    self.update_grid_from_values(line, new_values)

            for line in itertools.chain(self.horizontal_lines, self.vertical_lines):
                if self.is_unsolved(line):
                    self.add_line_to_solve(line)

        if self.lines_to_solve:
            line_to_solve_sorted_by_number_of_placements = sorted(
                self.lines_to_solve,
                key=lambda l: len(self.get_placements(l.clues, [self.grid[x][y] for x, y in l.coordinates]))
            )

            # Take a guess on the line that have the fewest number of placements possible
            line_to_solve = line_to_solve_sorted_by_number_of_placements[0]
            self.lines_to_solve.remove(line_to_solve)
            self.lines_to_solve_set.remove(line_to_solve)

            _clues, _values, (clues_start, clues_end), (values_start, values_end) = Nonogram.get_unsolved_part(
                line_to_solve.clues,
                [self.grid[x][y] for x, y in line_to_solve.coordinates]
            )
            for placement in self.get_placements(_clues[clues_start:clues_end], _values[values_start:values_end]):
                grid_copy = [row[:] for row in self.grid]
                new_values = (
                    *_values[:values_start],
                    *placement,
                    *_values[values_end:],
                )
                self.update_grid_from_values(line_to_solve, new_values)
                try:
                    self.solve()
                    if any(self.is_unsolved(line) for line in itertools.chain(self.horizontal_lines, self.vertical_lines)):
                        raise AssertionError
                    else:
                        break
                except (AssertionError, IndexError):
                    self.grid = grid_copy
                    for line in itertools.chain(self.horizontal_lines, self.vertical_lines):
                        line.unknown_count = [self.grid[x][y] for x, y in line.coordinates].count(UNKNOWN)
                        line.compute_score()

        return tuple(tuple(self.grid[x][y] for x in range(self.size_x)) for y in range(self.size_y))

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

        dash_line = '-' * (2 * max_length_horizontal + 4 * self.size_x + 1) + '\n'
        for y, clues in enumerate(self.horizontal_clues):
            s += dash_line
            s += f'{" ".join(str(clue) for clue in clues):>{2 * max_length_horizontal - 1}} '
            for x in range(self.size_x):
                s += f'| {"#" if self.grid[x][y] == FILLED else " " if self.grid[x][y] == EMPTY else "?"} '
            s += '|\n'
        s += dash_line
        return s
