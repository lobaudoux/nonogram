import argparse
import time

from gui import GUI
from nonogram import Nonogram


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', default=25, type=int)
    parser.add_argument('-m', default=25, type=int)
    parser.add_argument('-d', '--density', default=0.6, type=float)
    args = parser.parse_args()

    nonogram = Nonogram(n=args.n, m=args.m, density=args.density)

    density = (
        (sum(sum(clues) for clues in nonogram.vertical_clues) + sum(sum(clues) for clues in nonogram.horizontal_clues))
        / (2 * nonogram.x_size * nonogram.y_size)
    )
    print(f"Density is {density:.2f}")

    gui = GUI(nonogram, draw_crosses=True)
    nonogram.set_gui(gui)

    start = time.perf_counter()

    nonogram.solve()

    print(f"It took {time.perf_counter() - start:.2f}s to solve")

    gui.draw()
    gui.draw_unknown_cells()

    gui.wait_for_close()


if __name__ == '__main__':
    main()
