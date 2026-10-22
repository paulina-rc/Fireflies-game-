"""
Configuración del juego: aquí están TODOS los valores ajustables.

Si quieres cambiar algo del juego (velocidades, tamaños, colores, metas de
cada noche, duración de los power-ups...) se cambia aquí y no en el código.

Las medidas de tamaño y distancia están en "dp" (píxeles independientes de
la densidad de la pantalla). El código las convierte con dp() de Kivy.
Los tiempos están en segundos.

Este archivo no importa Kivy (salvo dentro de apply_window_config), así los
tests pueden usarlo sin abrir una ventana.
"""

from .drawing import hex_to_rgb

# ---------------------------------------------------------------------------
# Ventana y aplicación
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 450
FPS = 60.0
MAX_FRAME_TIME = 0.05  # evita saltos grandes si la ventana se congela
SCREEN_TRANSITION_DURATION = 0.4

APP_TITLE = 'Luciérnagas'
# Nombre de la carpeta de datos del usuario. Se mantiene el de la versión
# anterior del juego para no perder el récord ya guardado.
APP_DATA_NAME = 'luciernagas'

# Nombres internos de las pantallas (los usa el ScreenManager)
SCREEN_MENU = 'menu'
SCREEN_HOW_TO_PLAY = 'how_to_play'
SCREEN_GAME = 'game'
SCREEN_GAME_OVER = 'game_over'

# ---------------------------------------------------------------------------
# Récord (se guarda en un JSON en la carpeta de datos del usuario)
# ---------------------------------------------------------------------------
HIGHSCORE_FILE = 'record.json'
# Claves del JSON: se mantienen las de la versión anterior para que el
# récord guardado se siga leyendo.
HIGHSCORE_KEY = 'record'
HIGHSCORE_SCORE_FIELD = 'puntos'
HIGHSCORE_NIGHT_FIELD = 'noche'

# ---------------------------------------------------------------------------
# Teclado (códigos de teclas de Kivy)
# ---------------------------------------------------------------------------
KEYS_UP = {273, ord('w')}
KEYS_DOWN = {274, ord('s')}
KEYS_LEFT = {276, ord('a')}
KEYS_RIGHT = {275, ord('d')}
KEY_SPACE = 32
KEY_ESCAPE = 27
KEY_F11 = 292

# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
# Algunos colores se guardan también en hexadecimal porque el "markup" de
# los textos de Kivy ([color=F7E967]) los necesita así.
YELLOW_HEX = 'F7E967'
GOLD_HEX = 'FFC94D'
ICE_BLUE_HEX = '7FDBFF'

NIGHT_BLUE = hex_to_rgb('#0B1026')       # cielo arriba (Noche 1)
DARK_PURPLE = hex_to_rgb('#2B1B3F')      # cielo abajo (Noche 1)
LATE_NIGHT_BLUE = hex_to_rgb('#1C1240')  # cielo arriba en noches avanzadas
DEEP_PURPLE = hex_to_rgb('#4B2266')      # cielo abajo en noches avanzadas
YELLOW = hex_to_rgb(YELLOW_HEX)          # luciérnagas
GOLD = hex_to_rgb(GOLD_HEX)              # luciérnaga fugaz, estrella, combos
ICE_BLUE = hex_to_rgb(ICE_BLUE_HEX)      # luna azul, murciélagos congelados
CREAM = hex_to_rgb('#F5F0E6')            # textos
PINK = hex_to_rgb('#FF7A90')             # corazones
HALO_GREEN = (0.80, 0.95, 0.45)          # halo verdoso de las luciérnagas
PLAYER_LIGHT = (1.0, 0.96, 0.86)         # blanco cálido del espíritu
BAT_COLOR = (0.03, 0.025, 0.06)
EYE_RED = (1.0, 0.28, 0.28)

