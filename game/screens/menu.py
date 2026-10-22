"""
Menú principal: título, botones Jugar y Cómo jugar, récord y panel de
controles. El diseño está en kv/menu.kv.
"""

from kivy.app import App

# Se importan para que Kivy conozca los widgets que usa menu.kv.
from ..ui import background, buttons, decorations, keys, labels  # noqa: F401
from .base import AnimatedScreen, load_kv


class MenuScreen(AnimatedScreen):
    """Pantalla del menú. Anima el fondo y las luciérnagas de adorno."""

    def on_pre_enter(self, *args):
        score, night = App.get_running_app().highscores.get()
        self.ids.record_label.text = (f'Récord: [b]{score}[/b] puntos    ·    '
                                      f'Noche máxima: [b]{night}[/b]')
        self.start_loop()

    def on_leave(self, *args):
        self.stop_loop()
        self.ids.swarm.clear()

    def loop(self, dt):
        self.ids.background.update(dt)
        self.ids.swarm.update(dt)


load_kv('menu.kv')
