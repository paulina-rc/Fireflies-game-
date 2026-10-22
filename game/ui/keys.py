"""
Teclas dibujadas para el panel de controles del menú.

KeyCap dibuja una tecla (recuadro con relieve y una letra o una flecha).
KeyCluster las acomoda en cruz, como WASD. El panel completo
(ControlsPanel) se arma en kv/menu.kv.
"""

from kivy.graphics import Color, Line, RoundedRectangle, Triangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from ..config import CREAM, KEY_SHADOW_COLOR, KEY_SIZE, KEY_SPACING

KEY_RADIUS = 9    # bordes redondeados de la tecla
ARROW_SIZE = 8    # tamaño del triángulo de las flechas


class KeyCap(Label):
    """Una tecla. 'arrow' puede ser 'up', 'down', 'left' o 'right' (dibuja
    una flecha en vez de texto). 'width_units' = cuántas teclas de ancho
    mide (la barra espaciadora es más ancha)."""

    arrow = StringProperty('')
    width_units = NumericProperty(1.0)

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(16))
        kwargs.setdefault('bold', True)
        kwargs.setdefault('color', (*CREAM, 0.95))
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        with self.canvas.before:
            Color(*KEY_SHADOW_COLOR)
            self.shadow = RoundedRectangle()
            Color(*CREAM, 0.10)
            self.face = RoundedRectangle()
            Color(*CREAM, 0.45)
            self.border = Line(width=dp(1.1))
            self.arrow_color = Color(*CREAM, 0)
            self.triangle = Triangle()
        self.bind(pos=self._redraw, size=self._redraw, arrow=self._redraw,
                  width_units=self._resize)
        self._resize()

    def _resize(self, *args):
        side = dp(KEY_SIZE)
        self.size = (side * self.width_units, side)

    def _redraw(self, *args):
        radius = dp(KEY_RADIUS)
        self.shadow.pos = (self.x, self.y - dp(3))  # da sensación de relieve
        self.shadow.size = self.size
        self.shadow.radius = [radius]
        self.face.pos = self.pos
        self.face.size = self.size
        self.face.radius = [radius]
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, radius)
        self.arrow_color.a = 0.95 if self.arrow else 0
        if self.arrow:
            cx, cy, r = self.center_x, self.center_y, dp(ARROW_SIZE)
            tips = {
                'up': [cx - r, cy - r * 0.6, cx + r, cy - r * 0.6, cx, cy + r * 0.8],
                'down': [cx - r, cy + r * 0.6, cx + r, cy + r * 0.6, cx, cy - r * 0.8],
                'left': [cx + r * 0.6, cy - r, cx + r * 0.6, cy + r, cx - r * 0.8, cy],
                'right': [cx - r * 0.6, cy - r, cx - r * 0.6, cy + r, cx + r * 0.8, cy],
            }
            self.triangle.points = tips[self.arrow]


class KeyGap(Widget):
    """Espacio vacío del tamaño de una tecla (para armar la cruz)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(KEY_SIZE), dp(KEY_SIZE))


class KeyCluster(GridLayout):
    """Grilla de 3 x 2 para poner las teclas en cruz: una arriba y tres
    abajo (como WASD)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        side, gap = dp(KEY_SIZE), dp(KEY_SPACING)
        self.cols = 3
        self.spacing = gap
        self.size_hint = (None, None)
        self.size = (side * 3 + gap * 2, side * 2 + gap)


class ControlsPanel(BoxLayout):
    """Panel del menú que muestra los controles. Su diseño está en menu.kv."""
