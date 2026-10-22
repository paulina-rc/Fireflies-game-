"""
Etiqueta de texto que usan todas las pantallas.

Es un Label normal con valores por defecto del juego: color crema, texto
centrado y markup activado (para usar [b], [color=...] y [size=...]).
"""

from kivy.uix.label import Label

from ..config import CREAM


class TextLabel(Label):
    """Label cuyo texto se alinea dentro de su propio tamaño (por eso se
    enlaza text_size con size). Se usa desde los archivos .kv."""

    def __init__(self, **kwargs):
        kwargs.setdefault('color', (*CREAM, 1))
        kwargs.setdefault('halign', 'center')
        kwargs.setdefault('valign', 'middle')
        kwargs.setdefault('markup', True)
        super().__init__(**kwargs)
        self.bind(size=self._fit_text)

    def _fit_text(self, instance, size):
        self.text_size = size
