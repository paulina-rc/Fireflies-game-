# Luciérnagas

Juego tranquilo hecho en Python con Kivy. Es de noche en un estanque y aparecen
luciérnagas que flotan, brillan unos segundos y se apagan. Tienes que tocarlas
antes de que se apaguen. Cada partida dura 60 segundos.

Todo se dibuja con el canvas de Kivy: el juego no usa imágenes ni sonidos externos.

## Instalación

1. Instala Python 3.9 o más reciente.
2. Instala Kivy:
   ```
   pip install "kivy>=2.3"
   ```
3. Ejecuta el juego:
   ```
   python main.py
   ```

## Cómo jugar

- Toca (o haz clic en) las luciérnagas para atraparlas.
- **Amarilla:** +1 punto.
- **Dorada** (rara, más pequeña y rápida): +5 puntos.
- **Azul** (muy rara): congela el tiempo por 3 segundos.
- **Combo:** cada 3 luciérnagas seguidas sube el multiplicador (x2, x3… hasta x5).
  Si dejas que una se apague, el combo vuelve a x1.
- Tocar el agua vacía no quita puntos, solo hace una onda.
- Con el tiempo aparecen más seguido y duran un poco menos.
- El récord se guarda solo y se muestra en el menú.

## Estructura del código

Todo está en `main.py`, dividido en secciones:

| Parte | Qué hace |
|---|---|
| Configuración y constantes | Tamaño de la ventana (450x800), paleta de colores, duración de la partida. |
| `obtener_textura_cielo()` | Crea una textura de 1x256 píxeles con el degradado del cielo, que luego se estira a toda la pantalla. |
| `FondoNocturno` | Dibuja el cielo, la luna, las estrellas que titilan, el agua con brillos y los juncos que se mecen (hechos con curvas de Bézier). |
| `Firefly` | Una luciérnaga: núcleo + 3 halos que laten. Se mueve con seno y coseno, se enciende, vive unos segundos y se desvanece. |
| `Particle`, `Ripple`, `TextoFlotante` | Efectos: chispas al atrapar, ondas en el agua y el texto "+1" que sube. |
| `BotonRedondeado`, `CapaPausa`, `EnjambreDecorativo` | Botones propios, menú de pausa y luciérnagas de adorno para el menú. |
| `PantallaAnimada` | Pantalla base con un bucle a 60 FPS que se inicia y se detiene (así no quedan `Clock` corriendo). |
| `MenuScreen`, `JuegoScreen`, `FinScreen` | Las tres pantallas, manejadas con `ScreenManager` y `FadeTransition`. |
| `LuciernagasApp` | Crea las pantallas y guarda el récord con `JsonStore` en `App.user_data_dir`. |

**Idea principal del bucle de juego:** `JuegoScreen.bucle(dt)` se ejecuta 60 veces
por segundo. Todos los movimientos se multiplican por `dt` (los segundos que pasaron
desde el cuadro anterior), así el juego va a la misma velocidad aunque cambien los FPS.
