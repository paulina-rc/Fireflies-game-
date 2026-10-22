"""
Botón redondeado con hover.

ButtonBehavior le da el comportamiento de botón y Label el texto. Se
ilumina cuando el mouse pasa encima (hover) y al presionarlo.
"""

from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label

from ..config import (BUTTON_BORDER, BUTTON_FILL_NORMAL, BUTTON_FILL_PRIMARY,
                      BUTTON_MAX_RADIUS, CREAM, YELLOW)


class RoundedButton(ButtonBehavior, Label):
    """Botón con bordes redondeados y fondo semitransparente.
    primary=True lo pinta amarillo (botón principal de la pantalla)."""

    primary = BooleanProperty(False)
    hover = BooleanProperty(False)

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(21))
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        with self.canvas.before:
            self.fill_color = Color()
            self.fill = RoundedRectangle()
            self.border_color = Color()
            self.border = Line(width=dp(1.3))
        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw,
                  hover=self._redraw, primary=self._update_tone)
        # Window.mouse_pos cambia cada vez que se mueve el mouse.
        Window.bind(mouse_pos=self._mouse_moved)
        self._update_tone()

    @property
    def tone(self):
        return YELLOW if self.primary else CREAM

    def _update_tone(self, *args):
        self.color = (*self.tone, 1)
        self._redraw()

    def _mouse_moved(self, window, position):
        # get_root_window() es None si el botón no está en pantalla
        # (por ejemplo, si su pantalla no es la actual).
        self.hover = (self.get_root_window() is not None and
                      self.collide_point(*self.to_widget(*position)))

    def _redraw(self, *args):
        radius = min(self.height / 2, self.width / 2, dp(BUTTON_MAX_RADIUS)) * 0.99
        self.fill.pos = self.pos
        self.fill.size = self.size
        self.fill.radius = [radius]
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, radius)
        # Tres niveles de brillo: normal, mouse encima, presionado.
        if self.state == 'down':
            level = 2
        elif self.hover:
            level = 1
        else:
            level = 0
        fills = BUTTON_FILL_PRIMARY if self.primary else BUTTON_FILL_NORMAL
        self.fill_color.rgba = (*self.tone, fills[level])
        self.border_color.rgba = (*self.tone, BUTTON_BORDER[level])
