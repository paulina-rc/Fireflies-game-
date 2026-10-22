"""
Pantalla "Cómo jugar": explica cada elemento del juego con su dibujo
animado al lado. El diseño está en kv/how_to_play.kv; aquí se arma la
lista de elementos (cada fila tiene un dibujo y un texto).
"""

from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from ..config import (DELIVERY_MULTIPLIERS, FLEETING_MIN_NIGHT,
                      FREEZE_DURATION, MAGNET_DURATION, MAX_LIVES, MAX_TAIL,
                      POWERUP_HEART, POWERUP_MOON, POWERUP_STAR, YELLOW_HEX)
from ..entities.bat import Bat
from ..entities.firefly import Firefly
from ..entities.nest import Nest
from ..entities.player import Player
from ..entities.powerup import PowerUp
# Se importan para que Kivy conozca los widgets que usa how_to_play.kv.
from ..ui import background, buttons, labels  # noqa: F401
from ..ui.decorations import Showcase
from .base import AnimatedScreen, load_kv

SHOWCASE_WIDTH = 90


def _firefly(layer, fleeting=False):
    firefly = Firefly(layer, 0, 0, fleeting=fleeting)
    firefly.appear = 1.0  # que se vea encendida desde el principio
    return firefly


def _powerup(kind):
    def factory(layer):
        powerup = PowerUp(layer, kind, 0, 0)
        powerup.age = 1.0  # para que no parpadee
        return powerup
    return factory


def _showcase_items():
    """Lista de (crear dibujo, escala, título, descripción)."""
    (big_count, big_mult), (small_count, small_mult) = DELIVERY_MULTIPLIERS
    return [
        (lambda layer: Player(layer, 0, 0), 0.7, 'Tú: espíritu de luz',
         'Muévete con WASD o las flechas. Espacio hace un impulso (dash) que atraviesa murciélagos.'),
        (_firefly, 1.3, 'Luciérnaga',
         f'Tócala para sumarla a tu cola. La cola te sigue en fila (máximo {MAX_TAIL}).'),
        (Nest, 0.6, 'Nido',
         f'Entra con tu cola para entregarlas. Con {small_count} o más ganas x{small_mult}, '
         f'con {big_count} o más x{big_mult}.'),
        (lambda layer: Bat(layer, 0, 0, 0), 1.0, 'Murciélago',
         'Te persigue. Si te toca pierdes la cola; si no tienes cola, pierdes una vida.'),
        (_powerup(POWERUP_MOON), 1.0, 'Luna azul',
         f'Congela a los murciélagos por {FREEZE_DURATION:g} segundos.'),
        (_powerup(POWERUP_STAR), 1.0, 'Estrella dorada',
         f'Imán: las luciérnagas cercanas vuelan solas hacia ti por {MAGNET_DURATION:g} segundos.'),
        (_powerup(POWERUP_HEART), 1.0, 'Corazón',
         f'Recupera una vida (máximo {MAX_LIVES}).'),
        (lambda layer: _firefly(layer, fleeting=True), 1.3, 'Luciérnaga fugaz',
         f'Aparece desde la Noche {FLEETING_MIN_NIGHT}. Huye de ti, pero vale el triple.'),
    ]


class ShowcaseRow(BoxLayout):
    """Una fila de la explicación. El texto se diseña en how_to_play.kv y
    el dibujo animado (Showcase) se agrega a la izquierda desde Python."""

    text = StringProperty('')


class HowToPlayScreen(AnimatedScreen):
    """Pantalla de instrucciones con dibujos animados."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.showcases = []
        for factory, scale, title, description in _showcase_items():
            row = ShowcaseRow(text=f'[b][color={YELLOW_HEX}]{title}[/color][/b]\n{description}')
            showcase = Showcase(factory, scale, size_hint=(None, 1), width=dp(SHOWCASE_WIDTH))
            # index=len(children) lo pone primero (a la izquierda del texto).
            row.add_widget(showcase, index=len(row.children))
            self.showcases.append(showcase)
            self.ids.grid.add_widget(row)

    def on_pre_enter(self, *args):
        self.start_loop()

    def on_leave(self, *args):
        self.stop_loop()

    def loop(self, dt):
        self.ids.background.update(dt)
        for showcase in self.showcases:
            showcase.animate(dt)


load_kv('how_to_play.kv')
