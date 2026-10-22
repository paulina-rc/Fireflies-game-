# Luciérnagas

Juego para computadora hecho en Python con Kivy. Eres un espíritu de luz que vuela
sobre un estanque de noche. Tienes que juntar luciérnagas en una cola que te sigue
como una serpiente de luz, llevarlas al nido y esquivar a los murciélagos.

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

## Controles

| Tecla | Acción |
|---|---|
| W A S D o flechas | Moverse |
| Espacio | Impulso (dash) |
| Esc | Pausar / continuar |
| F11 | Pantalla completa |

El mouse solo se usa en los menús.

## Cómo jugar

- **Luciérnagas:** tócalas para sumarlas a tu cola (máximo 15).
- **Nido:** entra con tu cola para entregarlas. Puntos = luciérnagas × multiplicador
  (5 o más: x2, 10 o más: x3).
- **Murciélagos:** te persiguen. Si te tocan y tienes cola, la cola se dispersa;
  si no tienes cola, pierdes una vida. Tienes 3 vidas.
- **Dash:** un impulso rápido que atraviesa murciélagos sin daño. Se recarga en 2 segundos.
- **Power-ups** (duran 6 s en el mapa):
  - Luna azul: congela a los murciélagos por 4 s.
  - Estrella dorada: imán, las luciérnagas cercanas vuelan hacia ti por 5 s.
  - Corazón: +1 vida (máximo 3).
- **Noches:** cada noche tiene una meta (Noche 1: 10 luciérnagas, y +5 por noche).
  Al cumplirla empieza la siguiente noche, con un murciélago más, murciélagos más
  rápidos y el nido en otro lugar. Desde la Noche 4 aparece la **luciérnaga fugaz**,
  que huye de ti y vale el triple.
- El juego termina al perder las 3 vidas. El récord (puntaje y noche máxima) se guarda solo.

## Estructura del código

Todo está en `main.py`, dividido en 9 secciones numeradas:

| Sección | Qué contiene |
|---|---|
| 1. Configuración | Ventana de 1280x720, ESC sin cerrar la app, constantes y códigos de teclas. |
| 2. Ayudas | Paleta de colores, degradado del cielo (textura de 1x256 píxeles) y dibujo del corazón. |
| 3. `FondoNocturno` | Cielo, luna, estrellas que titilan, agua y juncos. Cada noche el cielo es más morado. |
| 4. Elementos del juego | `Jugador` (aceleración, fricción, dash y estela), `Luciernaga` (estados libre, cola, dispersa y entregando), `Nido`, `Murcielago` (persigue con giro limitado) y `PowerUp`. |
| 5. Efectos | `Particula`, `TextoFlotante` y `AnilloDestello`. |
| 6. `GestorNiveles` | Reglas de cada noche: meta, cantidad y velocidad de murciélagos. |
| 7. Interfaz | `BotonRedondeado` (con hover), `Tecla`, `PanelControles`, `HUD`, `CapaPausa`, `AvisoNoche` y `Vitrina`. |
| 8. Pantallas | `MenuScreen`, `ComoJugarScreen`, `JuegoScreen` y `FinScreen`. |
| 9. `LuciernagasApp` | Crea las pantallas, maneja F11 y guarda el récord con `JsonStore`. |

**Ideas principales:**

- **Bucle del juego:** `JuegoScreen.bucle(dt)` se ejecuta 60 veces por segundo con
  `Clock.schedule_interval`. Todo movimiento se multiplica por `dt`, así el juego va
  a la misma velocidad aunque cambien los FPS. Al pausar o salir, el Clock se cancela.
- **Teclado:** `Window.bind(on_key_down, on_key_up)` guarda en un `set` las teclas
  presionadas. Se desvincula al salir de la pantalla de juego.
- **Colisiones:** dos círculos chocan si la distancia entre sus centros es menor que
  la suma de sus radios (`math.hypot`).
- **Cola:** cada luciérnaga se acerca con interpolación a la anterior (la primera
  sigue al jugador), quedando siempre a la misma distancia.
- **Sacudida:** el fondo y el juego están dentro de un widget con un `Translate`
  que se mueve unos píxeles al azar cuando te golpean. El HUD no se mueve.
