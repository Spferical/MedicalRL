#!/usr/bin/env python3
from game import Game
import ui


def main():
    ui.init_tcod()
    while True:
        choice = ui.handle_main_menu()
        if choice == ui.MainMenuChoice.PLAY:
            game = Game()
            game.run()
        else:
            break


if __name__ == '__main__':
    main()
