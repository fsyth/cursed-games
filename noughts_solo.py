import curses
from random import choice

from noughts_multiplayer import MultiplayerNoughts, Square


class SoloNoughts(MultiplayerNoughts):
    def get_cpu_move(self) -> int:
        return choice([
            index
            for index, square in enumerate(self.squares)
            if square.player == Square.EMPTY
        ])


    def play(self, scr: curses.window, player_color=Square.PLAYER_O):
        self.is_playing = True

        while self.is_playing:
            self.render(scr)

            if self.is_game_over:
                self.render_end_state(scr)
                self.clear_board()
                continue

            if self.current_player == player_color or self.is_game_over:
                self.handle_keypress(scr.getch())
            else:
                self.make_move(self.get_cpu_move())


def main(scr: curses.window):
    board = SoloNoughts()
    board.play(scr)


if __name__ == '__main__':
    curses.wrapper(main)
