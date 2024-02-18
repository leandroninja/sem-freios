import pygame
import sys
import json
import os
from random import randint, uniform, choice
from dataclasses import dataclass

pygame.init()

# ── Constantes ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 619
FPS        = 60
ROAD_LEFT  = 125
ROAD_RIGHT = 620
CAR_W, CAR_H = 55, 90

HIGHSCORE_FILE = "highscore.json"

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (220,  50,  50)
GREEN  = ( 50, 210,  80)
YELLOW = (255, 220,  50)
ORANGE = (255, 150,   0)
GRAY   = (170, 170, 170)

# ── Highscore ─────────────────────────────────────────────────────────────────
def load_highscore() -> int:
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE) as f:
                return json.load(f).get("highscore", 0)
        except Exception:
            pass
    return 0

def save_highscore(score: int) -> None:
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump({"highscore": score}, f)

# ── Assets ────────────────────────────────────────────────────────────────────
def load_img(path: str, size=None) -> pygame.Surface:
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, size) if size else img

# ── Particulas ────────────────────────────────────────────────────────────────
@dataclass
class Particle:
    x: float; y: float
    vx: float; vy: float
    life: int; max_life: int
    color: tuple; size: float

    def update(self) -> bool:
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.35
        self.life -= 1
        return self.life > 0

    def draw(self, surf: pygame.Surface) -> None:
        r = max(1, int(self.size * self.life / self.max_life))
        alpha = int(255 * self.life / self.max_life)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surf.blit(s, (int(self.x) - r, int(self.y) - r))

def explode(particles: list, x: float, y: float) -> None:
    colors = [(255, 100, 30), (255, 210, 50), (255, 60, 60), (210, 210, 210)]
    for _ in range(45):
        spd = uniform(2, 9)
        vx  = uniform(-spd, spd)
        vy  = uniform(-spd, 0.5)
        life = randint(18, 44)
        particles.append(Particle(x, y, vx, vy, life, life, choice(colors), uniform(3, 8)))

# ── Linhas de velocidade ──────────────────────────────────────────────────────
@dataclass
class SpeedLine:
    x: float; y: float; length: int; speed: float

    @classmethod
    def random(cls) -> "SpeedLine":
        return cls(uniform(ROAD_LEFT, ROAD_RIGHT), uniform(0, SCREEN_H),
                   randint(20, 55), uniform(10, 18))

    def update(self) -> bool:
        self.y += self.speed
        return self.y < SCREEN_H + self.length

    def draw(self, surf: pygame.Surface, alpha: int) -> None:
        s = pygame.Surface((2, self.length), pygame.SRCALPHA)
        s.fill((255, 255, 255, alpha))
        surf.blit(s, (int(self.x), int(self.y)))

# ── Inimigo ───────────────────────────────────────────────────────────────────
LANES = [145, 205, 265, 325, 385, 445, 505, 560]

class EnemyCar:
    def __init__(self, images: list):
        self.images = images
        self.x = 0.0
        self.y = 0.0
        self.speed = 5.0
        self.image = images[0]

    def _respawn(self, base_speed: float, others: list = None) -> None:
        self.image = choice(self.images)
        self.x = float(choice(LANES))
        self.speed = base_speed + uniform(-0.4, 1.6)
        candidate = -randint(80, 300)
        if others:
            same_lane = [e for e in others if e is not self and abs(e.x - self.x) < 5]
            for _ in range(20):
                if not any(abs(candidate - e.y) < CAR_H + 20 for e in same_lane):
                    break
                candidate -= CAR_H + randint(20, 50)
        self.y = float(candidate)

    @property
    def rect(self) -> pygame.Rect:
        mx, my = 12, 10
        return pygame.Rect(int(self.x) + mx, int(self.y) + my, CAR_W - mx * 2, CAR_H - my * 2)

    def update(self, base_speed: float, others: list) -> None:
        self.y += self.speed
        if self.y > SCREEN_H + CAR_H:
            self._respawn(base_speed, others)

    def draw(self, surf: pygame.Surface) -> None:
        surf.blit(self.image, (int(self.x), int(self.y)))

