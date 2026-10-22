# Luciérnagas

Juego para computadora hecho en Python con Kivy. Eres un espíritu de luz que vuela
sobre un estanque de noche. Tienes que juntar luciérnagas en una cola que te sigue
como una serpiente de luz, llevarlas al nido y esquivar a los murciélagos.

Todo se dibuja con el canvas de Kivy: el juego no usa imágenes ni sonidos externos.

## Instalación

Necesitas Python 3.10 o más nuevo.

1. (Opcional) Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el juego:
   ```bash
   python main.py
   ```

## Controles

| Tecla | Acción |
|---|---|
| W A S D o flechas | Moverse |
| Espacio | Impulso (dash) |
| Esc | Pausar / continuar (en "Cómo jugar", vuelve al menú) |
| F11 | Pantalla completa |

El mouse solo se usa en los menús.

## Cómo jugar

- **Luciérnagas:** tócalas para sumarlas a tu cola (máximo 15).
- **Nido:** entra con tu cola para entregarlas. Puntos = luciérnagas × multiplicador
  (5 o más: x2, 10 o más: x3).
- **Murciélagos:** te persiguen. Si te tocan y tienes cola, la cola se dispersa;
  si no tienes cola, pierdes una vida. Tienes 3 vidas.
- **Dash:** un impulso rápido que atraviesa murciélagos sin daño. Se recarga en 2 segundos.
- **Power-ups** (duran 6 s en el mapa):
  - Luna azul: congela a los murciélagos por 4 s.
  - Estrella dorada: imán, las luciérnagas cercanas vuelan hacia ti por 5 s.
  - Corazón: +1 vida (máximo 3).
- **Noches:** cada noche tiene una meta (Noche 1: 10 luciérnagas, y +5 por noche).
  Al cumplirla empieza la siguiente noche, con un murciélago más, murciélagos más
  rápidos y el nido en otro lugar. Desde la Noche 4 aparece la **luciérnaga fugaz**,
  que huye de ti y vale el triple.
- El juego termina al perder las 3 vidas. El récord (puntaje y noche máxima) se guarda solo.

## Estructura del proyecto

```
├── main.py                  # Solo arranca la app
├── requirements.txt         # Dependencias (Kivy)
├── .gitignore
├── README.md
├── game/                    # Todo el código del juego
│   ├── app.py               # FirefliesApp: ScreenManager, F11 y récord
│   ├── config.py            # TODOS los valores ajustables
│   ├── drawing.py           # Ayudas de colores y dibujos (círculo, corazón)
│   ├── entities/            # Lo que se mueve en el mapa
│   │   ├── player.py        # Player: espíritu de luz, aceleración, dash y estela
│   │   ├── firefly.py       # Firefly: estados libre, cola, dispersa y entregando
│   │   ├── bat.py           # Bat: persigue al jugador girando poco a poco
│   │   ├── nest.py          # Nest: donde se entregan las luciérnagas
│   │   └── powerup.py       # PowerUp: luna, estrella y corazón
│   ├── effects/             # Efectos visuales
│   │   ├── particles.py     # Chispas, texto flotante de puntos y anillos
│   │   └── camera.py        # Sacudida de pantalla
│   ├── systems/             # Reglas y lógica sin dibujo
│   │   ├── collisions.py    # Colisiones por distancia
│   │   ├── levels.py        # LevelManager: noches, metas y dificultad
│   │   ├── keyboard_input.py# Teclas presionadas, dirección y dash
│   │   └── highscores.py    # Guardar y cargar el récord (JsonStore)
│   ├── screens/             # Las pantallas (la lógica)
│   │   ├── base.py          # Pantalla base con bucle a 60 FPS y carga de .kv
│   │   ├── menu.py
│   │   ├── how_to_play.py
│   │   ├── game_screen.py   # Pantalla de juego y bucle principal
│   │   └── game_over.py
│   ├── ui/                  # Widgets de interfaz
│   │   ├── background.py    # Cielo con degradado, estrellas, agua y juncos
│   │   ├── buttons.py       # Botón redondeado con hover
│   │   ├── hud.py           # Vidas, puntaje, meta y enfriamiento del dash
│   │   ├── labels.py        # Etiqueta de texto con el estilo del juego
│   │   ├── keys.py          # Teclas dibujadas del panel de controles
│   │   ├── overlays.py      # Menú de pausa y cartel "Noche N"
│   │   └── decorations.py   # Luciérnagas de adorno y vitrinas de "Cómo jugar"
│   └── kv/                  # Diseño de las pantallas en lenguaje KV
│       ├── menu.kv
│       ├── how_to_play.kv
│       ├── game_screen.kv   # Capas del juego, HUD, pausa y cartel de noche
│       └── game_over.kv
└── tests/                   # Pruebas con unittest (no abren ventana)
    ├── test_collisions.py
    └── test_levels.py
```

**Cómo se reparte el trabajo:**

- **Python vs. KV:** los archivos `.kv` dicen *dónde* va cada cosa (botones, textos,
  tamaños, posiciones). Los archivos `.py` dicen *qué hace*. Cada pantalla carga su
  `.kv` con `Builder.load_file`.
- **config.py:** si quieres cambiar algo del juego (velocidades, metas, colores,
  duración de los power-ups...) se cambia ahí, no en el código. Las medidas están
  en dp y los tiempos en segundos.
- **Entidades:** no son widgets. Cada una agrupa sus dibujos en un `InstructionGroup`
  y lo agrega a una capa; es más liviano que un widget por luciérnaga.

**Ideas principales:**

- **Bucle del juego:** `GameScreen.loop(dt)` se ejecuta 60 veces por segundo con
  `Clock.schedule_interval`. Todo movimiento se multiplica por `dt`, así el juego va
  a la misma velocidad aunque cambien los FPS. Al pausar o salir, el Clock se cancela.
- **Teclado:** `KeyboardInput` usa `Window.bind(on_key_down, on_key_up)` y guarda en un
  `set` las teclas presionadas. Se desvincula al salir de la pantalla de juego.
- **Colisiones:** dos círculos chocan si la distancia entre sus centros es menor que
  la suma de sus radios (`math.hypot`).
- **Cola:** cada luciérnaga se acerca con interpolación a la anterior (la primera
  sigue al jugador), quedando siempre a la misma distancia.
- **Sacudida:** el fondo y el juego están dentro de un widget con un `Translate`
  que se mueve unos píxeles al azar cuando te golpean. El HUD no se mueve.

## Pruebas

Las pruebas revisan las colisiones y las reglas de las noches (metas, cantidad y
velocidad de murciélagos, multiplicadores). No abren ninguna ventana:

```bash
python -m unittest discover tests
```
