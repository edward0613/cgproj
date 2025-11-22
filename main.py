import pygame
import sys
import random
import math
from collections import deque
from enum import Enum

pygame.init()

# ---- 설정값 ----
GRID_W = 24
GRID_H = 16
CELL_SIZE = 40         # 윈도우: 24*40=960, 16*40=640
TOP_MARGIN = 40
SCREEN_W = GRID_W * CELL_SIZE
SCREEN_H = GRID_H * CELL_SIZE + TOP_MARGIN + 80  # 아래 UI 영역 확보
FPS = 60

# 색상
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (150,150,150)
LIGHT_GRAY = (200,200,200)
RED = (200,50,50)
GREEN = (50,200,50)
YELLOW = (230,230,50)
BLUE = (50,100,200)
DARK = (30,30,30)

# 폰트
FONT = pygame.font.SysFont("malgungothic", 18)
BIGFONT = pygame.font.SysFont("malgungothic", 28)

# ---- 게임 데이터 구조 ----
class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 1
        self.max_hp = 3
        self.dead = False   # '죽은 칸' flag (여우의 가시로 생성, 회복 불가 unless re건축)

    def rect(self):
        # 현재 코드는 grid를 화면 위쪽부터 바로 그리므로 TOP_MARGIN은 사용 안 함
        return pygame.Rect(self.x * CELL_SIZE, self.y * CELL_SIZE + TOP_MARGIN, CELL_SIZE, CELL_SIZE)


