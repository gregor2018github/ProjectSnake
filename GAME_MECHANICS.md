# ProjectSnake — Game Mechanics Reference

Developer reference for the current mechanical systems.
Update this file whenever levels, buffs, or scoring rules change.

---

## Level System

Levels progress by **apples eaten** (not score). Each level changes what obstacle
type spawns when a normal apple is consumed. On transition, the previous level's
obstacle type is gradually removed one-by-one at a fixed interval
(`OBSTACLE_REMOVAL_INTERVAL` / `MOVING_OBSTACLE_REMOVAL_INTERVAL` ticks).

| Level | Trigger | Obstacle spawned per apple | Obstacle color |
|-------|---------|---------------------------|----------------|
| 1 | Start | Static block (`Obstacle`) | Gray |
| 2 | 10 apples | Orthogonal mover (`OrthogonalMovingObstacle`) | Orange |
| 3 | 20 apples | Diagonal mover (`MovingObstacle`) | Purple |
| 4 | 35 apples | — nothing new — | — |

**Level 4 has no ceiling.** The game runs indefinitely without enemies. Still eeds to get adjusted.

### Obstacle behavior

| Class | Movement | Collision with snake body | Bounces off |
|-------|----------|--------------------------|-------------|
| `Obstacle` | None (static) | Head kill (unless ghost/shield) | — |
| `OrthogonalMovingObstacle` | One axis only (float) | Head kill | Walls, snake body, static obstacles |
| `MovingObstacle` (diagonal) | Both axes (float) | Head kill | Walls, snake body, static obstacles |

Moving obstacles use **float sub-grid positions** for smooth movement and bounce
physics. Collision with the snake *head* kills; collision with the *body* bounces
the obstacle away.

### Temporary obstacles

Any obstacle can be given a `lifespan` attribute (integer tick count). When set,
`_update_mechanics_and_objects()` decrements it each tick and removes the obstacle
with a particle effect when it reaches 0. Used by the `spawn_enemies` buff.

---

## Scoring

| Event | Base points | Notes |
|-------|-------------|-------|
| Eat normal apple | 1 | Multiplied by combo and/or double_score buff |
| Eat normal apple (double_score active) | 2 | Before combo multiplier |
| Eat magic apple | 5 | Always; not affected by combo or double_score |

### Combo multiplier

Consecutive apples eaten within **`COMBO_WINDOW` ticks** (30) of each other build
a chain. The multiplier applies to the *base* score (so double_score stacks):

| Combo count | Multiplier |
|-------------|------------|
| 1 (first apple of chain) | ×1 |
| 2 | ×2 |
| 3 | ×3 |
| 4+ | ×4 (cap: `COMBO_MAX_MULT`) |

The chain **breaks** when `combo_timer` reaches 0 between apple pickups.
The HUD shows a colored pill (amber → orange → red) with a draining timer bar.
Best combo of the run appears on the death screen next to the score.

---

## Magic Apple System

### Spawn rules

- 10 % chance (`MAGIC_APPLE_SPAWN_PROBABILITY`) per normal apple eaten.
- In `--test-buff BUFF_TYPE` mode the first apple always forces that type.
- Magic apples despawn after `MAGIC_APPLE_LIFESPAN` ± 50 % ticks (randomised).
- A green→red outline ring on the apple shows remaining lifespan.
- Worth 5 points; always triggers one `snake.grow()`.

### Dispatch

`check_collisions()` calls `getattr(magic_apple_logic, magic_apple.type)(game)`.
Every buff type must have a matching function in `magic_apple_logic.py`.

---

## Buff Reference

### Buff mechanics

**Time-based buffs** store `active_buffs[key] = ticks_remaining`.
`_tick_active_buffs()` decrements them every game tick and cleans up expired ones.
Speed buffs also restore `game.game_speed` to `game.base_speed` on expiry.

**Charge-based buffs** store `active_buffs[key] = charges_remaining`.
They are listed in the `charge_based` tuple inside `_tick_active_buffs()` and
are **never** decremented there — each system decrements them in its own logic.