# ── Jogador ───────────────────────────────────────────────────────────────────
class Player:
    SPEED      = 6
    MAX_LIVES  = 3
    INV_FRAMES = 110

    def __init__(self, image: pygame.Surface):
        self.image = image
        self.x     = float(SCREEN_W // 2 - CAR_W // 2)
        self.y     = float(SCREEN_H - CAR_H - 40)
        self.lives = self.MAX_LIVES
        self.inv   = 0

    @property
    def rect(self) -> pygame.Rect:
        m = 8
        return pygame.Rect(int(self.x) + m, int(self.y) + m, CAR_W - m * 2, CAR_H - m * 2)

    def handle_input(self, keys) -> None:
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.SPEED
        if keys[pygame.K_DOWN] and self.y < SCREEN_H - CAR_H:
            self.y += self.SPEED
        if keys[pygame.K_LEFT] and self.x > ROAD_LEFT:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT] and self.x < ROAD_RIGHT - CAR_W:
            self.x += self.SPEED

    def hit(self) -> bool:
        if self.inv > 0:
            return False
        self.lives -= 1
        self.inv = self.INV_FRAMES
        return True

    def update(self) -> None:
        if self.inv > 0:
            self.inv -= 1

    def draw(self, surf: pygame.Surface) -> None:
        if self.inv > 0 and (self.inv // 6) % 2 == 0:
            return
        surf.blit(self.image, (int(self.x), int(self.y)))

# ── Texto com sombra ──────────────────────────────────────────────────────────
def draw_text(surf, text, font, color, x, y, center=False):
    shadow = font.render(text, True, BLACK)
    main   = font.render(text, True, color)
    r = main.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(shadow, r.move(2, 2))
    surf.blit(main, r)

# ── Coracao ───────────────────────────────────────────────────────────────────
def make_heart(size: int = 26) -> pygame.Surface:
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    r = size // 4
    cx = size // 2
    pygame.draw.circle(s, (220, 50, 60), (cx - r, r + 1), r)
    pygame.draw.circle(s, (220, 50, 60), (cx + r, r + 1), r)
    pygame.draw.polygon(s, (220, 50, 60), [(1, r + 4), (cx, size - 2), (size - 1, r + 4)])
    return s

# ── Jogo ──────────────────────────────────────────────────────────────────────
class Game:
    MENU      = "menu"
    PLAYING   = "playing"
    PAUSED    = "paused"
    GAME_OVER = "game_over"

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Sem Freios")
        self.clock  = pygame.time.Clock()
        self._load_assets()
        self.highscore = load_highscore()
        self.state = self.MENU
        self._init_game()

    def _load_assets(self):
        self.bg     = load_img("pista.png", (SCREEN_W, SCREEN_H))
        self.bg_y   = 0.0
        self.player_img = load_img("carro1.png", (CAR_W, CAR_H))

        enemy_files = [f"carro{i}.png" for i in range(2, 10)] + ["jipe.png", "jipe1.png"]
        self.enemy_imgs = [load_img(f, (CAR_W, CAR_H)) for f in enemy_files]

        self.heart_img = make_heart(28)

        self.font_xl = pygame.font.SysFont("Arial Black", 54, bold=True)
        self.font_lg = pygame.font.SysFont("Arial Black", 34, bold=True)
        self.font_md = pygame.font.SysFont("Arial Black", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Arial",       17)

        self.overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Overlay degradê pré-calculado para o menu
        self.menu_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for _row in range(SCREEN_H):
            _a = int(80 + 155 * _row / SCREEN_H)
            pygame.draw.line(self.menu_overlay, (0, 0, 0, _a), (0, _row), (SCREEN_W, _row))

        # Carros e linhas animados no menu
        self.menu_cars = []
        for _ in range(6):
            mc = EnemyCar(self.enemy_imgs)
            mc.x = float(choice(LANES))
            mc.y = float(randint(-500, 0))
            mc.speed = uniform(3.5, 6.0)
            self.menu_cars.append(mc)
        self.menu_lines = [SpeedLine.random() for _ in range(18)]

    def _init_game(self):
        self.player     = Player(self.player_img)
        self.enemies = []
        for _ in range(10):
            e = EnemyCar(self.enemy_imgs)
            e._respawn(5.0, self.enemies)
            self.enemies.append(e)
        self.particles  = []
        self.speed_lines = [SpeedLine.random() for _ in range(14)]
        self.ticks      = 0
        self.score      = 0
        self.base_speed = 5.0
        self.shake      = 0
        self.bg_y       = 0.0

    # ── Loop principal ────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            self._events()
            dispatch = {
                self.MENU:      self._menu,
                self.PLAYING:   self._playing,
                self.PAUSED:    self._paused,
                self.GAME_OVER: self._game_over,
            }
            dispatch[self.state]()
            pygame.display.flip()

    # ── Eventos ───────────────────────────────────────────────────────────────
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key

            if self.state == self.MENU and k in (pygame.K_RETURN, pygame.K_SPACE):
                self._init_game(); self.state = self.PLAYING

            elif self.state == self.PLAYING and k == pygame.K_ESCAPE:
                self.state = self.PAUSED

            elif self.state == self.PAUSED:
                if k == pygame.K_ESCAPE: self.state = self.PLAYING
                if k == pygame.K_q:      self.state = self.MENU

            elif self.state == self.GAME_OVER:
                if k in (pygame.K_RETURN, pygame.K_SPACE):
                    self._init_game(); self.state = self.PLAYING
                if k == pygame.K_q:
                    self.state = self.MENU

    # ── Menu ──────────────────────────────────────────────────────────────────
    def _menu(self):
        self._scroll_bg(4.5)

        # Carros animados no fundo
        for mc in self.menu_cars:
            mc.y += mc.speed
            if mc.y > SCREEN_H + CAR_H:
                mc.x     = float(choice(LANES))
                mc.y     = float(randint(-400, -CAR_H))
                mc.speed = uniform(3.5, 6.0)
                mc.image = choice(self.enemy_imgs)
            mc.draw(self.screen)

        # Linhas de velocidade
        self.menu_lines = [sl for sl in self.menu_lines if sl.update()]
        while len(self.menu_lines) < 18:
            self.menu_lines.append(SpeedLine.random())
        for sl in self.menu_lines:
            sl.draw(self.screen, 65)

        # Carro do jogador parado na base
        self.screen.blit(self.player_img, (SCREEN_W // 2 - CAR_W // 2, SCREEN_H - CAR_H - 20))

        # Overlay degradê
        self.screen.blit(self.menu_overlay, (0, 0))

        # Título com cor pulsante
        t_ms  = pygame.time.get_ticks()
        pulse = abs((t_ms % 1800) / 900.0 - 1.0)
        tc    = (255, int(180 + 75 * pulse), int(60 * pulse))
        draw_text(self.screen, "SEM FREIOS", self.font_xl, tc, SCREEN_W // 2, 130, center=True)

        # Painel de informações
        pw, ph = 430, 180
        panel  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        pygame.draw.rect(panel, (255, 200, 50, 120), (0, 0, pw, ph), 2, border_radius=10)
        self.screen.blit(panel, (SCREEN_W // 2 - pw // 2, 200))

        draw_text(self.screen, "Desvie do trafego!",           self.font_md, WHITE,  SCREEN_W // 2, 220, center=True)
        draw_text(self.screen, f"Recorde: {self.highscore}s",  self.font_md, ORANGE, SCREEN_W // 2, 263, center=True)
        draw_text(self.screen, "Setas: mover  |  ESC: pausar", self.font_sm, GRAY,   SCREEN_W // 2, 328, center=True)

        if (t_ms // 500) % 2 == 0:
            draw_text(self.screen, "ENTER ou ESPACO para jogar", self.font_lg, GREEN, SCREEN_W // 2, 430, center=True)

    # ── Jogando ───────────────────────────────────────────────────────────────
    def _playing(self):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update()

        self.ticks     += 1
        self.score      = self.ticks // FPS
        self.base_speed = min(5.0 + (self.score // 10) * 0.6, 15.0)

        ox, oy = 0, 0
        if self.shake > 0:
            self.shake -= 1
            ox = randint(-7, 7)
            oy = randint(-7, 7)

        for enemy in self.enemies:
            enemy.update(self.base_speed, self.enemies)

        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                if self.player.hit():
                    explode(self.particles, self.player.x + CAR_W // 2, self.player.y + CAR_H // 2)
                    self.shake = 22
                    if self.player.lives <= 0:
                        if self.score > self.highscore:
                            self.highscore = self.score
                            save_highscore(self.score)
                        self.state = self.GAME_OVER
                        return

        self.particles = [p for p in self.particles if p.update()]

        line_alpha = min(90, int((self.base_speed - 5) * 14))
        self.speed_lines = [sl for sl in self.speed_lines if sl.update()]
        while len(self.speed_lines) < 16:
            self.speed_lines.append(SpeedLine.random())

        self._scroll_bg(self.base_speed, ox, oy)

        if line_alpha > 0:
            for sl in self.speed_lines:
                sl.draw(self.screen, line_alpha)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        self._hud()

    # ── HUD ───────────────────────────────────────────────────────────────────
    def _hud(self):
        bar = pygame.Surface((SCREEN_W, 50), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 155))
        self.screen.blit(bar, (0, 0))

        draw_text(self.screen, f"Tempo: {self.score}s",       self.font_md, WHITE,  12, 14)
        draw_text(self.screen, f"Recorde: {self.highscore}s", self.font_md, YELLOW, 175, 14)

        vel = int((self.base_speed - 5) / 0.6) + 1
        cor = GREEN if vel <= 3 else YELLOW if vel <= 6 else RED
        draw_text(self.screen, f"Vel: {vel}", self.font_md, cor, SCREEN_W - 130, 14)

        for i in range(self.player.lives):
            self.screen.blit(self.heart_img, (SCREEN_W // 2 - 44 + i * 34, 11))

    # ── Pausado ───────────────────────────────────────────────────────────────
    def _paused(self):
        self._scroll_bg(0)
        for e in self.enemies:
            e.draw(self.screen)
        self.player.draw(self.screen)
        self._hud()

        self.overlay.fill((0, 0, 0, 175))
        self.screen.blit(self.overlay, (0, 0))

        draw_text(self.screen, "PAUSADO",         self.font_xl, YELLOW, SCREEN_W//2, 220, center=True)
        draw_text(self.screen, "ESC - Continuar", self.font_md, WHITE,  SCREEN_W//2, 330, center=True)
        draw_text(self.screen, "Q   - Menu",      self.font_md, GRAY,   SCREEN_W//2, 378, center=True)

    # ── Game Over ─────────────────────────────────────────────────────────────
    def _game_over(self):
        self._scroll_bg(1.5)
        self.overlay.fill((0, 0, 0, 185))
        self.screen.blit(self.overlay, (0, 0))

        draw_text(self.screen, "GAME OVER",             self.font_xl, RED,    SCREEN_W//2, 155, center=True)
        draw_text(self.screen, f"Tempo: {self.score}s", self.font_lg, WHITE,  SCREEN_W//2, 258, center=True)

        if self.score >= self.highscore and self.score > 0:
            draw_text(self.screen, "NOVO RECORDE!",                self.font_md, YELLOW, SCREEN_W//2, 318, center=True)
        else:
            draw_text(self.screen, f"Recorde: {self.highscore}s", self.font_md, ORANGE, SCREEN_W//2, 318, center=True)

        draw_text(self.screen, "ENTER - Jogar novamente", self.font_md, GREEN, SCREEN_W//2, 410, center=True)
        draw_text(self.screen, "Q     - Menu principal",  self.font_md, GRAY,  SCREEN_W//2, 458, center=True)

    # ── Scroll do fundo ───────────────────────────────────────────────────────
    def _scroll_bg(self, speed: float, ox: int = 0, oy: int = 0):
        self.bg_y = (self.bg_y + speed) % SCREEN_H
        y = int(self.bg_y)
        self.screen.blit(self.bg, (ox, oy + y - SCREEN_H))
        self.screen.blit(self.bg, (ox, oy + y))

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
