# Fireflies 

A computer game made with Python and Kivy. You play as a tiny light spirit
flying over a pond at night. Catch fireflies, lead them home to the nest, and try not to
get caught by the bats

Everything you see is drawn with code, so the game doesn't use any images or sound files.

## Controls

| Key | What it does |
|---|---|
| W A S D or arrow keys | Move |
| Space | Dash |
| Esc | Pause / resume (goes back to the menu from "How to play") |
| F11 | Fullscreen |

You only need the mouse for the menus.

## How to play

- **Fireflies:** touch them and they'll start following you in a glowing line (up to 15).
- **The nest:** fly into it to drop off your fireflies and get points. The longer your
  line, the better: 5 or more gives you x2 points, 10 or more gives you x3.
- **Bats:** they chase you around. If one hits you while you have fireflies, they all
  scatter and you have to catch them again. If you have none, you lose a life.
  You get 3 lives.
- **Dash:** a quick burst of speed that lets you fly right through bats. It recharges
  in 2 seconds.
- **Power-ups** (they disappear after 6 seconds, so be quick):
  - Blue moon: freezes the bats for 4 seconds.
  - Golden star: works like a magnet, pulling nearby fireflies to you for 5 seconds.
  - Heart: gives you one extra life (max 3).
- **Nights:** each night has a goal (Night 1 is 10 fireflies, then 5 more each night).
  Reach it and a new night starts, with one more bat, faster bats, and the nest in a
  new spot. From Night 4 on, watch out for the **shooting firefly**: it runs away
  from you, but it's worth triple points.
- The game ends when you lose all 3 lives. Your best score and highest night are saved
  automatically.

## What's in the project

```
├── main.py                  # Starts the game
├── requirements.txt         # What you need to install (Kivy)
├── .gitignore
├── README.md
├── game/                    # All the game code
│   ├── app.py               # Sets up the app, screens and fullscreen
│   ├── config.py            # All the numbers you can tweak
│   ├── drawing.py           # Helpers for colors and shapes
│   ├── entities/            # Everything that moves around
│   │   ├── player.py        # The light spirit
│   │   ├── firefly.py       # The fireflies
│   │   ├── bat.py           # The bats
│   │   ├── nest.py          # Where you drop off the fireflies
│   │   └── powerup.py       # Moon, star and heart
│   ├── effects/             # Eye candy
│   │   ├── particles.py     # Sparkles and floating points
│   │   └── camera.py        # Screen shake
│   ├── systems/             # The game rules
│   │   ├── collisions.py    # Checks when things touch
│   │   ├── levels.py        # Nights, goals and difficulty
│   │   ├── keyboard_input.py# Reads the keyboard
│   │   └── highscores.py    # Saves your best score
│   ├── screens/             # Each screen of the game
│   │   ├── base.py
│   │   ├── menu.py
│   │   ├── how_to_play.py
│   │   ├── game_screen.py   # Where the actual game happens
│   │   └── game_over.py
│   ├── ui/                  # Buttons, HUD and other pieces of the interface
│   │   ├── background.py    # Night sky, stars, water and reeds
│   │   ├── buttons.py
│   │   ├── hud.py           # Lives, score and dash meter
│   │   ├── labels.py
│   │   ├── keys.py          # The little keys in the controls panel
│   │   ├── overlays.py      # Pause menu and "Night N" banner
│   │   └── decorations.py   # Decorative fireflies
│   └── kv/                  # Screen layouts (Kivy's design language)
│       ├── menu.kv
│       ├── how_to_play.kv
│       ├── game_screen.kv
│       └── game_over.kv
└── tests/                   # Simple tests
    ├── test_collisions.py
    └── test_levels.py
```

## Tests

The tests check that collisions and the night rules work properly. They don't open
any window:

```bash
python -m unittest discover tests
```