**Instant buffs** apply their effect immediately and do not set `active_buffs`.

---

### Buff table

| Key | Label | Type | Duration / Charges | Effect | Tone |
|-----|-------|------|--------------------|--------|------|
| `increase_tick_speed` | Speed+ | Time-based | 120 ticks | Game speed +5 ticks/sec (max 30) | Bad |
| `decrease_tick_speed` | Slow | Time-based | 120 ticks | Game speed −4 ticks/sec (min 4) | Good |
| `ghost_mode` | Ghost | Time-based | 100 ticks | Snake head passes through static obstacles; body is semi-transparent | Good |
| `no_grow` | No Grow | Time-based | 80 ticks | Normal apples don't grow the snake | Good |
| `double_score` | x2 Score | Time-based | 100 ticks | Normal apple base score ×2 (stacks with combo multiplier) | Good |
| `freeze_obstacles` | Freeze | Time-based | 70 ticks | All moving obstacles stop; static obstacles unaffected | Good |
| `shrink` | Shrink! | Instant | — | Snake length halved instantly (floor: start length) | Mixed |
| `shield` | Shield | Charge-based | 3 hits | Next 3 obstacle collisions absorbed; counter shown in HUD | Good |
| `manual_control` | Manual | Charge-based | 20 moves | Snake stops auto-moving; each direction key press = one step | Mixed |
| `color_invert` | Invert | Time-based | 90 ticks | Themed color swap: snake→red, apple→green, bg→grey, magic apple fill→magenta, HUD text→blue | Bad |
| `spawn_enemies` | Swarm! | Instant | — | Spawns 5 random obstacles (static/ortho/diagonal) each with 100-tick lifespan | Bad |
| `darkness` | Darkness | Time-based | 80 ticks | Near-opaque vignette covers screen; only a soft-edged circle (radius 90 px) around the snake head is lit | Bad |

### HUD colors

| Tone | Color intent |
|------|-------------|
| Good | Green / blue / gold — player-friendly |
| Bad | Red / orange / magenta — hurts or distracts |
| Mixed | Orange — situational |

### Rendering layer order (during gameplay)

```
1. screen.clear()          — background + grid
2. particle_effects        — spawn/despawn rings and dust
3. snake                   — body + head + eyes
4. apple                   — normal red apple
5. magic_apples            — gold apples with lifespan ring
6. obstacles               — static gray blocks
7. moving_obstacles        — orange / purple movers
8. apply_darkness()        — vignette mask (if active) ← covers 1-7
9. buff_announcements      — big popup text ← above darkness
10. draw_score_and_level() — score, level, combo pill ← above darkness
11. draw_buffs()           — active buff pills top-right ← above darkness
```

---

## Adding a New Buff

1. Add the key string to `MAGIC_APPLE_TYPES` in `constants.py`.
2. Add any duration/count constants to `constants.py`.
3. Add `(label, RGB)` to `BUFF_DISPLAY_NAMES` in `constants.py`.
4. Add the function `def my_buff(game): ...` to `magic_apple_logic.py`.
   - Time-based: `game.active_buffs['my_buff'] = C.BUFF_DURATION_MY_BUFF`
   - Charge-based: same, plus add `'my_buff'` to the `charge_based` tuple in
     `_tick_active_buffs()` and decrement manually in the appropriate game logic.
   - Instant: apply effect directly, do not set `active_buffs`.
5. If the buff affects rendering, handle it in `Game.draw()` (or `Screen`).
6. Test with `python main.py --test-buff my_buff`.

## Adding a New Level

1. Add threshold constant to `constants.py` (e.g. `LEVEL_5_APPLES`).
2. Add an `elif` branch in `Game._check_for_level_up()`.
3. Add any new obstacle class to `game_objects.py` if needed.
4. Register it in the `obstacle_map` inside `Game._add_obstacle()`.
5. Add level-specific apple-eat logic in `Game.check_collisions()`.
6. Add gradual removal logic in `Game._update_mechanics_and_objects()` if old
   obstacles should clear on transition.
