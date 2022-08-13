import os

import pygame

from constants import *

BACKGROUND_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
RED_COLOR = (240, 0, 0)


class GUI:
    def __init__(self, nonogram, draw_crosses=False):
        self.nonogram = nonogram
        self.draw_crosses = draw_crosses

        pygame.init()
        os.environ['SDL_VIDEO_CENTERED'] = '1'

        self.max_length_vertical_clues = max(len(clues) for clues in nonogram.vertical_clues)
        self.max_length_horizontal_clues = max(len(clues) for clues in nonogram.horizontal_clues)

        self.size_x = len(nonogram.vertical_clues)
        self.size_y = len(nonogram.horizontal_clues)

        size_cell = 64
        while (self.size_y + self.max_length_vertical_clues) * size_cell > 1000:
            size_cell -= 4
        self.size_cell_pixel = size_cell

        self.line_width_pixel = max(self.size_cell_pixel // 16, 1)
        self.bold_line_width_pixel = self.line_width_pixel * 2

        self.text_font = pygame.font.Font('freesansbold.ttf', int(0.7 * self.size_cell_pixel))

        self.board_origin_x_pixel = self.max_length_horizontal_clues * self.size_cell_pixel
        self.board_origin_y_pixel = self.max_length_vertical_clues * self.size_cell_pixel

        self.res_x = (self.max_length_horizontal_clues + self.size_x) * self.size_cell_pixel
        self.res_y = (self.max_length_vertical_clues + self.size_y) * self.size_cell_pixel

        self.display = pygame.display.set_mode((self.res_x, self.res_y))
        self.display.fill(BACKGROUND_COLOR)
        self.draw_clues()

        pygame.display.set_caption("Nonogram")

        cross_sprite = pygame.image.load("../res/red_cross.png")
        self.cross_sprite = pygame.transform.scale(cross_sprite, (round(0.8 * self.size_cell_pixel), round(0.8 * self.size_cell_pixel)))

    def draw_clues(self):
        # Draw the vertical clues
        for i, clues in enumerate(self.nonogram.vertical_clues):
            y_shift = self.max_length_vertical_clues - len(clues)
            for j, clue in enumerate(clues):
                text_surface = self.text_font.render(str(clue), True, BLACK_COLOR)
                text_size_x, text_size_y = text_surface.get_size()
                self.display.blit(
                    text_surface,
                    (self.board_origin_x_pixel + i * self.size_cell_pixel - text_size_x / 2 + self.size_cell_pixel / 2,
                     (y_shift + j) * self.size_cell_pixel - text_size_y / 2 + self.size_cell_pixel / 2)
                )

        # Draw the horizontal clues
        for i, clues in enumerate(self.nonogram.horizontal_clues):
            x_shift = self.max_length_horizontal_clues - len(clues)
            for j, clue in enumerate(clues):
                text_surface = self.text_font.render(str(clue), True, BLACK_COLOR)
                text_size_x, text_size_y = text_surface.get_size()
                self.display.blit(
                    text_surface,
                    ((x_shift + j) * self.size_cell_pixel - text_size_x / 2 + self.size_cell_pixel / 2,
                     self.board_origin_y_pixel + i * self.size_cell_pixel - text_size_y / 2 + self.size_cell_pixel / 2)
                )

    def draw(self):
        # Draw the board
        for x in range(self.size_x):
            for y in range(self.size_y):
                if self.draw_crosses and self.nonogram.grid[x][y] == EMPTY:
                    rect = self.cross_sprite.get_rect()
                    rect.center = self.board_origin_x_pixel + (x + .5) * self.size_cell_pixel, self.board_origin_y_pixel + (y + .5) * self.size_cell_pixel
                    self.display.blit(self.cross_sprite, rect)
                else:
                    pygame.draw.rect(
                        self.display,
                        BLACK_COLOR if self.nonogram.grid[x][y] == FILLED else BACKGROUND_COLOR,
                        (
                            self.board_origin_x_pixel + x * self.size_cell_pixel,
                            self.board_origin_y_pixel + y * self.size_cell_pixel,
                            self.size_cell_pixel,
                            self.size_cell_pixel,
                        )
                    )

        # Draw bold contour lines
        bold_lines = [
            ((self.board_origin_x_pixel, 0), (self.board_origin_x_pixel, self.res_y)),
            ((0, self.board_origin_y_pixel), (self.res_x, self.board_origin_y_pixel)),
        ]
        for line_start, line_end in bold_lines:
            pygame.draw.line(self.display,
                             BLACK_COLOR,
                             line_start,
                             line_end,
                             self.bold_line_width_pixel)

        # Draw vertical lines
        for i in range(1, self.size_x):
            pygame.draw.line(self.display,
                             BLACK_COLOR,
                             (self.board_origin_x_pixel + i * self.size_cell_pixel, 0),
                             (self.board_origin_x_pixel + i * self.size_cell_pixel, self.res_y),
                             self.line_width_pixel)

        # Draw horizontal lines
        for i in range(1, self.size_y):
            pygame.draw.line(self.display,
                             BLACK_COLOR,
                             (0, self.board_origin_y_pixel + i * self.size_cell_pixel),
                             (self.res_x, self.board_origin_y_pixel + i * self.size_cell_pixel),
                             self.line_width_pixel)

        pygame.display.update()

    def draw_unknown_cells(self):
        for x in range(self.size_x):
            for y in range(self.size_y):
                if self.nonogram.grid[x][y] == UNKNOWN:
                    text_surface = self.text_font.render('?', True, BLACK_COLOR)
                    text_size_x, text_size_y = text_surface.get_size()
                    self.display.blit(
                        text_surface,
                        (self.board_origin_x_pixel + x * self.size_cell_pixel - text_size_x / 2 + self.size_cell_pixel / 2,
                         self.board_origin_y_pixel + y * self.size_cell_pixel - text_size_y / 2 + self.size_cell_pixel / 2)
                    )
        pygame.display.update()

    def wait_for_spacebar(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit(0)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return

    def wait_for_close(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit(0)
