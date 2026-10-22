"""
Pantalla de juego y bucle principal.

Coordina todo lo que pasa en la partida: jugador, cola de luciérnagas,
nido, murciélagos, power-ups, noches, pausa y fin del juego. El diseño de
la pantalla (HUD, cartel de noche y pausa) está en kv/game_screen.kv.
"""

import math
import random

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import InstructionGroup
from kivy.metrics import dp, sp

from ..config import (BAT_SPAWN_MIN_DISTANCE, BAT_SPAWN_TRIES, BAT_STUN_TIME,
                      CREAM, DASH_BURST_PARTICLES, DASH_TRAIL_LIFE,
                      DASH_TRAIL_SPEED, DEATH_PARTICLE_LIFE,
                      DEATH_PARTICLE_SPEED, DEATH_PARTICLES, DELIVERY_PARTICLES,
                      DELIVERY_RINGS, DELIVERY_STAGGER, FIREFLY_PICKUP_REACH,
                      FIREFLY_SPAWN_INTERVAL, FIREFLY_SPAWN_MIN_DISTANCE,
                      FLEETING_CHANCE, FLOATING_TEXT_TOP_GAP, FREEZE_DURATION,
                      GAME_OVER_DELAY, GOLD, HIT_INVULNERABILITY, HIT_PARTICLES,
                      HUD_BAND_HEIGHT, ICE_BLUE, INITIAL_FIREFLIES,
                      MAGNET_DURATION, MAX_LIVES, MAX_TAIL,
                      NIGHT_BANNER_DURATION, NIGHT_BANNER_FADE_IN,
                      NIGHT_BANNER_FADE_OUT, NIGHT_CHANGE_DELAY,
                      NIGHT_START_INVULNERABILITY, PICKUP_RING_DURATION,
                      PICKUP_RING_RADIUS, PINK, PLAY_AREA_MARGIN, PLAYER_LIGHT,
                      POWERUP_COLORS, POWERUP_FIRST_SPAWN, POWERUP_HEART,
                      POWERUP_MOON, POWERUP_PARTICLES, POWERUP_PICKUP_REACH,
                      POWERUP_RING, POWERUP_SPAWN_DELAY,
                      POWERUP_SPAWN_MIN_DISTANCE, POWERUP_STAR, SCATTER_SPEED,
                      SCREEN_GAME_OVER, SCREEN_MENU, SPAWN_TRIES,
                      TAIL_FOLLOW, TAIL_SPACING, YELLOW)
from ..effects.camera import ScreenShake
from ..effects.particles import FlashRing, FloatingText, Particle
from ..entities.bat import Bat
from ..entities.firefly import ARRIVED, DELIVERING, FREE, SCATTERED, TAIL, Firefly
from ..entities.nest import Nest
from ..entities.player import Player
from ..entities.powerup import PowerUp
from ..systems.collisions import circles_overlap, distance, is_within, point_distance
from ..systems.keyboard_input import KeyboardInput
from ..systems.levels import LevelManager, delivery_multiplier
# Se importan para que Kivy conozca los widgets que usa game_screen.kv.
from ..ui import background, buttons, hud, labels  # noqa: F401
from ..ui.overlays import NightBanner, PauseOverlay  # noqa: F401
from .base import AnimatedScreen, load_kv

# Estados de la partida
TRANSITION = 'transition'  # mostrando el cartel "Noche N"
PLAYING = 'playing'        # partida normal
ENDING = 'ending'          # el jugador perdió; espera un momento y va al final

# Capas de dibujo, en orden de abajo hacia arriba.
LAYERS = ('nest', 'fireflies', 'powerups', 'bats', 'player', 'effects')


