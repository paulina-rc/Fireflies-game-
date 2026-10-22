"""
Capas que se ponen encima del juego: el menú de pausa y el cartel
"Noche N" que aparece entre noches. Su diseño está en kv/game_screen.kv.
"""

from kivy.uix.floatlayout import FloatLayout


class PauseOverlay(FloatLayout):
    """Velo oscuro con el menú de pausa. Bloquea los clics al juego.

    Lanza los eventos on_resume (botón Continuar) y on_menu (botón Menú),
    que la pantalla de juego escucha con bind().
    """

    __events__ = ('on_resume', 'on_menu')

    def on_resume(self):
        pass

    def on_menu(self):
        pass

    def on_touch_down(self, touch):
        super().on_touch_down(touch)  # los botones sí reciben el clic
        return True                   # pero no pasa al juego


class NightBanner(FloatLayout):
    """Cartel "Noche 2" entre noches. Se muestra y oculta con opacity."""

    def show_night(self, night, goal):
        self.ids.title.text = f'Noche {night}'
        self.ids.subtitle.text = f'Entrega {goal} luciérnagas en el nido'
