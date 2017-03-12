#!/usr/bin/env python3
from game import Game
import ui
from random import choice
from vitals import diseases


def main():
    ui.init_tcod()
    while True:
        ch = ui.handle_main_menu()
        if ch == ui.MainMenuChoice.PLAY:
            preexisting_conditions = ui.ask_player_for_preexisting_conditions()
            game = Game()
            game.run(
                character_info={'ADDITONAL_FATIGUE': [],
                                'PREEXISTING_CONDITIONS': {},
                                'DISEASE': choice(diseases)})
        else:
            break


if __name__ == '__main__':
    main()
