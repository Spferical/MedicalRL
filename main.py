#!/usr/bin/env python3
from game import Game
import ui


def main():
    ui.init_tcod()
    while True:
        choice = ui.handle_main_menu()
        if choice == ui.MainMenuChoice.PLAY:
            preexisting_conditions = ui.ask_player_for_preexisting_conditions()
            game = Game()
            game.run(
                character_info={'ADDITONAL_FATIGUE': [],
                                'PREEXISTING_CONDITIONS':
                                preexisting_conditions})
        else:
            break


if __name__ == '__main__':
    main()
