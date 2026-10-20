# -*- coding: utf-8 -*-
"""
Luciérnagas
===========
Juego tranquilo hecho con Kivy: atrapa las luciérnagas de un estanque
nocturno antes de que se apaguen. Todo se dibuja con el canvas de Kivy,
sin imágenes ni sonidos externos.

Estructura general del archivo:
  1. Configuración de la ventana y constantes (colores, duración...).
  2. Funciones de ayuda (colores, degradado, etiquetas).
  3. FondoNocturno: cielo, estrellas, luna, agua y juncos.
  4. Elementos del juego: Firefly, Particle, Ripple, TextoFlotante.
  5. Widgets de interfaz: BotonRedondeado, CapaPausa, EnjambreDecorativo.
  6. Pantallas: MenuScreen, JuegoScreen, FinScreen.
  7. LuciernagasApp: crea las pantallas y guarda el récord.
"""

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA VENTANA
# ---------------------------------------------------------------------------
# La configuración debe hacerse ANTES de importar el resto de Kivy,
# porque la ventana se crea en cuanto se importa kivy.core.window.
from kivy.config import Config

Config.set('graphics', 'width', '450')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'resizable', '1')
# Evita que el clic derecho dibuje puntos rojos (simulación multitáctil).
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

import math
import os
import random

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, Mesh,
                           Rectangle, RoundedRectangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.storage.jsonstore import JsonStore
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
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


# Paleta de colores del juego
AZUL_NOCHE = hex_a_rgb('#0B1026')   # parte de arriba del cielo
MORADO_OSCURO = hex_a_rgb('#2B1B3F')  # parte de abajo del cielo
AMARILLO = hex_a_rgb('#F7E967')     # luciérnaga normal
DORADO = hex_a_rgb('#FFC94D')       # luciérnaga dorada
AZUL_HIELO = hex_a_rgb('#7FDBFF')   # luciérnaga azul (congela el tiempo)
CREMA = hex_a_rgb('#F5F0E6')        # textos
VERDE_HALO = (0.80, 0.95, 0.45)     # halo verdoso de la luciérnaga normal

DURACION_PARTIDA = 60.0   # segundos que dura cada partida
DURACION_CONGELADO = 3.0  # segundos que la luciérnaga azul congela el tiempo
FPS = 60.0

_textura_cielo = None  # se crea una sola vez y se reutiliza


def obtener_textura_cielo():
    """Crea (una sola vez) una textura de 1 x 256 píxeles con el degradado
    del cielo. Al estirarla sobre un rectángulo del tamaño de la pantalla,
    la tarjeta gráfica interpola los colores y queda un degradado suave."""
    global _textura_cielo
    if _textura_cielo is None:
        alto = 256
        textura = Texture.create(size=(1, alto), colorfmt='rgba')
        datos = bytearray()
        # La fila 0 de la textura es la de ABAJO.
        for fila in range(alto):
            t = fila / (alto - 1)  # 0 = abajo, 1 = arriba
            for canal in range(3):
                valor = MORADO_OSCURO[canal] * (1 - t) + AZUL_NOCHE[canal] * t
                datos.append(int(valor * 255))
            datos.append(255)  # canal alfa (opaco)
        textura.blit_buffer(bytes(datos), colorfmt='rgba', bufferfmt='ubyte')
        textura.mag_filter = 'linear'
        textura.min_filter = 'linear'
        textura.wrap = 'clamp_to_edge'
        _textura_cielo = textura
    return _textura_cielo


