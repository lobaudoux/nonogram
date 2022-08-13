import time

from gui import GUI
from nonogram import Nonogram


def main():
    nonogram = Nonogram(n=30, m=30, density=0.65)

    gui = GUI(nonogram, draw_crosses=True)
    nonogram.set_gui(gui)

    gui.wait_for_spacebar()

    start = time.perf_counter()
    nonogram.solve()
    print(f"It took {time.perf_counter() - start:.2f}s to solve")

    gui.draw_unknown_cells()

    gui.wait_for_close()


if __name__ == '__main__':
    main()
