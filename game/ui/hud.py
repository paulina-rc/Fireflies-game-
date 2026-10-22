"""
HUD: los marcadores que se ven durante la partida.

Izquierda = vidas y progreso de la noche, centro = puntaje, cola y
power-ups activos, derecha = enfriamiento del dash. La posición de cada
marcador está en kv/game_screen.kv; aquí solo está cómo se dibujan y
cómo se actualizan.
"""

from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle, Triangle
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from ..config import (CREAM, GOLD_HEX, ICE_BLUE_HEX, MAX_LIVES, MAX_TAIL,
                      PINK, YELLOW)
from ..drawing import place_heart, set_circle
from ..systems.levels import delivery_multiplier
from .labels import TextLabel


class HeartIcon(Widget):
    """Corazón del HUD: lleno (vida disponible) o apagado (vida perdida)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(*PINK, 1)
            self.circle_1, self.circle_2 = Ellipse(), Ellipse()
            self.triangle = Triangle()
        self.bind(pos=self._redraw, size=self._redraw)

    def set_full(self, full):
        self.color.rgba = (*PINK, 1) if full else (*CREAM, 0.15)

    def _redraw(self, *args):
        r = min(self.width, self.height) * 0.45
        place_heart(self.circle_1, self.circle_2, self.triangle,
                    self.center_x, self.center_y, r)


class DashIndicator(Widget):
    """Arco circular que se llena mientras el dash se recarga."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.glow_color = Color(*YELLOW, 0)
            self.glow = Ellipse()
            Color(*CREAM, 0.12)
            self.track = Line(width=dp(3))
            self.arc_color = Color(*CREAM, 0.7)
            self.arc = Line(width=dp(3.2), cap='round')
        self.label = TextLabel(text='', font_size=sp(13), bold=True)
        self.add_widget(self.label)
        self.progress = 1.0
        self.bind(pos=self._redraw, size=self._redraw)

    def set_progress(self, progress, seconds):
        self.progress = progress
        self.label.text = 'DASH' if progress >= 1 else f'{seconds:.1f}'
        self._redraw()

    def _redraw(self, *args):
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - dp(4)
        self.label.pos = self.pos
        self.label.size = self.size
        self.track.circle = (cx, cy, r)
        ready = self.progress >= 1
        self.arc_color.rgba = (*YELLOW, 1) if ready else (*CREAM, 0.75)
        self.label.color = (*YELLOW, 1) if ready else (*CREAM, 0.8)
        self.glow_color.a = 0.14 if ready else 0
        set_circle(self.glow, cx, cy, r * 1.35)
        # Line(circle=(x, y, radio, ángulo_inicio, ángulo_fin)), en grados.
        self.arc.circle = (cx, cy, r, 0, max(1.0, 360 * self.progress))


class GoalBar(Widget):
    """Barra delgada que muestra cuánto falta para la meta de la noche."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0.0
        with self.canvas:
            Color(*CREAM, 0.12)
            self.track = RoundedRectangle(radius=[dp(3)])
            Color(*YELLOW, 0.9)
            # Rectangle normal: un RoundedRectangle de ancho 0 no se
            # redibuja bien y la barra quedaba llena.
            self.fill = Rectangle()
        self.bind(pos=self._redraw, size=self._redraw)

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self._redraw()

    def _redraw(self, *args):
        self.track.pos = self.pos
        self.track.size = self.size
        self.fill.pos = self.pos
        self.fill.size = (self.width * self.progress, self.height)


class HUD(FloatLayout):
    """Marcadores del juego. Sus widgets (ids) se definen en game_screen.kv."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hearts = [HeartIcon() for _ in range(MAX_LIVES)]

    def on_kv_post(self, base_widget):
        # Kivy llama a esto cuando ya aplicó el diseño del .kv; antes de
        # eso self.ids todavía está vacío.
        # Un corazón por cada vida posible.
        for heart in self.hearts:
            self.ids.lives_box.add_widget(heart)

    def update(self, game):
        """Copia el estado de la partida (GameScreen) a los marcadores."""
        levels = game.levels
        ids = self.ids
        for i, heart in enumerate(self.hearts):
            heart.set_full(i < game.lives)
        ids.night_label.text = f'NOCHE {levels.night}'
        ids.goal_label.text = (f'{min(levels.delivered_tonight, levels.goal)} / '
                               f'{levels.goal} luciérnagas')
        ids.goal_bar.set_progress(levels.delivered_tonight / levels.goal)

        ids.score_label.text = str(game.score)
        count = len(game.tail)
        text = f'Cola {count} / {MAX_TAIL}'
        multiplier = delivery_multiplier(count)
        if multiplier > 1:
            text += f'   [color={GOLD_HEX}][b]x{multiplier}[/b][/color]'
        ids.tail_label.text = text

        states = []
        if game.frozen > 0:
            states.append(f'[color={ICE_BLUE_HEX}]Murciélagos congelados {game.frozen:.1f} s[/color]')
        if game.magnet > 0:
            states.append(f'[color={GOLD_HEX}]Imán {game.magnet:.1f} s[/color]')
        ids.status_label.text = '     '.join(states)

        player = game.player
        ids.dash_indicator.set_progress(player.dash_progress, player.cooldown)
