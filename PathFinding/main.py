import enum
import os
import random
import time
from functools import partial
from math import sqrt

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QEventLoop, QTimer
import sys
import enum
from queue import PriorityQueue

from PyQt5.QtGui import QFont


class MyPriorityQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.counter = 0

    def put(self, item):
        i = item.i
        j = item.j
        h = item.h
        g = item.g
        f = item.f
        PriorityQueue.put(self, (f, g, h, j, i))
        self.counter += 1

    def get(self, *args, **kwargs):
        f, g, h, j, i = PriorityQueue.get(self, *args, **kwargs)
        return A_Star_Node(i, j, h, g, f)


class DialogMode(enum.Enum):
    WinGame = 1
    FailedPathFinding = 2
    InformingUser = 3


class Mode(enum.Enum):
    Computer = 1
    User = 2


class MoveMode(enum.Enum):
    Animate = 1
    InAnimate = 2

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
    Cyan = "#ccd9ff"
    Purple = "#ac00e6"


class A_Star_Node:
    def __init__(self, i, j, h, g, f):
        self.i = i
        self.j = j
        self.h = h
        self.g = g
        self.f = f


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
        self.mode = Mode.Computer
        self.green_btn_position = None
        self.red_btn_position = None
        self.visited = set()
        self.cells_queue = list()
        self.find_dst = False
        self.enemies_density = 0.1
        self.duration = 10
        self.move_mode = MoveMode.Animate
        self.dfs_result = list()
        self.divide_screen()
        self.create_board()
        self.create_bottom_panel()
        self.view()
        # self.test_dfs()

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

        self.panel_grid_layout = QtWidgets.QGridLayout()
        self.main_vertical_layout.addLayout(self.panel_grid_layout)

    def create_board(self):
        for i in range(self.board_width):
            board_horizontal_layout = QtWidgets.QHBoxLayout()
            board_horizontal_layout.setSpacing(1)
            self.board_vertical_layout.addLayout(board_horizontal_layout)
            for j in range(self.board_height):
                self.grid_board[i][j] = QtWidgets.QPushButton()
                self.grid_board[i][j].setFocusPolicy(QtCore.Qt.NoFocus)
                if self.is_wall_btn(i, j):
                    self.grid_board[i][j].setStyleSheet(f"background-color: {Colors.Black.value}")
                    self.grid_board_colors[i][j] = Colors.Black
                else:
                    self.grid_board[i][j].setStyleSheet(f"background-color: {Colors.White.value}")
                    self.grid_board[i][j].pressed.connect(partial(self.grid_cells_pressed, i, j))
                    self.grid_board_colors[i][j] = Colors.White
                board_horizontal_layout.addWidget(self.grid_board[i][j])

    def create_bottom_panel(self):
        self.board_options_grid_layout = QtWidgets.QGridLayout()
        self.panel_grid_layout.addLayout(self.board_options_grid_layout, 0, 0)
        self.create_board_panel()

        self.modes_grid_layout = QtWidgets.QGridLayout()
        self.panel_grid_layout.addLayout(self.modes_grid_layout, 0, 1)
        self.create_modes_panel()

        self.colors_horizontal_layout = QtWidgets.QHBoxLayout()
        self.panel_grid_layout.addLayout(self.colors_horizontal_layout, 1, 0)
        self.colors_panel()

        self.run_panel_vertical_layout = QtWidgets.QVBoxLayout()
        self.panel_grid_layout.addLayout(self.run_panel_vertical_layout, 1, 1)
        self.run_panel()

    def run_panel(self):
        self.run_information = QtWidgets.QHBoxLayout()

        self.open_nodes_title_lbl = QtWidgets.QLabel("open nodes:")
        self.run_information.addWidget(self.open_nodes_title_lbl)

        self.open_nodes_lbl = QtWidgets.QLabel("0")
        self.run_information.addWidget(self.open_nodes_lbl)

        self.run_time_title_lbl = QtWidgets.QLabel("time:")
        self.run_information.addWidget(self.run_time_title_lbl)

        self.run_time_lbl = QtWidgets.QLabel("0")
        self.run_information.addWidget(self.run_time_lbl)

        self.run_panel_vertical_layout.addLayout(self.run_information)

        self.run_algorithm_btn = QtWidgets.QPushButton("run")
        self.run_algorithm_btn.pressed.connect(self.run_algorithm)
        self.run_panel_vertical_layout.addWidget(self.run_algorithm_btn)


    def create_board_panel(self):
        self.handy_pattern_btn = QtWidgets.QPushButton("Handy pattern")
        self.handy_pattern_btn.pressed.connect(self.change_mode_to_handy)
        self.board_options_grid_layout.addWidget(self.handy_pattern_btn, 0, 0)

        self.auto_generate_pattern_btn = QtWidgets.QPushButton("Generate random pattern")
        self.auto_generate_pattern_btn.pressed.connect(self.change_mode_to_auto_generate)
        self.board_options_grid_layout.addWidget(self.auto_generate_pattern_btn, 0, 1)

        self.clear_grid_btn = QtWidgets.QPushButton("Clear grid")
        self.clear_grid_btn.pressed.connect(self.clear_board)
        self.board_options_grid_layout.addWidget(self.clear_grid_btn, 1, 0)

        self.undo_btn = QtWidgets.QPushButton("Undo")
        self.undo_btn.pressed.connect(self.undo)
        self.board_options_grid_layout.addWidget(self.undo_btn, 1, 1)

    def colors_panel(self):
        self.animate_or_inanimate_lbl = QtWidgets.QLabel("animation: ")
        self.colors_horizontal_layout.addWidget(self.animate_or_inanimate_lbl)
        self.animate_or_inanimate_lbl.setFixedHeight(30)
        self.animate_or_inanimate_lbl.setFixedWidth(65)

        self.animate_or_inanimate_move_combo_box = QtWidgets.QComboBox()
        modes = ['animate', 'inanimate']
        self.animate_or_inanimate_move_combo_box.addItems(modes)
        self.animate_or_inanimate_move_combo_box.currentIndexChanged.connect(self.change_move_mode)
        self.colors_horizontal_layout.addWidget(self.animate_or_inanimate_move_combo_box)


        self.duration_lbl = QtWidgets.QLabel("duration: ")
        self.duration_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.duration_lbl.setFixedHeight(30)
        self.duration_lbl.setFixedWidth(65)
        self.colors_horizontal_layout.addWidget(self.duration_lbl)

        self.duration_combo_box = QtWidgets.QComboBox()
        durations = ['10 ms', '30 ms', '50 ms', '70 ms', '100 ms', '200 ms', '300 ms', '500 ms', '1000 ms']
        self.duration_combo_box.addItems(durations)
        self.duration_combo_box.currentIndexChanged.connect(self.change_duration)
        self.colors_horizontal_layout.addWidget(self.duration_combo_box)

    def create_modes_panel(self):

        self.solver_lbl = QtWidgets.QLabel("solver: ")
        self.modes_grid_layout.addWidget(self.solver_lbl, 0, 0)
        self.solver_lbl.setFixedHeight(30)
        self.solver_lbl.setFixedWidth(50)
        self.solver_lbl.setAlignment(QtCore.Qt.AlignCenter)

        self.main_mode_combo_box = QtWidgets.QComboBox()
        modes = ['Computer', 'User']
        self.main_mode_combo_box.addItems(modes)
        self.main_mode_combo_box.currentIndexChanged.connect(self.change_main_mode)
        self.modes_grid_layout.addWidget(self.main_mode_combo_box, 0, 1)

        self.algorithm_lbl = QtWidgets.QLabel("algorithm: ")
        self.modes_grid_layout.addWidget(self.algorithm_lbl, 0, 2)
        self.algorithm_lbl.setFixedHeight(30)
        self.algorithm_lbl.setFixedWidth(70)
        self.algorithm_lbl.setAlignment(QtCore.Qt.AlignCenter)

        self.algorithms_combo_box = QtWidgets.QComboBox()
        algorithms = ['BFS', 'DFS', 'A*', 'UCS', 'ID']
        self.algorithms_combo_box.addItems(algorithms)
        self.algorithms_combo_box.currentIndexChanged.connect(self.change_algorithm)
        self.modes_grid_layout.addWidget(self.algorithms_combo_box, 0, 3)


        self.density_lbl = QtWidgets.QLabel("density: ")
        self.modes_grid_layout.addWidget(self.density_lbl, 1, 0)
        self.density_lbl.setFixedHeight(30)
        self.density_lbl.setFixedWidth(60)
        self.density_lbl.setAlignment(QtCore.Qt.AlignCenter)

        self.enemies_density_combo_box = QtWidgets.QComboBox()
        densities = ['0.1', '0.2', '0.3', '0.4', '0.5']
        self.enemies_density_combo_box.addItems(densities)
        self.enemies_density_combo_box.currentIndexChanged.connect(self.change_density)
        self.modes_grid_layout.addWidget(self.enemies_density_combo_box, 1, 1)


        self.color_lbl = QtWidgets.QLabel("color: ")
        self.modes_grid_layout.addWidget(self.color_lbl, 1, 2)
        self.color_lbl.setFixedHeight(30)
        self.color_lbl.setFixedWidth(60)
        self.color_lbl.setAlignment(QtCore.Qt.AlignCenter)

        self.colors_combo_box = QtWidgets.QComboBox()
        colors = ['Black', 'White', 'Red', 'Green']
        self.colors_combo_box.addItems(colors)
        self.colors_combo_box.currentIndexChanged.connect(self.change_colors_combo_box)
        self.modes_grid_layout.addWidget(self.colors_combo_box, 1, 3)

    def change_duration(self):
        duration = self.duration_combo_box.currentText()
        duration = int(duration.split()[0])
        self.duration = duration


    def change_move_mode(self):
        mode = self.animate_or_inanimate_move_combo_box.currentText()
        if mode == 'animate':
            self.move_mode = MoveMode.Animate
        if mode == 'inanimate':
            self.move_mode = MoveMode.InAnimate


    def change_density(self):
        density = self.enemies_density_combo_box.currentText()
        self.enemies_density = float(density)

    def change_main_mode(self):
        mode = self.main_mode_combo_box.currentText()
        if mode == 'Computer':
            self.mode = Mode.Computer
            self.undo_btn.setEnabled(True)
            self.algorithms_combo_box.setEnabled(True)
            self.run_algorithm_btn.setEnabled(True)

        elif mode == 'User':
            self.mode = Mode.User
            self.undo_btn.setEnabled(False)
            self.algorithms_combo_box.setEnabled(False)
            self.run_algorithm_btn.setEnabled(False)

    def is_white(self, i, j):
        return (not self.is_wall_btn(i, j)) and self.grid_board_colors[i][j] != Colors.Black

    def show_dialog(self, message, type):
        if type == DialogMode.WinGame:
            dialog = QtWidgets.QDialog()
            lbl = QtWidgets.QLabel(message, dialog)
            lbl.move(10, 30)
            lbl.setStyleSheet("color: green")
            lbl.setFont(QFont('Calibri', 13))
            dialog.setWindowTitle("win game")
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()
        elif type == DialogMode.InformingUser:
            dialog = QtWidgets.QDialog()
            lbl = QtWidgets.QLabel(message, dialog)
            lbl.move(10, 30)
            lbl.setStyleSheet("color: black")
            lbl.setFont(QFont('Calibri', 13))
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()
        elif type == DialogMode.FailedPathFinding:
            dialog = QtWidgets.QDialog()
            lbl = QtWidgets.QLabel(message, dialog)
            lbl.move(10, 30)
            lbl.setStyleSheet("color: Red")
            lbl.setFont(QFont('Calibri', 13))
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()

    def move_green_btn(self, i, j):
        x, y = self.green_btn_position
        if (i, j) == self.red_btn_position:
            self.show_dialog("You win game", DialogMode.WinGame)
            self.random_fill_board()
            return
        self.change_btn_color(x, y, Colors.White)
        self.change_btn_color(i, j, Colors.Green)
        self.green_btn_position = (i, j)


    def move_up(self):
        i, j = self.green_btn_position
        if self.is_white(i-1, j):
            self.move_green_btn(i-1, j)

    def move_down(self):
        i, j = self.green_btn_position
        if self.is_white(i+1, j):
            self.move_green_btn(i+1, j)

    def move_right(self):
        i, j = self.green_btn_position
        if self.is_white(i, j+1):
            self.move_green_btn(i, j+1)

    def move_left(self):
        i, j = self.green_btn_position
        if self.is_white(i, j-1):
            self.move_green_btn(i, j-1)

    def keyPressEvent(self, event):
        if self.mode == Mode.User:
            key = event.key()
            if key == QtCore.Qt.Key.Key_W:
                self.move_up()
            if key == QtCore.Qt.Key.Key_S:
                self.move_down()
            if key == QtCore.Qt.Key.Key_D:
                self.move_right()
            if key == QtCore.Qt.Key.Key_A:
                self.move_left()
        # else:


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

    def add_neighbors(self, center_pos):
        if self.algorithm == FindPathAlgorithm.BFS:
            cx, cy = center_pos
            points = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            for x, y in points:
                xx, yy = cx + x, cy + y
                if (xx, yy) not in self.visited and (self.grid_board_colors[xx][yy] == Colors.White or self.grid_board_colors[xx][yy] == Colors.Red):
                    self.cells_queue.append((xx, yy))
                    if self.algorithm == FindPathAlgorithm.BFS:
                        self.visited.add((xx, yy))
                    self.previous_cells[xx][yy] = (cx, cy)

        if self.algorithm == FindPathAlgorithm.DFS:
            cx, cy = center_pos
            points = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            points = points[::-1]
            for x, y in points:
                xx, yy = cx + x, cy + y
                if (xx, yy) not in self.all_stack_set and (self.grid_board_colors[xx][yy] == Colors.White or self.grid_board_colors[xx][yy] == Colors.Red):
                    self.cells_stack.append((xx, yy))
                    self.previous_cells[xx][yy] = (cx, cy)

            self.cells_stack = list(dict.fromkeys(self.cells_stack[::-1]))
            self.cells_stack = self.cells_stack[::-1]

        if self.algorithm == FindPathAlgorithm.A_Star:
            cx, cy = center_pos.i, center_pos.j
            points = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            for x, y in points:
                xx, yy = cx + x, cy + y
                if (xx, yy) not in self.visited and (self.grid_board_colors[xx][yy] == Colors.White or self.grid_board_colors[xx][yy] == Colors.Red):
                    h = self.h(xx, yy)
                    g = center_pos.g + 1
                    f = h + g
                    self.min_heap.put(A_Star_Node(xx, yy, h, g, f))
                    self.visited.add((xx, yy))
                    self.previous_cells[xx][yy] = (cx, cy)

    def bfs(self):
        self.cells_queue = list()
        self.visited = set()
        self.visited.add(self.green_btn_position)
        self.add_neighbors(self.green_btn_position)
        while self.cells_queue:
            x, y = self.cells_queue.pop(0)
            if (x, y) == self.red_btn_position:
                return
            else:
                self.change_btn_color(x, y, Colors.Cyan)
                if self.move_mode == MoveMode.Animate:
                    self.sleep_program(self.duration)
                self.add_neighbors((x, y))

    def sleep_program(self, milli_second):
        loop = QEventLoop()
        QTimer.singleShot(milli_second, loop.quit)
        loop.exec_()

    def dfs(self):
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
        self.cells_stack = list()
        self.all_stack_set = set()
        self.visited = set()
        self.visited.add(self.green_btn_position)
        self.all_stack_set.add(self.green_btn_position)
        self.add_neighbors(self.green_btn_position)
        while self.cells_stack:
            x, y = self.cells_stack.pop()
            if (x, y) == self.red_btn_position:
                return
            else:
                self.change_btn_color(x, y, Colors.Cyan)
                self.visited.add((x, y))
                self.all_stack_set.add((x, y))
                if self.move_mode == MoveMode.Animate:
                    self.sleep_program(self.duration)
                self.add_neighbors((x, y))

    def euclidean_distance(self, i, j):
        return pow(i-self.red_btn_position[0], 2) + pow(j-self.red_btn_position[1], 2)

    def h(self, i, j):
        return self.euclidean_distance(i, j)

    def a_star(self):
        self.visited = set()
        self.min_heap = MyPriorityQueue()
        i, j = self.green_btn_position
        h = self.h(i, j)
        g = 0
        f = h + g
        self.add_neighbors(A_Star_Node(i, j, h, g, f))
        while not self.min_heap.empty():
            best_node = self.min_heap.get()
            i, j = best_node.i, best_node.j
            if (i, j) == self.red_btn_position:
                return
            self.change_btn_color(i, j, Colors.Cyan)
            if self.move_mode == MoveMode.Animate:
                self.sleep_program(self.duration)
            self.add_neighbors(best_node)

    def increase_path_counter(self):
        self.counter += 1

    def add_number_to_btn(self, i, j):
        self.increase_path_counter()
        self.grid_board[i][j].setText(str(self.counter))
        self.grid_board[i][j].setStyleSheet(self.grid_board[i][j].styleSheet() + "; color: white;")

    def recursive_draw_path(self, i, j):
        x,  y = self.previous_cells[i][j]
        if self.previous_cells[x][y] is None:
            return
        i, j = self.previous_cells[i][j]
        self.recursive_draw_path(i, j)
        self.change_btn_color(i, j, Colors.Purple)
        if self.move_mode == MoveMode.Animate:
            self.sleep_program(self.duration)
        self.add_number_to_btn(i, j)
        # self.sleep_program(300)

    def shortest_path(self):
        i, j = self.red_btn_position
        self.recursive_draw_path(i, j)
        # while self.previous_cells[i][j]:
        #     self.change_btn_color(i, j, Colors.Purple)
        #     # self.sleep_program(200)
        #     i, j = self.previous_cells[i][j]

    def emptying_variables(self):
        self.find_dst = False
        self.previous_cells = [[None for _ in range(self.board_height)]for _ in range(self.board_width)]
        self.counter = 0

    def run_algorithm(self):
        self.emptying_variables()
        self.undo()
        if self.algorithm == FindPathAlgorithm.BFS:
            s = time.time()
            self.bfs()
            self.shortest_path()
            print(time.time()-s)
        elif self.algorithm == FindPathAlgorithm.DFS:
            s = time.time()
            self.dfs()
            self.shortest_path()
            # self.sleep_program(2000)
            # for item in self.dfs_result:
            #     i, j = item
            #     self.change_btn_color(i, j, Colors.Red)
            #     # self.sleep_program(300)
            # self.shortest_path()
            print(time.time()-s)
        elif self.algorithm == FindPathAlgorithm.A_Star:
            self.a_star()
            self.shortest_path()

    def clear_board(self):
        for i in range(1, self.board_width-1):
            for j in range(1, self.board_height-1):
                self.change_btn_color(i, j, Colors.White)
                self.grid_board[i][j].setText("")

    def undo(self):
        for i in range(1, self.board_width - 1):
            for j in range(1, self.board_height - 1):
                if self.grid_board_colors[i][j] != Colors.White and self.grid_board_colors[i][j] != Colors.Black and self.grid_board_colors[i][j] != Colors.Green and self.grid_board_colors[i][j] != Colors.Red:
                    self.change_btn_color(i, j, Colors.White)
                self.grid_board[i][j].setText("")

    def random_fill_board(self):
        self.clear_board()
        density = self.enemies_density

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

    def test_dfs(self):
        all_time = 0
        i = 100
        self.algorithm = FindPathAlgorithm.DFS
        while i:
            self.random_fill_board()
            start = time.time()
            self.run_algorithm()
            all_time += (time.time()-start)
            i -= 1
            # self.sleep_program(3000)
        print(f"all time is:{all_time}")

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
        # if

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec_())
