import chess
import curses

from helpers import ColorPair


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


# Color pair IDs and 256-color palette values
COLORS = {
    'text':       ColorPair(fg=-1, bg= -1),
    'light':      ColorPair(fg= 0, bg=250),
    'dark':       ColorPair(fg= 0, bg=247),
    'cursor':     ColorPair(fg= 0, bg=123),
    'selected':   ColorPair(fg= 0, bg=228),
    'legal_move': ColorPair(fg= 0, bg=114),
    'capture':    ColorPair(fg= 0, bg=210),
}


# Sizes in characters
SQUARE_COLS = 3
SQUARE_ROWS = 1
COORD_COL_PAD = 1
MARGIN_LEFT = 2 * COORD_COL_PAD + 1
MARGIN_TOP = 1
MARGIN_BOTTOM = 1
STATUS_MARGIN = 1


class Chessboard(chess.Board):
    def __init__(self, scr: curses.window):
        super().__init__()

        self.scr = scr
        self.running = True
        self.selected = None
        self.cursor = chess.E2

        self.setup_colors()


    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()

        for color in COLORS.values():
            curses.init_pair(color.id, color.fg, color.bg)


    def get_square_position_y_down(self, square: chess.Square) -> tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        row = 7 - rank
        col = file

        return row, col


    def is_square_dark(self, square: chess.Square) -> bool:
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        return (rank + file) & 1 == 0


    def get_square_color_pair(self, square: chess.Square) -> ColorPair:
        if square == self.selected:
            return COLORS['selected']

        if square == self.cursor:
            return COLORS['cursor']

        if self.selected:
            move = chess.Move(self.selected, square)
            if self.is_legal(move):
                return COLORS['capture' if self.is_capture(move) else 'legal_move']

        return COLORS['dark' if self.is_square_dark(square) else 'light']


    def draw_square(self, square: chess.Square):
        piece = self.piece_at(square)

        row, col = self.get_square_position_y_down(square)

        # Leave room for rank labels and file labels.
        y = row + MARGIN_TOP
        x = col * SQUARE_COLS + MARGIN_LEFT

        symbol = PIECES[piece.symbol()] if piece else ' '
        paddedSymbol = f' {symbol} '

        pair = self.get_square_color_pair(square).to_curses()

        self.scr.addstr(y, x, paddedSymbol, pair)


    def draw_board(self):
        for square in chess.SQUARES:
            self.draw_square(square)


    def draw_coordinates_border(self):
        pair = COLORS['text'].to_curses()

        # File labels
        for file in range(8):
            x = MARGIN_LEFT + COORD_COL_PAD + file * SQUARE_COLS
            y = MARGIN_TOP + 8 * SQUARE_ROWS
            fileLabel = chr(ord('a') + file)
            self.scr.addstr(y, x, fileLabel, pair)

        # Rank labels
        for rank in range(8):
            x = COORD_COL_PAD
            y = MARGIN_TOP + rank
            rankLabel = str(8 - rank)
            self.scr.addstr(y, x, rankLabel, pair)


    def draw_status_text(self):
        x = COORD_COL_PAD
        y = MARGIN_TOP + 8 * SQUARE_ROWS + MARGIN_BOTTOM + STATUS_MARGIN
        pair = COLORS['text'].to_curses()

        if self.is_checkmate():
            winner = 'White' if self.turn == chess.BLACK else 'Black'
            text = f'Checkmate! {winner} wins!'

        elif self.is_stalemate():
            text = 'Stalemate'

        elif self.is_check():
            player = 'White' if self.turn == chess.WHITE else 'Black'
            text = f'{player} is in check'

        else:
            player = 'White' if self.turn == chess.WHITE else 'Black'
            text = f'{player} to move'

        self.scr.addstr(y, x, text, pair)


    def render(self):
        self.scr.erase()

        self.draw_board()
        self.draw_coordinates_border()
        self.draw_status_text()

        self.scr.refresh()


    def move_cursor(self, dx, dy):
        file = chess.square_file(self.cursor)
        rank = chess.square_rank(self.cursor)

        file = (file + dx) % 8
        rank = (rank + dy) % 8

        self.cursor = chess.square(file, rank)


    def select_or_move(self):
        if self.selected is None:
            piece = self.piece_at(self.cursor)

            # Only allow selecting the side whose turn it is
            if piece and piece.color == self.turn:
                self.selected = self.cursor

            return

        # Selecting the same square deselects it
        if self.cursor == self.selected:
            self.selected = None
            return

        move = chess.Move(self.selected, self.cursor)
        piece = self.piece_at(self.selected)
        assert piece

        # Set pawn promotion choice automatically for now
        if (
            piece.piece_type == chess.PAWN and
            chess.square_rank(self.cursor) in (0, 7)
        ):
            move.promotion = chess.QUEEN

        # Make the move if possible
        if self.is_legal(move):
            self.push(move)
            self.selected = None
            return

        # Allow reselecting another piece of the same color
        other_piece = self.piece_at(self.cursor)

        if other_piece and other_piece.color == self.turn:
            self.selected = self.cursor
            return

        # Deselect the piece if selecting an illegal move
        self.selected = None


    def handle_keypress(self):
        key = self.scr.getch()

        if key == ord('q'):
            self.running = False

        elif key == curses.KEY_UP:
            self.move_cursor(0, 1)

        elif key == curses.KEY_DOWN:
            self.move_cursor(0, -1)

        elif key == curses.KEY_LEFT:
            self.move_cursor(-1, 0)

        elif key == curses.KEY_RIGHT:
            self.move_cursor(1, 0)

        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            self.select_or_move()


    def play(self):
        curses.curs_set(0)
        self.scr.keypad(True)

        while self.running:
            self.render()
            self.handle_keypress()


def main(scr: curses.window):
    board = Chessboard(scr)
    board.play()


if __name__ == '__main__':
    curses.wrapper(main)
