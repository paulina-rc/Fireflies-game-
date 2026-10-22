# -*- coding: utf-8 -*-
"""
Luciérnagas
===========
Juego para computadora hecho con Kivy. Eres un espíritu de luz que vuela
sobre un estanque de noche: junta luciérnagas en una cola (como una
serpiente de luz) y llévalas al nido, esquivando a los murciélagos.

Todo se dibuja con el canvas de Kivy: no hay imágenes ni sonidos externos.

Estructura del archivo:
  1. Configuración de la ventana y constantes.
  2. Funciones de ayuda (colores, degradado del cielo, dibujos simples).
  3. FondoNocturno: cielo, estrellas, luna, agua y juncos.
  4. Elementos del juego: Jugador, Luciernaga, Nido, Murcielago, PowerUp.
  5. Efectos visuales: Particula, TextoFlotante, AnilloDestello.
  6. GestorNiveles: reglas de cada "Noche".
  7. Widgets de interfaz: botones con hover, teclas, HUD, pausa...
  8. Pantallas: Menú, Cómo jugar, Juego y Fin de partida.
  9. LuciernagasApp: crea las pantallas, F11 y el récord.
"""

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA VENTANA
# ---------------------------------------------------------------------------
# Debe hacerse ANTES de importar el resto de Kivy, porque la ventana se crea
# en cuanto se importa kivy.core.window.
from kivy.config import Config

Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', '1')
# Evita que el clic derecho dibuje puntos rojos (simulación multitáctil).
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
# Por defecto Kivy cierra la app con ESC; aquí ESC sirve para pausar.
Config.set('kivy', 'exit_on_escape', '0')

import math
import os
import random
from collections import deque

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, Mesh,
                           PopMatrix, PushMatrix, Rectangle,
                           RoundedRectangle, Scale, Translate, Triangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.storage.jsonstore import JsonStore
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.widget import Widget


