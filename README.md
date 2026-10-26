# Fireflies 

A computer game made with Python and Kivy. You play as a tiny light spirit
flying over a pond at night. Catch fireflies, lead them home to the nest, and try not to
get caught by the bats

Everything you see is drawn with code, so the game doesn't use any images or sound files.

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

## Author

**Paulina Rojas** — [@paulina-rc](https://github.com/paulina-rc)

## License
License. See [LICENSE](LICENSE) for details.
