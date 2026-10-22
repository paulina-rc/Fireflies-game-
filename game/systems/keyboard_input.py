"""
Manejo del teclado durante la partida.

Window.bind(on_key_down, on_key_up) avisa cuando se presiona o suelta una
tecla. Aquí se guardan en un set las teclas que están presionadas, y de
ahí se calcula la dirección de movimiento y si se pidió el dash.

(Se llama keyboard_input.py y no input.py para no confundirse con la
función input() de Python.)
"""

from kivy.core.window import Window

from ..config import KEY_ESCAPE, KEY_SPACE, KEYS_DOWN, KEYS_LEFT, KEYS_RIGHT, KEYS_UP


class KeyboardInput:
    """Escucha el teclado y recuerda qué teclas están presionadas.

    on_escape: función que se llama al presionar ESC (pausa).
    paused: mientras es True solo se escucha ESC.
    """

    def __init__(self, on_escape):
        self.on_escape = on_escape
        self.pressed = set()        # teclas presionadas ahora
        self.dash_requested = False
        self.paused = False
        self.active = False

    def activate(self):
        if not self.active:
            Window.bind(on_key_down=self._key_down, on_key_up=self._key_up)
            self.active = True

    def deactivate(self):
        if self.active:
            Window.unbind(on_key_down=self._key_down, on_key_up=self._key_up)
            self.active = False
        self.pressed.clear()

    def clear(self):
        """Olvida las teclas presionadas (por ejemplo al pausar)."""
        self.pressed.clear()

    def reset(self):
        self.pressed.clear()
        self.dash_requested = False

    def _key_down(self, window, key, scancode, text, modifiers):
        if key == KEY_ESCAPE:
            self.on_escape()
            return True  # True = "ya lo manejé"
        if self.paused:
            return False
        # Al mantener una tecla, Kivy repite el evento; el dash solo se
        # pide la primera vez (cuando todavía no estaba en el set).
        if key == KEY_SPACE and key not in self.pressed:
            self.dash_requested = True
        self.pressed.add(key)
        return False  # deja pasar otras teclas (como F11)

    def _key_up(self, window, key, scancode):
        self.pressed.discard(key)
        return False

    def direction(self):
        """Convierte las teclas presionadas en una dirección (dx, dy),
        donde cada valor es -1, 0 o 1."""
        dx = (1 if self.pressed & KEYS_RIGHT else 0) - (1 if self.pressed & KEYS_LEFT else 0)
        dy = (1 if self.pressed & KEYS_UP else 0) - (1 if self.pressed & KEYS_DOWN else 0)
        return dx, dy

    def take_dash_request(self):
        """Devuelve True una sola vez por cada vez que se presionó Espacio."""
        requested = self.dash_requested
        self.dash_requested = False
        return requested