def crear_etiqueta(texto, tam, color=CREMA, alfa=1.0, negrita=False,
                   halign='center', **kwargs):
    """Crea un Label cuyo texto se alinea dentro de su propio tamaño
    (por eso se enlaza text_size con size)."""
    etiqueta = Label(text=texto, font_size=tam, color=(*color, alfa),
                     bold=negrita, halign=halign, valign='middle',
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
    píxeles en reconstruir(), así el dibujo se adapta si cambia la ventana.
    """

    ALTURA_HORIZONTE = 0.30  # el agua ocupa el 30 % inferior

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.t = 0.0  # tiempo acumulado para las animaciones
        # Semilla fija: el paisaje es siempre igual en todas las pantallas.
        azar = random.Random(11)

        # Datos de las estrellas (posición relativa, tamaño, velocidad).
        self.estrellas = [{
            'rx': azar.random(),
            'ry': azar.uniform(0.40, 0.99),
            'radio': azar.uniform(0.6, 1.8),
            'fase': azar.uniform(0, math.tau),
            'vel': azar.uniform(0.4, 1.4),  # titilan lentamente
        } for _ in range(75)]

        # Pequeñas líneas de luz sobre el agua.
        self.brillos = [{
            'rx': azar.random(),
            'ry': azar.uniform(0.05, 0.27),
            'largo': azar.uniform(0.03, 0.10),
            'fase': azar.uniform(0, math.tau),
            'vel': azar.uniform(0.5, 1.2),
        } for _ in range(16)]

        # Juncos: primero una capa de atrás (más clara y baja) y luego una
        # capa de adelante (más oscura y alta). Así se ve profundidad.
        self.juncos = []
        for capa, cantidad in (('atras', 18), ('adelante', 22)):
            for _ in range(cantidad):
                adelante = capa == 'adelante'
                self.juncos.append({
                    'rx': azar.uniform(-0.02, 1.02),
                    'alto': azar.uniform(0.10, 0.22) if adelante
                    else azar.uniform(0.06, 0.14),
                    'inclina': azar.uniform(-0.05, 0.05),
                    'ancho': dp(azar.uniform(3.5, 6.5)),
                    'fase': azar.uniform(0, math.tau),
                    'vel': azar.uniform(0.6, 1.1),
                    'color': (0.02, 0.025, 0.06, 1) if adelante
                    else (0.10, 0.075, 0.17, 1),
                    'flor': adelante and azar.random() < 0.35,  # espadaña
                })

        # --- Instrucciones de dibujo (el orden define qué queda encima) ---
        with self.canvas:
            # Cielo: rectángulo con la textura del degradado.
            Color(1, 1, 1, 1)
            self.rect_cielo = Rectangle(texture=obtener_textura_cielo())

            # Estrellas
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

            # Agua: un velo oscuro sobre la parte baja del cielo.
            Color(0.02, 0.03, 0.10, 0.55)
            self.rect_agua = Rectangle()
            Color(*CREMA, 0.10)
            self.linea_horizonte = Line(width=dp(1))

            # Brillos del agua
            for brillo in self.brillos:
                brillo['color'] = Color(*CREMA, 0)
                brillo['linea'] = Line(width=dp(1))

            # Reflejo de la luna: líneas horizontales debajo de ella.
            self.reflejos = []
            for _ in range(7):
                color = Color(*CREMA, 0)
                self.reflejos.append((color, Line(width=dp(1.4))))

            # Juncos: cada uno es una malla (Mesh) en forma de hoja.
            for junco in self.juncos:
                Color(*junco['color'])
                junco['malla'] = Mesh(mode='triangle_strip')
                if junco['flor']:
                    junco['elipse'] = Ellipse()

            # Franja de orilla en el borde inferior
            Color(0.015, 0.02, 0.05, 1)
            self.rect_orilla = Rectangle()

        self.bind(pos=self.reconstruir, size=self.reconstruir)

    def reconstruir(self, *args):
        """Recalcula las partes que solo dependen del tamaño de la ventana."""
        x, y, ancho, alto = self.x, self.y, self.width, self.height
        horizonte = y + alto * self.ALTURA_HORIZONTE

        self.rect_cielo.pos = self.pos
        self.rect_cielo.size = self.size

        # Luna
        self.luna_x = x + ancho * 0.24
        self.luna_y = y + alto * 0.83
        radio = dp(20)
        self.luna.pos = (self.luna_x - radio, self.luna_y - radio)
        self.luna.size = (radio * 2, radio * 2)
        for elipse, factor in self.halos_luna:
            r = radio * factor
            elipse.pos = (self.luna_x - r, self.luna_y - r)
            elipse.size = (r * 2, r * 2)

        # Agua
        self.rect_agua.pos = self.pos
        self.rect_agua.size = (ancho, horizonte - y)
        self.linea_horizonte.points = [x, horizonte, x + ancho, horizonte]

        self.rect_orilla.pos = self.pos
        self.rect_orilla.size = (ancho, dp(8))

        # Los juncos usan siempre el mismo orden de vértices.
        for junco in self.juncos:
            junco['malla'].indices = list(range(2 * 9))

        # Dibuja también las partes animadas en su posición actual.
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
            r = dp(e['radio'])
            ex = x + e['rx'] * ancho
            ey = y + e['ry'] * alto
            e['forma'].pos = (ex - r, ey - r)
            e['forma'].size = (r * 2, r * 2)

        # Brillos del agua: se desplazan un poco y aparecen/desaparecen.
        for b in self.brillos:
            bx = x + b['rx'] * ancho + math.sin(t * 0.3 + b['fase']) * dp(8)
            by = y + b['ry'] * alto
            largo = b['largo'] * ancho
            b['color'].a = 0.03 + 0.09 * (0.5 + 0.5 * math.sin(t * b['vel'] + b['fase']))
            b['linea'].points = [bx, by, bx + largo, by]

        # Reflejo de la luna: líneas cada vez más cortas hacia abajo.
        for i, (color, linea) in enumerate(self.reflejos):
            ry = horizonte - dp(8) - i * dp(9)
            mitad = dp(26) * (1 - i * 0.11)
            ondula = math.sin(t * 1.3 + i * 0.9) * dp(3)
            color.a = (0.22 - i * 0.025) * (0.75 + 0.25 * math.sin(t * 2 + i))
            linea.points = [self.luna_x - mitad + ondula, ry,
                            self.luna_x + mitad + ondula, ry]

        # Juncos que se mecen suavemente.
        for junco in self.juncos:
            self._dibujar_junco(junco)

    def _dibujar_junco(self, junco):
        """Construye la hoja del junco como una tira de triángulos que sigue
        una curva de Bézier cuadrática y se va afinando hacia la punta."""
        x0 = self.x + junco['rx'] * self.width
        y0 = self.y
        alto = junco['alto'] * self.height
        vaiven = math.sin(self.t * junco['vel'] + junco['fase']) * dp(4)
        x2 = x0 + junco['inclina'] * self.width + vaiven  # punta
        y1 = y0 + alto * 0.55                               # punto de control
        y2 = y0 + alto

        vertices = []
        pasos = 8
        for i in range(pasos + 1):
            s = i / pasos
            # Fórmula de Bézier: (1-s)²·P0 + 2(1-s)s·P1 + s²·P2
            px = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * x0 + s * s * x2
            py = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * y1 + s * s * y2
            medio_ancho = junco['ancho'] * (1 - s) / 2
            # Mesh usa 4 valores por vértice: x, y, u, v (u, v no se usan).
            vertices += [px - medio_ancho, py, 0, 0, px + medio_ancho, py, 0, 0]
        junco['malla'].vertices = vertices

        if junco['flor']:
            # La espadaña (la "salchicha" del junco) va cerca de la punta.
            s = 0.78
            px = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * x0 + s * s * x2
            py = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * y1 + s * s * y2
            w, h = dp(7), dp(20)
            junco['elipse'].pos = (px - w / 2, py - h / 2)
            junco['elipse'].size = (w, h)


# ---------------------------------------------------------------------------
# 4. ELEMENTOS DEL JUEGO
# ---------------------------------------------------------------------------
# Estos objetos NO son widgets: son clases simples que agrupan sus
# instrucciones de dibujo en un InstructionGroup. Es más liviano que crear
# un widget por cada luciérnaga o partícula.

class Firefly:
    """Una luciérnaga: núcleo brillante + 3 halos que laten.
    Se mueve deambulando con un vaivén de seno/coseno, vive unos segundos
    y luego se desvanece lentamente."""

    # Características de cada tipo de luciérnaga.
    TIPOS = {
        'normal': {'color': AMARILLO, 'halo': VERDE_HALO, 'radio': 4.5,
                   'puntos': 1, 'vida': 2.5, 'velocidad': 18,
                   'vaiven': 14, 'frecuencia': 1.2},
        'dorada': {'color': DORADO, 'halo': DORADO, 'radio': 3.2,
                   'puntos': 5, 'vida': 1.8, 'velocidad': 60,
                   'vaiven': 20, 'frecuencia': 2.4},
        'azul': {'color': AZUL_HIELO, 'halo': AZUL_HIELO, 'radio': 4.5,
                 'puntos': 0, 'vida': 2.4, 'velocidad': 22,
                 'vaiven': 14, 'frecuencia': 1.4},
    }
    DURACION_APARICION = 0.35  # segundos que tarda en encenderse
    DURACION_APAGADO = 0.9     # segundos que tarda en desvanecerse

    def __init__(self, canvas, area, tipo='normal', x=0, y=0, vida=None):
        datos = self.TIPOS[tipo]
        self.canvas = canvas
        self.area = area  # función que devuelve (xmin, ymin, xmax, ymax)
        self.tipo = tipo
        self.color = datos['color']
        self.radio = dp(datos['radio'])
        self.puntos = datos['puntos']
        self.vida = vida if vida is not None else datos['vida']
        self.velocidad = dp(datos['velocidad'])
        self.vaiven = dp(datos['vaiven'])
        self.frecuencia = datos['frecuencia']

        self.bx, self.by = x, y      # posición "base" (sin el vaivén)
        self.cx, self.cy = x, y      # posición real dibujada
        self.angulo = random.uniform(0, math.tau)  # dirección en que avanza
        self.fase = random.uniform(0, math.tau)    # para que no se muevan igual
        self.edad = 0.0
        self.apagandose = False
        self.terminada = False

        # Instrucciones de dibujo: halos (de grande a pequeño) y núcleo.
        self.grupo = InstructionGroup()
        self.halos = []
        for factor, alfa in ((4.8, 0.08), (3.1, 0.16), (1.9, 0.32)):
            color = Color(*datos['halo'], 0)
            elipse = Ellipse()
            self.grupo.add(color)
            self.grupo.add(elipse)
            self.halos.append((color, elipse, factor, alfa))
        self.color_nucleo = Color(*self.color, 0)
        self.nucleo = Ellipse()
        self.color_centro = Color(1, 1, 0.95, 0)  # puntito casi blanco
        self.centro = Ellipse()
        for instruccion in (self.color_nucleo, self.nucleo,
                            self.color_centro, self.centro):
            self.grupo.add(instruccion)
        canvas.add(self.grupo)
        self._dibujar(0)

    @property
    def atrapable(self):
        """Solo se puede atrapar mientras está encendida."""
        return not self.apagandose and not self.terminada

    def actualizar(self, dt):
        """Mueve y anima la luciérnaga. Devuelve 'apagada' en el momento
        exacto en que se le acaba la vida (para romper el combo)."""
        self.edad += dt
        evento = None

        # Deambular: la dirección cambia un poquito al azar en cada cuadro.
        self.angulo += random.uniform(-1, 1) * 2.0 * dt
        self.bx += math.cos(self.angulo) * self.velocidad * dt
        self.by += math.sin(self.angulo) * self.velocidad * dt

        # Rebota en los bordes del área permitida.
        xmin, ymin, xmax, ymax = self.area()
        if self.bx < xmin or self.bx > xmax:
            self.bx = min(max(self.bx, xmin), xmax)
            self.angulo = math.pi - self.angulo
        if self.by < ymin or self.by > ymax:
            self.by = min(max(self.by, ymin), ymax)
            self.angulo = -self.angulo

        # Vaivén suave con seno y coseno (dibuja una especie de ocho).
        t = self.edad * self.frecuencia
        self.cx = self.bx + math.sin(t + self.fase) * self.vaiven
        self.cy = self.by + math.cos(t * 0.8 + self.fase * 1.3) * self.vaiven * 0.6

        if not self.apagandose and self.edad >= self.vida:
            self.apagandose = True
            evento = 'apagada'

        # Opacidad: se enciende al nacer y se desvanece al final.
        alfa = min(1.0, self.edad / self.DURACION_APARICION)
        if self.apagandose:
            progreso = (self.edad - self.vida) / self.DURACION_APAGADO
            alfa *= max(0.0, 1.0 - progreso)
            if progreso >= 1:
                self.terminada = True

        self._dibujar(alfa)
        return evento

    def _dibujar(self, alfa):
        """Actualiza tamaño, posición y opacidad de los círculos."""
        latido = 1 + 0.18 * math.sin(self.edad * 4 + self.fase)    # el halo late
        brillo = 0.85 + 0.15 * math.sin(self.edad * 9 + self.fase * 2)
        quedan = self.vida - self.edad
        if 0 < quedan < 0.7:
            # Parpadeo más rápido como aviso de que se va a apagar.
            brillo *= 0.75 + 0.25 * math.sin(self.edad * 22)

        for color, elipse, factor, alfa_halo in self.halos:
            r = self.radio * factor * latido
            color.a = alfa_halo * alfa * brillo
            elipse.pos = (self.cx - r, self.cy - r)
            elipse.size = (r * 2, r * 2)

        r = self.radio
        self.color_nucleo.a = alfa
        self.nucleo.pos = (self.cx - r, self.cy - r)
        self.nucleo.size = (r * 2, r * 2)
        r = self.radio * 0.45
        self.color_centro.a = alfa * 0.9
        self.centro.pos = (self.cx - r, self.cy - r)
        self.centro.size = (r * 2, r * 2)

    def quitar(self):
        """Borra sus dibujos del canvas."""
        self.canvas.remove(self.grupo)


class Particle:
    """Chispita que sale disparada al atrapar una luciérnaga, se frena,
    se encoge y se desvanece."""

    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        angulo = random.uniform(0, math.tau)
        rapidez = random.uniform(dp(50), dp(150))
        self.vx = math.cos(angulo) * rapidez
        self.vy = math.sin(angulo) * rapidez
        self.x, self.y = x, y
        self.vida = random.uniform(0.5, 0.9)
        self.edad = 0.0
        self.radio = random.uniform(dp(1.5), dp(3))

        self.grupo = InstructionGroup()
        self.color_brillo = Color(*color, 0.15)  # resplandor alrededor
        self.brillo = Ellipse()
        self.color_punto = Color(*color, 1)
        self.punto = Ellipse()
        for instruccion in (self.color_brillo, self.brillo,
                            self.color_punto, self.punto):
            self.grupo.add(instruccion)
        canvas.add(self.grupo)
        self.actualizar(0)

    def actualizar(self, dt):
        """Devuelve False cuando la partícula ya terminó."""
        self.edad += dt
        if self.edad >= self.vida:
            return False
        freno = max(0.0, 1 - 3 * dt)  # rozamiento: se va frenando
        self.vx *= freno
        self.vy *= freno
        self.vy += dp(15) * dt        # sube un poquito, como flotando
        self.x += self.vx * dt
        self.y += self.vy * dt

        progreso = self.edad / self.vida
        alfa = 1 - progreso
        r = self.radio * (1 - 0.5 * progreso)
        self.color_punto.a = alfa
        self.color_brillo.a = 0.15 * alfa
        self.punto.pos = (self.x - r, self.y - r)
        self.punto.size = (r * 2, r * 2)
        rb = r * 2.2
        self.brillo.pos = (self.x - rb, self.y - rb)
        self.brillo.size = (rb * 2, rb * 2)
        return True

    def quitar(self):
        self.canvas.remove(self.grupo)


class Ripple:
    """Onda en el agua: tres anillos achatados (en perspectiva) que se
    agrandan uno detrás de otro y se desvanecen."""

    DURACION = 1.3
    RETRASOS = (0.0, 0.22, 0.44)

    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x, self.y = x, y
        self.edad = 0.0
        self.grupo = InstructionGroup()
        self.anillos = []
        for retraso in self.RETRASOS:
            color = Color(*CREMA, 0)
            linea = Line(ellipse=(x, y, 1, 1), width=dp(1.2))
            self.grupo.add(color)
            self.grupo.add(linea)
            self.anillos.append((color, linea, retraso))
        canvas.add(self.grupo)

    def actualizar(self, dt):
        self.edad += dt
        for color, linea, retraso in self.anillos:
            progreso = (self.edad - retraso) / self.DURACION
            if progreso <= 0 or progreso >= 1:
                color.a = 0
                continue
            suave = 1 - (1 - progreso) ** 2  # rápido al inicio, lento al final
            r = dp(6) + dp(55) * suave
            color.a = 0.45 * (1 - progreso)
            # El alto es menor que el ancho para que parezca agua vista de lado.
            linea.ellipse = (self.x - r, self.y - r * 0.4, r * 2, r * 0.8)
        return self.edad < self.DURACION + self.RETRASOS[-1]

    def quitar(self):
        self.canvas.remove(self.grupo)


class TextoFlotante:
    """Texto como "+1" o "+5" que sube y desaparece.
    Se dibuja con CoreLabel, que convierte el texto en una textura."""

    DURACION = 0.9

    def __init__(self, canvas, x, y, texto, color, tam=None):
        self.canvas = canvas
        etiqueta = CoreLabel(text=texto, font_size=tam or sp(24), bold=True)
        etiqueta.refresh()
        textura = etiqueta.texture
        self.x = x - textura.width / 2  # centrado horizontalmente
        self.y = y + dp(8)
        self.edad = 0.0
        self.grupo = InstructionGroup()
        self.color = Color(*color, 1)  # tiñe la textura blanca del texto
        self.rect = Rectangle(texture=textura, size=textura.size,
                              pos=(self.x, self.y))
        self.grupo.add(self.color)
        self.grupo.add(self.rect)
        canvas.add(self.grupo)

    def actualizar(self, dt):
        self.edad += dt
        progreso = self.edad / self.DURACION
        self.rect.pos = (self.x, self.y + dp(45) * progreso)
        self.color.a = max(0.0, 1 - progreso ** 2)
        return progreso < 1

    def quitar(self):
        self.canvas.remove(self.grupo)


# ---------------------------------------------------------------------------
# 5. WIDGETS DE INTERFAZ
# ---------------------------------------------------------------------------
class BotonRedondeado(ButtonBehavior, Label):
    """Botón propio: fondo semitransparente con bordes redondeados.
    ButtonBehavior le da el comportamiento de botón (on_release, state)
    y Label le da el texto. Al presionarlo se ilumina un poco."""

    def __init__(self, principal=False, **kwargs):
        kwargs.setdefault('font_size', sp(20))
        kwargs.setdefault('bold', True)
        self.principal = principal
        self.tono = AMARILLO if principal else CREMA
        kwargs.setdefault('color', (*self.tono, 1))
        super().__init__(**kwargs)
        with self.canvas.before:
            self.color_fondo = Color()
            self.fondo = RoundedRectangle()
            self.color_borde = Color()
            self.borde = Line(width=dp(1.2))
        self.bind(pos=self._redibujar, size=self._redibujar,
                  state=self._redibujar)
        self._redibujar()

    def _redibujar(self, *args):
        radio = min(self.height / 2, self.width / 2, dp(28)) * 0.99
        self.fondo.pos = self.pos
        self.fondo.size = self.size
        self.fondo.radius = [radio]
        self.borde.rounded_rectangle = (self.x, self.y, self.width,
                                        self.height, radio)
        presionado = self.state == 'down'
        if self.principal:
            alfa_fondo = 0.30 if presionado else 0.14
        else:
            alfa_fondo = 0.20 if presionado else 0.07
        self.color_fondo.rgba = (*self.tono, alfa_fondo)
        self.color_borde.rgba = (*self.tono, 0.95 if presionado else 0.5)


class CapaPausa(FloatLayout):
    """Velo oscuro con el menú de pausa. Se pone encima del juego y
    bloquea los toques para que no se atrapen luciérnagas en pausa."""

    def __init__(self, al_seguir, al_menu, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.03, 0.03, 0.09, 0.75)
            self.velo = Rectangle()
        self.bind(pos=self._ajustar, size=self._ajustar)

        self.add_widget(crear_etiqueta(
            'Pausa', sp(42), color=CREMA, negrita=True,
            size_hint=(1, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.62}))
        boton_seguir = BotonRedondeado(
            text='Seguir', principal=True, size_hint=(0.55, None),
            height=dp(56), pos_hint={'center_x': 0.5, 'center_y': 0.48})
        boton_seguir.bind(on_release=lambda *_: al_seguir())
        boton_menu = BotonRedondeado(
            text='Menú', size_hint=(0.55, None), height=dp(56),
            pos_hint={'center_x': 0.5, 'center_y': 0.38})
        boton_menu.bind(on_release=lambda *_: al_menu())
        self.add_widget(boton_seguir)
        self.add_widget(boton_menu)

    def _ajustar(self, *args):
        self.velo.pos = self.pos
        self.velo.size = self.size

    def on_touch_down(self, touch):
        super().on_touch_down(touch)  # deja que los botones lo reciban
        return True                   # y no lo deja pasar al juego


class EnjambreDecorativo(Widget):
    """Luciérnagas de adorno para el menú y la pantalla final.
    Reutiliza la clase Firefly, pero con vidas más largas."""

    MAXIMO = 9

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.luciernagas = []
        self.espera = 0.0

    def area(self):
        return (self.x + dp(20), self.y + self.height * 0.2,
                self.right - dp(20), self.top - dp(20))

    def actualizar(self, dt):
        self.espera -= dt
        if self.espera <= 0 and len(self.luciernagas) < self.MAXIMO:
            xmin, ymin, xmax, ymax = self.area()
            tipo = 'dorada' if random.random() < 0.12 else 'normal'
            self.luciernagas.append(Firefly(
                self.canvas, self.area, tipo,
                random.uniform(xmin, xmax), random.uniform(ymin, ymax),
                vida=random.uniform(3.0, 6.0)))
            self.espera = random.uniform(0.3, 0.9)
        for luciernaga in self.luciernagas[:]:
            luciernaga.actualizar(dt)
            if luciernaga.terminada:
                luciernaga.quitar()
                self.luciernagas.remove(luciernaga)

    def limpiar(self):
        for luciernaga in self.luciernagas:
            luciernaga.quitar()
        self.luciernagas = []


# ---------------------------------------------------------------------------
# 6. PANTALLAS
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
    """Pantalla de inicio: título, botón Jugar y récord."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = FloatLayout()
        self.add_widget(raiz)

        self.fondo = FondoNocturno()
        self.enjambre = EnjambreDecorativo()
        raiz.add_widget(self.fondo)
        raiz.add_widget(self.enjambre)

        raiz.add_widget(crear_etiqueta(
            'Luciérnagas', sp(54), color=AMARILLO, negrita=True,
            size_hint=(1, 0.12), pos_hint={'center_x': 0.5, 'center_y': 0.66}))
        raiz.add_widget(crear_etiqueta(
            'Atrapa la luz antes de que se apague', sp(17), alfa=0.8,
            size_hint=(0.9, 0.05), pos_hint={'center_x': 0.5, 'center_y': 0.585}))

        boton_jugar = BotonRedondeado(
            text='Jugar', principal=True, font_size=sp(24),
            size_hint=(0.55, None), height=dp(62),
            pos_hint={'center_x': 0.5, 'center_y': 0.45})
        boton_jugar.bind(on_release=self.jugar)
        raiz.add_widget(boton_jugar)

        self.etiqueta_record = crear_etiqueta(
            '', sp(18), alfa=0.9, size_hint=(0.9, 0.05),
            pos_hint={'center_x': 0.5, 'center_y': 0.36})
        raiz.add_widget(self.etiqueta_record)

        # Instrucciones cortas con colores (markup de Kivy).
        dorado = '[color=FFC94D][b]Doradas[/b][/color]'
        azul = '[color=7FDBFF][b]Azules[/b][/color]'
        raiz.add_widget(crear_etiqueta(
            f'Toca las luciérnagas para atraparlas.\n'
            f'{dorado}: +5 puntos   ·   {azul}: congelan el tiempo',
            sp(13), alfa=0.65, size_hint=(0.95, 0.07),
            pos_hint={'center_x': 0.5, 'center_y': 0.28}))

    def on_pre_enter(self, *args):
        record = App.get_running_app().obtener_record()
        self.etiqueta_record.text = f'Récord: [b]{record}[/b]'
        self.iniciar_bucle()

    def on_leave(self, *args):
        self.detener_bucle()
        self.enjambre.limpiar()

    def bucle(self, dt):
        dt = min(dt, 0.05)  # evita saltos grandes si la ventana se congela
        self.fondo.actualizar(dt)
        self.enjambre.actualizar(dt)

    def jugar(self, *args):
        self.manager.current = 'juego'


class CapaJuego(Widget):
    """Capa donde se dibujan luciérnagas y efectos. Recibe los toques
    y se los pasa a la pantalla de juego."""

    def __init__(self, juego, **kwargs):
        super().__init__(**kwargs)
        self.juego = juego

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.juego.tocar(*touch.pos)
            return True
        return False


class JuegoScreen(PantallaAnimada):
    """La partida: genera luciérnagas, maneja puntaje, combo, tiempo,
    congelado, dificultad y pausa."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raiz = FloatLayout()
        self.add_widget(raiz)
        self.raiz = raiz

        self.fondo = FondoNocturno()
        self.capa = CapaJuego(self)
        raiz.add_widget(self.fondo)
        raiz.add_widget(self.capa)

        # Velo azul que aparece mientras el tiempo está congelado.
        # Va en canvas.after para quedar encima de las luciérnagas.
        with self.capa.canvas.after:
            self.color_hielo = Color(*AZUL_HIELO, 0)
            self.velo_hielo = Rectangle()
        self.capa.bind(pos=self._ajustar_velo, size=self._ajustar_velo)

        # --- Marcadores (HUD) ---
        raiz.add_widget(crear_etiqueta(
            'PUNTOS', sp(12), alfa=0.6, halign='left', size_hint=(0.4, 0.03),
            pos_hint={'x': 0.05, 'top': 0.985}))
        self.etiqueta_puntos = crear_etiqueta(
            '0', sp(34), negrita=True, halign='left', size_hint=(0.4, 0.06),
            pos_hint={'x': 0.05, 'top': 0.957})
        raiz.add_widget(self.etiqueta_puntos)

        raiz.add_widget(crear_etiqueta(
            'TIEMPO', sp(12), alfa=0.6, halign='right', size_hint=(0.4, 0.03),
            pos_hint={'right': 0.95, 'top': 0.985}))
        self.etiqueta_tiempo = crear_etiqueta(
            '60', sp(34), negrita=True, halign='right', size_hint=(0.4, 0.06),
            pos_hint={'right': 0.95, 'top': 0.957})
        raiz.add_widget(self.etiqueta_tiempo)

        self.etiqueta_combo = crear_etiqueta(
            '', sp(26), color=DORADO, negrita=True, size_hint=(0.3, 0.06),
            pos_hint={'center_x': 0.5, 'top': 0.965})
        self.etiqueta_combo.opacity = 0
        raiz.add_widget(self.etiqueta_combo)

        boton_pausa = BotonRedondeado(
            text='II', font_size=sp(15), size_hint=(None, None),
            size=(dp(42), dp(42)), pos_hint={'right': 0.95, 'top': 0.885})
        boton_pausa.bind(on_release=lambda *_: self.pausar())
        raiz.add_widget(boton_pausa)

        self.capa_pausa = CapaPausa(al_seguir=self.reanudar,
                                    al_menu=self.ir_al_menu)
        self.pausado = False

        self.luciernagas = []
        self.efectos = []  # partículas, ondas y textos flotantes

    # ---------- Ciclo de vida de la pantalla ----------
    def on_pre_enter(self, *args):
        self.reiniciar()

    def on_enter(self, *args):
        # El bucle empieza cuando termina la transición.
        self.iniciar_bucle()

    def on_pre_leave(self, *args):
        # Al salir se detiene todo para no dejar Clocks corriendo.
        self.detener_bucle()
        self.ocultar_pausa()

    def on_leave(self, *args):
        self.limpiar()

    def reiniciar(self):
        """Deja todo listo para una partida nueva."""
        self.limpiar()
        self.puntos = 0
        self.tiempo = DURACION_PARTIDA
        self.transcurrido = 0.0   # tiempo jugado (para la dificultad)
        self.congelado = 0.0      # segundos de congelado que quedan
        self.racha = 0            # luciérnagas atrapadas seguidas
        self.espera_aparicion = 0.6
        self.ocultar_pausa()
        self.actualizar_marcadores()
        self.etiqueta_combo.opacity = 0
        self.color_hielo.a = 0

    def limpiar(self):
        for objeto in self.luciernagas + self.efectos:
            objeto.quitar()
        self.luciernagas = []
        self.efectos = []

    def _ajustar_velo(self, *args):
        self.velo_hielo.pos = self.capa.pos
        self.velo_hielo.size = self.capa.size

    # ---------- Pausa ----------
    def pausar(self):
        if self.pausado:
            return
        self.pausado = True
        self.detener_bucle()
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

    # ---------- Lógica del juego ----------
    def area_luciernagas(self):
        """Zona donde pueden volar: evita los marcadores de arriba y los
        juncos de abajo."""
        c = self.capa
        return (c.x + dp(30), c.y + c.height * 0.20,
                c.right - dp(30), c.y + c.height * 0.84)

    @property
    def multiplicador(self):
        """Cada 3 luciérnagas seguidas el multiplicador sube 1 (máximo x5)."""
        return min(5, 1 + self.racha // 3)

    def bucle(self, dt):
        """Se ejecuta 60 veces por segundo. Todo se multiplica por dt
        (segundos desde el cuadro anterior), así el juego va a la misma
        velocidad aunque los FPS cambien."""
        dt = min(dt, 0.05)
        self.fondo.actualizar(dt)
        self.transcurrido += dt

        # Reloj de la partida (no avanza mientras está congelado).
        if self.congelado > 0:
            self.congelado = max(0.0, self.congelado - dt)
        else:
            self.tiempo -= dt

        # Aparición de nuevas luciérnagas.
        self.espera_aparicion -= dt
        if self.espera_aparicion <= 0:
            self.generar_luciernaga()

        # Actualizar luciérnagas
        for luciernaga in self.luciernagas[:]:
            if luciernaga.actualizar(dt) == 'apagada':
                self.romper_combo()
            if luciernaga.terminada:
                luciernaga.quitar()
                self.luciernagas.remove(luciernaga)

        # Actualizar efectos (cada uno dice si sigue vivo)
        for efecto in self.efectos[:]:
            if not efecto.actualizar(dt):
                efecto.quitar()
                self.efectos.remove(efecto)

        # Velo azul suave mientras dura el congelado.
        self.color_hielo.a = 0.10 * min(1.0, self.congelado / 0.5)

        self.actualizar_marcadores()

        if self.tiempo <= 0:
            self.terminar_partida()

    def dificultad(self):
        """Valor de 0 (inicio) a 1 (final de la partida)."""
        return min(1.0, self.transcurrido / DURACION_PARTIDA)

    def generar_luciernaga(self):
        d = self.dificultad()
        # Con la dificultad aparecen más seguido...
        self.espera_aparicion = random.uniform(0.75, 1.15) * (1.0 - 0.5 * d)
        if len(self.luciernagas) >= 3 + int(5 * d):
            return  # ya hay suficientes en pantalla

        azar = random.random()
        if azar < 0.05:
            tipo = 'azul'
        elif azar < 0.15:
            tipo = 'dorada'
        else:
            tipo = 'normal'
        # ...y viven un poco menos (hasta un 30 % menos al final).
        vida = Firefly.TIPOS[tipo]['vida'] * (1.0 - 0.3 * d)

        # Busca un lugar que no esté encima de otra luciérnaga.
        xmin, ymin, xmax, ymax = self.area_luciernagas()
        for _ in range(8):
            x = random.uniform(xmin, xmax)
            y = random.uniform(ymin, ymax)
            if all(math.hypot(x - l.cx, y - l.cy) > dp(60) for l in self.luciernagas):
                break
        self.luciernagas.append(Firefly(self.capa.canvas, self.area_luciernagas,
                                        tipo, x, y, vida))

    def tocar(self, x, y):
        """Busca la luciérnaga encendida más cercana al toque. Si no hay
        ninguna cerca, solo se dibuja una onda en el agua."""
        if self.pausado or self.evento_bucle is None:
            return
        alcance = dp(34)  # zona generosa para que sea fácil y relajado
        mejor, mejor_distancia = None, alcance
        for luciernaga in self.luciernagas:
            if luciernaga.atrapable:
                distancia = math.hypot(x - luciernaga.cx, y - luciernaga.cy)
                if distancia < mejor_distancia:
                    mejor, mejor_distancia = luciernaga, distancia
        if mejor:
            self.atrapar(mejor)
        else:
            self.efectos.append(Ripple(self.capa.canvas, x, y))

    def atrapar(self, luciernaga):
        multiplicador_antes = self.multiplicador
        self.racha += 1
        x, y, color = luciernaga.cx, luciernaga.cy, luciernaga.color

        # Explosión de partículas del mismo color.
        for _ in range(random.randint(8, 12)):
            self.efectos.append(Particle(self.capa.canvas, x, y, color))

        if luciernaga.tipo == 'azul':
            self.congelado = DURACION_CONGELADO
            texto = '¡Congelado!'
        else:
            ganados = luciernaga.puntos * self.multiplicador
            self.puntos += ganados
            texto = f'+{ganados}'
        self.efectos.append(TextoFlotante(self.capa.canvas, x, y, texto, color))

        luciernaga.quitar()
        self.luciernagas.remove(luciernaga)

        # Pequeño "salto" del texto del combo cuando sube el multiplicador.
        if self.multiplicador > multiplicador_antes:
            Animation.cancel_all(self.etiqueta_combo, 'font_size')
            (Animation(font_size=sp(34), d=0.08) +
             Animation(font_size=sp(26), d=0.18)).start(self.etiqueta_combo)

    def romper_combo(self):
        self.racha = 0

    def actualizar_marcadores(self):
        self.etiqueta_puntos.text = str(self.puntos)
        self.etiqueta_tiempo.text = str(max(0, math.ceil(self.tiempo)))
        if self.congelado > 0:
            self.etiqueta_tiempo.color = (*AZUL_HIELO, 1)
        elif self.tiempo <= 10:
            self.etiqueta_tiempo.color = (*DORADO, 1)  # aviso suave
        else:
            self.etiqueta_tiempo.color = (*CREMA, 1)
        if self.multiplicador >= 2:
            self.etiqueta_combo.text = f'x{self.multiplicador}'
            self.etiqueta_combo.opacity = 1
        else:
            self.etiqueta_combo.opacity = 0

    def terminar_partida(self):
        self.detener_bucle()
        app = App.get_running_app()
        nuevo_record = app.guardar_record(self.puntos)
        self.manager.get_screen('fin').mostrar_resultado(
            self.puntos, app.obtener_record(), nuevo_record)
        self.manager.current = 'fin'


class FinScreen(PantallaAnimada):
    """Pantalla final: puntaje, récord y botones para seguir."""

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
            'Fin de la partida', sp(22), alfa=0.8,
            size_hint=(1, 0.05), pos_hint={'center_x': 0.5, 'center_y': 0.74}))
        self.etiqueta_puntos = crear_etiqueta(
            '0', sp(80), color=AMARILLO, negrita=True,
            size_hint=(1, 0.12), pos_hint={'center_x': 0.5, 'center_y': 0.655})
        raiz.add_widget(self.etiqueta_puntos)
        raiz.add_widget(crear_etiqueta(
            'puntos', sp(15), alfa=0.6,
            size_hint=(1, 0.04), pos_hint={'center_x': 0.5, 'center_y': 0.585}))

        self.etiqueta_nuevo = crear_etiqueta(
            '¡Nuevo récord!', sp(24), color=DORADO, negrita=True,
            size_hint=(1, 0.05), pos_hint={'center_x': 0.5, 'center_y': 0.525})
        raiz.add_widget(self.etiqueta_nuevo)
        self.etiqueta_record = crear_etiqueta(
            '', sp(17), alfa=0.85,
            size_hint=(1, 0.04), pos_hint={'center_x': 0.5, 'center_y': 0.475})
        raiz.add_widget(self.etiqueta_record)

        boton_otra = BotonRedondeado(
            text='Otra vez', principal=True, size_hint=(0.55, None),
            height=dp(58), pos_hint={'center_x': 0.5, 'center_y': 0.38})
        boton_otra.bind(on_release=lambda *_: setattr(self.manager, 'current', 'juego'))
        boton_menu = BotonRedondeado(
            text='Menú', size_hint=(0.55, None), height=dp(58),
            pos_hint={'center_x': 0.5, 'center_y': 0.29})
        boton_menu.bind(on_release=lambda *_: setattr(self.manager, 'current', 'menu'))
        raiz.add_widget(boton_otra)
        raiz.add_widget(boton_menu)

    def mostrar_resultado(self, puntos, record, nuevo_record):
        self.nuevo_record = nuevo_record
        self.etiqueta_puntos.text = str(puntos)
        self.etiqueta_record.text = f'Récord: [b]{record}[/b]'
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
# 7. LA APLICACIÓN
# ---------------------------------------------------------------------------
class LuciernagasApp(App):
    """Crea el ScreenManager con las tres pantallas y maneja el récord."""

    title = 'Luciérnagas'

    def build(self):
        Window.clearcolor = (*AZUL_NOCHE, 1)
        # El récord se guarda en un archivo JSON dentro de la carpeta de
        # datos del usuario (cambia según el sistema operativo).
        self.almacen = JsonStore(os.path.join(self.user_data_dir, 'record.json'))

        gestor = ScreenManager(transition=FadeTransition(duration=0.4))
        gestor.add_widget(MenuScreen(name='menu'))
        gestor.add_widget(JuegoScreen(name='juego'))
        gestor.add_widget(FinScreen(name='fin'))
        return gestor

    def obtener_record(self):
        if self.almacen.exists('record'):
            return self.almacen.get('record')['puntos']
        return 0

    def guardar_record(self, puntos):
        """Guarda el puntaje si supera el récord. Devuelve True si es nuevo."""
        if puntos > self.obtener_record():
            self.almacen.put('record', puntos=puntos)
            return True
        return False


if __name__ == '__main__':
    LuciernagasApp().run()