class SkillTargetRule:
    """타겟 영역 계산 (마우스 기준)"""
    @staticmethod
    def area_from_mouse(mx, my, w_cells, h_cells):
        cx = mx // CELL_SIZE
        cy = my // CELL_SIZE
        # apply odd/even rules
        if w_cells % 2 == 1 and h_cells % 2 == 1:
            # center-based
            half_w = w_cells//2
            half_h = h_cells//2
            xs = range(cx-half_w, cx+half_w+1)
            ys = range(cy-half_h, cy+half_h+1)
        elif w_cells % 2 == 1 and h_cells % 2 == 0:
            half_w = w_cells//2
            ys = range(cy-(h_cells//2), cy+(h_cells//2))
            xs = range(cx-half_w, cx+half_w+1)
        elif w_cells % 2 == 0 and h_cells % 2 == 1:
            xs = range(cx-(w_cells//2), cx+(w_cells//2))
            ys = range(cy-(h_cells//2), cy+(h_cells//2)+1)
        else:
            # both even: mouse is top-left corner
            xs = range(cx, cx+w_cells)
            ys = range(cy, cy+h_cells)
        # clamp to grid
        coords = [(x,y) for x in xs for y in ys if 0 <= x < GRID_W and 0 <= y < GRID_H]
        return coords

# 스킬 정의 (간단한 메타)
class Skill:
    def __init__(self, id, name, cost, target_w, target_h, delay=0.0, effect=None, target_all=False, area_is_cross=False):
        self.id = id
        self.name = name
        self.cost = cost
        self.target_w = target_w
        self.target_h = target_h
        self.delay = delay
        self.effect = effect  # function(game, targets)
        self.target_all = target_all
        self.area_is_cross = area_is_cross

# 여우 스킬과 게 스킬을 각각 정의
def effect_fox_spike(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if cell.hp <= 0:
            cell.dead = True

def effect_fox_arrow(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp -= 1
            if cell.hp <= 0:
                cell.hp = 0

def effect_fox_tracker(game, coords):
    game.fox_tracked = True
    game.fox_track_timer = 2.0

def effect_fox_peel(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp -= 1
    game.schedule_delayed(lambda g=game, c=coords: effect_peel_restore(g, c), 1.0)

def effect_peel_restore(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp += 1
            if cell.hp > cell.max_hp:
                cell.hp = cell.max_hp

def effect_fox_focus(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp -= 2
            if cell.hp <= 0:
                cell.hp = 0

def effect_fox_beam(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp -= 1
            if cell.hp <= 0:
                cell.hp = 0
                cell.dead = True

def effect_fox_cross(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp -= 1
            if cell.hp <= 0:
                cell.hp = 0

# Crab (player) effects
def effect_build(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp += 1
            if cell.hp > cell.max_hp:
                cell.hp = cell.max_hp

def effect_haste(game, coords):
    # 한 칸 이동 시간 단축
    game.player_speed_bonus = 0.2
    game.player_haste_timer = 2.0

def effect_rebuild(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if cell.dead:
            cell.dead = False
            cell.hp = 1
            cell.max_hp = 1

def effect_construct(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        cell.max_hp += 1

def effect_meditate(game, coords):
    p = game.player
    if p.hp == 1:
        p.can_move = False
        game.schedule_delayed(lambda g=game: setattr(g.player, "can_move", True), 2.0)
        p.hp = 2
    elif p.hp == 2:
        area = []
        cx,cy = p.x, p.y
        xs = range(cx-1, cx+2)
        ys = range(cy-1, cy+2)
        for x in xs:
            for y in ys:
                if 0<=x<GRID_W and 0<=y<GRID_H:
                    area.append((x,y))
        for x,y in area:
            cell = game.grid[y][x]
            if not cell.dead:
                cell.hp = min(cell.max_hp, cell.hp+1)

def effect_crab_cross(game, coords):
    for x,y in coords:
        cell = game.grid[y][x]
        if not cell.dead:
            cell.hp += 1
            if cell.hp > cell.max_hp:
                cell.hp = cell.max_hp

# 스킬 객체들
FOX_SKILLS = [
    Skill("fox_spike","가시",4,2,2,delay=1.0,effect=effect_fox_spike),
    Skill("fox_arrow","화살",5,3,5,delay=0.0,effect=effect_fox_arrow),
    Skill("fox_tracker","추적자",2,0,0,delay=0.0,effect=effect_fox_tracker,target_all=True),
    Skill("fox_peel","들춰보기",3,2,3,delay=0.7,effect=effect_fox_peel),
    Skill("fox_focus","집중타격",5,3,3,delay=0.7,effect=effect_fox_focus,area_is_cross=True),
    Skill("fox_beam","직사광선",4,1,8,delay=0.3,effect=effect_fox_beam),
    Skill("fox_cross","십자가",2,1,1,delay=0.5,effect=effect_fox_cross,area_is_cross=True),
]

CRAB_SKILLS = [
    Skill("build","건축",3,3,3,delay=0.5,effect=effect_build),
    Skill("haste","신속",2,0,0,delay=0.0,effect=effect_haste,target_all=True),
    Skill("rebuild","재건축",6,4,4,delay=0.5,effect=effect_rebuild),
    Skill("construct","공사",4,5,4,delay=0.0,effect=effect_construct),
    Skill("meditate","명상",2,1,1,delay=0.0,effect=effect_meditate),
    Skill("crab_cross","십자가",2,1,1,delay=0.0,effect=effect_crab_cross,area_is_cross=True),
]

# ---- 게임 클래스 ----
class Player:
    def __init__(self):
        self.x = GRID_W//2
        self.y = GRID_H//2
        # 부드러운 이동을 위한 픽셀 좌표 (칸 중앙)
        self.pixel_x = self.x * CELL_SIZE + CELL_SIZE / 2
        self.pixel_y = self.y * CELL_SIZE + CELL_SIZE / 2
        self.hp = 2
        self.can_move = True
        self.invulnerable = False
        self.invul_timer = 0.0

class Fox:
    def __init__(self):
        self.x = 0
        self.y = 0

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = "MENU"  # MENU, SKILL_SELECT, PLAY, GAME_OVER
        self.grid = [[Cell(x,y) for x in range(GRID_W)] for y in range(GRID_H)]
        self.player = Player()
        self.fox = Fox()

        # deck & hand
        self.selected_skills = []
        self.deck = deque()
        self.hand = [None]*4

        # money/time system
        self.money = 0
        self.money_timer = 0.0

        # skill selection UI
        self.skill_cards_pool = CRAB_SKILLS[:]
        self.selection_slots = [None]*8

        # scheduled events
        self.scheduled = []  # [ [time, func], ... ]

        # fox behavior
        self.fox_timer = 3.0
        self.fox_action_cooldown = 3.0
        self.fox_tracked = False
        self.fox_track_timer = 0.0

        # player speed
        self.player_speed = 0.3
        self.player_speed_bonus = None
        self.player_haste_timer = 0.0

        # card highlight / target preview
        self.current_target_preview = []

        # movement control (부드러운 이동용)
        self.move_path = []           # 남은 (x,y) 칸 리스트
        self.base_move_interval = 0.2 # 한 칸 이동에 걸리는 기본 시간(초)
        self.moving = False
        self.segment_from = None      # (x,y)
        self.segment_to = None        # (x,y)
        self.segment_t = 0.0          # 0~1
        self.segment_duration = self.base_move_interval

        self.pending_card_index = None
        self.pending_preview = None
        self.messages = []

        self.init_defaults()

    def set_player_cell(self, x, y):
        self.player.x = x
        self.player.y = y
        self.player.pixel_x = x * CELL_SIZE + CELL_SIZE / 2
        self.player.pixel_y = y * CELL_SIZE + CELL_SIZE / 2

    def init_defaults(self):
        self.set_player_cell(GRID_W//2, GRID_H//2)
        self.selection_slots = random.sample(CRAB_SKILLS*2, 8)
        self.money = 0

    def show_message(self, text, duration=2.0):
        self.messages.append([text, duration])

    def build_preview_for_card(self, index, mouse_pos):
        card = self.hand[index]
        if card is None:
            return None
        if card.target_all:
            coords = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
            center = None
        else:
            px, py = mouse_pos
            py_adj = py - TOP_MARGIN
            center_cell = (px // CELL_SIZE, py_adj // CELL_SIZE)
            coords = SkillTargetRule.area_from_mouse(px, py, card.target_w, card.target_h)
            center = center_cell
        return {"index": index, "center": center, "coords": coords, "card": card}

    def clear_pending_card_preview(self):
        self.pending_card_index = None
        self.pending_preview = None
        self.current_target_preview = []

    def schedule_delayed(self, func, delay):
        self.scheduled.append([delay, func])

    def update_scheduled(self, dt):
        to_run = []
        for item in list(self.scheduled):
            item[0] -= dt
            if item[0] <= 0:
                to_run.append(item[1])
                self.scheduled.remove(item)
        for f in to_run:
            try:
                f()
            except Exception as e:
                print("scheduled exec error", e)

    def start_play(self):
        if len(self.selected_skills) != 5:
            print("deck not ready")
            return
        self.deck = deque(self.selected_skills[:])
        random.shuffle(self.deck)
        for i in range(4):
            if self.deck:
                self.hand[i] = self.deck.popleft()
            else:
                self.hand[i] = None

        self.state = "PLAY"
        self.money = 0
        self.money_timer = 0.0

        for row in self.grid:
            for c in row:
                c.hp = 1
                c.max_hp = 3
                c.dead = False

        self.player = Player()
        self.fox_timer = 2.0
        self.fox_tracked = False
        self.fox_track_timer = 0.0

        self.move_path = []
        self.moving = False
        self.segment_from = None
        self.segment_to = None
        self.segment_t = 0.0
        self.segment_duration = self.base_move_interval

    def spawn_fox_action(self):
        sk = random.choice(FOX_SKILLS)
        if sk.target_all:
            coords = [(x,y) for x in range(GRID_W) for y in range(GRID_H)]
        else:
            mx = random.randint(0, GRID_W-1)
            my = random.randint(0, GRID_H-1)
            px = mx * CELL_SIZE + CELL_SIZE//2
            py = my * CELL_SIZE + CELL_SIZE//2
            if sk.area_is_cross:
                coords = []
                if sk.name == "집중타격":
                    cx,cy = mx,my
                    coords.append((cx,cy))
                    for d in [1,2]:
                        if cx+d < GRID_W: coords.append((cx+d,cy))
                        if cx-d >=0: coords.append((cx-d,cy))
                        if cy+d < GRID_H: coords.append((cx,cy+d))
                        if cy-d >=0: coords.append((cx,cy-d))
                else:
                    cx,cy = mx,my
                    coords = [(cx,cy)]
                    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx,ny = cx+dx,cy+dy
                        if 0<=nx<GRID_W and 0<=ny<GRID_H:
                            coords.append((nx,ny))
            else:
                coords = SkillTargetRule.area_from_mouse(px,py,sk.target_w,sk.target_h)
        self.current_target_preview = coords
        if sk.delay > 0:
            self.schedule_delayed(lambda s=sk,c=coords: s.effect(self,c), sk.delay)
        else:
            sk.effect(self, coords)

    # ---- 부드러운 이동 ----
    def start_movement_to_path(self, path):
        self.move_path = path
        if not self.move_path:
            self.moving = False
            self.segment_from = None
            self.segment_to = None
            self.segment_t = 0.0
            return
        self.moving = True
        self.segment_from = (self.player.x, self.player.y)
        self.start_next_segment()

    def start_next_segment(self):
        if not self.move_path:
            self.moving = False
            self.segment_to = None
            self.segment_t = 0.0
            return

        nx, ny = self.move_path.pop(0)
        self.segment_from = (self.player.x, self.player.y)
        self.segment_to = (nx, ny)
        self.segment_t = 0.0

        interval = self.player_speed_bonus if self.player_speed_bonus is not None else self.base_move_interval
        self.segment_duration = max(0.001, interval)

    def update_movement(self, dt):
        if not self.moving or self.segment_to is None:
            self.player.pixel_x = self.player.x * CELL_SIZE + CELL_SIZE / 2
            self.player.pixel_y = self.player.y * CELL_SIZE + CELL_SIZE / 2
            return

        self.segment_t += dt / self.segment_duration
        if self.segment_t > 1.0:
            self.segment_t = 1.0

        sx, sy = self.segment_from
        ex, ey = self.segment_to

        sx_px = sx * CELL_SIZE + CELL_SIZE / 2
        sy_px = sy * CELL_SIZE + CELL_SIZE / 2
        ex_px = ex * CELL_SIZE + CELL_SIZE / 2
        ey_px = ey * CELL_SIZE + CELL_SIZE / 2

        self.player.pixel_x = sx_px + (ex_px - sx_px) * self.segment_t
        self.player.pixel_y = sy_px + (ey_px - sy_px) * self.segment_t

        if self.segment_t >= 1.0:
            nx, ny = self.segment_to
            cell = self.grid[ny][nx]

            if cell.hp <= 0 or cell.dead:
                if not self.player.invulnerable:
                    self.player.hp -= 1
                    if self.player.hp <= 0:
                        self.on_player_death()
                        self.move_path = []
                        self.moving = False
                        self.segment_from = None
                        self.segment_to = None
                        return
                    else:
                        found = False
                        for yrow in range(GRID_H):
                            for xcell in range(GRID_W):
                                c = self.grid[yrow][xcell]
                                if c.hp >= 1 and not c.dead:
                                    self.set_player_cell(xcell, yrow)
                                    found = True
                                    break
                            if found:
                                break
                        self.player.invulnerable = True
                        self.player.invul_timer = 1.0
                        self.move_path = []
                        self.moving = False
                        self.segment_from = None
                        self.segment_to = None
                        return
            else:
                self.set_player_cell(nx, ny)

            if self.move_path:
                self.start_next_segment()
            else:
                self.moving = False
                self.segment_from = None
                self.segment_to = None

    # -----------------------
    def update(self, dt):
        for m in list(self.messages):
            m[1] -= dt
            if m[1] <= 0:
                self.messages.remove(m)

        self.money_timer += dt
        if self.money_timer >= 1.0:
            self.money_timer -= 1.0
            self.money = min(12, self.money + 1)

        self.update_scheduled(dt)
        self.update_movement(dt)

        self.fox_timer -= dt
        if self.fox_timer <= 0:
            self.spawn_fox_action()
            self.fox_timer = random.uniform(2.0, 4.0)

        if self.fox_tracked:
            self.fox_track_timer -= dt
            if self.fox_track_timer <= 0:
                self.fox_tracked = False

        if self.player_haste_timer > 0:
            self.player_haste_timer -= dt
            if self.player_haste_timer <= 0:
                self.player_speed_bonus = None

        if self.player.invul_timer > 0:
            self.player.invul_timer -= dt
            if self.player.invul_timer <= 0:
                self.player.invulnerable = False

    def draw_grid(self):
        for y,row in enumerate(self.grid):
            for x,cell in enumerate(row):
                r = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if cell.dead:
                    color = (100,80,80)
                else:
                    hp_frac = cell.hp / max(1, cell.max_hp)
                    base = 220 - int(120*(1-hp_frac))
                    color = (base, base, base)
                pygame.draw.rect(self.screen, color, r)
                pygame.draw.rect(self.screen, BLACK, r, 1)
                txt = FONT.render(f"{cell.hp}" if not cell.dead else "D", True, BLACK if not cell.dead else RED)
                self.screen.blit(txt, (x*CELL_SIZE+2, y*CELL_SIZE+2))

    def draw_ui(self):
        ui_rect = pygame.Rect(0, GRID_H*CELL_SIZE, SCREEN_W, SCREEN_H - GRID_H*CELL_SIZE)
        pygame.draw.rect(self.screen, DARK, ui_rect)

        money_txt = BIGFONT.render(f"돈: {self.money}", True, YELLOW)
        self.screen.blit(money_txt, (10, GRID_H*CELL_SIZE+10))

        for i,card in enumerate(self.hand):
            cx = 200 + i*(200)
            card_rect = pygame.Rect(cx, GRID_H*CELL_SIZE+10, 180, 60)
            pygame.draw.rect(self.screen, LIGHT_GRAY, card_rect)
            pygame.draw.rect(self.screen, BLACK, card_rect, 2)
            keyname = ["Q","W","E","R"][i]
            if card:
                name_txt = FONT.render(f"{keyname}  {card.name}  (cost:{card.cost})", True, BLACK)
            else:
                name_txt = FONT.render(f"{keyname}  (빈 슬롯)", True, BLACK)
            self.screen.blit(name_txt, (cx+10, GRID_H*CELL_SIZE+20))

        ptxt = FONT.render(f"게 체력: {self.player.hp}", True, WHITE)
        self.screen.blit(ptxt, (10, GRID_H*CELL_SIZE+50))

    def draw_preview(self):
        for (x,y) in getattr(self, "current_target_preview", []):
            r = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill((255,255,0,80))
            self.screen.blit(s, r.topleft)

    def on_player_death(self):
        self.state = "GAME_OVER"
        self.move_path = []
        self.moving = False
        self.pending_preview = None
        self.pending_card_index = None
        self.current_target_preview = []
        self.show_message("게임 오버 - R 키로 재시작", 9999)

    def handle_card_use(self, index, mouse_pos):
        card = self.hand[index]
        if card is None or self.money < card.cost:
            return
        if card.target_all:
            coords = [(x,y) for x in range(GRID_W) for y in range(GRID_H)]
        elif card.area_is_cross and card.target_w==1 and card.target_h==1 and card.name in ["십자가","crab_cross","집중타격"]:
            px,py = mouse_pos
            mx,my = px//CELL_SIZE, py//CELL_SIZE
            coords = [(mx,my)]
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx,ny = mx+dx,my+dy
                if 0<=nx<GRID_W and 0<=ny<GRID_H:
                    coords.append((nx,ny))
        else:
            px,py = mouse_pos
            coords = SkillTargetRule.area_from_mouse(px,py,card.target_w,card.target_h)

        self.money -= card.cost
        if card.delay > 0:
            self.current_target_preview = coords
            self.schedule_delayed(lambda c=coords, s=card: s.effect(self, c), card.delay)
        else:
            card.effect(self, coords)

        used = self.hand[index]
        self.deck.append(used)
        if self.deck:
            self.hand[index] = self.deck.popleft()
        else:
            self.hand[index] = None

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        if self.current_target_preview:
            self.draw_preview()
        # 플레이어 (부드러운 이동 좌표 기준)
        size = CELL_SIZE - 10
        pr = pygame.Rect(0, 0, size, size)
        pr.center = (self.player.pixel_x, self.player.pixel_y)
        pygame.draw.ellipse(self.screen, BLUE, pr)

        if self.fox_tracked:
            txt = FONT.render("추적중", True, RED)
            self.screen.blit(txt, (SCREEN_W-80, 10))

        self.draw_ui()
        pygame.display.flip()

    def draw_top_banner(self):
        banner_rect = pygame.Rect(0, 0, SCREEN_W, TOP_MARGIN)
        pygame.draw.rect(self.screen, (40, 40, 40), banner_rect)
        if self.messages:
            txt = FONT.render(self.messages[0][0], True, WHITE)
            self.screen.blit(txt, (10, (TOP_MARGIN - txt.get_height()) // 2))

    def execute_card_use(self, index, coords):
        card = self.hand[index]
        if card is None or self.money < card.cost:
            return
        self.money -= card.cost
        if card.delay > 0:
            self.current_target_preview = coords
            self.schedule_delayed(lambda c=coords, s=card: s.effect(self, c), card.delay)
        else:
            card.effect(self, coords)
        used = self.hand[index]
        self.deck.append(used)
        if self.deck:
            self.hand[index] = self.deck.popleft()
        else:
            self.hand[index] = None

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if self.state == "MENU":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.state = "SKILL_SELECT"
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.state = "SKILL_SELECT"

                elif self.state == "SKILL_SELECT":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx,my = pygame.mouse.get_pos()
                        start_x = 60
                        start_y = 80
                        slot_w = 100
                        slot_h = 60
                        for i,slot in enumerate(self.selection_slots):
                            rx = start_x + i*(slot_w+10)
                            ry = start_y
                            rect = pygame.Rect(rx,ry,slot_w,slot_h)
                            if rect.collidepoint(mx,my):
                                if slot in self.selected_skills:
                                    self.selected_skills.remove(slot)
                                else:
                                    if len(self.selected_skills) < 5:
                                        self.selected_skills.append(slot)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        if len(self.selected_skills) == 5:
                            self.start_play()
                        else:
                            print("5개 선택해야 합니다.")

                elif self.state == "PLAY":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        # grid 영역 안에서만 이동 (위쪽부터 grid)
                        if 0 <= my < GRID_H * CELL_SIZE:
                            tx = mx // CELL_SIZE
                            ty = my // CELL_SIZE
                            if self.player.can_move:
                                # ---- 이동 중이어도 항상 새 목적지로 갈아타기 ----
                                # 현재 pixel 위치 기준으로 가장 가까운 칸으로 스냅
                                start_cx = int(self.player.pixel_x // CELL_SIZE)
                                start_cy = int(self.player.pixel_y // CELL_SIZE)
                                start_cx = max(0, min(GRID_W - 1, start_cx))
                                start_cy = max(0, min(GRID_H - 1, start_cy))
                                self.set_player_cell(start_cx, start_cy)

                                # 새로운 맨해튼 경로 생성
                                path = []
                                cx, cy = self.player.x, self.player.y
                                while cx != tx:
                                    cx += 1 if tx > cx else -1
                                    path.append((cx, cy))
                                while cy != ty:
                                    cy += 1 if ty > cy else -1
                                    path.append((cx, cy))

                                # 이전 경로 무시하고 새 경로로 부드럽게 이동
                                self.start_movement_to_path(path)
                                # 스킬 타겟 프리뷰 취소
                                self.clear_pending_card_preview()

                    if event.type == pygame.KEYDOWN:
                        keymap = {pygame.K_q: 0, pygame.K_w: 1, pygame.K_e: 2, pygame.K_r: 3}
                        if event.key in keymap:
                            idx = keymap[event.key]
                            mx, my = pygame.mouse.get_pos()
                            new_preview = self.build_preview_for_card(idx, (mx, my))
                            if new_preview is None:
                                continue
                            if self.pending_preview is None:
                                self.pending_preview = new_preview
                                self.pending_card_index = idx
                                self.current_target_preview = new_preview["coords"]
                            else:
                                if self.pending_card_index == idx and new_preview["center"] == self.pending_preview["center"]:
                                    self.execute_card_use(idx, new_preview["coords"])
                                    self.clear_pending_card_preview()
                                else:
                                    self.pending_preview = new_preview
                                    self.pending_card_index = idx
                                    self.current_target_preview = new_preview["coords"]

                elif self.state == "GAME_OVER":
                    self.draw()
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 160))
                    self.screen.blit(overlay, (0, 0))
                    go = BIGFONT.render("GAME OVER", True, RED)
                    sub = FONT.render("R: 재시작  Q: 종료", True, WHITE)
                    self.screen.blit(go, (SCREEN_W // 2 - go.get_width() // 2, SCREEN_H // 2 - 40))
                    self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 + 10))
                    pygame.display.flip()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            # 다시 초기화
                            self.__init__(self.screen)
                        if event.key == pygame.K_q:
                            running = False

            # 상태별 업데이트 & 그리기
            if self.state == "MENU":
                self.screen.fill(DARK)
                t = BIGFONT.render("컴과 프로젝트 – 메뉴 (클릭 또는 Enter로 진행)", True, WHITE)
                self.screen.blit(t, (50, SCREEN_H//2-30))
                pygame.display.flip()
            elif self.state == "SKILL_SELECT":
                self.screen.fill(DARK)
                t = BIGFONT.render("스킬 선택 (마우스 클릭으로 토글, Enter로 완료)", True, WHITE)
                self.screen.blit(t, (30, 20))
                start_x = 60
                start_y = 80
                slot_w = 100
                slot_h = 60
                for i,slot in enumerate(self.selection_slots):
                    rx = start_x + i*(slot_w+10)
                    ry = start_y
                    rect = pygame.Rect(rx,ry,slot_w,slot_h)
                    pygame.draw.rect(self.screen, LIGHT_GRAY if slot not in self.selected_skills else GREEN, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 2)
                    name = slot.name
                    txt = FONT.render(f"{name} (cost:{slot.cost})", True, BLACK)
                    self.screen.blit(txt, (rx+6, ry+20))
                info = FONT.render(f"선택 수: {len(self.selected_skills)}/5", True, WHITE)
                self.screen.blit(info, (30, 160))
                pygame.display.flip()
            elif self.state == "PLAY":
                self.update(dt)
                self.draw()

        pygame.quit()
        sys.exit()

# ---- 실행 ----
if __name__ == "__main__":
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("컴과 프로젝트 - Crab vs Fox (Prototype)")
    game = Game(screen)
    game.run()