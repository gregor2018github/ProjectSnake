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


def double_score(game):
    """Each normal apple grants 2 points instead of 1 for a limited time."""
    game.active_buffs['double_score'] = C.BUFF_DURATION_DOUBLE_SCORE


def freeze_obstacles(game):
    """All moving obstacles stop moving for a limited time."""
    game.active_buffs['freeze_obstacles'] = C.BUFF_DURATION_FREEZE


def shrink(game):
    """Instantly halve the snake's length (minimum: starting length).
    Useful for escaping tight spots."""
    target = max(C.SNAKE_START_LENGTH, len(game.snake.positions) // 2)
    game.snake.positions = game.snake.positions[:target]
    game.snake.length = target


def shield(game):
    """Absorb up to SHIELD_HITS obstacle collisions without dying.
    The HUD counter shows remaining charges."""
    game.active_buffs['shield'] = C.SHIELD_HITS


def manual_control(game):
    """Snake stops auto-moving; player must press a direction key for each step.
    Lasts BUFF_MANUAL_MOVES key-presses (move-count-based, not time-based)."""
    game.active_buffs['manual_control'] = C.BUFF_MANUAL_MOVES
