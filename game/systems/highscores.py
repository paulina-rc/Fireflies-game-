"""
Guardar y cargar el récord (mejor puntaje y noche máxima).

Usa JsonStore de Kivy, que guarda un diccionario en un archivo JSON.
"""

from kivy.storage.jsonstore import JsonStore

from ..config import HIGHSCORE_KEY, HIGHSCORE_NIGHT_FIELD, HIGHSCORE_SCORE_FIELD


class HighScores:
    """Lee y escribe el récord en el archivo JSON indicado."""

    def __init__(self, path):
        self.store = JsonStore(path)

    def get(self):
        """Devuelve (mejor puntaje, noche máxima)."""
        if self.store.exists(HIGHSCORE_KEY):
            data = self.store.get(HIGHSCORE_KEY)
            return data.get(HIGHSCORE_SCORE_FIELD, 0), data.get(HIGHSCORE_NIGHT_FIELD, 1)
        return 0, 1

    def save_result(self, score, night):
        """Guarda el récord si se superó. Devuelve True si el puntaje es
        un nuevo récord."""
        best_score, best_night = self.get()
        is_new = score > best_score
        if is_new or night > best_night:
            self.store.put(HIGHSCORE_KEY, **{
                HIGHSCORE_SCORE_FIELD: max(score, best_score),
                HIGHSCORE_NIGHT_FIELD: max(night, best_night),
            })
        return is_new
