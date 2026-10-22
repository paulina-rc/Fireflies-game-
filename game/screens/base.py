"""
Base común de las pantallas.

AnimatedScreen: pantalla con un bucle a 60 FPS que se inicia y se detiene.
load_kv: carga un archivo de diseño de la carpeta game/kv.
"""

import os

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from ..config import FPS, MAX_FRAME_TIME

KV_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kv')


def load_kv(filename):
    """Carga un archivo .kv de la carpeta game/kv con Builder.load_file."""
    Builder.load_file(os.path.join(KV_FOLDER, filename))


class AnimatedScreen(Screen):
    """Pantalla con un bucle a 60 FPS que se puede iniciar y detener.
    Guardar el evento del Clock permite cancelarlo después, para que no
    queden procesos corriendo cuando la pantalla no se ve."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop_event = None

    def start_loop(self):
        if self.loop_event is None:
            self.loop_event = Clock.schedule_interval(self._tick, 1 / FPS)

    def stop_loop(self):
        if self.loop_event is not None:
            self.loop_event.cancel()
            self.loop_event = None

    def _tick(self, dt):
        # Limita dt para evitar saltos grandes si la ventana se congela.
        self.loop(min(dt, MAX_FRAME_TIME))

    def loop(self, dt):
        """Lo redefine cada pantalla: se llama en cada cuadro."""

    def go_to(self, screen_name):
        self.manager.current = screen_name
