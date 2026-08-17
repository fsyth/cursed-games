import chess
import curses


class Chessboard(chess.Board):
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
        self.running = True

        self.selected = None
        self.cursor = chess.E2

        self.setup_colors()


    def setup_colors(self) -> None:
        curses.start_color()
        curses.use_default_colors()

        # 256-color palette values.
        LIGHT_SQUARE = 250
        DARK_SQUARE = 247

        # Normal pieces
        curses.init_pair(1, curses.COLOR_BLACK, DARK_SQUARE)
        curses.init_pair(2, curses.COLOR_BLACK, LIGHT_SQUARE)
        curses.init_pair(3, curses.COLOR_WHITE, DARK_SQUARE)
        curses.init_pair(4, curses.COLOR_WHITE, LIGHT_SQUARE)

        # Selected square
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_YELLOW)

        # Legal move
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_GREEN)

        # Legal capture
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_RED)

        # Cursor
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)

        # Status text
        curses.init_pair(9, curses.COLOR_WHITE, -1)


    def get_square_position(self, square: chess.Square) -> tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        row = 7 - rank
        col = file

        return row, col


    def is_square_dark(self, square: chess.Square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        return (rank + file) % 2 == 0


    def get_square_color_pair(self, square: chess.Square):
        piece = self.piece_at(square)
        dark_square = self.is_square_dark(square)

        if piece is None:
            return 1 if dark_square else 2

        if piece.color == chess.WHITE:
            return 3 if dark_square else 4

        return 1 if dark_square else 2


    def legal_moves_from(self, square: chess.Square) -> set[chess.Square]:
        return {
            move.to_square
            for move in self.legal_moves
            if move.from_square == square
        }


    def draw_square(self, square: chess.Square) -> None:
        piece = self.piece_at(square)

        row, col = self.get_square_position(square)

        # Leave room for rank labels and file labels.
        y = row + 1
        x = col * 3 + 3

        legal_moves = (
            self.legal_moves_from(self.selected)
            if self.selected is not None
            else set()
        )

        # Determine which visual state this square has.
        if square == self.selected:
            pair = 5
        elif square == self.cursor:
            pair = 8
        elif square in legal_moves:
            if self.piece_at(square) is None:
                pair = 6
            else:
                pair = 7
        else:
            pair = self.get_square_color_pair(square)

        symbol = self.PIECES.get(piece.symbol(), ' ') if piece else ' '
        paddedSymbol = f' {symbol} '

        self.scr.addstr(y, x, paddedSymbol, curses.color_pair(pair))


    def draw_coordinates_border(self):
        # File labels
        for file in range(8):
            x = file * 3 + 4
            y = 9
            fileLabel = chr(ord('a') + file)
            self.scr.addstr(y, x, fileLabel, curses.color_pair(9))

        # Rank labels
        for rank in range(8):
            x = 1
            y = rank + 1
            rankLabel = str(8 - rank)
            self.scr.addstr(y, x, rankLabel, curses.color_pair(9))


    def draw_status(self):
        x = 1
        y = 11

        if self.is_checkmate():
            winner = 'White' if self.turn == chess.BLACK else 'Black'
            text = f'Checkmate — {winner} wins!'

        elif self.is_stalemate():
            text = 'Stalemate'

        elif self.is_check():
            player = 'White' if self.turn == chess.WHITE else 'Black'
            text = f'{player} is in check'

        else:
            player = 'White' if self.turn == chess.WHITE else 'Black'
            text = f'{player} to move'

        self.scr.addstr(y, x, text, curses.color_pair(9))


    def render(self):
        self.scr.erase()

        for square in chess.SQUARES:
            self.draw_square(square)

        self.draw_coordinates_border()
        self.draw_status()

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

            # Only allow selecting the side whose turn it is.
            if piece is not None and piece.color == self.turn:
                self.selected = self.cursor

            return

        # Clicking/selecting the same square deselects it.
        if self.cursor == self.selected:
            self.selected = None
            return

        move = chess.Move(self.selected, self.cursor)
        piece = self.piece_at(self.selected)
        assert piece

        # Handle pawn promotion automatically for now.
        if (
            piece.piece_type == chess.PAWN and
            chess.square_rank(self.cursor) in (0, 7)
        ):
            move.promotion = chess.QUEEN

        if move in self.legal_moves:
            self.push(move)
            self.selected = None

        else:
            # Allow selecting another piece of the same color.
            piece = self.piece_at(self.cursor)

            if piece is not None and piece.color == self.turn:
                self.selected = self.cursor
            else:
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
