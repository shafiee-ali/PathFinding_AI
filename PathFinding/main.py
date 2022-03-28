import enum
import os
import random
import time
from functools import partial

from PyQt5 import QtWidgets
from PyQt5.QtCore import QEventLoop, QTimer
import sys
import enum


class CreateBoard(enum.Enum):
    handy = 1
    auto = 2


class FindPathAlgorithm(enum.Enum):
    BFS = 1
    DFS = 2
    A_Star = 3
    UCS = 4
    Iterative_Deepening = 5


class Colors(enum.Enum):
    Black = '#171717'
    White = '#FFFFFF'
    Red = '#DC143C'
    Green = '#00A572'
    Cyan = "#34ebcf"
    Purple = "#eb38ff"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, height=30, width=20):
        super(MainWindow, self).__init__()
        self.board_height = height
        self.board_width = width
        self.grid_board = [[None for _ in range(height)]for _ in range(width)]
        self.grid_board_colors = [[None for _ in range(height)]for _ in range(width)]
        self.previous_cells = [[None for _ in range(height)]for _ in range(width)]
        self.pen_color = Colors.Black
        self.setFixedWidth(height * 30)
        self.setFixedHeight(width * 30)
        self.create_board_mode = CreateBoard.handy
        self.algorithm = FindPathAlgorithm.BFS
        self.green_btn_position = None
        self.red_btn_position = None
        self.cells_set = set()
        self.cells_queue = list()
        self.find_dst = False
        self.dfs_result = list()
        self.divide_screen()
        self.create_board()
        self.create_bottom_panel()
        self.view()

    def view(self):
        widget = QtWidgets.QWidget()
        widget.setLayout(self.main_vertical_layout)
        self.setCentralWidget(widget)
        self.setLayout(self.main_vertical_layout)
        self.show()

    def divide_screen(self):
        self.main_vertical_layout = QtWidgets.QVBoxLayout()
        self.main_vertical_layout.setSpacing(0)

        self.board_vertical_layout = QtWidgets.QVBoxLayout()
        self.board_vertical_layout.setSpacing(1)
        self.main_vertical_layout.addLayout(self.board_vertical_layout)

        self.panel_horizontal_layout = QtWidgets.QHBoxLayout()
        self.main_vertical_layout.addLayout(self.panel_horizontal_layout)

    def create_board(self):
        for i in range(self.board_width):
            board_horizontal_layout = QtWidgets.QHBoxLayout()
            board_horizontal_layout.setSpacing(1)
            self.board_vertical_layout.addLayout(board_horizontal_layout)
            for j in range(self.board_height):
                self.grid_board[i][j] = QtWidgets.QPushButton()
                if self.is_wall_btn(i, j):
                    self.grid_board[i][j].setStyleSheet(f"background-color: {Colors.Black.value}")
                    self.grid_board_colors[i][j] = Colors.Black
                else:
                    self.grid_board[i][j].setStyleSheet(f"background-color: {Colors.White.value}")
                    self.grid_board[i][j].pressed.connect(partial(self.grid_cells_pressed, i, j))
                    self.grid_board_colors[i][j] = Colors.White
                board_horizontal_layout.addWidget(self.grid_board[i][j])

    def create_bottom_panel(self):
        self.create_board_mode_vlayout = QtWidgets.QVBoxLayout()
        self.panel_horizontal_layout.addLayout(self.create_board_mode_vlayout)
        self.handy_pattern_btn = QtWidgets.QPushButton("Handy pattern")
        self.auto_generate_pattern_btn = QtWidgets.QPushButton("Generate random pattern")
        self.auto_generate_pattern_btn.pressed.connect(self.change_mode_to_auto_generate)
        self.handy_pattern_btn.pressed.connect(self.change_mode_to_handy)
        self.create_board_mode_vlayout.addWidget(self.auto_generate_pattern_btn)
        self.create_board_mode_vlayout.addWidget(self.handy_pattern_btn)

        self.handy_pattern_options = QtWidgets.QHBoxLayout()
        self.panel_horizontal_layout.addLayout(self.handy_pattern_options)
        self.clear_grid_btn = QtWidgets.QPushButton("Clear grid")
        self.colors_combo_box = QtWidgets.QComboBox()
        colors = ['Black', 'White', 'Red', 'Green']
        self.colors_combo_box.addItems(colors)
        self.colors_combo_box.currentIndexChanged.connect(self.change_colors_combo_box)
        self.handy_pattern_options.addWidget(self.clear_grid_btn)
        self.handy_pattern_options.addWidget(self.colors_combo_box)

        self.run_algorithms_box = QtWidgets.QVBoxLayout()
        self.panel_horizontal_layout.addLayout(self.run_algorithms_box)
        self.algorithms_combo_box = QtWidgets.QComboBox()
        algorithms = ['BFS', 'DFS', 'A*', 'UCS', 'ID']
        self.algorithms_combo_box.addItems(algorithms)
        self.algorithms_combo_box.currentIndexChanged.connect(self.change_algorithm)
        self.run_algorithms_box.addWidget(self.algorithms_combo_box)
        self.run_algorithm_btn = QtWidgets.QPushButton("run")
        self.run_algorithms_box.addWidget(self.run_algorithm_btn)
        self.run_algorithm_btn.pressed.connect(self.run_algorithm)

    def change_algorithm(self):
        algo = self.algorithms_combo_box.currentText()
        if algo == 'BFS':
            self.algorithm = FindPathAlgorithm.BFS
        if algo == 'DFS':
            self.algorithm = FindPathAlgorithm.DFS
        if algo == 'A*':
            self.algorithm = FindPathAlgorithm.A_Star
        if algo == 'UCS':
            self.algorithm = FindPathAlgorithm.UCS
        if algo == 'ID':
            self.algorithm = FindPathAlgorithm.Iterative_Deepening

    def add_neighbors_to_queue(self, center_pos):
        cx, cy = center_pos
        points = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        if self.algorithm == FindPathAlgorithm.DFS:
            points = points[::-1]
        for x, y in points:
            xx, yy = cx + x, cy + y
            if (not self.is_wall_btn(xx, yy)) and (xx, yy) not in self.cells_set and (self.grid_board_colors[xx][yy] == Colors.White or self.grid_board_colors[xx][yy] == Colors.Red):
                self.cells_queue.append((xx, yy))
                self.previous_cells[xx][yy] = (cx, cy)

    def bfs(self):
        self.cells_queue = list()
        self.cells_set = set()
        self.cells_set.add(self.green_btn_position)
        self.add_neighbors_to_queue(self.green_btn_position)
        while self.cells_queue:
            x, y = self.cells_queue.pop(0)
            if (x, y) == self.red_btn_position:
                print("end")
                return
            elif self.grid_board_colors[x][y] == Colors.Black:
                continue
            else:
                self.change_btn_color(x, y, Colors.Cyan)
                self.sleep_program(300)
                self.add_neighbors_to_queue((x, y))

    def sleep_program(self, milli_second):
        loop = QEventLoop()
        QTimer.singleShot(milli_second, loop.quit)
        loop.exec_()

    def dfs(self, i, j):
        # if (i, j) == self.red_btn_position:
        #     self.find_dst = True
        #     return
        # if self.is_wall_btn(i, j) or self.grid_board_colors[i][j] == Colors.Black or self.grid_board_colors[i][j] == Colors.Cyan:
        #     return
        # self.change_btn_color(i, j, Colors.Cyan)
        # self.previous_cells[i-1][j] = (i, j)
        # self.dfs(i-1, j)
        # if not self.find_dst:
        #     self.previous_cells[i - 1][j] = (i, j)
        #     self.dfs(i, j+1)
        # if not self.find_dst:
        #     self.previous_cells[i - 1][j] = (i, j)
        #     self.dfs(i+1, j)
        # if not self.find_dst:
        #     self.previous_cells[i - 1][j] = (i, j)
        #     self.dfs(i, j-1)
        self.cells_queue = list()
        self.cells_set = set()
        self.cells_set.add(self.green_btn_position)
        self.add_neighbors_to_queue(self.green_btn_position)
        while self.cells_queue:
            x, y = self.cells_queue.pop()
            if (x, y) == self.red_btn_position:
                print("end")
                return
            elif self.grid_board_colors[x][y] == Colors.Black:
                continue
            else:
                self.change_btn_color(x, y, Colors.Cyan)
                self.cells_set.add((x, y))
                # self.sleep_program(500)
                self.add_neighbors_to_queue((x, y))

    def draw_shortest_path(self):
        i, j = self.red_btn_position
        while self.previous_cells[i][j]:
            self.change_btn_color(i, j, Colors.Purple)
            self.change_btn_color(i, j, Colors.Purple)
            # self.sleep_program(200)
            i, j = self.previous_cells[i][j]

    def emptying_variables(self):
        self.find_dst = False
        self.previous_cells = [[None for _ in range(self.board_height)]for _ in range(self.board_width)]

    def run_algorithm(self):
        self.emptying_variables()
        if self.algorithm == FindPathAlgorithm.BFS:
            print("BFS")
            s = time.time()
            self.bfs()
            # self.draw_shortest_path()
            print(time.time()-s)
        elif self.algorithm == FindPathAlgorithm.DFS:
            s = time.time()
            src_i, src_j = self.green_btn_position
            self.dfs(src_i, src_j)
            # self.sleep_program(2000)
            # for item in self.dfs_result:
            #     i, j = item
            #     self.change_btn_color(i, j, Colors.Red)
            #     # self.sleep_program(300)
            self.draw_shortest_path()
            print(time.time()-s)


    def clear_board(self):
        for i in range(1, self.board_width-1):
            for j in range(1, self.board_height-1):
                self.change_btn_color(i, j, Colors.White)

    def random_fill_board(self):
        self.clear_board()
        density = 0.1

        self.green_btn_position = (int(random.uniform(1, self.board_width-1)), int(random.uniform(1, self.board_height-1)))
        self.red_btn_position = (int(random.uniform(1, self.board_width-1)), int(random.uniform(1, self.board_height-1)))
        for i in range(1, self.board_width - 1):
            for j in range(1, self.board_height - 1):
                x = random.uniform(0, 1)
                if (i, j) == self.green_btn_position:
                    self.change_btn_color(i, j, Colors.Green)
                elif (i, j) == self.red_btn_position:
                    self.change_btn_color(i, j, Colors.Red)
                else:
                    if x < density:
                        self.change_btn_color(i, j, Colors.Black)

    def change_mode_to_auto_generate(self):
        self.create_board_mode = CreateBoard.auto
        self.random_fill_board()

    def change_mode_to_handy(self):
        self.create_board_mode = CreateBoard.handy

    def change_colors_combo_box(self):
        color = self.colors_combo_box.currentText()
        self.pen_color = Colors[color]

    def is_wall_btn(self, i, j):
        return i == 0 or j == 0 or i == self.board_width - 1 or j == self.board_height - 1

    def change_btn_color(self, i, j, color):
        self.grid_board_colors[i][j] = color
        self.grid_board[i][j].setStyleSheet(f"background-color: {color.value}")

    def grid_cells_pressed(self, i, j):
        if self.create_board_mode == CreateBoard.handy:
            self.grid_board[i][j].setStyleSheet(f"background-color: {self.pen_color.value}")
            if self.pen_color == Colors.Green:
                if self.green_btn_position is not None:
                    x, y = self.green_btn_position
                    if self.grid_board_colors[x][y] == Colors.Green:
                        self.change_btn_color(x, y, Colors.White)
                self.green_btn_position = (i, j)

            elif self.pen_color == Colors.Red:
                if self.red_btn_position is not None:
                    x, y = self.red_btn_position
                    if self.grid_board_colors[x][y] == Colors.Red:
                        self.change_btn_color(x, y, Colors.White)
                self.red_btn_position = (i, j)
            self.change_btn_color(i, j, self.pen_color)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec_())






