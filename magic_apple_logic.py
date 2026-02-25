"""
The player can pick up special apples that grant unique bonuses or malus effects.
Each function receives the Game instance and mutates its state directly.
"""

import constants as C


def increase_tick_speed(game):
    """Temporarily increase game speed by 5 ticks/sec (max 30)."""
    game.game_speed = min(game.game_speed + 5, 30)
    game.active_buffs['increase_tick_speed'] = C.BUFF_DURATION_SPEED_UP


def decrease_tick_speed(game):
    """Temporarily decrease game speed by 4 ticks/sec (min 4)."""
    game.game_speed = max(game.game_speed - 4, 4)
    game.active_buffs['decrease_tick_speed'] = C.BUFF_DURATION_SPEED_DOWN


def ghost_mode(game):
    """Snake head passes through static obstacles for a limited time."""
    game.active_buffs['ghost_mode'] = C.BUFF_DURATION_GHOST


def no_grow(game):
    """Eating normal apples does not grow the snake for a limited time."""
    game.active_buffs['no_grow'] = C.BUFF_DURATION_NO_GROW