class GameScreen(AnimatedScreen):
    """La partida."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # El "mundo" (ids.world) contiene el fondo y el juego. La sacudida
        # lo mueve sin mover el HUD.
        self.shake = ScreenShake(self.ids.world)
        self.layers = {}
        for name in LAYERS:
            self.layers[name] = InstructionGroup()
            self.ids.game_layer.canvas.add(self.layers[name])

        self.pause_overlay = PauseOverlay()
        self.pause_overlay.bind(on_resume=lambda *_: self.resume(),
                                on_menu=lambda *_: self.go_to(SCREEN_MENU))

        self.levels = LevelManager()
        self.keyboard = KeyboardInput(on_escape=self.toggle_pause)
        self.paused = False
        self.player = None
        self.nest = None
        self.fireflies = []     # todas las luciérnagas del mapa
        self.tail = []          # las que siguen al jugador, en orden
        self.bats = []
        self.powerup = None
        self.effects = []

    # ---------- Ciclo de vida de la pantalla ----------
    def on_pre_enter(self, *args):
        self.reset()

    def on_enter(self, *args):
        self.keyboard.activate()
        self.start_loop()

    def on_pre_leave(self, *args):
        # Al salir se detiene todo: bucle, teclado y pausa.
        self.stop_loop()
        self.keyboard.deactivate()
        self.hide_pause()

    def on_leave(self, *args):
        self.clear()

    def area(self):
        """Zona donde se puede volar (deja libre la franja del HUD)."""
        width, height = Window.size
        margin = dp(PLAY_AREA_MARGIN)
        return (margin, margin, width - margin, height - dp(HUD_BAND_HEIGHT))

    def reset(self):
        """Deja todo listo para una partida nueva."""
        self.clear()
        self.levels.reset()
        self.score = 0
        self.lives = MAX_LIVES
        self.frozen = 0.0           # segundos de murciélagos congelados
        self.magnet = 0.0           # segundos de imán
        self.firefly_wait = 0.0
        self.powerup_wait = random.uniform(*POWERUP_FIRST_SPAWN)
        self.night_change_wait = None  # cuenta atrás tras cumplir la meta
        self.ending_time = 0.0
        self.keyboard.reset()
        self.ids.background.set_night(1)
        self.shake.reset()

        xmin, ymin, xmax, ymax = self.area()
        self.nest = Nest(self.layers['nest'])
        self.player = Player(self.layers['player'], (xmin + xmax) / 2, (ymin + ymax) / 2)
        self.nest.move(self.area(), avoid=(self.player.x, self.player.y))
        self.nest.update(0, self.area())
        for _ in range(INITIAL_FIREFLIES):
            self.spawn_firefly()
        self.spawn_bats()
        self.start_transition(advance=False)
        self.ids.hud.update(self)

    def clear(self):
        """Borra todos los dibujos y listas."""
        for layer in self.layers.values():
            layer.clear()
        self.fireflies, self.tail, self.bats, self.effects = [], [], [], []
        self.powerup = None

    # ---------- Pausa ----------
    def toggle_pause(self):
        """La llama el teclado al presionar ESC."""
        if self.paused:
            self.resume()
        else:
            self.pause()

    def pause(self):
        if self.paused:
            return
        self.paused = True
        self.keyboard.paused = True
        self.stop_loop()  # el teclado sigue activo solo para escuchar ESC
        self.keyboard.clear()
        self.ids.root_layout.add_widget(self.pause_overlay)

    def resume(self):
        self.hide_pause()
        self.start_loop()

    def hide_pause(self):
        self.paused = False
        self.keyboard.paused = False
        if self.pause_overlay.parent:
            self.ids.root_layout.remove_widget(self.pause_overlay)

    # ---------- Noches ----------
    def start_transition(self, advance):
        """Muestra el cartel de la noche. Si advance=True, a mitad del
        cartel se prepara la noche siguiente."""
        self.game_state = TRANSITION
        self.transition_time = 0.0
        self.transition_advances = advance
        self.transition_applied = False
        night = self.levels.night + (1 if advance else 0)
        self.ids.banner.show_night(night, self.levels.goal_for(night))

    def update_transition(self, dt):
        self.transition_time += dt
        t, total = self.transition_time, NIGHT_BANNER_DURATION
        banner = self.ids.banner
        # Aparece, se queda, y desaparece al final.
        if t < NIGHT_BANNER_FADE_IN:
            banner.opacity = t / NIGHT_BANNER_FADE_IN
        elif t < total - NIGHT_BANNER_FADE_OUT:
            banner.opacity = 1
        else:
            banner.opacity = max(0.0, (total - t) / NIGHT_BANNER_FADE_OUT)
        # Cuando el cartel ya tapa el juego, se cambia la noche.
        if not self.transition_applied and t >= NIGHT_BANNER_FADE_IN:
            self.transition_applied = True
            if self.transition_advances:
                self.prepare_next_night()
        if t >= total:
            self.game_state = PLAYING
            banner.opacity = 0
            self.player.invulnerable = NIGHT_START_INVULNERABILITY  # un respiro al empezar
            self.keyboard.clear()

    def prepare_next_night(self):
        """Nueva noche: cielo más morado, nido en otro lugar y un
        murciélago más (y más rápidos)."""
        self.levels.next_night()
        self.ids.background.set_night(self.levels.night)
        self.nest.move(self.area(), avoid=(self.player.x, self.player.y))
        for bat in self.bats:
            bat.remove()
        self.bats = []
        self.spawn_bats()
        if self.powerup:
            self.powerup.remove()
            self.powerup = None
        self.frozen = self.magnet = 0.0

    def spawn_bats(self):
        """Los murciélagos nacen en los bordes, lejos del jugador."""
        xmin, ymin, xmax, ymax = self.area()
        for _ in range(self.levels.bat_count):
            for _ in range(BAT_SPAWN_TRIES):
                if random.random() < 0.5:
                    x = random.choice((xmin, xmax))
                    y = random.uniform(ymin, ymax)
                else:
                    x = random.uniform(xmin, xmax)
                    y = random.choice((ymin, ymax))
                if point_distance(x, y, self.player.x, self.player.y) > dp(BAT_SPAWN_MIN_DISTANCE):
                    break
            self.bats.append(Bat(self.layers['bats'], x, y, dp(self.levels.bat_speed)))

    # ---------- Bucle principal ----------
    def loop(self, dt):
        """Se ejecuta 60 veces por segundo. Todo se multiplica por dt
        (segundos desde el cuadro anterior), así el juego va a la misma
        velocidad aunque cambien los FPS."""
        area = self.area()
        self.ids.background.update(dt)
        self.update_effects(dt)
        self.shake.update(dt)
        self.nest.update(dt, area)

        if self.game_state == TRANSITION:
            self.update_transition(dt)
            self.player.draw()
            self.ids.hud.update(self)
            return
        if self.game_state == ENDING:
            self.ending_time += dt
            if self.ending_time >= GAME_OVER_DELAY:
                self.go_to_game_over()
            return

        self.update_player(dt, area)
        self.update_timers(dt)
        self.update_fireflies(dt, area)
        self.update_bats(dt, area)
        self.update_powerup(dt)

        # Cambio de noche (espera un poco para ver la entrega)
        if self.night_change_wait is not None:
            self.night_change_wait -= dt
            if self.night_change_wait <= 0:
                self.night_change_wait = None
                self.start_transition(advance=True)

        self.ids.hud.update(self)

    def update_player(self, dt, area):
        dx, dy = self.keyboard.direction()
        if self.keyboard.take_dash_request() and self.player.try_dash():
            self.burst(self.player.x, self.player.y, PLAYER_LIGHT, DASH_BURST_PARTICLES)
        self.player.update(dt, dx, dy, area)
        if self.player.is_dashing:
            # Chispas mientras dura el impulso
            self.effects.append(Particle(self.layers['effects'], self.player.x,
                                         self.player.y, PLAYER_LIGHT,
                                         speed=DASH_TRAIL_SPEED, life=DASH_TRAIL_LIFE))

    def update_timers(self, dt):
        """Temporizadores de los power-ups."""
        self.frozen = max(0.0, self.frozen - dt)
        self.magnet = max(0.0, self.magnet - dt)
        self.player.magnet = self.magnet > 0
        self.player.draw()

    def update_fireflies(self, dt, area):
        self.spawn_things(dt, area)
        self.move_tail(dt)
        for firefly in self.fireflies[:]:
            event = firefly.update(dt, area, self.player, self.magnet > 0, self.nest)
            if event == ARRIVED:
                self.burst(self.nest.x, self.nest.y, firefly.color, DELIVERY_PARTICLES)
            if firefly.finished:
                firefly.remove()
                self.fireflies.remove(firefly)
        self.pick_up_fireflies()
        if self.tail and is_within(self.player, self.nest, self.nest.radius):
            self.deliver()

    def update_bats(self, dt, area):
        for bat in self.bats:
            bat.frozen = self.frozen > 0
            bat.update(dt, self.player.x, self.player.y, area)
            if (not bat.frozen and self.player.invulnerable <= 0
                    and not self.player.is_dashing
                    and circles_overlap(self.player, bat)):
                self.hit(bat)
                if self.game_state != PLAYING:
                    break

    def update_powerup(self, dt):
        if self.powerup:
            self.powerup.update(dt)
            if is_within(self.player, self.powerup,
                         self.player.radius + dp(POWERUP_PICKUP_REACH)):
                self.collect_powerup()
            elif self.powerup.finished:
                self.powerup.remove()
                self.powerup = None

    # ---------- Efectos ----------
    def update_effects(self, dt):
        for effect in self.effects[:]:
            if not effect.update(dt):
                effect.remove()
                self.effects.remove(effect)

    def burst(self, x, y, color, count, **kwargs):
        """Lanza 'count' chispas desde (x, y)."""
        for _ in range(count):
            self.effects.append(Particle(self.layers['effects'], x, y, color, **kwargs))

    def ring(self, x, y, color, radius, duration):
        self.effects.append(FlashRing(self.layers['effects'], x, y, color, radius, duration))

    def floating_text(self, x, y, text, color, size=None):
        # Que el texto no suba por encima del área de juego (tapa el HUD).
        y = min(y, self.area()[3] - dp(FLOATING_TEXT_TOP_GAP))
        self.effects.append(FloatingText(self.layers['effects'], x, y, text, color, size))

    # ---------- Aparición de luciérnagas y power-ups ----------
    def free_spot(self, area, min_distance_to_player):
        """Busca una posición al azar que no esté encima del jugador ni del nido."""
        xmin, ymin, xmax, ymax = area
        for _ in range(SPAWN_TRIES):
            x, y = random.uniform(xmin, xmax), random.uniform(ymin, ymax)
            if (point_distance(x, y, self.player.x, self.player.y) > min_distance_to_player
                    and point_distance(x, y, self.nest.x, self.nest.y) > self.nest.radius * 2):
                break
        return x, y

    def spawn_firefly(self):
        has_fleeting = any(f.fleeting and f.state == FREE for f in self.fireflies)
        fleeting = (self.levels.allows_fleeting and not has_fleeting
                    and random.random() < FLEETING_CHANCE)
        x, y = self.free_spot(self.area(), dp(FIREFLY_SPAWN_MIN_DISTANCE))
        self.fireflies.append(Firefly(self.layers['fireflies'], x, y, fleeting=fleeting))

    def spawn_things(self, dt, area):
        self.firefly_wait -= dt
        if self.firefly_wait <= 0:
            self.firefly_wait = FIREFLY_SPAWN_INTERVAL
            loose = sum(1 for f in self.fireflies if f.state in (FREE, SCATTERED))
            if loose < self.levels.max_free_fireflies:
                self.spawn_firefly()

        if self.powerup is None:
            self.powerup_wait -= dt
            if self.powerup_wait <= 0:
                self.powerup_wait = random.uniform(*POWERUP_SPAWN_DELAY)
                kinds = [POWERUP_MOON, POWERUP_STAR]
                if self.lives < MAX_LIVES:
                    kinds.append(POWERUP_HEART)
                x, y = self.free_spot(area, dp(POWERUP_SPAWN_MIN_DISTANCE))
                self.powerup = PowerUp(self.layers['powerups'], random.choice(kinds), x, y)

    # ---------- Cola de luciérnagas ----------
    def move_tail(self, dt):
        """Cada luciérnaga de la cola sigue a la anterior (la primera sigue
        al jugador). Se acerca con interpolación hasta quedar a una
        distancia fija: así se forma una serpiente de luz."""
        spacing = dp(TAIL_SPACING)
        leader = self.player
        for firefly in self.tail:
            dx, dy = leader.x - firefly.x, leader.y - firefly.y
            dist = math.hypot(dx, dy)
            if dist > spacing:
                target_x = leader.x - dx / dist * spacing
                target_y = leader.y - dy / dist * spacing
                k = min(1.0, dt * TAIL_FOLLOW)
                firefly.x += (target_x - firefly.x) * k
                firefly.y += (target_y - firefly.y) * k
            leader = firefly

    def pick_up_fireflies(self):
        reach = self.player.radius + dp(FIREFLY_PICKUP_REACH)
        for firefly in self.fireflies:
            if len(self.tail) >= MAX_TAIL:
                break
            if firefly.state == FREE and distance(self.player, firefly) < reach:
                firefly.set_state(TAIL)
                self.tail.append(firefly)
                self.ring(firefly.x, firefly.y, firefly.color,
                          dp(PICKUP_RING_RADIUS), PICKUP_RING_DURATION)
                if firefly.fleeting:
                    self.floating_text(firefly.x, firefly.y + dp(10), '¡Fugaz!', GOLD, sp(20))

    def deliver(self):
        """Entrega toda la cola: puntos = valor x multiplicador."""
        count = len(self.tail)
        multiplier = delivery_multiplier(count)
        earned = sum(f.value for f in self.tail) * multiplier
        self.score += earned
        for i, firefly in enumerate(self.tail):
            firefly.set_state(DELIVERING)
            firefly.delay = i * DELIVERY_STAGGER  # entran una detrás de otra
        self.tail = []

        # Destello en el nido y puntaje flotando
        self.nest.flash = 1.0
        for radius, duration in DELIVERY_RINGS:
            self.ring(self.nest.x, self.nest.y, YELLOW, dp(radius), duration)
        self.floating_text(self.nest.x, self.nest.y + self.nest.radius,
                           f'+{earned}', YELLOW, sp(34))
        if multiplier > 1:
            self.floating_text(self.nest.x, self.nest.y + self.nest.radius + dp(40),
                               f'x{multiplier}', GOLD, sp(24))

        if self.levels.register_delivery(count) and self.night_change_wait is None:
            self.night_change_wait = NIGHT_CHANGE_DELAY

    # ---------- Golpes y power-ups ----------
    def hit(self, bat):
        """Un murciélago tocó al jugador."""
        self.shake.shake()
        # El murciélago se aleja un momento para no volver a golpear enseguida.
        bat.stunned = BAT_STUN_TIME
        bat.angle = math.atan2(bat.y - self.player.y, bat.x - self.player.x)
        self.player.invulnerable = HIT_INVULNERABILITY
        if self.tail:
            # La cola se dispersa: cada luciérnaga sale volando al azar.
            for firefly in self.tail:
                angle = random.uniform(0, math.tau)
                speed = dp(random.uniform(*SCATTER_SPEED))
                firefly.vx = math.cos(angle) * speed
                firefly.vy = math.sin(angle) * speed
                firefly.set_state(SCATTERED)
            self.tail = []
            self.floating_text(self.player.x, self.player.y + dp(30),
                               '¡Se escaparon!', CREAM, sp(20))
        else:
            self.lives -= 1
            self.burst(self.player.x, self.player.y, PINK, HIT_PARTICLES)
            if self.lives <= 0:
                self.end_game()

    def collect_powerup(self):
        kind, x, y = self.powerup.kind, self.powerup.x, self.powerup.y
        color = POWERUP_COLORS[kind]
        if kind == POWERUP_MOON:
            self.frozen = FREEZE_DURATION
            self.floating_text(x, y + dp(20), '¡Murciélagos congelados!', ICE_BLUE, sp(20))
        elif kind == POWERUP_STAR:
            self.magnet = MAGNET_DURATION
            self.floating_text(x, y + dp(20), '¡Imán!', GOLD, sp(22))
        else:
            self.lives = min(MAX_LIVES, self.lives + 1)
            self.floating_text(x, y + dp(20), '+1 vida', PINK, sp(22))
        ring_radius, ring_duration = POWERUP_RING
        self.ring(x, y, color, dp(ring_radius), ring_duration)
        self.burst(x, y, color, POWERUP_PARTICLES)
        self.powerup.remove()
        self.powerup = None

    # ---------- Fin de la partida ----------
    def end_game(self):
        self.game_state = ENDING
        self.ending_time = 0.0
        self.player.visible = False
        self.player.draw()
        self.burst(self.player.x, self.player.y, PLAYER_LIGHT, DEATH_PARTICLES,
                   speed=DEATH_PARTICLE_SPEED, life=DEATH_PARTICLE_LIFE)

    def go_to_game_over(self):
        self.stop_loop()
        highscores = App.get_running_app().highscores
        is_new_record = highscores.save_result(self.score, self.levels.night)
        self.manager.get_screen(SCREEN_GAME_OVER).show_result(
            self.score, self.levels.night, self.levels.delivered_total,
            highscores.get(), is_new_record)
        self.go_to(SCREEN_GAME_OVER)


load_kv('game_screen.kv')