BAT_AURA_COLOR = (0.5, 0.3, 0.75, 0.16)    # aura para que el murciélago se vea
FROZEN_BAT_BODY = (0.30, 0.50, 0.70, 1)
FIREFLY_CENTER_COLOR = (1, 1, 0.95)
BACK_REED_COLOR = (0.10, 0.075, 0.17, 1)
WATER_VEIL_COLOR = (0.02, 0.03, 0.10, 0.55)
SHORE_COLOR = (0.015, 0.02, 0.05, 1)
PANEL_COLOR = (0.04, 0.04, 0.11, 0.55)     # panel de controles del menú
PAUSE_VEIL_COLOR = (0.03, 0.03, 0.09, 0.75)
BANNER_VEIL_COLOR = (0.02, 0.02, 0.07, 0.65)
KEY_SHADOW_COLOR = (0, 0, 0, 0.35)

# ---------------------------------------------------------------------------
# Fondo nocturno
# ---------------------------------------------------------------------------
SCENERY_SEED = 11          # semilla fija: el paisaje es igual en todas las pantallas
HORIZON_HEIGHT = 0.24      # el agua ocupa el 24 % inferior
SKY_TEXTURE_HEIGHT = 256   # píxeles del degradado del cielo
SKY_TINT_PER_NIGHT = 0.14  # cuánto más morado es el cielo cada noche
STAR_COUNT = 150
WATER_SPARKLE_COUNT = 28
BACK_REED_COUNT = 36
FRONT_REED_COUNT = 44
REED_FLOWER_CHANCE = 0.35  # probabilidad de que un junco tenga espadaña
REED_SEGMENTS = 8          # tramos de la curva de cada junco
MOON_RADIUS = 22
MOON_HALOS = ((3.4, 0.04), (2.3, 0.07), (1.6, 0.12))  # (tamaño, opacidad)
MOON_REFLECTION_LINES = 7
SHORE_HEIGHT = 8

# Posición relativa (0..1) de la luna en cada pantalla
MOON_POS_DEFAULT = (0.83, 0.74)
MOON_POS_MENU = (0.93, 0.84)         # fuera del panel de controles
MOON_POS_HOW_TO_PLAY = (0.94, 0.9)

# ---------------------------------------------------------------------------
# Jugador (espíritu de luz)
# ---------------------------------------------------------------------------
PLAYER_RADIUS = 11
PLAYER_ACCELERATION = 2100    # dp por segundo²
PLAYER_FRICTION = 5.5         # cuánto frena por segundo
DASH_SPEED = 1000             # dp por segundo
DASH_DURATION = 0.17
DASH_COOLDOWN = 2.0
TRAIL_LENGTH = 16             # cuántas posiciones guarda la estela
TRAIL_INTERVAL = 0.02         # cada cuánto se guarda una posición
TRAIL_FULL_SPEED = 250        # a esta rapidez la estela se ve completa
PLAYER_HALOS = ((5.5, 0.06), (3.4, 0.12), (2.0, 0.26))
PLAYER_BLINK_RATE = 14        # parpadeos por segundo cuando es invulnerable
PLAYER_BLINK_ALPHA = 0.3
PLAYER_MAGNET_TINT = 0.7      # cuánto dorado toma con el imán
PLAYER_DASH_GLOW = 1.3        # el halo crece durante el dash
HIT_INVULNERABILITY = 1.5     # segundos sin daño después de un golpe
NIGHT_START_INVULNERABILITY = 1.0

# ---------------------------------------------------------------------------
# Luciérnagas
# ---------------------------------------------------------------------------
FIREFLY_RADIUS = 4.6
FLEETING_RADIUS = 4.2
FIREFLY_VALUE = 1
FLEETING_VALUE = 3            # la fugaz vale el triple
FIREFLY_HALOS = ((4.8, 0.08), (3.1, 0.16), (1.9, 0.32))
FIREFLY_WANDER_SPEED = 26     # velocidad al pasear
FIREFLY_WANDER_TURN = 2       # cuánto cambia de dirección al pasear
FIREFLY_FADE_IN_SPEED = 2.5   # qué tan rápido se enciende
FIREFLY_FADE_OUT_TIME = 0.9   # las decorativas se apagan en este tiempo
MAGNET_RANGE = 320
MAGNET_SPEED = 340
FLEETING_FLEE_RANGE = 220
FLEETING_FLEE_SPEED = 240
SCATTER_FRICTION = 2.5
SCATTER_TIME = 0.7            # segundos volando sueltas tras un golpe
SCATTER_SPEED = (250, 450)
DELIVERY_FOLLOW = 7           # qué tan rápido vuelan al nido
DELIVERY_REACH = 5            # a esta distancia se considera que llegó
DELIVERY_STAGGER = 0.05       # entran al nido una detrás de otra
DELIVERY_SHRINK_DISTANCE = 60
FIREFLY_SWAY_FREE = 9         # vaivén cuando está libre
FIREFLY_SWAY_OTHER = 2        # vaivén en la cola o volando

