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
    'light':      ColorPair(fg= 0, bg=223),
    'dark':       ColorPair(fg= 0, bg=137),
    'cursor':     ColorPair(fg= 0, bg=123),
    'selected':   ColorPair(fg= 0, bg=228),
    'legal_move': ColorPair(fg= 0, bg=114),
    'capture':    ColorPair(fg= 0, bg=210),
}


# Sizes in characters
SQUARE_COLS = 2
SQUARE_ROWS = 1
COORD_COL_PAD = 1
MARGIN_LEFT = 2 * COORD_COL_PAD + 1
MARGIN_TOP = 1
MARGIN_BOTTOM = 1
STATUS_MARGIN = 1

PROMOTION_CHOICES = chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT


class MultiplayerChess(chess.Board):
    def __init__(self, scr: curses.window):
        super().__init__()

        self.scr = scr
        self.is_running = True
        self.selected: chess.Square | None = None
        self.cursor = chess.E2
        self.is_selecting_promotion = False
        self.selected_promotion = chess.QUEEN

        curses.curs_set(0)
        self.scr.keypad(True)
        self.setup_colors()


    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()

        for color in COLORS.values():
            curses.init_pair(color.id, color.fg, color.bg)


    def get_square_row_col(self, square: chess.Square) -> tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        row = 7 - rank
        col = file

        return row, col


    def is_square_dark(self, square: chess.Square) -> bool:
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        return (rank + file) & 1 == 0


    def requires_promotion(self, move: chess.Move):
        promotionMove = chess.Move(move.from_square, move.to_square, chess.QUEEN)
        return self.is_legal(promotionMove)


    def get_square_color_pair(self, square: chess.Square) -> ColorPair:
        if square == self.selected:
            return COLORS['selected']

        if square == self.cursor:
            return COLORS['cursor']

        if self.selected is not None:
            move = chess.Move(self.selected, square)

            if self.requires_promotion(move):
                move.promotion = chess.QUEEN  # Only needed to check legality

            if self.is_legal(move):
                return COLORS['capture' if self.is_capture(move) else 'legal_move']

        return COLORS['dark' if self.is_square_dark(square) else 'light']


    def draw_square(self, square: chess.Square):
        piece = self.piece_at(square)

        row, col = self.get_square_row_col(square)

        # Leave room for rank labels and file labels.
        y = row + MARGIN_TOP
        x = col * SQUARE_COLS + MARGIN_LEFT

        symbol = PIECES[piece.symbol()] if piece is not None else ' '
        paddedSymbol = f'{symbol} '

        pair = self.get_square_color_pair(square).to_curses()

        self.scr.addstr(y, x, paddedSymbol, pair)


    def draw_coordinates_border(self):
        pair = COLORS['text'].to_curses()

        # File labels
        for file in range(8):
            x = MARGIN_LEFT + file * SQUARE_COLS
            y = MARGIN_TOP + 8 * SQUARE_ROWS
            fileLabel = chr(ord('a') + file)
            self.scr.addstr(y, x, fileLabel, pair)

        # Rank labels
        for rank in range(8):
            x = COORD_COL_PAD
            y = MARGIN_TOP + rank
            rankLabel = str(8 - rank)
            self.scr.addstr(y, x, rankLabel, pair)


    def draw_board(self):
        for square in chess.SQUARES:
            self.draw_square(square)

        self.draw_coordinates_border()


    def draw_promotion_selection(self):
        x = MARGIN_LEFT + 2 * SQUARE_COLS
        y = MARGIN_TOP + 8 * SQUARE_ROWS + MARGIN_BOTTOM + STATUS_MARGIN

        for pieceType in PROMOTION_CHOICES:
            pairName = 'selected' if pieceType == self.selected_promotion else 'text'
            pair = COLORS[pairName].to_curses()

            piece = chess.Piece(pieceType, self.turn)
            text = f'{PIECES[piece.symbol()]} '

            self.scr.addstr(y, x, text, pair)
            x += len(text)


    def draw_status_text(self):
        x = MARGIN_LEFT
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

        if self.is_selecting_promotion:
            self.draw_promotion_selection()
        else:
            self.draw_status_text()

        self.scr.refresh()


    def move_promotion_cursor(self, d_index: int):
        index = PROMOTION_CHOICES.index(self.selected_promotion)
        index = (index + d_index) % len(PROMOTION_CHOICES)
        self.selected_promotion = PROMOTION_CHOICES[index]


    def make_promotion_move(self):
        assert self.selected is not None
        move = chess.Move(self.selected, self.cursor, self.selected_promotion)

        assert self.is_legal(move)
        self.push(move)

        self.selected = None
        self.is_selecting_promotion = False
        self.selected_promotion = chess.QUEEN


    def handle_promotion_keypress(self, key: int):
        if key == curses.KEY_RIGHT:
            self.move_promotion_cursor(1)

        elif key == curses.KEY_LEFT:
            self.move_promotion_cursor(-1)

        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            self.make_promotion_move()


    def move_cursor(self, dx: int, dy: int):
        file = chess.square_file(self.cursor)
        rank = chess.square_rank(self.cursor)

        file = (file + dx) % 8
        rank = (rank + dy) % 8

        self.cursor = chess.square(file, rank)


    def select_or_move(self):
        if self.selected is None:
            piece = self.piece_at(self.cursor)

            # Only allow selecting the side whose turn it is
            if piece is not None and piece.color == self.turn:
                self.selected = self.cursor

            return

        # Selecting the same square deselects it
        if self.cursor == self.selected:
            self.selected = None
            return

        move = chess.Move(self.selected, self.cursor)

        if self.requires_promotion(move):
            self.is_selecting_promotion = True
            return

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


    def handle_board_keypress(self, key: int):
        if key == curses.KEY_UP:
            self.move_cursor(0, 1)

        elif key == curses.KEY_DOWN:
            self.move_cursor(0, -1)

        elif key == curses.KEY_LEFT:
            self.move_cursor(-1, 0)

        elif key == curses.KEY_RIGHT:
            self.move_cursor(1, 0)

        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            self.select_or_move()


    def handle_keypress(self, key: int):
        if key in (ord('q'), 27):
            self.is_running = False

        elif self.is_selecting_promotion:
            self.handle_promotion_keypress(key)

        else:
            self.handle_board_keypress(key)


    def play(self):
        while self.is_running:
            self.render()
            key = self.scr.getch()
            self.handle_keypress(key)


def main(scr: curses.window):
    board = MultiplayerChess(scr)
    board.play()


if __name__ == '__main__':
    curses.wrapper(main)
