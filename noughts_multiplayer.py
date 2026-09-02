import curses


class Square:
    EMPTY = 0
    PLAYER_O = 1
    PLAYER_X = 2
    TOKENS = ' ', '○', '⨉'


    def __init__(self, player = EMPTY):
        self.player = player


    def get_token(self, isSelected = False):
        token = self.TOKENS[self.player]
        color = curses.color_pair(self.player) | (
            isSelected and curses.A_UNDERLINE)

        return token, color


class MultiplayerNoughts:
    DESIGN = (
        ' 0 │ 1 │ 2 ',
        '───┼───┼───',
        ' 3 │ 4 │ 5 ',
        '───┼───┼───',
        ' 6 │ 7 │ 8 ',
    )

    SLOT_POSITIONS = tuple(
        (row, col)
        for row, line in enumerate(DESIGN)
        for col, char in enumerate(line)
        if char.isdigit()
    )

    INFO_ROW = len(DESIGN) + 1

    WINNING_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6),             # diagonals
    )

    COLS = 3
    ROWS = 3
    SIZE = ROWS * COLS
    LAST_COL = COLS - 1
    LAST_ROW = (ROWS - 1) * COLS


    def __init__(self):
        self.selected_index = 0
        self.current_player = Square.PLAYER_O
        self.clear_board()

        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)  # player O
        curses.init_pair(2, curses.COLOR_RED,  -1)  # player X


    def clear_board(self):
        self.squares = [Square() for _ in range(self.SIZE)]
        self.is_game_over = False
        self.winner = Square.EMPTY


    def handle_keypress(self, key_code: int):
        if key_code == ord('q') or key_code == 27:  # Esc
            self.is_playing = False
        elif key_code == curses.KEY_LEFT:
            self.move_left()
        elif key_code == curses.KEY_RIGHT:
            self.move_right()
        elif key_code == curses.KEY_UP:
            self.move_up()
        elif key_code == curses.KEY_DOWN:
            self.move_down()
        elif key_code == ord(' ') or key_code == ord('\n'):
            self.make_move(self.selected_index)


    def move_left(self):
        if self.selected_index % self.COLS == 0:
            self.selected_index += self.LAST_COL
        else:
            self.selected_index -= 1


    def move_right(self):
        if self.selected_index % self.COLS == self.LAST_COL:
            self.selected_index -= self.LAST_COL
        else:
            self.selected_index += 1


    def move_up(self):
        if self.selected_index < self.COLS:
            self.selected_index += self.LAST_ROW
        else:
            self.selected_index -= self.COLS


    def move_down(self):
        if self.selected_index >= self.LAST_ROW:
            self.selected_index -= self.LAST_ROW
        else:
            self.selected_index += self.COLS


    def make_move(self, selected_index: int):
        if self.is_game_over:
            return

        selected_square = self.squares[selected_index]

        if selected_square.player != Square.EMPTY:  # already occupied
            return

        selected_square.player = self.current_player
        self.current_player = (self.current_player % 2) + 1
        self.check_game_state()


    def check_game_state(self):
        # Check for win
        for i, j, k in self.WINNING_LINES:
            p = self.squares[i].player
            if p != Square.EMPTY and p == self.squares[j].player == self.squares[k].player:
                self.winner = p
                self.is_game_over = True
                return

        # Check for draw
        if all(square.player != Square.EMPTY for square in self.squares):
            self.is_game_over = True


    def render(self, scr: curses.window):
        scr.clear()

        for row, line in enumerate(self.DESIGN):
            scr.addstr(row, 0, line)

        for i, square in enumerate(self.squares):
            row, col = self.SLOT_POSITIONS[i]
            is_selected = i == self.selected_index
            token, color = square.get_token(is_selected)
            scr.addstr(row, col, token, color)

        color = curses.color_pair(self.current_player)
        msg = f"Player {self.current_player}'s turn."
        scr.addstr(self.INFO_ROW, 0, msg, color)
        scr.refresh()


    def render_end_state(self, scr: curses.window):
        assert self.is_game_over

        if self.winner:
            msg = f"Player {self.winner} wins! Press any key to restart."
        else:
            msg = "It's a draw! Press any key to restart."

        color = curses.color_pair(self.winner)
        scr.addstr(self.INFO_ROW, 0, msg, color)
        scr.refresh()
        scr.getch()


    def play(self, scr: curses.window):
        self.is_playing = True

        while self.is_playing:
            self.render(scr)

            if self.is_game_over:
                self.render_end_state(scr)
                self.clear_board()
                continue

            self.handle_keypress(scr.getch())


def main(scr: curses.window):
    board = MultiplayerNoughts()
    board.play(scr)


if __name__ == '__main__':
    curses.wrapper(main)