# ---------------------------------------------------------------------------
# Nido
# ---------------------------------------------------------------------------
NEST_RADIUS = 40
NEST_HALOS = ((2.2, 0.05), (1.6, 0.08), (1.15, 0.12))
NEST_ORBIT_DOTS = 8
NEST_ORBIT_SPEED = 0.8
NEST_FLASH_DECAY = 1.5
NEST_MIN_DISTANCE_FROM_PLAYER = 320
NEST_AREA_X = (0.08, 0.92)    # zona relativa donde puede aparecer
NEST_AREA_Y = (0.12, 0.88)
NEST_PLACEMENT_TRIES = 30

# ---------------------------------------------------------------------------
# Murciélagos
# ---------------------------------------------------------------------------
BAT_SIZE = 17
BAT_RADIUS = 15               # radio de colisión
BAT_MAX_TURN = 2.0            # radianes por segundo que puede girar
BAT_SPEED_WOBBLE = 0.12       # la rapidez varía un poco
BAT_STUN_TIME = 0.8           # después de golpear, se aleja un momento
BAT_STUN_SPEED_BOOST = 1.3
BAT_SPAWN_MIN_DISTANCE = 350
BAT_SPAWN_TRIES = 20

# ---------------------------------------------------------------------------
# Power-ups
# ---------------------------------------------------------------------------
POWERUP_MOON = 'moon'         # congela a los murciélagos
POWERUP_STAR = 'star'         # imán de luciérnagas
POWERUP_HEART = 'heart'       # +1 vida
POWERUP_COLORS = {POWERUP_MOON: ICE_BLUE, POWERUP_STAR: GOLD, POWERUP_HEART: PINK}
POWERUP_RADIUS = 13
POWERUP_LIFETIME = 6.0        # segundos que dura en el mapa
POWERUP_WARNING_TIME = 1.5    # parpadea cuando le queda este tiempo
POWERUP_HALOS = ((3.0, 0.08), (1.9, 0.16))
POWERUP_PICKUP_REACH = 20
POWERUP_FIRST_SPAWN = (8, 12)  # segundos hasta el primer power-up
POWERUP_SPAWN_DELAY = (9, 14)  # segundos entre power-ups
POWERUP_SPAWN_MIN_DISTANCE = 180
FREEZE_DURATION = 4.0          # luna azul
MAGNET_DURATION = 5.0          # estrella dorada

# ---------------------------------------------------------------------------
# Partida
# ---------------------------------------------------------------------------
MAX_LIVES = 3
MAX_TAIL = 15
INITIAL_FIREFLIES = 6
FIREFLY_SPAWN_INTERVAL = 0.7
FLEETING_CHANCE = 0.15
FIREFLY_SPAWN_MIN_DISTANCE = 150
SPAWN_TRIES = 20
FIREFLY_PICKUP_REACH = 20
TAIL_SPACING = 22             # distancia entre luciérnagas de la cola
TAIL_FOLLOW = 12              # qué tan rápido se acomoda la cola
PLAY_AREA_MARGIN = 30
HUD_BAND_HEIGHT = 110         # franja de arriba reservada para el HUD
FLOATING_TEXT_TOP_GAP = 70    # los textos no suben hasta el HUD
NIGHT_BANNER_DURATION = 2.6
NIGHT_BANNER_FADE_IN = 0.5
NIGHT_BANNER_FADE_OUT = 0.6
NIGHT_CHANGE_DELAY = 1.0      # espera tras la entrega antes del cartel
GAME_OVER_DELAY = 1.6

