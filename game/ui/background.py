"""
Fondo nocturno: cielo con degradado, luna, estrellas que titilan, el agua
del estanque con brillos y los juncos que se mecen.
"""

import math
import random

from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.widget import Widget

from ..config import (BACK_REED_COLOR, BACK_REED_COUNT, BAT_COLOR, CREAM,
                      DARK_PURPLE, DEEP_PURPLE, FRONT_REED_COUNT,
                      HORIZON_HEIGHT, LATE_NIGHT_BLUE, MOON_HALOS,
                      MOON_POS_DEFAULT, MOON_RADIUS, MOON_REFLECTION_LINES,
                      NIGHT_BLUE, REED_FLOWER_CHANCE, REED_SEGMENTS,
                      SCENERY_SEED, SHORE_COLOR, SHORE_HEIGHT,
                      SKY_TEXTURE_HEIGHT, SKY_TINT_PER_NIGHT, STAR_COUNT,
                      WATER_SPARKLE_COUNT, WATER_VEIL_COLOR)
from ..drawing import mix, set_circle

_sky_textures = {}  # caché: una textura por tono de cielo


def get_sky_texture(night=1):
    """Crea una textura de 1 x 256 píxeles con el degradado del cielo.
    Al estirarla sobre un rectángulo del tamaño de la pantalla, la tarjeta
    gráfica interpola los colores y queda un degradado suave.
    Cada noche el cielo es un poco más morado."""
    tint = round(min(1.0, (night - 1) * SKY_TINT_PER_NIGHT), 2)
    if tint not in _sky_textures:
        bottom = mix(DARK_PURPLE, DEEP_PURPLE, tint)
        top = mix(NIGHT_BLUE, LATE_NIGHT_BLUE, tint)
        height = SKY_TEXTURE_HEIGHT
        texture = Texture.create(size=(1, height), colorfmt='rgba')
        data = bytearray()
        for row in range(height):  # la fila 0 de la textura es la de ABAJO
            t = row / (height - 1)
            for channel in range(3):
                data.append(int((bottom[channel] * (1 - t) + top[channel] * t) * 255))
            data.append(255)  # canal alfa (opaco)
        texture.blit_buffer(bytes(data), colorfmt='rgba', bufferfmt='ubyte')
        texture.mag_filter = 'linear'
        texture.min_filter = 'linear'
        texture.wrap = 'clamp_to_edge'
        _sky_textures[tint] = texture
    return _sky_textures[tint]


