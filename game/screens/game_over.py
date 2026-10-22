"""
Pantalla de fin de partida: puntaje, noche alcanzada, total de
luciérnagas entregadas y récord. El diseño está en kv/game_over.kv.
"""

import math

from kivy.properties import BooleanProperty

# Se importan para que Kivy conozca los widgets que usa game_over.kv.
from ..ui import background, buttons, decorations, labels  # noqa: F401
from .base import AnimatedScreen, load_kv


class GameOverScreen(AnimatedScreen):
    """Muestra el resultado de la partida que acaba de terminar."""

    new_record = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.t = 0.0

    def show_result(self, score, night, delivered, record, new_record):
        """La llama GameScreen antes de cambiar a esta pantalla."""
        ids = self.ids
        self.new_record = new_record
        ids.score_label.text = str(score)
        ids.detail_label.text = (f'Noche alcanzada: [b]{night}[/b]        '
                                 f'Luciérnagas entregadas: [b]{delivered}[/b]')
        best_score, best_night = record
        ids.record_label.text = (f'Récord: {best_score} puntos  ·  '
                                 f'Noche máxima: {best_night}')
        ids.new_record_label.opacity = 1 if new_record else 0

    def on_pre_enter(self, *args):
        self.start_loop()

    def on_leave(self, *args):
        self.stop_loop()
        self.ids.swarm.clear()

    def loop(self, dt):
        self.t += dt
        self.ids.background.update(dt)
        self.ids.swarm.update(dt)
        if self.new_record:
            # El texto de nuevo récord "respira" suavemente.
            self.ids.new_record_label.opacity = 0.7 + 0.3 * math.sin(self.t * 3)


load_kv('game_over.kv')