# ---------------------------------------------------------------------------
# 2. FUNCIONES DE AYUDA Y CONSTANTES
# ---------------------------------------------------------------------------
def hex_a_rgb(codigo):
    """Convierte un color '#RRGGBB' a una tupla (r, g, b) con valores 0..1,
    que es el formato que usa Kivy."""
    codigo = codigo.lstrip('#')
    return tuple(int(codigo[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def mezclar(color_a, color_b, t):
    """Mezcla dos colores: t=0 da color_a, t=1 da color_b."""
    return tuple(a * (1 - t) + b * t for a, b in zip(color_a, color_b))


def poner_circulo(elipse, x, y, radio):
    """Coloca una Ellipse de Kivy como un círculo de centro (x, y)."""
    elipse.pos = (x - radio, y - radio)
    elipse.size = (radio * 2, radio * 2)


def colocar_corazon(circulo_1, circulo_2, triangulo, cx, cy, r):
    """Un corazón son dos círculos arriba y un triángulo abajo."""
    rc = r * 0.56
    poner_circulo(circulo_1, cx - 0.5 * r, cy + 0.3 * r, rc)
    poner_circulo(circulo_2, cx + 0.5 * r, cy + 0.3 * r, rc)
    triangulo.points = [cx - 1.04 * r, cy + 0.18 * r,
                        cx + 1.04 * r, cy + 0.18 * r,
                        cx, cy - 1.0 * r]


# Paleta de colores
AZUL_NOCHE = hex_a_rgb('#0B1026')     # cielo arriba (Noche 1)
MORADO_OSCURO = hex_a_rgb('#2B1B3F')  # cielo abajo (Noche 1)
AZUL_NOCHE_TARDE = hex_a_rgb('#1C1240')  # cielo arriba en noches avanzadas
MORADO_PROFUNDO = hex_a_rgb('#4B2266')   # cielo abajo en noches avanzadas
AMARILLO = hex_a_rgb('#F7E967')       # luciérnagas
DORADO = hex_a_rgb('#FFC94D')         # luciérnaga fugaz, estrella, combos
AZUL_HIELO = hex_a_rgb('#7FDBFF')     # luna azul, murciélagos congelados
CREMA = hex_a_rgb('#F5F0E6')          # textos
ROSA = hex_a_rgb('#FF7A90')           # corazones
VERDE_HALO = (0.80, 0.95, 0.45)       # halo verdoso de las luciérnagas
LUZ_JUGADOR = (1.0, 0.96, 0.86)       # blanco cálido del espíritu
COLOR_MURCIELAGO = (0.03, 0.025, 0.06)
ROJO_OJOS = (1.0, 0.28, 0.28)

FPS = 60.0
VIDAS_MAXIMAS = 3
COLA_MAXIMA = 15
DURACION_CONGELADO = 4.0  # luna azul
DURACION_IMAN = 5.0       # estrella dorada

# Códigos de teclas de Kivy
TECLAS_ARRIBA = {273, ord('w')}
TECLAS_ABAJO = {274, ord('s')}
TECLAS_IZQUIERDA = {276, ord('a')}
TECLAS_DERECHA = {275, ord('d')}
TECLA_ESPACIO = 32
TECLA_ESC = 27
TECLA_F11 = 292

_texturas_cielo = {}  # caché: una textura por tono de cielo


def obtener_textura_cielo(noche=1):
    """Crea una textura de 1 x 256 píxeles con el degradado del cielo.
    Al estirarla sobre un rectángulo del tamaño de la pantalla, la tarjeta
    gráfica interpola los colores y queda un degradado suave.
    Cada noche el cielo es un poco más morado."""
    tono = round(min(1.0, (noche - 1) * 0.14), 2)
    if tono not in _texturas_cielo:
        abajo = mezclar(MORADO_OSCURO, MORADO_PROFUNDO, tono)
        arriba = mezclar(AZUL_NOCHE, AZUL_NOCHE_TARDE, tono)
        alto = 256
        textura = Texture.create(size=(1, alto), colorfmt='rgba')
        datos = bytearray()
        for fila in range(alto):  # la fila 0 de la textura es la de ABAJO
            t = fila / (alto - 1)
            for canal in range(3):
                datos.append(int((abajo[canal] * (1 - t) + arriba[canal] * t) * 255))
            datos.append(255)  # canal alfa (opaco)
        textura.blit_buffer(bytes(datos), colorfmt='rgba', bufferfmt='ubyte')
        textura.mag_filter = 'linear'
        textura.min_filter = 'linear'
        textura.wrap = 'clamp_to_edge'
        _texturas_cielo[tono] = textura
    return _texturas_cielo[tono]


def crear_etiqueta(texto, tam, color=CREMA, alfa=1.0, negrita=False,
                   halign='center', valign='middle', **kwargs):
    """Crea un Label cuyo texto se alinea dentro de su propio tamaño
    (por eso se enlaza text_size con size)."""
    etiqueta = Label(text=texto, font_size=tam, color=(*color, alfa),
                     bold=negrita, halign=halign, valign=valign,
                     markup=True, **kwargs)
    etiqueta.bind(size=lambda inst, valor: setattr(inst, 'text_size', valor))
    return etiqueta


# ---------------------------------------------------------------------------
# 3. FONDO NOCTURNO
# ---------------------------------------------------------------------------
class FondoNocturno(Widget):
    """Dibuja el paisaje: cielo con degradado, luna, estrellas que titilan,
    el agua del estanque con brillos y los juncos que se mecen.

    Las posiciones se guardan en valores RELATIVOS (0..1) y se convierten a
    píxeles en reconstruir(), así el dibujo se adapta al tamaño de la ventana.
    """

    ALTURA_HORIZONTE = 0.24  # el agua ocupa el 24 % inferior

    def __init__(self, luna=(0.83, 0.74), **kwargs):
        super().__init__(**kwargs)
        self.t = 0.0
        self.luna_relativa = luna  # posición de la luna (cambia según la pantalla)
        # Semilla fija: el paisaje es igual en todas las pantallas.
        azar = random.Random(11)

        self.estrellas = [{
            'rx': azar.random(),
            'ry': azar.uniform(0.32, 0.99),
            'radio': azar.uniform(0.6, 1.8),
            'fase': azar.uniform(0, math.tau),
            'vel': azar.uniform(0.4, 1.4),  # titilan lentamente
        } for _ in range(150)]

        self.brillos = [{
            'rx': azar.random(),
            'ry': azar.uniform(0.04, 0.21),
            'largo': azar.uniform(0.02, 0.07),
            'fase': azar.uniform(0, math.tau),
            'vel': azar.uniform(0.5, 1.2),
        } for _ in range(28)]

        # Juncos: una capa de atrás (más clara y baja) y otra de adelante
        # (más oscura y alta), así se ve profundidad.
        self.juncos = []
        for capa, cantidad in (('atras', 36), ('adelante', 44)):
            adelante = capa == 'adelante'
            for _ in range(cantidad):
                self.juncos.append({
                    'rx': azar.uniform(-0.01, 1.01),
                    'alto': azar.uniform(0.09, 0.22) if adelante
                    else azar.uniform(0.05, 0.13),
                    'inclina': azar.uniform(-0.025, 0.025),
                    'ancho': dp(azar.uniform(3.5, 6.5)),
                    'fase': azar.uniform(0, math.tau),
                    'vel': azar.uniform(0.6, 1.1),
                    'color': COLOR_MURCIELAGO + (1,) if adelante
                    else (0.10, 0.075, 0.17, 1),
                    'flor': adelante and azar.random() < 0.35,  # espadaña
                })

        # --- Instrucciones de dibujo (el orden define qué queda encima) ---
        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect_cielo = Rectangle(texture=obtener_textura_cielo(1))

            for estrella in self.estrellas:
                estrella['color'] = Color(*CREMA, 1)
                estrella['forma'] = Ellipse()

            # Luna con halos suaves
            self.halos_luna = []
            for factor, alfa in ((3.4, 0.04), (2.3, 0.07), (1.6, 0.12)):
                Color(*CREMA, alfa)
                self.halos_luna.append((Ellipse(), factor))
            Color(*CREMA, 0.95)
            self.luna = Ellipse()

            # Agua: velo oscuro sobre la parte baja + línea de horizonte
            Color(0.02, 0.03, 0.10, 0.55)
            self.rect_agua = Rectangle()
            Color(*CREMA, 0.10)
            self.linea_horizonte = Line(width=dp(1))

            for brillo in self.brillos:
                brillo['color'] = Color(*CREMA, 0)
                brillo['linea'] = Line(width=dp(1))

            # Reflejo de la luna: líneas horizontales debajo de ella
            self.reflejos = []
            for _ in range(7):
                self.reflejos.append((Color(*CREMA, 0), Line(width=dp(1.4))))

            # Juncos: cada uno es una malla (Mesh) con forma de hoja
            for junco in self.juncos:
                Color(*junco['color'])
                junco['malla'] = Mesh(mode='triangle_strip')
                if junco['flor']:
                    junco['elipse'] = Ellipse()

            Color(0.015, 0.02, 0.05, 1)  # orilla en el borde inferior
            self.rect_orilla = Rectangle()

        self.bind(pos=self.reconstruir, size=self.reconstruir)

    def cambiar_noche(self, noche):
        """Cambia el tono del cielo según la noche."""
        self.rect_cielo.texture = obtener_textura_cielo(noche)

    def reconstruir(self, *args):
        """Recalcula las partes que solo dependen del tamaño de la ventana."""
        x, y, ancho, alto = self.x, self.y, self.width, self.height
        horizonte = y + alto * self.ALTURA_HORIZONTE

        self.rect_cielo.pos = self.pos
        self.rect_cielo.size = self.size

        self.luna_x = x + ancho * self.luna_relativa[0]
        self.luna_y = y + alto * self.luna_relativa[1]
        radio = dp(22)
        poner_circulo(self.luna, self.luna_x, self.luna_y, radio)
        for elipse, factor in self.halos_luna:
            poner_circulo(elipse, self.luna_x, self.luna_y, radio * factor)

        self.rect_agua.pos = self.pos
        self.rect_agua.size = (ancho, horizonte - y)
        self.linea_horizonte.points = [x, horizonte, x + ancho, horizonte]
        self.rect_orilla.pos = self.pos
        self.rect_orilla.size = (ancho, dp(8))

        for junco in self.juncos:
            junco['malla'].indices = list(range(2 * 9))
        self.actualizar(0)

    def actualizar(self, dt):
        """Avanza las animaciones del fondo. Lo llama el bucle de cada
        pantalla (así no hay un Clock extra corriendo)."""
        self.t += dt
        t = self.t
        x, y, ancho, alto = self.x, self.y, self.width, self.height
        horizonte = y + alto * self.ALTURA_HORIZONTE

        # Estrellas: la opacidad sube y baja con una onda seno.
        for e in self.estrellas:
            brillo = 0.5 + 0.5 * math.sin(t * e['vel'] + e['fase'])
            e['color'].a = 0.25 + 0.75 * brillo
            poner_circulo(e['forma'], x + e['rx'] * ancho, y + e['ry'] * alto,
                          dp(e['radio']))

        # Brillos del agua: se desplazan un poco y aparecen/desaparecen.
        for b in self.brillos:
            bx = x + b['rx'] * ancho + math.sin(t * 0.3 + b['fase']) * dp(8)
            by = y + b['ry'] * alto
            b['color'].a = 0.03 + 0.09 * (0.5 + 0.5 * math.sin(t * b['vel'] + b['fase']))
            b['linea'].points = [bx, by, bx + b['largo'] * ancho, by]

        # Reflejo de la luna: líneas cada vez más cortas hacia abajo.
        for i, (color, linea) in enumerate(self.reflejos):
            ry = horizonte - dp(8) - i * dp(9)
            mitad = dp(28) * (1 - i * 0.11)
            ondula = math.sin(t * 1.3 + i * 0.9) * dp(3)
            color.a = (0.22 - i * 0.025) * (0.75 + 0.25 * math.sin(t * 2 + i))
            linea.points = [self.luna_x - mitad + ondula, ry,
                            self.luna_x + mitad + ondula, ry]

        for junco in self.juncos:
            self._dibujar_junco(junco)

    def _dibujar_junco(self, junco):
        """Construye la hoja del junco como una tira de triángulos que sigue
        una curva de Bézier cuadrática y se afina hacia la punta."""
        x0 = self.x + junco['rx'] * self.width
        y0 = self.y
        alto = junco['alto'] * self.height
        vaiven = math.sin(self.t * junco['vel'] + junco['fase']) * dp(4)
        x2 = x0 + junco['inclina'] * self.width + vaiven  # punta
        y1 = y0 + alto * 0.55                               # punto de control
        y2 = y0 + alto

        def punto(s):
            # Fórmula de Bézier: (1-s)²·P0 + 2(1-s)s·P1 + s²·P2
            px = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * x0 + s * s * x2
            py = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * y1 + s * s * y2
            return px, py

        vertices = []
        for i in range(9):
            s = i / 8
            px, py = punto(s)
            medio = junco['ancho'] * (1 - s) / 2
            # Mesh usa 4 valores por vértice: x, y, u, v (u, v no se usan).
            vertices += [px - medio, py, 0, 0, px + medio, py, 0, 0]
        junco['malla'].vertices = vertices

        if junco['flor']:
            px, py = punto(0.78)
            junco['elipse'].pos = (px - dp(3.5), py - dp(10))
            junco['elipse'].size = (dp(7), dp(20))


# ---------------------------------------------------------------------------
# 4. ELEMENTOS DEL JUEGO
# ---------------------------------------------------------------------------
# Estos objetos NO son widgets: son clases simples que agrupan sus
# instrucciones de dibujo en un InstructionGroup y lo agregan a una "capa".
# Es más liviano que crear un widget por cada luciérnaga.
# Todos tienen x, y, t (tiempo para animar) y un método dibujar().

class Jugador:
    """El espíritu de luz. Se mueve con aceleración y fricción (no se
    detiene de golpe), deja una estela y puede hacer un impulso (dash)."""

    ACELERACION = 2100     # dp por segundo²
    FRICCION = 5.5         # cuánto frena por segundo
    VELOCIDAD_DASH = 1000  # dp por segundo
    DURACION_DASH = 0.17
    ENFRIAMIENTO_DASH = 2.0

    def __init__(self, capa, x, y):
        self.capa = capa
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.dir_x, self.dir_y = 1.0, 0.0  # última dirección de movimiento
        self.radio = dp(11)
        self.t = 0.0
        self.tiempo_dash = 0.0
        self.enfriamiento = 0.0
        self.invulnerable = 0.0
        self.iman = False      # lo activa el juego (halo dorado)
        self.visible = True
        self.estela = deque(maxlen=16)  # últimas posiciones
        self.reloj_estela = 0.0

        self.grupo = InstructionGroup()
        self.puntos_estela = []
        for _ in range(16):
            color, elipse = Color(*LUZ_JUGADOR, 0), Ellipse()
            self.grupo.add(color)
            self.grupo.add(elipse)
            self.puntos_estela.append((color, elipse))
        self.halos = []
        for factor, alfa in ((5.5, 0.06), (3.4, 0.12), (2.0, 0.26)):
            color, elipse = Color(*LUZ_JUGADOR, alfa), Ellipse()
            self.grupo.add(color)
            self.grupo.add(elipse)
            self.halos.append((color, elipse, factor, alfa))
        self.color_nucleo = Color(*LUZ_JUGADOR, 1)
        self.nucleo = Ellipse()
        self.color_centro = Color(1, 1, 1, 1)
        self.centro = Ellipse()
        for instruccion in (self.color_nucleo, self.nucleo,
                            self.color_centro, self.centro):
            self.grupo.add(instruccion)
        capa.add(self.grupo)
        self.dibujar()

    @property
    def en_dash(self):
        return self.tiempo_dash > 0

    @property
    def progreso_dash(self):
        """0 = recién usado, 1 = listo para usar otra vez."""
        return 1 - self.enfriamiento / self.ENFRIAMIENTO_DASH

    def actualizar(self, dt, dx, dy, area):
        """dx, dy = dirección pedida con el teclado (-1, 0 o 1)."""
        self.t += dt
        largo = math.hypot(dx, dy)
        if largo:
            dx, dy = dx / largo, dy / largo  # en diagonal no va más rápido
            self.dir_x, self.dir_y = dx, dy

        if self.tiempo_dash > 0:
            self.tiempo_dash -= dt  # durante el dash no hay control ni fricción
        else:
            # Aceleración: la velocidad cambia de a poco, no de golpe.
            self.vx += dx * dp(self.ACELERACION) * dt
            self.vy += dy * dp(self.ACELERACION) * dt
            # Fricción: en cada cuadro se pierde una parte de la velocidad.
            freno = max(0.0, 1 - self.FRICCION * dt)
            self.vx *= freno
            self.vy *= freno

        self.x += self.vx * dt
        self.y += self.vy * dt

        # No puede salir del área de juego.
        xmin, ymin, xmax, ymax = area
        if not xmin <= self.x <= xmax:
            self.x = min(max(self.x, xmin), xmax)
            self.vx = 0
        if not ymin <= self.y <= ymax:
            self.y = min(max(self.y, ymin), ymax)
            self.vy = 0

        self.enfriamiento = max(0.0, self.enfriamiento - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)

        # Guarda una posición para la estela cada 0.02 s.
        self.reloj_estela += dt
        if self.reloj_estela >= 0.02:
            self.reloj_estela = 0
            self.estela.append((self.x, self.y))

    def intentar_dash(self):
        """Hace el impulso si no está en enfriamiento. Devuelve True si salió."""
        if self.enfriamiento > 0:
            return False
        self.vx = self.dir_x * dp(self.VELOCIDAD_DASH)
        self.vy = self.dir_y * dp(self.VELOCIDAD_DASH)
        self.tiempo_dash = self.DURACION_DASH
        self.enfriamiento = self.ENFRIAMIENTO_DASH
        return True

    def dibujar(self):
        alfa = 1.0
        if not self.visible:
            alfa = 0.0
        elif self.invulnerable > 0 and int(self.t * 14) % 2:
            alfa = 0.3  # parpadeo mientras es invulnerable

        # Estela: círculos más chicos y transparentes mientras más viejos.
        rapidez = min(1.0, math.hypot(self.vx, self.vy) / max(1.0, dp(250)))
        posiciones = list(self.estela)
        for i, (color, elipse) in enumerate(self.puntos_estela):
            if i < len(posiciones):
                fraccion = (i + 1) / len(posiciones)
                px, py = posiciones[i]
                color.a = 0.22 * fraccion * rapidez * alfa
                poner_circulo(elipse, px, py, self.radio * (0.3 + 0.6 * fraccion))
            else:
                color.a = 0

        tono = mezclar(LUZ_JUGADOR, DORADO, 0.7) if self.iman else LUZ_JUGADOR
        latido = 1 + 0.08 * math.sin(self.t * 3)
        if self.en_dash:
            latido *= 1.3
        for color, elipse, factor, alfa_halo in self.halos:
            color.rgba = (*tono, alfa_halo * alfa)
            poner_circulo(elipse, self.x, self.y, self.radio * factor * latido)
        self.color_nucleo.a = alfa
        poner_circulo(self.nucleo, self.x, self.y, self.radio * 0.8)
        self.color_centro.a = alfa
        poner_circulo(self.centro, self.x, self.y, self.radio * 0.45)

    def quitar(self):
        self.capa.remove(self.grupo)


class Luciernaga:
    """Luciérnaga: núcleo brillante + 3 halos que laten.

    Estados posibles:
      'libre'      -> flota por el mapa esperando ser atrapada
      'cola'       -> sigue al jugador en fila (lo maneja JuegoScreen)
      'dispersa'   -> sale volando porque un murciélago golpeó al jugador
      'entregando' -> vuela hacia el nido
    """

    def __init__(self, capa, x, y, fugaz=False, vida=None):
        self.capa = capa
        self.x, self.y = x, y
        self.fugaz = fugaz             # la fugaz huye y vale el triple
        self.valor = 3 if fugaz else 1
        self.color = DORADO if fugaz else AMARILLO
        self.radio = dp(4.2 if fugaz else 4.6)
        self.estado = 'libre'
        self.tiempo_estado = 0.0       # segundos en el estado actual
        self.t = random.uniform(0, 100)
        self.fase = random.uniform(0, math.tau)
        self.angulo = random.uniform(0, math.tau)  # dirección al pasear
        self.vx = self.vy = 0.0
        self.aparicion = 0.0           # 0 -> 1 al encenderse
        self.vida = vida               # solo las decorativas tienen vida
        self.edad = 0.0
        self.retraso = 0.0             # espera antes de volar al nido
        self.escala = 1.0
        self.terminada = False

        color_halo = CREMA if fugaz else VERDE_HALO
        self.grupo = InstructionGroup()
        self.halos = []
        for factor, alfa in ((4.8, 0.08), (3.1, 0.16), (1.9, 0.32)):
            color, elipse = Color(*color_halo, 0), Ellipse()
            self.grupo.add(color)
            self.grupo.add(elipse)
            self.halos.append((color, elipse, factor, alfa))
        self.color_nucleo = Color(*self.color, 0)
        self.nucleo = Ellipse()
        self.color_centro = Color(1, 1, 0.95, 0)
        self.centro = Ellipse()
        for instruccion in (self.color_nucleo, self.nucleo,
                            self.color_centro, self.centro):
            self.grupo.add(instruccion)
        capa.add(self.grupo)
        self.dibujar()

    def cambiar_estado(self, estado):
        self.estado = estado
        self.tiempo_estado = 0.0

    def actualizar(self, dt, area, jugador=None, iman=False, nido=None):
        """Mueve la luciérnaga según su estado. Devuelve 'llego' cuando
        termina de entrar al nido."""
        self.t += dt
        self.edad += dt
        self.tiempo_estado += dt
        self.aparicion = min(1.0, self.aparicion + dt * 2.5)
        evento = None

        if self.estado == 'libre':
            # Pasea: la dirección cambia un poquito al azar.
            self.angulo += random.uniform(-1, 1) * 2 * dt
            mx = math.cos(self.angulo) * dp(26)
            my = math.sin(self.angulo) * dp(26)
            if jugador is not None:
                dx, dy = jugador.x - self.x, jugador.y - self.y
                distancia = max(1.0, math.hypot(dx, dy))
                if iman and distancia < dp(320):
                    # Imán: vuela sola hacia el jugador.
                    mx, my = dx / distancia * dp(340), dy / distancia * dp(340)
                elif self.fugaz and distancia < dp(220):
                    # La fugaz huye en dirección contraria al jugador.
                    mx, my = -dx / distancia * dp(240), -dy / distancia * dp(240)
            self.x += mx * dt
            self.y += my * dt
            if self.vida is not None and self.edad > self.vida + 0.9:
                self.terminada = True

        elif self.estado == 'dispersa':
            self.x += self.vx * dt
            self.y += self.vy * dt
            freno = max(0.0, 1 - 2.5 * dt)
            self.vx *= freno
            self.vy *= freno
            if self.tiempo_estado > 0.7:
                self.cambiar_estado('libre')

        elif self.estado == 'entregando':
            if self.retraso > 0:
                self.retraso -= dt  # salen una detrás de otra
            else:
                dx, dy = nido.x - self.x, nido.y - self.y
                distancia = math.hypot(dx, dy)
                k = min(1.0, dt * 7)  # interpolación: se acerca de a poco
                self.x += dx * k
                self.y += dy * k
                self.escala = max(0.3, min(1.0, distancia / dp(60)))
                if distancia < dp(5):
                    self.terminada = True
                    evento = 'llego'

        # Rebote en los bordes del área (solo cuando vuela suelta).
        if self.estado in ('libre', 'dispersa'):
            xmin, ymin, xmax, ymax = area
            if not xmin <= self.x <= xmax:
                self.x = min(max(self.x, xmin), xmax)
                self.angulo = math.pi - self.angulo
                self.vx = -self.vx
            if not ymin <= self.y <= ymax:
                self.y = min(max(self.y, ymin), ymax)
                self.angulo = -self.angulo
                self.vy = -self.vy

        self.dibujar()
        return evento

    def dibujar(self):
        alfa = self.aparicion
        if self.vida is not None and self.edad > self.vida:
            alfa *= max(0.0, 1 - (self.edad - self.vida) / 0.9)  # se apaga lento
        latido = 1 + 0.18 * math.sin(self.t * 4 + self.fase)   # el halo late
        brillo = 0.85 + 0.15 * math.sin(self.t * 9 + self.fase * 2)
        if self.fugaz:
            brillo *= 0.8 + 0.2 * math.sin(self.t * 20)  # titila nerviosa

        # Vaivén suave con seno y coseno (más amplio cuando está libre).
        amplitud = dp(9) if self.estado == 'libre' else dp(2)
        self.cx = self.x + math.sin(self.t * 1.3 + self.fase) * amplitud
        self.cy = self.y + math.cos(self.t * 1.0 + self.fase * 1.3) * amplitud * 0.6

        r = self.radio * self.escala
        for color, elipse, factor, alfa_halo in self.halos:
            color.a = alfa_halo * alfa * brillo
            poner_circulo(elipse, self.cx, self.cy, r * factor * latido)
        self.color_nucleo.a = alfa
        poner_circulo(self.nucleo, self.cx, self.cy, r)
        self.color_centro.a = alfa * 0.9
        poner_circulo(self.centro, self.cx, self.cy, r * 0.45)

    def quitar(self):
        self.capa.remove(self.grupo)


class Nido:
    """Círculo brillante donde se entregan las luciérnagas. Su posición se
    guarda en valores relativos (rx, ry) para adaptarse a la ventana."""

    def __init__(self, capa):
        self.capa = capa
        self.radio = dp(40)
        self.rx, self.ry = 0.5, 0.5
        self.x = self.y = 0.0
        self.t = 0.0
        self.destello = 0.0  # 1 al entregar, baja hasta 0

        self.grupo = InstructionGroup()
        self.halos = []
        for factor, alfa in ((2.2, 0.05), (1.6, 0.08), (1.15, 0.12)):
            color, elipse = Color(*AMARILLO, alfa), Ellipse()
            self.grupo.add(color)
            self.grupo.add(elipse)
            self.halos.append((elipse, factor))
        self.color_destello = Color(*CREMA, 0)
        self.elipse_destello = Ellipse()
        self.color_anillo = Color(*AMARILLO, 0.7)
        self.anillo = Line(width=dp(2))
        self.color_anillo_interior = Color(*AMARILLO, 0.25)
        self.anillo_interior = Line(width=dp(1.2))
        for instruccion in (self.color_destello, self.elipse_destello,
                            self.color_anillo, self.anillo,
                            self.color_anillo_interior, self.anillo_interior):
            self.grupo.add(instruccion)
        # Puntitos que giran alrededor del nido
        self.color_orbita = Color(*CREMA, 0.8)
        self.grupo.add(self.color_orbita)
        self.orbita = [Ellipse() for _ in range(8)]
        for punto in self.orbita:
            self.grupo.add(punto)
        capa.add(self.grupo)

    def mover(self, area, evitar=None):
        """Elige un lugar nuevo, lejos de 'evitar' (la posición del jugador)."""
        xmin, ymin, xmax, ymax = area
        for _ in range(30):
            rx, ry = random.uniform(0.08, 0.92), random.uniform(0.12, 0.88)
            x = xmin + rx * (xmax - xmin)
            y = ymin + ry * (ymax - ymin)
            if evitar is None or math.hypot(x - evitar[0], y - evitar[1]) > dp(320):
                break
        self.rx, self.ry = rx, ry

    def actualizar(self, dt, area):
        self.t += dt
        self.destello = max(0.0, self.destello - dt * 1.5)
        xmin, ymin, xmax, ymax = area
        self.x = xmin + self.rx * (xmax - xmin)
        self.y = ymin + self.ry * (ymax - ymin)
        self.dibujar()

    def dibujar(self):
        pulso = 0.85 + 0.15 * math.sin(self.t * 2.5)
        r = self.radio * (1 + 0.15 * self.destello)
        for elipse, factor in self.halos:
            poner_circulo(elipse, self.x, self.y, r * factor * pulso)
        # Destello: un disco claro que crece y se apaga al entregar.
        self.color_destello.a = 0.45 * self.destello
        poner_circulo(self.elipse_destello, self.x, self.y,
                      r * (1.0 + (1 - self.destello) * 0.8))
        self.color_anillo.a = 0.55 + 0.3 * pulso + 0.3 * self.destello
        self.anillo.circle = (self.x, self.y, r)
        self.anillo_interior.circle = (self.x, self.y, r * 0.68)
        for k, punto in enumerate(self.orbita):
            angulo = self.t * 0.8 + k * math.tau / len(self.orbita)
            poner_circulo(punto, self.x + math.cos(angulo) * r * 1.12,
                          self.y + math.sin(angulo) * r * 1.12, dp(2.2))

    def quitar(self):
        self.capa.remove(self.grupo)


class Murcielago:
    """Enemigo: silueta con alas que aletean (mallas de triángulos) y ojos
    rojos. Persigue al jugador girando poco a poco, así se puede esquivar."""

    GIRO_MAXIMO = 2.0  # radianes por segundo que puede girar

    # Contorno de un ala (lado derecho), en unidades del tamaño del murciélago.
    # Cada punto es (x, y, cuánto se mueve con el aleteo).
    ALA = [(0.25, 0.22, 0.00), (0.95, 0.42, 0.45), (1.70, 0.30, 0.70),
           (1.40, -0.10, 0.50), (1.10, 0.02, 0.35), (0.80, -0.22, 0.25),
           (0.50, -0.05, 0.12), (0.25, -0.22, 0.00)]

    def __init__(self, capa, x, y, velocidad):
        self.capa = capa
        self.x, self.y = x, y
        self.velocidad = velocidad
        self.tam = dp(17)
        self.radio = dp(15)   # radio de colisión
        self.angulo = random.uniform(0, math.tau)
        self.t = random.uniform(0, 10)
        self.aturdido = 0.0   # después de golpear, se aleja un momento
        self.congelado = False

        self.grupo = InstructionGroup()
        self.color_brillo = Color(0.5, 0.3, 0.75, 0.16)  # aura para que se vea
        self.brillo = Ellipse()
        self.color_cuerpo = Color(*COLOR_MURCIELAGO, 1)
        self.ala_izquierda = Mesh(mode='triangle_fan')
        self.ala_derecha = Mesh(mode='triangle_fan')
        indices = list(range(len(self.ALA) + 1))
        self.ala_izquierda.indices = indices
        self.ala_derecha.indices = indices
        self.cuerpo = Ellipse()
        self.cabeza = Ellipse()
        self.oreja_izquierda = Triangle()
        self.oreja_derecha = Triangle()
        self.color_brillo_ojos = Color(*ROJO_OJOS, 0.35)
        self.brillo_ojos = [Ellipse(), Ellipse()]
        self.color_ojos = Color(*ROJO_OJOS, 1)
        self.ojos = [Ellipse(), Ellipse()]
        for instruccion in (self.color_brillo, self.brillo, self.color_cuerpo,
                            self.ala_izquierda, self.ala_derecha, self.cuerpo,
                            self.cabeza, self.oreja_izquierda,
                            self.oreja_derecha, self.color_brillo_ojos,
                            *self.brillo_ojos, self.color_ojos, *self.ojos):
            self.grupo.add(instruccion)
        capa.add(self.grupo)
        self.dibujar()

    def actualizar(self, dt, objetivo_x, objetivo_y, area):
        if not self.congelado:
            self.t += dt
            if self.aturdido > 0:
                self.aturdido -= dt
            else:
                # Giro suave: calcula hacia dónde debería mirar y gira
                # como máximo GIRO_MAXIMO radianes por segundo.
                deseado = math.atan2(objetivo_y - self.y, objetivo_x - self.x)
                diferencia = (deseado - self.angulo + math.pi) % math.tau - math.pi
                giro = self.GIRO_MAXIMO * dt
                self.angulo += max(-giro, min(giro, diferencia))
            rapidez = self.velocidad * (1 + 0.12 * math.sin(self.t * 1.7))
            if self.aturdido > 0:
                rapidez *= 1.3
            self.x += math.cos(self.angulo) * rapidez * dt
            self.y += math.sin(self.angulo) * rapidez * dt
            xmin, ymin, xmax, ymax = area
            if not xmin <= self.x <= xmax:
                self.x = min(max(self.x, xmin), xmax)
                self.angulo = math.pi - self.angulo
            if not ymin <= self.y <= ymax:
                self.y = min(max(self.y, ymin), ymax)
                self.angulo = -self.angulo
        self.dibujar()

    def dibujar(self):
        s = self.tam
        x0 = self.x
        if self.congelado:
            y0, aleteo = self.y, 0.2  # quieto, con las alas a medio abrir
            self.color_cuerpo.rgba = (0.30, 0.50, 0.70, 1)
            self.color_brillo.rgba = (*AZUL_HIELO, 0.22)
            self.color_ojos.rgba = (*AZUL_HIELO, 1)
            self.color_brillo_ojos.rgba = (*AZUL_HIELO, 0.3)
        else:
            y0 = self.y + math.sin(self.t * 6) * dp(3)  # sube y baja al volar
            aleteo = math.sin(self.t * 14)
            self.color_cuerpo.rgba = (*COLOR_MURCIELAGO, 1)
            self.color_brillo.rgba = (0.5, 0.3, 0.75, 0.16)
            self.color_ojos.rgba = (*ROJO_OJOS, 1)
            self.color_brillo_ojos.rgba = (*ROJO_OJOS, 0.35)

        poner_circulo(self.brillo, x0, y0, s * 1.7)

        # Alas: abanico de triángulos desde el hombro hacia el contorno.
        for lado, malla in ((1, self.ala_derecha), (-1, self.ala_izquierda)):
            vertices = [x0 + lado * 0.2 * s, y0, 0, 0]
            for px, py, mov in self.ALA:
                vertices += [x0 + lado * px * s, y0 + (py + mov * aleteo) * s, 0, 0]
            malla.vertices = vertices

        self.cuerpo.pos = (x0 - 0.31 * s, y0 - 0.52 * s)
        self.cuerpo.size = (0.62 * s, 0.95 * s)
        self.cabeza.pos = (x0 - 0.27 * s, y0 + 0.17 * s)
        self.cabeza.size = (0.55 * s, 0.5 * s)
        self.oreja_izquierda.points = [x0 - 0.26 * s, y0 + 0.55 * s,
                                       x0 - 0.06 * s, y0 + 0.6 * s,
                                       x0 - 0.22 * s, y0 + 0.92 * s]
        self.oreja_derecha.points = [x0 + 0.26 * s, y0 + 0.55 * s,
                                     x0 + 0.06 * s, y0 + 0.6 * s,
                                     x0 + 0.22 * s, y0 + 0.92 * s]
        # Los ojos se corren un poquito hacia donde vuela.
        mira = math.cos(self.angulo) * 0.05 * s
        for lado, ojo, brillo in ((-1, self.ojos[0], self.brillo_ojos[0]),
                                  (1, self.ojos[1], self.brillo_ojos[1])):
            ox, oy = x0 + lado * 0.12 * s + mira, y0 + 0.44 * s
            poner_circulo(brillo, ox, oy, 0.18 * s)
            poner_circulo(ojo, ox, oy, 0.07 * s)

    def quitar(self):
        self.capa.remove(self.grupo)


class PowerUp:
    """Objeto especial que aparece un rato en el mapa:
      'luna'     -> congela a los murciélagos
      'estrella' -> imán de luciérnagas
      'corazon'  -> +1 vida
    """

    DURACION = 6.0
    COLORES = {'luna': AZUL_HIELO, 'estrella': DORADO, 'corazon': ROSA}

    def __init__(self, capa, tipo, x, y):
        self.capa = capa
        self.tipo = tipo
        self.x, self.y = x, y
        self.radio = dp(13)
        self.edad = 0.0
        self.t = 0.0
        self.terminado = False
        color = self.COLORES[tipo]

        self.grupo = InstructionGroup()
        self.halos = []
        for factor, alfa in ((3.0, 0.08), (1.9, 0.16)):
            c, e = Color(*color, alfa), Ellipse()
            self.grupo.add(c)
            self.grupo.add(e)
            self.halos.append((c, e, factor, alfa))
        self.color_forma = Color(*color, 1)
        self.grupo.add(self.color_forma)
        if tipo == 'luna':
            self.malla = Mesh(mode='triangle_strip', indices=list(range(26)))
            self.grupo.add(self.malla)
        elif tipo == 'estrella':
            self.malla = Mesh(mode='triangle_fan', indices=list(range(12)))
            self.grupo.add(self.malla)
        else:
            self.circulo_1, self.circulo_2 = Ellipse(), Ellipse()
            self.triangulo = Triangle()
            for instruccion in (self.circulo_1, self.circulo_2, self.triangulo):
                self.grupo.add(instruccion)
        capa.add(self.grupo)
        self.dibujar()

    def actualizar(self, dt):
        self.edad += dt
        self.t += dt
        if self.edad >= self.DURACION:
            self.terminado = True
        self.dibujar()

    def dibujar(self):
        alfa = min(1.0, self.edad / 0.3)
        if self.DURACION - self.edad < 1.5:
            alfa *= 0.35 + 0.65 * (0.5 + 0.5 * math.cos(self.t * 16))  # aviso
        cx = self.x
        cy = self.y + math.sin(self.t * 2.5) * dp(4)  # flota
        r = self.radio
        latido = 1 + 0.12 * math.sin(self.t * 4)
        for color, elipse, factor, alfa_halo in self.halos:
            color.a = alfa_halo * alfa
            poner_circulo(elipse, cx, cy, r * factor * latido)
        self.color_forma.a = alfa

        if self.tipo == 'luna':
            # Media luna: tira de triángulos entre una media circunferencia
            # (borde de afuera) y una media elipse delgada (borde de adentro).
            vertices = []
            for k in range(13):
                a = -math.pi / 2 + math.pi * k / 12
                vertices += [cx - 0.25 * r + r * math.cos(a), cy + r * math.sin(a), 0, 0,
                             cx - 0.25 * r + 0.35 * r * math.cos(a), cy + r * math.sin(a), 0, 0]
            self.malla.vertices = vertices
        elif self.tipo == 'estrella':
            # Estrella de 5 puntas: abanico desde el centro con radios
            # alternados (punta larga, hueco corto). Gira despacio.
            vertices = [cx, cy, 0, 0]
            for k in range(11):
                a = math.pi / 2 + k * math.pi / 5 + self.t * 0.6
                largo = r * 1.15 if k % 2 == 0 else r * 0.5
                vertices += [cx + math.cos(a) * largo, cy + math.sin(a) * largo, 0, 0]
            self.malla.vertices = vertices
        else:
            colocar_corazon(self.circulo_1, self.circulo_2, self.triangulo,
                            cx, cy, r * 0.95)

    def quitar(self):
        self.capa.remove(self.grupo)


# ---------------------------------------------------------------------------
# 5. EFECTOS VISUALES
# ---------------------------------------------------------------------------
# Cada efecto tiene actualizar(dt), que devuelve False cuando terminó,
# y quitar(), que borra sus dibujos.

class Particula:
    """Chispita que sale disparada, se frena, se encoge y se desvanece."""

    def __init__(self, capa, x, y, color, rapidez=(50, 150), vida=(0.5, 0.9)):
        self.capa = capa
        angulo = random.uniform(0, math.tau)
        velocidad = dp(random.uniform(*rapidez))
        self.vx = math.cos(angulo) * velocidad
        self.vy = math.sin(angulo) * velocidad
        self.x, self.y = x, y
        self.vida = random.uniform(*vida)
        self.edad = 0.0
        self.radio = random.uniform(dp(1.5), dp(3))
        self.grupo = InstructionGroup()
        self.color_brillo = Color(*color, 0.15)
        self.brillo = Ellipse()
        self.color_punto = Color(*color, 1)
        self.punto = Ellipse()
        for instruccion in (self.color_brillo, self.brillo,
                            self.color_punto, self.punto):
            self.grupo.add(instruccion)
        capa.add(self.grupo)
        self.actualizar(0)

    def actualizar(self, dt):
        self.edad += dt
        if self.edad >= self.vida:
            return False
        freno = max(0.0, 1 - 3 * dt)  # rozamiento
        self.vx *= freno
        self.vy *= freno
        self.vy += dp(15) * dt        # sube un poquito, como flotando
        self.x += self.vx * dt
        self.y += self.vy * dt
        progreso = self.edad / self.vida
        r = self.radio * (1 - 0.5 * progreso)
        self.color_punto.a = 1 - progreso
        self.color_brillo.a = 0.15 * (1 - progreso)
        poner_circulo(self.punto, self.x, self.y, r)
        poner_circulo(self.brillo, self.x, self.y, r * 2.2)
        return True

    def quitar(self):
        self.capa.remove(self.grupo)


class TextoFlotante:
    """Texto como "+12" que sube y desaparece. CoreLabel convierte el texto
    en una textura que se dibuja con un Rectangle."""

    def __init__(self, capa, x, y, texto, color, tam=None, duracion=1.0):
        self.capa = capa
        etiqueta = CoreLabel(text=texto, font_size=tam or sp(24), bold=True)
        etiqueta.refresh()
        textura = etiqueta.texture
        self.x = x - textura.width / 2
        self.y = y
        self.duracion = duracion
        self.edad = 0.0
        self.grupo = InstructionGroup()
        self.color = Color(*color, 1)  # tiñe la textura blanca del texto
        self.rect = Rectangle(texture=textura, size=textura.size, pos=(self.x, self.y))
        self.grupo.add(self.color)
        self.grupo.add(self.rect)
        capa.add(self.grupo)

    def actualizar(self, dt):
        self.edad += dt
        progreso = self.edad / self.duracion
        self.rect.pos = (self.x, self.y + dp(50) * progreso)
        self.color.a = max(0.0, 1 - progreso ** 2)
        return progreso < 1

    def quitar(self):
        self.capa.remove(self.grupo)


class AnilloDestello:
    """Anillo que se agranda y se desvanece (al entregar o recoger algo)."""

    def __init__(self, capa, x, y, color, radio_final=None, duracion=0.6):
        self.capa = capa
        self.x, self.y = x, y
        self.radio_final = radio_final or dp(90)
        self.duracion = duracion
        self.edad = 0.0
        self.grupo = InstructionGroup()
        self.color = Color(*color, 0.8)
        self.linea = Line(circle=(x, y, 1), width=dp(2))
        self.grupo.add(self.color)
        self.grupo.add(self.linea)
        capa.add(self.grupo)

    def actualizar(self, dt):
        self.edad += dt
        progreso = min(1.0, self.edad / self.duracion)
        suave = 1 - (1 - progreso) ** 2  # rápido al inicio, lento al final
        self.color.a = 0.8 * (1 - progreso)
        self.linea.circle = (self.x, self.y, max(1.0, self.radio_final * suave))
        return progreso < 1

    def quitar(self):
        self.capa.remove(self.grupo)


# ---------------------------------------------------------------------------
# 6. GESTOR DE NIVELES
# ---------------------------------------------------------------------------
class GestorNiveles:
    """Guarda en qué noche vamos y calcula las reglas de cada noche."""

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.noche = 1
        self.entregadas_noche = 0  # luciérnagas entregadas en esta noche
        self.entregadas_total = 0  # en toda la partida

    def meta_de(self, noche):
        """Noche 1: 10 luciérnagas, y +5 por cada noche."""
        return 10 + 5 * (noche - 1)

    @property
    def meta(self):
        return self.meta_de(self.noche)

    @property
    def cantidad_murcielagos(self):
        return 1 + self.noche  # Noche 1: 2 murciélagos, y uno más cada noche

    @property
    def velocidad_murcielagos(self):
        # Cada noche un 9 % más rápidos (con un tope para que sea justo).
        return dp(105) * min(1.8, 1 + 0.09 * (self.noche - 1))

    @property
    def permite_fugaz(self):
        return self.noche >= 4

    @property
    def maximo_luciernagas_libres(self):
        return min(14, 7 + self.noche)

    def registrar_entrega(self, cantidad):
        """Suma luciérnagas entregadas. Devuelve True si se cumplió la meta."""
        self.entregadas_noche += cantidad
        self.entregadas_total += cantidad
        return self.entregadas_noche >= self.meta

    def siguiente_noche(self):
        self.noche += 1
        self.entregadas_noche = 0


def multiplicador_entrega(cantidad):
    """5 o más luciérnagas: x2. 10 o más: x3."""
    if cantidad >= 10:
        return 3
    if cantidad >= 5:
        return 2
    return 1


# ---------------------------------------------------------------------------
# 7. WIDGETS DE INTERFAZ
# ---------------------------------------------------------------------------
class BotonRedondeado(ButtonBehavior, Label):
    """Botón propio con bordes redondeados y fondo semitransparente.
    ButtonBehavior le da el comportamiento de botón y Label el texto.
    Se ilumina cuando el mouse pasa encima (hover) y al presionarlo."""

    def __init__(self, principal=False, **kwargs):
        kwargs.setdefault('font_size', sp(21))
        kwargs.setdefault('bold', True)
        self.principal = principal
        self.tono = AMARILLO if principal else CREMA
        self.hover = False
        kwargs.setdefault('color', (*self.tono, 1))
        super().__init__(**kwargs)
        with self.canvas.before:
            self.color_fondo = Color()
            self.fondo = RoundedRectangle()
            self.color_borde = Color()
            self.borde = Line(width=dp(1.3))
        self.bind(pos=self._redibujar, size=self._redibujar, state=self._redibujar)
        # Window.mouse_pos cambia cada vez que se mueve el mouse.
        Window.bind(mouse_pos=self._mouse_movido)
        self._redibujar()

    def _mouse_movido(self, ventana, posicion):
        # get_root_window() es None si el botón no está en pantalla
        # (por ejemplo, si su pantalla no es la actual).
        encima = (self.get_root_window() is not None and
                  self.collide_point(*self.to_widget(*posicion)))
        if encima != self.hover:
            self.hover = encima
            self._redibujar()

    def _redibujar(self, *args):
        radio = min(self.height / 2, self.width / 2, dp(28)) * 0.99
        self.fondo.pos = self.pos
        self.fondo.size = self.size
        self.fondo.radius = [radio]
        self.borde.rounded_rectangle = (self.x, self.y, self.width, self.height, radio)
        # Tres niveles de brillo: normal, mouse encima, presionado.
        if self.state == 'down':
            nivel = 2
        elif self.hover:
            nivel = 1
        else:
            nivel = 0
        fondos = (0.14, 0.24, 0.34) if self.principal else (0.07, 0.15, 0.24)
        self.color_fondo.rgba = (*self.tono, fondos[nivel])
        self.color_borde.rgba = (*self.tono, (0.5, 0.85, 1.0)[nivel])


class Tecla(Label):
    """Dibujo de una tecla del teclado: recuadro redondeado con la letra
    adentro (o una flecha dibujada con un triángulo)."""

    def __init__(self, texto='', flecha=None, ancho=1.0, **kwargs):
        lado = dp(44)
        super().__init__(text='' if flecha else texto, size_hint=(None, None),
                         size=(lado * ancho, lado), font_size=sp(16), bold=True,
                         color=(*CREMA, 0.95), **kwargs)
        self.flecha = flecha
        with self.canvas.before:
            Color(0, 0, 0, 0.35)
            self.sombra = RoundedRectangle()
            Color(*CREMA, 0.10)
            self.fondo = RoundedRectangle()
            Color(*CREMA, 0.45)
            self.borde = Line(width=dp(1.1))
            Color(*CREMA, 0.95 if flecha else 0)
            self.triangulo = Triangle()
        self.bind(pos=self._redibujar, size=self._redibujar)

    def _redibujar(self, *args):
        radio = dp(9)
        self.sombra.pos = (self.x, self.y - dp(3))  # da sensación de relieve
        self.sombra.size = self.size
        self.sombra.radius = [radio]
        self.fondo.pos = self.pos
        self.fondo.size = self.size
        self.fondo.radius = [radio]
        self.borde.rounded_rectangle = (self.x, self.y, self.width, self.height, radio)
        if self.flecha:
            cx, cy, r = self.center_x, self.center_y, dp(8)
            puntas = {
                'arriba': [cx - r, cy - r * 0.6, cx + r, cy - r * 0.6, cx, cy + r * 0.8],
                'abajo': [cx - r, cy + r * 0.6, cx + r, cy + r * 0.6, cx, cy - r * 0.8],
                'izquierda': [cx + r * 0.6, cy - r, cx + r * 0.6, cy + r, cx - r * 0.8, cy],
                'derecha': [cx - r * 0.6, cy - r, cx - r * 0.6, cy + r, cx + r * 0.8, cy],
            }
            self.triangulo.points = puntas[self.flecha]


def grupo_de_teclas(teclas):
    """Arma una cruz de teclas: una arriba y tres abajo (como WASD)."""
    lado, espacio = dp(44), dp(6)
    grilla = GridLayout(cols=3, spacing=espacio, size_hint=(None, None),
                        size=(lado * 3 + espacio * 2, lado * 2 + espacio))
    arriba, izquierda, abajo, derecha = teclas
    for tecla in (None, arriba, None, izquierda, abajo, derecha):
        grilla.add_widget(tecla or Widget(size_hint=(None, None), size=(lado, lado)))
    return grilla


class PanelControles(BoxLayout):
    """Panel del menú que muestra los controles dibujados como teclas."""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=dp(24), spacing=dp(16),
                         size_hint=(None, None), size=(dp(500), dp(330)), **kwargs)
        with self.canvas.before:
            Color(0.04, 0.04, 0.11, 0.55)
            self.fondo = RoundedRectangle(radius=[dp(18)])
            Color(*CREMA, 0.15)
            self.borde = Line(width=dp(1))
        self.bind(pos=self._redibujar, size=self._redibujar)

        self.add_widget(crear_etiqueta('Controles', sp(20), negrita=True,
                                       halign='left', size_hint_y=None, height=dp(28)))

        fila = BoxLayout(spacing=dp(14), size_hint_y=None, height=dp(94))
        fila.add_widget(grupo_de_teclas([Tecla('W'), Tecla('A'), Tecla('S'), Tecla('D')]))
        fila.add_widget(crear_etiqueta('o', sp(15), alfa=0.6, size_hint_x=None, width=dp(16)))
        fila.add_widget(grupo_de_teclas([Tecla(flecha='arriba'), Tecla(flecha='izquierda'),
                                         Tecla(flecha='abajo'), Tecla(flecha='derecha')]))
        fila.add_widget(crear_etiqueta('Moverse', sp(16), halign='left'))
        self.add_widget(fila)

        fila = BoxLayout(spacing=dp(14), size_hint_y=None, height=dp(44))
        fila.add_widget(Tecla('Espacio', ancho=4.4))
        fila.add_widget(crear_etiqueta('Impulso (dash)', sp(16), halign='left'))
        self.add_widget(fila)

        fila = BoxLayout(spacing=dp(14), size_hint_y=None, height=dp(44))
        fila.add_widget(Tecla('Esc', ancho=1.3))
        fila.add_widget(crear_etiqueta('Pausa', sp(16), halign='left'))
        fila.add_widget(Tecla('F11', ancho=1.3))
        fila.add_widget(crear_etiqueta('Pantalla completa', sp(16), halign='left'))
        self.add_widget(fila)

    def _redibujar(self, *args):
        self.fondo.pos = self.pos
        self.fondo.size = self.size
        self.borde.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(18))


class IconoCorazon(Widget):
    """Corazón del HUD: lleno (vida disponible) o apagado (vida perdida)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(*ROSA, 1)
            self.circulo_1, self.circulo_2 = Ellipse(), Ellipse()
            self.triangulo = Triangle()
        self.bind(pos=self._redibujar, size=self._redibujar)

    def poner_lleno(self, lleno):
        self.color.rgba = (*ROSA, 1) if lleno else (*CREMA, 0.15)

    def _redibujar(self, *args):
        r = min(self.width, self.height) * 0.45
        colocar_corazon(self.circulo_1, self.circulo_2, self.triangulo,
                        self.center_x, self.center_y, r)


class IndicadorDash(Widget):
    """Arco circular que se llena mientras el dash se recarga."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color_brillo = Color(*AMARILLO, 0)
            self.brillo = Ellipse()
            Color(*CREMA, 0.12)
            self.aro = Line(width=dp(3))
            self.color_arco = Color(*CREMA, 0.7)
            self.arco = Line(width=dp(3.2), cap='round')
        self.texto = crear_etiqueta('', sp(13), negrita=True)
        self.add_widget(self.texto)
        self.progreso = 1.0
        self.bind(pos=self._redibujar, size=self._redibujar)

    def poner_progreso(self, progreso, segundos):
        self.progreso = progreso
        self.texto.text = 'DASH' if progreso >= 1 else f'{segundos:.1f}'
        self._redibujar()

    def _redibujar(self, *args):
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - dp(4)
        self.texto.pos = self.pos
        self.texto.size = self.size
        self.aro.circle = (cx, cy, r)
        listo = self.progreso >= 1
        self.color_arco.rgba = (*AMARILLO, 1) if listo else (*CREMA, 0.75)
        self.texto.color = (*AMARILLO, 1) if listo else (*CREMA, 0.8)
        self.color_brillo.a = 0.14 if listo else 0
        poner_circulo(self.brillo, cx, cy, r * 1.35)
        # Line(circle=(x, y, radio, ángulo_inicio, ángulo_fin)), en grados.
        self.arco.circle = (cx, cy, r, 0, max(1.0, 360 * self.progreso))


class BarraProgreso(Widget):
    """Barra delgada que muestra cuánto falta para la meta de la noche."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progreso = 0.0
        with self.canvas:
            Color(*CREMA, 0.12)
            self.fondo = RoundedRectangle(radius=[dp(3)])
            Color(*AMARILLO, 0.9)
            # Rectangle normal: un RoundedRectangle de ancho 0 no se
            # redibuja bien y la barra quedaba llena.
            self.relleno = Rectangle()
        self.bind(pos=self._redibujar, size=self._redibujar)

    def poner(self, progreso):
        self.progreso = max(0.0, min(1.0, progreso))
        self._redibujar()

    def _redibujar(self, *args):
        self.fondo.pos = self.pos
        self.fondo.size = self.size
        self.relleno.pos = self.pos
        self.relleno.size = (self.width * self.progreso, self.height)


class HUD(FloatLayout):
    """Marcadores del juego, repartidos a lo ancho de la pantalla:
    izquierda = vidas y noche, centro = puntaje y cola, derecha = dash."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # --- Izquierda: vidas y progreso de la noche ---
        caja_vidas = BoxLayout(spacing=dp(8), size_hint=(None, None),
                               size=(dp(3 * 30 + 2 * 8), dp(30)),
                               pos_hint={'x': 0.02, 'top': 0.965})
        self.corazones = [IconoCorazon() for _ in range(VIDAS_MAXIMAS)]
        for corazon in self.corazones:
            caja_vidas.add_widget(corazon)
        self.add_widget(caja_vidas)
        self.etiqueta_noche = crear_etiqueta(
            'NOCHE 1', sp(20), negrita=True, halign='left',
            size_hint=(0.3, None), height=dp(28), pos_hint={'x': 0.02, 'top': 0.905})
        self.etiqueta_meta = crear_etiqueta(
            '', sp(14), alfa=0.75, halign='left',
            size_hint=(0.3, None), height=dp(20), pos_hint={'x': 0.02, 'top': 0.86})
        self.barra = BarraProgreso(size_hint=(0.15, None), height=dp(6),
                                   pos_hint={'x': 0.02, 'top': 0.825})
        for widget in (self.etiqueta_noche, self.etiqueta_meta, self.barra):
            self.add_widget(widget)

        # --- Centro: puntaje, cola y power-ups activos ---
        self.etiqueta_puntos = crear_etiqueta(
            '0', sp(42), negrita=True, size_hint=(0.3, None), height=dp(52),
            pos_hint={'center_x': 0.5, 'top': 0.985})
        self.etiqueta_cola = crear_etiqueta(
            '', sp(15), alfa=0.85, size_hint=(0.4, None), height=dp(22),
            pos_hint={'center_x': 0.5, 'top': 0.905})
        self.etiqueta_estado = crear_etiqueta(
            '', sp(14), size_hint=(0.5, None), height=dp(20),
            pos_hint={'center_x': 0.5, 'top': 0.87})
        for widget in (self.etiqueta_puntos, self.etiqueta_cola, self.etiqueta_estado):
            self.add_widget(widget)

        # --- Derecha: enfriamiento del dash ---
        caja_dash = BoxLayout(spacing=dp(12), size_hint=(None, None),
                              size=(dp(200), dp(66)),
                              pos_hint={'right': 0.975, 'top': 0.965})
        caja_dash.add_widget(crear_etiqueta(
            f'IMPULSO\n[size={int(sp(12))}]tecla Espacio[/size]', sp(14),
            alfa=0.7, halign='right'))
        self.indicador_dash = IndicadorDash(size_hint=(None, None), size=(dp(66), dp(66)))
        caja_dash.add_widget(self.indicador_dash)
        self.add_widget(caja_dash)

    def actualizar(self, juego):
        gestor = juego.gestor
        for i, corazon in enumerate(self.corazones):
            corazon.poner_lleno(i < juego.vidas)
        self.etiqueta_noche.text = f'NOCHE {gestor.noche}'
        self.etiqueta_meta.text = f'{min(gestor.entregadas_noche, gestor.meta)} / {gestor.meta} luciérnagas'
        self.barra.poner(gestor.entregadas_noche / gestor.meta)

        self.etiqueta_puntos.text = str(juego.puntos)
        cantidad = len(juego.cola)
        texto = f'Cola {cantidad} / {COLA_MAXIMA}'
        multiplicador = multiplicador_entrega(cantidad)
        if multiplicador > 1:
            texto += f'   [color=FFC94D][b]x{multiplicador}[/b][/color]'
        self.etiqueta_cola.text = texto

        estados = []
        if juego.congelado > 0:
            estados.append(f'[color=7FDBFF]Murciélagos congelados {juego.congelado:.1f} s[/color]')
        if juego.iman > 0:
            estados.append(f'[color=FFC94D]Imán {juego.iman:.1f} s[/color]')
        self.etiqueta_estado.text = '     '.join(estados)

        jugador = juego.jugador
        self.indicador_dash.poner_progreso(jugador.progreso_dash, jugador.enfriamiento)


class CapaPausa(FloatLayout):
    """Velo oscuro con el menú de pausa. Bloquea los clics al juego."""

    def __init__(self, al_seguir, al_menu, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.03, 0.03, 0.09, 0.75)
            self.velo = Rectangle()
        self.bind(pos=self._ajustar, size=self._ajustar)
        self.add_widget(crear_etiqueta(
            'Pausa', sp(48), negrita=True, size_hint=(1, None), height=dp(60),
            pos_hint={'center_x': 0.5, 'center_y': 0.64}))
        self.add_widget(crear_etiqueta(
            'Presiona Esc para continuar', sp(15), alfa=0.6, size_hint=(1, None),
            height=dp(24), pos_hint={'center_x': 0.5, 'center_y': 0.57}))
        boton_seguir = BotonRedondeado(
            text='Continuar', principal=True, size_hint=(None, None),
            size=(dp(260), dp(56)), pos_hint={'center_x': 0.5, 'center_y': 0.46})
        boton_seguir.bind(on_release=lambda *_: al_seguir())
        boton_menu = BotonRedondeado(
            text='Menú', size_hint=(None, None), size=(dp(260), dp(56)),
            pos_hint={'center_x': 0.5, 'center_y': 0.36})
        boton_menu.bind(on_release=lambda *_: al_menu())
        self.add_widget(boton_seguir)
        self.add_widget(boton_menu)

    def _ajustar(self, *args):
        self.velo.pos = self.pos
        self.velo.size = self.size

    def on_touch_down(self, touch):
        super().on_touch_down(touch)  # los botones sí reciben el clic
        return True                   # pero no pasa al juego


class AvisoNoche(FloatLayout):
    """Cartel "Noche 2" que aparece entre noches (se controla con opacity)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.02, 0.02, 0.07, 0.65)
            self.velo = Rectangle()
        self.bind(pos=self._ajustar, size=self._ajustar)
        self.titulo = crear_etiqueta('', sp(64), color=AMARILLO, negrita=True,
                                     size_hint=(1, None), height=dp(80),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.55})
        self.subtitulo = crear_etiqueta('', sp(19), alfa=0.85, size_hint=(1, None),
                                        height=dp(30),
                                        pos_hint={'center_x': 0.5, 'center_y': 0.45})
        self.add_widget(self.titulo)
        self.add_widget(self.subtitulo)
        self.opacity = 0

    def _ajustar(self, *args):
        self.velo.pos = self.pos
        self.velo.size = self.size


class EnjambreDecorativo(Widget):
    """Luciérnagas de adorno para los menús (con vida limitada)."""

    MAXIMO = 14

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.luciernagas = []
        self.espera = 0.0

    def area(self):
        return (self.x + dp(20), self.y + self.height * 0.15,
                self.right - dp(20), self.top - dp(20))

    def actualizar(self, dt):
        area = self.area()
        self.espera -= dt
        if self.espera <= 0 and len(self.luciernagas) < self.MAXIMO:
            xmin, ymin, xmax, ymax = area
            self.luciernagas.append(Luciernaga(
                self.canvas, random.uniform(xmin, xmax), random.uniform(ymin, ymax),
                fugaz=random.random() < 0.12, vida=random.uniform(3.0, 6.0)))
            self.espera = random.uniform(0.2, 0.6)
        for luciernaga in self.luciernagas[:]:
            luciernaga.actualizar(dt, area)
            if luciernaga.terminada:
                luciernaga.quitar()
                self.luciernagas.remove(luciernaga)

    def limpiar(self):
        for luciernaga in self.luciernagas:
            luciernaga.quitar()
        self.luciernagas = []


class Vitrina(Widget):
    """Muestra un elemento del juego animado (para "Cómo jugar").
    Usa Translate y Scale para dibujarlo centrado y del tamaño deseado."""

    def __init__(self, fabrica, escala=1.0, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            PushMatrix()
            self.traslado = Translate(0, 0)
            Scale(x=escala, y=escala, z=1)
        self.grupo = InstructionGroup()
        self.canvas.add(self.grupo)
        with self.canvas.after:
            PopMatrix()
        self.entidad = fabrica(self.grupo)  # el elemento se dibuja en (0, 0)

    def animar(self, dt):
        # El centro se actualiza en cada cuadro, así siempre sigue al
        # widget aunque la grilla lo reacomode.
        self.traslado.xy = self.center
        self.entidad.t += dt
        self.entidad.x = self.entidad.y = 0
        self.entidad.dibujar()


# ---------------------------------------------------------------------------
# 8. PANTALLAS
# ---------------------------------------------------------------------------
class PantallaAnimada(Screen):
    """Pantalla base con un bucle a 60 FPS que se puede iniciar y detener.
    Guardar el evento del Clock permite cancelarlo después, para que no
    queden procesos corriendo cuando la pantalla no se ve."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.evento_bucle = None

    def iniciar_bucle(self):
        if self.evento_bucle is None:
            self.evento_bucle = Clock.schedule_interval(self.bucle, 1 / FPS)

    def detener_bucle(self):
        if self.evento_bucle is not None:
            self.evento_bucle.cancel()
            self.evento_bucle = None

    def bucle(self, dt):
        pass  # cada pantalla lo redefine


class MenuScreen(PantallaAnimada):
    """Menú principal: título, botones, récord y panel de controles."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = FloatLayout()
        self.add_widget(raiz)
        self.fondo = FondoNocturno(luna=(0.93, 0.84))  # luna fuera del panel
        self.enjambre = EnjambreDecorativo()
        raiz.add_widget(self.fondo)
        raiz.add_widget(self.enjambre)

        # Columna izquierda
        raiz.add_widget(crear_etiqueta(
            'Luciérnagas', sp(76), color=AMARILLO, negrita=True,
            size_hint=(0.55, 0.15), pos_hint={'center_x': 0.3, 'center_y': 0.71}))
        raiz.add_widget(crear_etiqueta(
            'Guía la luz de vuelta a casa', sp(20), alfa=0.8,
            size_hint=(0.55, 0.06), pos_hint={'center_x': 0.3, 'center_y': 0.61}))
        boton_jugar = BotonRedondeado(
            text='Jugar', principal=True, font_size=sp(24), size_hint=(None, None),
            size=(dp(300), dp(62)), pos_hint={'center_x': 0.3, 'center_y': 0.47})
        boton_jugar.bind(on_release=lambda *_: self.ir_a('juego'))
        boton_como = BotonRedondeado(
            text='Cómo jugar', size_hint=(None, None), size=(dp(300), dp(56)),
            pos_hint={'center_x': 0.3, 'center_y': 0.37})
        boton_como.bind(on_release=lambda *_: self.ir_a('como'))
        raiz.add_widget(boton_jugar)
        raiz.add_widget(boton_como)
        self.etiqueta_record = crear_etiqueta(
            '', sp(18), alfa=0.9, size_hint=(0.55, 0.05),
            pos_hint={'center_x': 0.3, 'center_y': 0.27})
        raiz.add_widget(self.etiqueta_record)

        # Columna derecha
        raiz.add_widget(PanelControles(pos_hint={'center_x': 0.73, 'center_y': 0.52}))

    def ir_a(self, nombre):
        self.manager.current = nombre

    def on_pre_enter(self, *args):
        puntos, noche = App.get_running_app().obtener_record()
        self.etiqueta_record.text = (f'Récord: [b]{puntos}[/b] puntos    ·    '
                                     f'Noche máxima: [b]{noche}[/b]')
        self.iniciar_bucle()

    def on_leave(self, *args):
        self.detener_bucle()
        self.enjambre.limpiar()

    def bucle(self, dt):
        dt = min(dt, 0.05)  # evita saltos grandes si la ventana se congela
        self.fondo.actualizar(dt)
        self.enjambre.actualizar(dt)


class ComoJugarScreen(PantallaAnimada):
    """Explica cada elemento con su dibujo animado al lado."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = FloatLayout()
        self.add_widget(raiz)
        self.fondo = FondoNocturno(luna=(0.94, 0.9))
        raiz.add_widget(self.fondo)

        raiz.add_widget(crear_etiqueta(
            'Cómo jugar', sp(44), color=AMARILLO, negrita=True,
            size_hint=(1, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.91}))

        def luciernaga(capa, fugaz=False):
            elemento = Luciernaga(capa, 0, 0, fugaz=fugaz)
            elemento.aparicion = 1.0
            return elemento

        def powerup(tipo):
            def fabrica(capa):
                elemento = PowerUp(capa, tipo, 0, 0)
                elemento.edad = 1.0  # para que no parpadee
                return elemento
            return fabrica

        elementos = [
            (lambda c: Jugador(c, 0, 0), 0.7, 'Tú: espíritu de luz',
             'Muévete con WASD o las flechas. Espacio hace un impulso (dash) que atraviesa murciélagos.'),
            (luciernaga, 1.3, 'Luciérnaga',
             f'Tócala para sumarla a tu cola. La cola te sigue en fila (máximo {COLA_MAXIMA}).'),
            (Nido, 0.6, 'Nido',
             'Entra con tu cola para entregarlas. Con 5 o más ganas x2, con 10 o más x3.'),
            (lambda c: Murcielago(c, 0, 0, 0), 1.0, 'Murciélago',
             'Te persigue. Si te toca pierdes la cola; si no tienes cola, pierdes una vida.'),
            (powerup('luna'), 1.0, 'Luna azul',
             'Congela a los murciélagos por 4 segundos.'),
            (powerup('estrella'), 1.0, 'Estrella dorada',
             'Imán: las luciérnagas cercanas vuelan solas hacia ti por 5 segundos.'),
            (powerup('corazon'), 1.0, 'Corazón',
             'Recupera una vida (máximo 3).'),
            (lambda c: luciernaga(c, fugaz=True), 1.3, 'Luciérnaga fugaz',
             'Aparece desde la Noche 4. Huye de ti, pero vale el triple.'),
        ]

        grilla = GridLayout(cols=2, spacing=(dp(40), dp(10)), size_hint=(0.9, 0.68),
                            pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.vitrinas = []
        for fabrica, escala, titulo, descripcion in elementos:
            fila = BoxLayout(spacing=dp(18))
            vitrina = Vitrina(fabrica, escala, size_hint=(None, 1), width=dp(90))
            self.vitrinas.append(vitrina)
            fila.add_widget(vitrina)
            fila.add_widget(crear_etiqueta(
                f'[b][color=F7E967]{titulo}[/color][/b]\n{descripcion}', sp(15),
                alfa=0.9, halign='left'))
            grilla.add_widget(fila)
        raiz.add_widget(grilla)

        boton_volver = BotonRedondeado(
            text='Volver', size_hint=(None, None), size=(dp(220), dp(52)),
            pos_hint={'center_x': 0.5, 'center_y': 0.08})
        boton_volver.bind(on_release=lambda *_: setattr(self.manager, 'current', 'menu'))
        raiz.add_widget(boton_volver)

    def on_pre_enter(self, *args):
        self.iniciar_bucle()

    def on_leave(self, *args):
        self.detener_bucle()

    def bucle(self, dt):
        dt = min(dt, 0.05)
        self.fondo.actualizar(dt)
        for vitrina in self.vitrinas:
            vitrina.animar(dt)


class JuegoScreen(PantallaAnimada):
    """La partida. Maneja teclado, jugador, cola, nido, murciélagos,
    power-ups, noches, pausa y fin del juego.

    self.estado puede ser:
      'transicion' -> mostrando el cartel "Noche N"
      'jugando'    -> partida normal
      'terminando' -> el jugador perdió; espera un momento y va al final
    """

    DURACION_TRANSICION = 2.6

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = FloatLayout()
        self.add_widget(raiz)
        self.raiz = raiz

        # "mundo" contiene el fondo y el juego. Su Translate se usa para
        # sacudir la pantalla sin mover el HUD.
        self.mundo = FloatLayout()
        with self.mundo.canvas.before:
            PushMatrix()
            self.traslado_sacudida = Translate(0, 0)
        with self.mundo.canvas.after:
            PopMatrix()
        self.fondo = FondoNocturno()
        self.capa = Widget()
        self.mundo.add_widget(self.fondo)
        self.mundo.add_widget(self.capa)
        raiz.add_widget(self.mundo)

        # Capas de dibujo, en orden de abajo hacia arriba.
        self.capas = {}
        for nombre in ('nido', 'luciernagas', 'powerups', 'murcielagos',
                       'jugador', 'efectos'):
            self.capas[nombre] = InstructionGroup()
            self.capa.canvas.add(self.capas[nombre])

        self.hud = HUD()
        raiz.add_widget(self.hud)
        self.aviso = AvisoNoche()
        raiz.add_widget(self.aviso)
        self.capa_pausa = CapaPausa(al_seguir=self.reanudar, al_menu=self.ir_al_menu)

        self.gestor = GestorNiveles()
        self.teclas = set()       # teclas que están presionadas ahora
        self.teclado_activo = False
        self.pausado = False
        self.jugador = None
        self.nido = None
        self.luciernagas = []     # todas las luciérnagas del mapa
        self.cola = []            # las que siguen al jugador, en orden
        self.murcielagos = []
        self.powerup = None
        self.efectos = []

    # ---------- Ciclo de vida de la pantalla ----------
    def on_pre_enter(self, *args):
        self.reiniciar()

    def on_enter(self, *args):
        self.activar_teclado()
        self.iniciar_bucle()

    def on_pre_leave(self, *args):
        # Al salir se detiene todo: bucle, teclado y pausa.
        self.detener_bucle()
        self.desactivar_teclado()
        self.ocultar_pausa()

    def on_leave(self, *args):
        self.limpiar()

    def area(self):
        """Zona donde se puede volar (deja libre la franja del HUD)."""
        ancho, alto = Window.size
        return (dp(30), dp(30), ancho - dp(30), alto - dp(110))

    def reiniciar(self):
        """Deja todo listo para una partida nueva."""
        self.limpiar()
        self.gestor.reiniciar()
        self.puntos = 0
        self.vidas = VIDAS_MAXIMAS
        self.congelado = 0.0          # segundos de murciélagos congelados
        self.iman = 0.0               # segundos de imán
        self.sacudida = 0.0           # intensidad de la sacudida (0..1)
        self.espera_luciernaga = 0.0
        self.espera_powerup = random.uniform(8, 12)
        self.espera_transicion = None  # cuenta atrás tras cumplir la meta
        self.tiempo_fin = 0.0
        self.teclas.clear()
        self.pedir_dash = False
        self.fondo.cambiar_noche(1)
        self.traslado_sacudida.xy = (0, 0)

        xmin, ymin, xmax, ymax = self.area()
        self.nido = Nido(self.capas['nido'])
        self.jugador = Jugador(self.capas['jugador'], (xmin + xmax) / 2, (ymin + ymax) / 2)
        self.nido.mover(self.area(), evitar=(self.jugador.x, self.jugador.y))
        self.nido.actualizar(0, self.area())
        for _ in range(6):
            self.generar_luciernaga()
        self.crear_murcielagos()
        self.iniciar_transicion(avanzar=False)
        self.hud.actualizar(self)

    def limpiar(self):
        """Borra todos los dibujos y listas."""
        for capa in self.capas.values():
            capa.clear()
        self.luciernagas, self.cola, self.murcielagos, self.efectos = [], [], [], []
        self.powerup = None

    # ---------- Teclado ----------
    def activar_teclado(self):
        if not self.teclado_activo:
            Window.bind(on_key_down=self.tecla_abajo, on_key_up=self.tecla_arriba)
            self.teclado_activo = True

    def desactivar_teclado(self):
        if self.teclado_activo:
            Window.unbind(on_key_down=self.tecla_abajo, on_key_up=self.tecla_arriba)
            self.teclado_activo = False
        self.teclas.clear()

    def tecla_abajo(self, ventana, tecla, codigo, texto, modificadores):
        if tecla == TECLA_ESC:
            if self.pausado:
                self.reanudar()
            else:
                self.pausar()
            return True  # True = "ya lo manejé"
        if self.pausado:
            return False
        # Al mantener una tecla, Kivy repite el evento; el dash solo se
        # pide la primera vez (cuando todavía no estaba en el set).
        if tecla == TECLA_ESPACIO and tecla not in self.teclas:
            self.pedir_dash = True
        self.teclas.add(tecla)
        return False  # deja pasar otras teclas (como F11)

    def tecla_arriba(self, ventana, tecla, codigo):
        self.teclas.discard(tecla)
        return False

    def direccion_teclado(self):
        """Convierte las teclas presionadas en una dirección (dx, dy)."""
        dx = (1 if self.teclas & TECLAS_DERECHA else 0) - (1 if self.teclas & TECLAS_IZQUIERDA else 0)
        dy = (1 if self.teclas & TECLAS_ARRIBA else 0) - (1 if self.teclas & TECLAS_ABAJO else 0)
        return dx, dy

    # ---------- Pausa ----------
    def pausar(self):
        if self.pausado:
            return
        self.pausado = True
        self.detener_bucle()  # el teclado sigue activo solo para escuchar ESC
        self.teclas.clear()
        self.raiz.add_widget(self.capa_pausa)

    def reanudar(self):
        self.ocultar_pausa()
        self.iniciar_bucle()

    def ocultar_pausa(self):
        self.pausado = False
        if self.capa_pausa.parent:
            self.raiz.remove_widget(self.capa_pausa)

    def ir_al_menu(self):
        self.manager.current = 'menu'

    # ---------- Noches ----------
    def iniciar_transicion(self, avanzar):
        """Muestra el cartel de la noche. Si avanzar=True, a mitad del
        cartel se prepara la noche siguiente."""
        self.estado = 'transicion'
        self.tiempo_transicion = 0.0
        self.transicion_avanza = avanzar
        self.transicion_aplicada = False
        noche = self.gestor.noche + (1 if avanzar else 0)
        self.aviso.titulo.text = f'Noche {noche}'
        self.aviso.subtitulo.text = f'Entrega {self.gestor.meta_de(noche)} luciérnagas en el nido'

    def actualizar_transicion(self, dt):
        self.tiempo_transicion += dt
        t, total = self.tiempo_transicion, self.DURACION_TRANSICION
        # Aparece en 0.5 s, se queda, y desaparece en los últimos 0.6 s.
        if t < 0.5:
            self.aviso.opacity = t / 0.5
        elif t < total - 0.6:
            self.aviso.opacity = 1
        else:
            self.aviso.opacity = max(0.0, (total - t) / 0.6)
        # Cuando el cartel ya tapa el juego, se cambia la noche.
        if not self.transicion_aplicada and t >= 0.5:
            self.transicion_aplicada = True
            if self.transicion_avanza:
                self.preparar_noche_siguiente()
        if t >= total:
            self.estado = 'jugando'
            self.aviso.opacity = 0
            self.jugador.invulnerable = 1.0  # un respiro al empezar
            self.teclas.clear()

    def preparar_noche_siguiente(self):
        """Nueva noche: cielo más morado, nido en otro lugar y un
        murciélago más (y más rápidos)."""
        self.gestor.siguiente_noche()
        self.fondo.cambiar_noche(self.gestor.noche)
        self.nido.mover(self.area(), evitar=(self.jugador.x, self.jugador.y))
        for murcielago in self.murcielagos:
            murcielago.quitar()
        self.murcielagos = []
        self.crear_murcielagos()
        if self.powerup:
            self.powerup.quitar()
            self.powerup = None
        self.congelado = self.iman = 0.0

    def crear_murcielagos(self):
        """Los murciélagos nacen en los bordes, lejos del jugador."""
        xmin, ymin, xmax, ymax = self.area()
        for _ in range(self.gestor.cantidad_murcielagos):
            for _ in range(20):
                if random.random() < 0.5:
                    x = random.choice((xmin, xmax))
                    y = random.uniform(ymin, ymax)
                else:
                    x = random.uniform(xmin, xmax)
                    y = random.choice((ymin, ymax))
                if math.hypot(x - self.jugador.x, y - self.jugador.y) > dp(350):
                    break
            self.murcielagos.append(Murcielago(self.capas['murcielagos'], x, y,
                                               self.gestor.velocidad_murcielagos))

    # ---------- Bucle principal ----------
    def bucle(self, dt):
        """Se ejecuta 60 veces por segundo. Todo se multiplica por dt
        (segundos desde el cuadro anterior), así el juego va a la misma
        velocidad aunque cambien los FPS."""
        dt = min(dt, 0.05)
        area = self.area()
        self.fondo.actualizar(dt)
        self.actualizar_efectos(dt)
        self.actualizar_sacudida(dt)
        self.nido.actualizar(dt, area)

        if self.estado == 'transicion':
            self.actualizar_transicion(dt)
            self.jugador.dibujar()
            self.hud.actualizar(self)
            return
        if self.estado == 'terminando':
            self.tiempo_fin += dt
            if self.tiempo_fin >= 1.6:
                self.ir_al_final()
            return

        # 1) Jugador
        dx, dy = self.direccion_teclado()
        if self.pedir_dash:
            self.pedir_dash = False
            if self.jugador.intentar_dash():
                for _ in range(10):
                    self.efectos.append(Particula(self.capas['efectos'], self.jugador.x,
                                                  self.jugador.y, LUZ_JUGADOR))
        self.jugador.actualizar(dt, dx, dy, area)
        if self.jugador.en_dash:
            # Chispas mientras dura el impulso
            self.efectos.append(Particula(self.capas['efectos'], self.jugador.x,
                                          self.jugador.y, LUZ_JUGADOR, rapidez=(10, 40),
                                          vida=(0.3, 0.5)))

        # 2) Temporizadores de power-ups
        self.congelado = max(0.0, self.congelado - dt)
        self.iman = max(0.0, self.iman - dt)
        self.jugador.iman = self.iman > 0
        self.jugador.dibujar()

        # 3) Luciérnagas
        self.aparecer_cosas(dt, area)
        self.mover_cola(dt)
        for luciernaga in self.luciernagas[:]:
            evento = luciernaga.actualizar(dt, area, self.jugador, self.iman > 0, self.nido)
            if evento == 'llego':
                for _ in range(4):
                    self.efectos.append(Particula(self.capas['efectos'], self.nido.x,
                                                  self.nido.y, luciernaga.color))
            if luciernaga.terminada:
                luciernaga.quitar()
                self.luciernagas.remove(luciernaga)
        self.recoger_luciernagas()
        if self.cola and self.distancia(self.jugador, self.nido) < self.nido.radio:
            self.entregar()

        # 4) Murciélagos
        for murcielago in self.murcielagos:
            murcielago.congelado = self.congelado > 0
            murcielago.actualizar(dt, self.jugador.x, self.jugador.y, area)
            if (not murcielago.congelado and self.jugador.invulnerable <= 0
                    and not self.jugador.en_dash
                    and self.distancia(self.jugador, murcielago) < murcielago.radio + self.jugador.radio):
                self.golpe(murcielago)
                if self.estado != 'jugando':
                    break

        # 5) Power-up
        if self.powerup:
            self.powerup.actualizar(dt)
            if self.distancia(self.jugador, self.powerup) < self.jugador.radio + dp(20):
                self.recoger_powerup()
            elif self.powerup.terminado:
                self.powerup.quitar()
                self.powerup = None

        # 6) Cambio de noche (espera un poco para ver la entrega)
        if self.espera_transicion is not None:
            self.espera_transicion -= dt
            if self.espera_transicion <= 0:
                self.espera_transicion = None
                self.iniciar_transicion(avanzar=True)

        self.hud.actualizar(self)

    @staticmethod
    def distancia(a, b):
        """Colisiones: dos círculos se tocan si la distancia entre sus
        centros es menor que la suma de sus radios."""
        return math.hypot(a.x - b.x, a.y - b.y)

    def actualizar_efectos(self, dt):
        for efecto in self.efectos[:]:
            if not efecto.actualizar(dt):
                efecto.quitar()
                self.efectos.remove(efecto)

    def actualizar_sacudida(self, dt):
        """Mueve el mundo unos píxeles al azar; la fuerza va bajando."""
        self.sacudida = max(0.0, self.sacudida - dt * 2.5)
        fuerza = dp(10) * self.sacudida ** 2
        self.traslado_sacudida.xy = (random.uniform(-fuerza, fuerza),
                                     random.uniform(-fuerza, fuerza))

    def texto(self, x, y, texto, color, tam=None):
        # Que el texto no suba por encima del área de juego (tapa el HUD).
        y = min(y, self.area()[3] - dp(70))
        self.efectos.append(TextoFlotante(self.capas['efectos'], x, y, texto, color, tam))

    # ---------- Aparición de luciérnagas y power-ups ----------
    def lugar_libre(self, area, lejos_de_jugador):
        """Busca una posición al azar que no esté encima del jugador."""
        xmin, ymin, xmax, ymax = area
        for _ in range(20):
            x, y = random.uniform(xmin, xmax), random.uniform(ymin, ymax)
            if (math.hypot(x - self.jugador.x, y - self.jugador.y) > lejos_de_jugador
                    and math.hypot(x - self.nido.x, y - self.nido.y) > self.nido.radio * 2):
                break
        return x, y

    def generar_luciernaga(self):
        hay_fugaz = any(l.fugaz and l.estado == 'libre' for l in self.luciernagas)
        fugaz = self.gestor.permite_fugaz and not hay_fugaz and random.random() < 0.15
        x, y = self.lugar_libre(self.area(), dp(150))
        self.luciernagas.append(Luciernaga(self.capas['luciernagas'], x, y, fugaz=fugaz))

    def aparecer_cosas(self, dt, area):
        self.espera_luciernaga -= dt
        if self.espera_luciernaga <= 0:
            self.espera_luciernaga = 0.7
            sueltas = sum(1 for l in self.luciernagas if l.estado in ('libre', 'dispersa'))
            if sueltas < self.gestor.maximo_luciernagas_libres:
                self.generar_luciernaga()

        if self.powerup is None:
            self.espera_powerup -= dt
            if self.espera_powerup <= 0:
                self.espera_powerup = random.uniform(9, 14)
                tipos = ['luna', 'estrella']
                if self.vidas < VIDAS_MAXIMAS:
                    tipos.append('corazon')
                x, y = self.lugar_libre(area, dp(180))
                self.powerup = PowerUp(self.capas['powerups'], random.choice(tipos), x, y)

    # ---------- Cola de luciérnagas ----------
    def mover_cola(self, dt):
        """Cada luciérnaga de la cola sigue a la anterior (la primera sigue
        al jugador). Se acerca con interpolación hasta quedar a una
        distancia fija: así se forma una serpiente de luz."""
        espacio = dp(22)
        lider = self.jugador
        for luciernaga in self.cola:
            dx, dy = lider.x - luciernaga.x, lider.y - luciernaga.y
            distancia = math.hypot(dx, dy)
            if distancia > espacio:
                objetivo_x = lider.x - dx / distancia * espacio
                objetivo_y = lider.y - dy / distancia * espacio
                k = min(1.0, dt * 12)
                luciernaga.x += (objetivo_x - luciernaga.x) * k
                luciernaga.y += (objetivo_y - luciernaga.y) * k
            lider = luciernaga

    def recoger_luciernagas(self):
        alcance = self.jugador.radio + dp(20)
        for luciernaga in self.luciernagas:
            if len(self.cola) >= COLA_MAXIMA:
                break
            if luciernaga.estado == 'libre' and self.distancia(self.jugador, luciernaga) < alcance:
                luciernaga.cambiar_estado('cola')
                self.cola.append(luciernaga)
                self.efectos.append(AnilloDestello(self.capas['efectos'], luciernaga.x,
                                                   luciernaga.y, luciernaga.color,
                                                   radio_final=dp(28), duracion=0.35))
                if luciernaga.fugaz:
                    self.texto(luciernaga.x, luciernaga.y + dp(10), '¡Fugaz!', DORADO, sp(20))

    def entregar(self):
        """Entrega toda la cola: puntos = valor x multiplicador."""
        cantidad = len(self.cola)
        multiplicador = multiplicador_entrega(cantidad)
        ganados = sum(l.valor for l in self.cola) * multiplicador
        self.puntos += ganados
        for i, luciernaga in enumerate(self.cola):
            luciernaga.cambiar_estado('entregando')
            luciernaga.retraso = i * 0.05  # entran una detrás de otra
        self.cola = []

        # Destello en el nido y puntaje flotando
        self.nido.destello = 1.0
        for radio, duracion in ((dp(110), 0.6), (dp(160), 0.9)):
            self.efectos.append(AnilloDestello(self.capas['efectos'], self.nido.x,
                                               self.nido.y, AMARILLO, radio, duracion))
        self.texto(self.nido.x, self.nido.y + self.nido.radio, f'+{ganados}', AMARILLO, sp(34))
        if multiplicador > 1:
            self.texto(self.nido.x, self.nido.y + self.nido.radio + dp(40),
                       f'x{multiplicador}', DORADO, sp(24))

        if self.gestor.registrar_entrega(cantidad) and self.espera_transicion is None:
            self.espera_transicion = 1.0

    # ---------- Golpes y power-ups ----------
    def golpe(self, murcielago):
        """Un murciélago tocó al jugador."""
        self.sacudida = 1.0
        # El murciélago se aleja un momento para no volver a golpear enseguida.
        murcielago.aturdido = 0.8
        murcielago.angulo = math.atan2(murcielago.y - self.jugador.y,
                                       murcielago.x - self.jugador.x)
        self.jugador.invulnerable = 1.5
        if self.cola:
            # La cola se dispersa: cada luciérnaga sale volando al azar.
            for luciernaga in self.cola:
                angulo = random.uniform(0, math.tau)
                rapidez = dp(random.uniform(250, 450))
                luciernaga.vx = math.cos(angulo) * rapidez
                luciernaga.vy = math.sin(angulo) * rapidez
                luciernaga.cambiar_estado('dispersa')
            self.cola = []
            self.texto(self.jugador.x, self.jugador.y + dp(30), '¡Se escaparon!', CREMA, sp(20))
        else:
            self.vidas -= 1
            for _ in range(12):
                self.efectos.append(Particula(self.capas['efectos'], self.jugador.x,
                                              self.jugador.y, ROSA))
            if self.vidas <= 0:
                self.terminar_partida()

    def recoger_powerup(self):
        tipo, x, y = self.powerup.tipo, self.powerup.x, self.powerup.y
        color = PowerUp.COLORES[tipo]
        if tipo == 'luna':
            self.congelado = DURACION_CONGELADO
            self.texto(x, y + dp(20), '¡Murciélagos congelados!', AZUL_HIELO, sp(20))
        elif tipo == 'estrella':
            self.iman = DURACION_IMAN
            self.texto(x, y + dp(20), '¡Imán!', DORADO, sp(22))
        else:
            self.vidas = min(VIDAS_MAXIMAS, self.vidas + 1)
            self.texto(x, y + dp(20), '+1 vida', ROSA, sp(22))
        self.efectos.append(AnilloDestello(self.capas['efectos'], x, y, color, dp(70), 0.5))
        for _ in range(10):
            self.efectos.append(Particula(self.capas['efectos'], x, y, color))
        self.powerup.quitar()
        self.powerup = None

    # ---------- Fin de la partida ----------
    def terminar_partida(self):
        self.estado = 'terminando'
        self.tiempo_fin = 0.0
        self.jugador.visible = False
        self.jugador.dibujar()
        for _ in range(30):
            self.efectos.append(Particula(self.capas['efectos'], self.jugador.x, self.jugador.y,
                                          LUZ_JUGADOR, rapidez=(80, 260), vida=(0.8, 1.4)))

    def ir_al_final(self):
        self.detener_bucle()
        app = App.get_running_app()
        nuevo_record = app.guardar_resultado(self.puntos, self.gestor.noche)
        self.manager.get_screen('fin').mostrar_resultado(
            self.puntos, self.gestor.noche, self.gestor.entregadas_total,
            app.obtener_record(), nuevo_record)
        self.manager.current = 'fin'


class FinScreen(PantallaAnimada):
    """Pantalla final: puntaje, noche alcanzada, total entregado y récord."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nuevo_record = False
        self.t = 0.0
        raiz = FloatLayout()
        self.add_widget(raiz)
        self.fondo = FondoNocturno()
        self.enjambre = EnjambreDecorativo()
        raiz.add_widget(self.fondo)
        raiz.add_widget(self.enjambre)

        raiz.add_widget(crear_etiqueta(
            'Fin de la partida', sp(26), alfa=0.8,
            size_hint=(1, 0.06), pos_hint={'center_x': 0.5, 'center_y': 0.82}))
        self.etiqueta_puntos = crear_etiqueta(
            '0', sp(96), color=AMARILLO, negrita=True,
            size_hint=(1, 0.15), pos_hint={'center_x': 0.5, 'center_y': 0.69})
        raiz.add_widget(self.etiqueta_puntos)
        raiz.add_widget(crear_etiqueta(
            'puntos', sp(16), alfa=0.6,
            size_hint=(1, 0.04), pos_hint={'center_x': 0.5, 'center_y': 0.595}))
        self.etiqueta_detalle = crear_etiqueta(
            '', sp(19), alfa=0.9,
            size_hint=(1, 0.05), pos_hint={'center_x': 0.5, 'center_y': 0.52})
        raiz.add_widget(self.etiqueta_detalle)
        self.etiqueta_nuevo = crear_etiqueta(
            '¡Nuevo récord!', sp(28), color=DORADO, negrita=True,
            size_hint=(1, 0.06), pos_hint={'center_x': 0.5, 'center_y': 0.445})
        raiz.add_widget(self.etiqueta_nuevo)
        self.etiqueta_record = crear_etiqueta(
            '', sp(16), alfa=0.75,
            size_hint=(1, 0.04), pos_hint={'center_x': 0.5, 'center_y': 0.385})

        raiz.add_widget(self.etiqueta_record)
        boton_otra = BotonRedondeado(
            text='Otra vez', principal=True, size_hint=(None, None),
            size=(dp(240), dp(58)), pos_hint={'center_x': 0.4, 'center_y': 0.26})
        boton_otra.bind(on_release=lambda *_: setattr(self.manager, 'current', 'juego'))
        boton_menu = BotonRedondeado(
            text='Menú', size_hint=(None, None), size=(dp(240), dp(58)),
            pos_hint={'center_x': 0.6, 'center_y': 0.26})
        boton_menu.bind(on_release=lambda *_: setattr(self.manager, 'current', 'menu'))
        raiz.add_widget(boton_otra)
        raiz.add_widget(boton_menu)

    def mostrar_resultado(self, puntos, noche, entregadas, record, nuevo_record):
        self.nuevo_record = nuevo_record
        self.etiqueta_puntos.text = str(puntos)
        self.etiqueta_detalle.text = (f'Noche alcanzada: [b]{noche}[/b]        '
                                      f'Luciérnagas entregadas: [b]{entregadas}[/b]')
        mejor_puntos, mejor_noche = record
        self.etiqueta_record.text = (f'Récord: {mejor_puntos} puntos  ·  '
                                     f'Noche máxima: {mejor_noche}')
        self.etiqueta_nuevo.opacity = 1 if nuevo_record else 0

    def on_pre_enter(self, *args):
        self.iniciar_bucle()

    def on_leave(self, *args):
        self.detener_bucle()
        self.enjambre.limpiar()

    def bucle(self, dt):
        dt = min(dt, 0.05)
        self.t += dt
        self.fondo.actualizar(dt)
        self.enjambre.actualizar(dt)
        if self.nuevo_record:
            # El texto de nuevo récord "respira" suavemente.
            self.etiqueta_nuevo.opacity = 0.7 + 0.3 * math.sin(self.t * 3)


# ---------------------------------------------------------------------------
# 9. LA APLICACIÓN
# ---------------------------------------------------------------------------
class LuciernagasApp(App):
    """Crea el ScreenManager con las pantallas, maneja F11 y el récord."""

    title = 'Luciérnagas'

    def build(self):
        Window.clearcolor = (*AZUL_NOCHE, 1)
        Window.minimum_width, Window.minimum_height = 800, 450
        # El récord se guarda en un JSON dentro de la carpeta de datos del
        # usuario (la ruta depende del sistema operativo).
        self.almacen = JsonStore(os.path.join(self.user_data_dir, 'record.json'))
        # Teclas que funcionan en cualquier pantalla (F11).
        Window.bind(on_key_down=self.tecla_global)

        self.gestor_pantallas = ScreenManager(transition=FadeTransition(duration=0.4))
        self.gestor_pantallas.add_widget(MenuScreen(name='menu'))
        self.gestor_pantallas.add_widget(ComoJugarScreen(name='como'))
        self.gestor_pantallas.add_widget(JuegoScreen(name='juego'))
        self.gestor_pantallas.add_widget(FinScreen(name='fin'))
        return self.gestor_pantallas

    def tecla_global(self, ventana, tecla, codigo, texto, modificadores):
        if tecla == TECLA_F11:
            # 'auto' usa la resolución del monitor; False vuelve a ventana.
            Window.fullscreen = False if Window.fullscreen else 'auto'
            return True
        if tecla == TECLA_ESC and self.gestor_pantallas.current == 'como':
            self.gestor_pantallas.current = 'menu'
            return True
        return False

    def obtener_record(self):
        """Devuelve (mejor puntaje, noche máxima)."""
        if self.almacen.exists('record'):
            datos = self.almacen.get('record')
            return datos.get('puntos', 0), datos.get('noche', 1)
        return 0, 1

    def guardar_resultado(self, puntos, noche):
        """Guarda el récord si se superó. Devuelve True si el puntaje es
        un nuevo récord."""
        mejor_puntos, mejor_noche = self.obtener_record()
        nuevo = puntos > mejor_puntos
        if nuevo or noche > mejor_noche:
            self.almacen.put('record', puntos=max(puntos, mejor_puntos),
                             noche=max(noche, mejor_noche))
        return nuevo


if __name__ == '__main__':
    LuciernagasApp().run()
