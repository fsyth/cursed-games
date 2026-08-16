import chess
import curses


class CursesBoard(chess.Board):
    PIECES = {
        'K': '♔',
        'Q': '♕',
        'R': '♖',
        'B': '♗',
        'N': '♘',
        'P': '♙',
        'k': '♚',
        'q': '♛',
        'r': '♜',
        'b': '♝',
        'n': '♞',
        'p': '♟',
    }

    def __init__(self, scr: curses.window):
        super().__init__()
        self.scr = scr

        curses.start_color()
        # curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_WHITE)


    def handle_keypress(self):
        key_code = self.scr.getch()
        if key_code == ord('q'):
            self.is_playing = False


    def render(self):
        self.scr.clear()

        for rank in range(7, -1, -1):
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.piece_at(square)

                # Alternating board colours
                bg = (rank + file) % 2
                white_piece = piece and piece.color

                if white_piece:
                    color = curses.color_pair(4 if bg else 3)
                else:
                    color = curses.color_pair(2 if bg else 1)

                symbol = CursesBoard.PIECES.get(piece.symbol(), ' ') if piece else ' '

                self.scr.addstr(
                    f" {symbol} ",
                    curses.color_pair(color)
                )

            self.scr.addstr("\n")

        self.scr.refresh()


    def play(self): 
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        self.is_playing = True
        while self.is_playing:
            self.render()
            self.handle_keypress()


def main(scr: curses.window):
    board = CursesBoard(scr)
    board.play()


if __name__ == '__main__':
    curses.wrapper(main)
