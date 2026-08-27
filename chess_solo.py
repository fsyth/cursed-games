import chess
import curses
from random import choice

from chess_multiplayer import MultiplayerChess

class SoloChess(MultiplayerChess):
    def get_cpu_move(self):
        return choice(list(self.legal_moves))


    def play(self, player_color=chess.WHITE):
        while self.is_running:
            if self.turn == player_color or self.is_game_over():
                self.render()
                key = self.scr.getch()
                self.handle_keypress(key)
            else:
                self.render()
                self.push(self.get_cpu_move())


def main(scr: curses.window):
    board = SoloChess(scr)
    board.play()


if __name__ == '__main__':
    curses.wrapper(main)
