"""
La aplicación: crea el ScreenManager con las cuatro pantallas, maneja las
teclas que funcionan en cualquier pantalla (F11 y ESC en "Cómo jugar") y
abre el archivo del récord.
"""

import os

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from .config import (APP_DATA_NAME, APP_TITLE, HIGHSCORE_FILE, KEY_ESCAPE,
                     KEY_F11, NIGHT_BLUE, SCREEN_GAME, SCREEN_GAME_OVER,
                     SCREEN_HOW_TO_PLAY, SCREEN_MENU,
                     SCREEN_TRANSITION_DURATION, WINDOW_MIN_HEIGHT,
                     WINDOW_MIN_WIDTH)
from .screens.game_over import GameOverScreen
from .screens.game_screen import GameScreen
from .screens.how_to_play import HowToPlayScreen
from .screens.menu import MenuScreen
from .systems.highscores import HighScores


class FirefliesApp(App):
    """App principal del juego Luciérnagas."""

    title = APP_TITLE

    @property
    def name(self):
        """Kivy usa este nombre para la carpeta de datos del usuario
        (user_data_dir). Se deja el de la versión anterior para que el
        récord guardado no se pierda."""
        return APP_DATA_NAME

    def build(self):
        Window.clearcolor = (*NIGHT_BLUE, 1)
        Window.minimum_width, Window.minimum_height = WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
        # El récord se guarda en un JSON dentro de la carpeta de datos del
        # usuario (la ruta depende del sistema operativo).
        self.highscores = HighScores(os.path.join(self.user_data_dir, HIGHSCORE_FILE))
        # Teclas que funcionan en cualquier pantalla (F11).
        Window.bind(on_key_down=self.global_key)

        self.screens = ScreenManager(transition=FadeTransition(duration=SCREEN_TRANSITION_DURATION))
        self.screens.add_widget(MenuScreen(name=SCREEN_MENU))
        self.screens.add_widget(HowToPlayScreen(name=SCREEN_HOW_TO_PLAY))
        self.screens.add_widget(GameScreen(name=SCREEN_GAME))
        self.screens.add_widget(GameOverScreen(name=SCREEN_GAME_OVER))
        return self.screens

    def global_key(self, window, key, scancode, text, modifiers):
        if key == KEY_F11:
            # 'auto' usa la resolución del monitor; False vuelve a ventana.
            Window.fullscreen = False if Window.fullscreen else 'auto'
            return True
        if key == KEY_ESCAPE and self.screens.current == SCREEN_HOW_TO_PLAY:
            self.screens.current = SCREEN_MENU
            return True
        return False