class NightBackground(Widget):
    """Dibuja el paisaje nocturno.

    Las posiciones se guardan en valores RELATIVOS (0..1) y se convierten a
    píxeles en rebuild(), así el dibujo se adapta al tamaño de la ventana.
    moon_pos es la posición relativa de la luna (cambia según la pantalla
    y se puede poner desde el archivo .kv).
    """

    moon_pos = ListProperty(MOON_POS_DEFAULT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.t = 0.0
        self.moon_x = self.moon_y = 0.0
        # Semilla fija: el paisaje es igual en todas las pantallas.
        rng = random.Random(SCENERY_SEED)

        self.stars = [{
            'rx': rng.random(),
            'ry': rng.uniform(0.32, 0.99),
            'radius': rng.uniform(0.6, 1.8),
            'phase': rng.uniform(0, math.tau),
            'speed': rng.uniform(0.4, 1.4),  # titilan lentamente
        } for _ in range(STAR_COUNT)]

        self.sparkles = [{
            'rx': rng.random(),
            'ry': rng.uniform(0.04, 0.21),
            'length': rng.uniform(0.02, 0.07),
            'phase': rng.uniform(0, math.tau),
            'speed': rng.uniform(0.5, 1.2),
        } for _ in range(WATER_SPARKLE_COUNT)]

        # Juncos: una capa de atrás (más clara y baja) y otra de adelante
        # (más oscura y alta), así se ve profundidad.
        self.reeds = []
        for in_front, count in ((False, BACK_REED_COUNT), (True, FRONT_REED_COUNT)):
            for _ in range(count):
                self.reeds.append({
                    'rx': rng.uniform(-0.01, 1.01),
                    'height': rng.uniform(0.09, 0.22) if in_front
                    else rng.uniform(0.05, 0.13),
                    'lean': rng.uniform(-0.025, 0.025),
                    'width': dp(rng.uniform(3.5, 6.5)),
                    'phase': rng.uniform(0, math.tau),
                    'speed': rng.uniform(0.6, 1.1),
                    'color': BAT_COLOR + (1,) if in_front else BACK_REED_COLOR,
                    'flower': in_front and rng.random() < REED_FLOWER_CHANCE,  # espadaña
                })

        # --- Instrucciones de dibujo (el orden define qué queda encima) ---
        with self.canvas:
            Color(1, 1, 1, 1)
            self.sky_rect = Rectangle(texture=get_sky_texture(1))

            for star in self.stars:
                star['color'] = Color(*CREAM, 1)
                star['shape'] = Ellipse()

            # Luna con halos suaves
            self.moon_halos = []
            for factor, alpha in MOON_HALOS:
                Color(*CREAM, alpha)
                self.moon_halos.append((Ellipse(), factor))
            Color(*CREAM, 0.95)
            self.moon = Ellipse()

            # Agua: velo oscuro sobre la parte baja + línea de horizonte
            Color(*WATER_VEIL_COLOR)
            self.water_rect = Rectangle()
            Color(*CREAM, 0.10)
            self.horizon_line = Line(width=dp(1))

            for sparkle in self.sparkles:
                sparkle['color'] = Color(*CREAM, 0)
                sparkle['line'] = Line(width=dp(1))

            # Reflejo de la luna: líneas horizontales debajo de ella
            self.reflections = []
            for _ in range(MOON_REFLECTION_LINES):
                self.reflections.append((Color(*CREAM, 0), Line(width=dp(1.4))))

            # Juncos: cada uno es una malla (Mesh) con forma de hoja
            for reed in self.reeds:
                Color(*reed['color'])
                reed['mesh'] = Mesh(mode='triangle_strip')
                if reed['flower']:
                    reed['ellipse'] = Ellipse()

            Color(*SHORE_COLOR)  # orilla en el borde inferior
            self.shore_rect = Rectangle()

        self.bind(pos=self.rebuild, size=self.rebuild, moon_pos=self.rebuild)

    def set_night(self, night):
        """Cambia el tono del cielo según la noche."""
        self.sky_rect.texture = get_sky_texture(night)

    def rebuild(self, *args):
        """Recalcula las partes que solo dependen del tamaño de la ventana."""
        x, y, width, height = self.x, self.y, self.width, self.height
        horizon = y + height * HORIZON_HEIGHT

        self.sky_rect.pos = self.pos
        self.sky_rect.size = self.size

        self.moon_x = x + width * self.moon_pos[0]
        self.moon_y = y + height * self.moon_pos[1]
        radius = dp(MOON_RADIUS)
        set_circle(self.moon, self.moon_x, self.moon_y, radius)
        for ellipse, factor in self.moon_halos:
            set_circle(ellipse, self.moon_x, self.moon_y, radius * factor)

        self.water_rect.pos = self.pos
        self.water_rect.size = (width, horizon - y)
        self.horizon_line.points = [x, horizon, x + width, horizon]
        self.shore_rect.pos = self.pos
        self.shore_rect.size = (width, dp(SHORE_HEIGHT))

        for reed in self.reeds:
            reed['mesh'].indices = list(range(2 * (REED_SEGMENTS + 1)))
        self.update(0)

    def update(self, dt):
        """Avanza las animaciones del fondo. Lo llama el bucle de cada
        pantalla (así no hay un Clock extra corriendo)."""
        self.t += dt
        t = self.t
        x, y, width, height = self.x, self.y, self.width, self.height
        horizon = y + height * HORIZON_HEIGHT

        # Estrellas: la opacidad sube y baja con una onda seno.
        for star in self.stars:
            glow = 0.5 + 0.5 * math.sin(t * star['speed'] + star['phase'])
            star['color'].a = 0.25 + 0.75 * glow
            set_circle(star['shape'], x + star['rx'] * width, y + star['ry'] * height,
                       dp(star['radius']))

        # Brillos del agua: se desplazan un poco y aparecen/desaparecen.
        for sparkle in self.sparkles:
            sx = x + sparkle['rx'] * width + math.sin(t * 0.3 + sparkle['phase']) * dp(8)
            sy = y + sparkle['ry'] * height
            sparkle['color'].a = 0.03 + 0.09 * (0.5 + 0.5 * math.sin(t * sparkle['speed']
                                                                     + sparkle['phase']))
            sparkle['line'].points = [sx, sy, sx + sparkle['length'] * width, sy]

        # Reflejo de la luna: líneas cada vez más cortas hacia abajo.
        for i, (color, line) in enumerate(self.reflections):
            ry = horizon - dp(8) - i * dp(9)
            half = dp(28) * (1 - i * 0.11)
            wave = math.sin(t * 1.3 + i * 0.9) * dp(3)
            color.a = (0.22 - i * 0.025) * (0.75 + 0.25 * math.sin(t * 2 + i))
            line.points = [self.moon_x - half + wave, ry,
                           self.moon_x + half + wave, ry]

        for reed in self.reeds:
            self._draw_reed(reed)

    def _draw_reed(self, reed):
        """Construye la hoja del junco como una tira de triángulos que sigue
        una curva de Bézier cuadrática y se afina hacia la punta."""
        x0 = self.x + reed['rx'] * self.width
        y0 = self.y
        height = reed['height'] * self.height
        sway = math.sin(self.t * reed['speed'] + reed['phase']) * dp(4)
        x2 = x0 + reed['lean'] * self.width + sway  # punta
        y1 = y0 + height * 0.55                      # punto de control
        y2 = y0 + height

        def point(s):
            # Fórmula de Bézier: (1-s)²·P0 + 2(1-s)s·P1 + s²·P2
            px = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * x0 + s * s * x2
            py = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * y1 + s * s * y2
            return px, py

        vertices = []
        for i in range(REED_SEGMENTS + 1):
            s = i / REED_SEGMENTS
            px, py = point(s)
            half = reed['width'] * (1 - s) / 2
            # Mesh usa 4 valores por vértice: x, y, u, v (u, v no se usan).
            vertices += [px - half, py, 0, 0, px + half, py, 0, 0]
        reed['mesh'].vertices = vertices

        if reed['flower']:
            px, py = point(0.78)
            reed['ellipse'].pos = (px - dp(3.5), py - dp(10))
            reed['ellipse'].size = (dp(7), dp(20))