# Cantidad de chispas de cada efecto
DASH_BURST_PARTICLES = 10
DASH_TRAIL_SPEED = (10, 40)
DASH_TRAIL_LIFE = (0.3, 0.5)
DELIVERY_PARTICLES = 4
HIT_PARTICLES = 12
POWERUP_PARTICLES = 10
DEATH_PARTICLES = 30
DEATH_PARTICLE_SPEED = (80, 260)
DEATH_PARTICLE_LIFE = (0.8, 1.4)

# ---------------------------------------------------------------------------
# Noches (dificultad)
# ---------------------------------------------------------------------------
FIRST_NIGHT_GOAL = 10         # Noche 1: 10 luciérnagas
GOAL_INCREASE_PER_NIGHT = 5   # y 5 más cada noche
EXTRA_BATS = 1                # murciélagos = noche + EXTRA_BATS
BAT_BASE_SPEED = 105          # dp por segundo en la Noche 1
BAT_SPEED_INCREASE = 0.09     # 9 % más rápidos cada noche
BAT_MAX_SPEED_FACTOR = 1.8    # tope para que sea justo
FLEETING_MIN_NIGHT = 4        # desde esta noche aparece la fugaz
FREE_FIREFLIES_BASE = 7       # luciérnagas libres = base + noche
FREE_FIREFLIES_MAX = 14
# Multiplicador de la entrega: (mínimo de luciérnagas, multiplicador),
# de mayor a menor.
DELIVERY_MULTIPLIERS = ((10, 3), (5, 2))

# ---------------------------------------------------------------------------
# Efectos
# ---------------------------------------------------------------------------
SHAKE_STRENGTH = 10           # dp que se mueve el mundo en la sacudida
SHAKE_DECAY = 2.5
PARTICLE_SPEED = (50, 150)
PARTICLE_LIFE = (0.5, 0.9)
PARTICLE_SIZE = (1.5, 3)
PARTICLE_FRICTION = 3
PARTICLE_RISE = 15            # las chispas suben un poquito, como flotando
FLOATING_TEXT_SIZE = 24       # en sp
FLOATING_TEXT_RISE = 50
FLOATING_TEXT_DURATION = 1.0
FLASH_RING_RADIUS = 90
FLASH_RING_DURATION = 0.6
PICKUP_RING_RADIUS = 28
PICKUP_RING_DURATION = 0.35
DELIVERY_RINGS = ((110, 0.6), (160, 0.9))  # (radio, duración)
POWERUP_RING = (70, 0.5)

# ---------------------------------------------------------------------------
# Menús
# ---------------------------------------------------------------------------
SWARM_MAX = 14                # luciérnagas de adorno a la vez
SWARM_LIFETIME = (3.0, 6.0)
SWARM_SPAWN_DELAY = (0.2, 0.6)
SWARM_FLEETING_CHANCE = 0.12
KEY_SIZE = 44                 # tamaño de las teclas dibujadas
KEY_SPACING = 6
BUTTON_MAX_RADIUS = 28
# Opacidad del fondo y del borde del botón: (normal, mouse encima, presionado)
BUTTON_FILL_PRIMARY = (0.14, 0.24, 0.34)
BUTTON_FILL_NORMAL = (0.07, 0.15, 0.24)
BUTTON_BORDER = (0.5, 0.85, 1.0)


def apply_window_config():
    """Configura la ventana de Kivy. Debe llamarse ANTES de importar el
    resto de Kivy, porque la ventana se crea en cuanto se importa
    kivy.core.window."""
    from kivy.config import Config

    Config.set('graphics', 'width', str(WINDOW_WIDTH))
    Config.set('graphics', 'height', str(WINDOW_HEIGHT))
    Config.set('graphics', 'resizable', '1')
    # Evita que el clic derecho dibuje puntos rojos (simulación multitáctil).
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    # Por defecto Kivy cierra la app con ESC; aquí ESC sirve para pausar.
    Config.set('kivy', 'exit_on_escape', '0')
