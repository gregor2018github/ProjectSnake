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
    args = parser.parse_args()
    game = Game(test_buff=args.test_buff)
    game.run()

if __name__ == "__main__":
    main()