# IMPORTS
import argparse
from game import Game

def main():
    parser = argparse.ArgumentParser(description='ProjectSnake')
    parser.add_argument(
        '--test-buff', metavar='BUFF_TYPE', default=None,
        help='Force this magic apple type to spawn immediately after the first apple is eaten. '
             'Example: --test-buff manual_control'
    )
    parser.add_argument(
        '--start-level', metavar='N', type=int, default=1,
        help='Start the game at level N (1-4), with apples_eaten pre-set to that '
             'level\'s threshold and a few representative obstacles already on the field. '
             'Example: --start-level 3'
    )
    args = parser.parse_args()
    game = Game(test_buff=args.test_buff, start_level=args.start_level)
    game.run()

if __name__ == "__main__":
    main()