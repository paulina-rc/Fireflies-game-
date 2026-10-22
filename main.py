"""
Luciérnagas: punto de entrada del juego.

Ejecuta:  python main.py
Todo el código del juego está en el paquete game/.
"""

from game.config import apply_window_config

# La ventana se configura ANTES de importar el resto de Kivy.
apply_window_config()

from game.app import FirefliesApp  # noqa: E402

if __name__ == '__main__':
    FirefliesApp().run()
