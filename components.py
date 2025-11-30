import pygame
import random
from config import (
    CELL_WIDTH, CELL_HEIGHT, GRID_WIDTH, GRID_HEIGHT,
    PLAYER_START_HP, PLAYER_MOVE_TIME, PLAYER_SWIFT_MOVE_TIME, PLAYER_INVINCIBLE_TIME,
    IMAGE_PATH
)
from utils import load_image, get_screen_pos
from config import IMAGE_PATH, SCREEN_WIDTH, SCREEN_HEIGHT


class Cell:
    """
    게임판의 각 칸(Cell)을 나타내는 클래스.
    """

    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.hp = 1
        self.max_hp = 3
        self.is_dead = False  # '가시' 스킬로 인한 죽은 상태

        # 셀의 화면 위치 (미리 계산)
        self.screen_x, self.screen_y = get_screen_pos(self.grid_x, self.grid_y)
        self.rect = pygame.Rect(self.screen_x, self.screen_y, CELL_WIDTH, CELL_HEIGHT)

        # 셀 이미지 로드
        self.cell_images = {
            'dead': pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_DEAD')), (CELL_WIDTH, CELL_HEIGHT)),
            0: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_0')), (CELL_WIDTH, CELL_HEIGHT)),
            1: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_1')), (CELL_WIDTH, CELL_HEIGHT)),
            2: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_2')), (CELL_WIDTH, CELL_HEIGHT)),
            3: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_3')), (CELL_WIDTH, CELL_HEIGHT)),
            4: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_4')), (CELL_WIDTH, CELL_HEIGHT)),
            5: pygame.transform.scale(load_image(IMAGE_PATH.get('CELL_5')), (CELL_WIDTH, CELL_HEIGHT)),
            # ... (더 많은 체력 이미지 추가 가능)
        }
        self.image = self.get_current_image()

    def get_current_image(self):
        """현재 상태에 맞는 이미지를 반환합니다."""
        if self.is_dead:
            return self.cell_images['dead']

        # 체력 0~5 범위 내의 이미지를 사용. 5 이상은 5 이미지 사용.
        hp_key = max(0, min(self.hp, 5))

        if hp_key not in self.cell_images:
            # 해당 체력 이미지가 없으면 0 이미지 사용
            return self.cell_images[0]
        return self.cell_images[hp_key]

    def update_hp(self, amount):
        """
        칸의 체력을 amount만큼 변경합니다.
        죽은 칸은 체력을 변경할 수 없습니다 (재건축 스킬 제외).
        """
        if self.is_dead:
            return

        self.hp += amount
        # 체력은 0과 최대체력 사이로 제한
        self.hp = max(0, min(self.hp, self.max_hp))
        self.image = self.get_current_image()

    def set_max_hp(self, amount):
        """최대 체력을 amount만큼 증가시킵니다."""
        if self.is_dead:
            return
        self.max_hp += amount

    def kill_cell(self):
        """'가시' 또는 '직사광선' 스킬로 칸을 죽은 상태로 만듭니다."""
        self.hp = 0
        self.is_dead = True
        self.image = self.get_current_image()

    def revive_cell(self):
        """'재건축' 스킬로 칸을 부활시킵니다."""
        if self.is_dead:
            self.is_dead = False
            self.hp = 1
            self.max_hp = 1  # 최대체력 1로 부활
            self.image = self.get_current_image()

    def draw(self, surface):
        """칸을 그립니다."""
        surface.blit(self.image, self.rect.topleft)
        # (옵션) 체력 텍스트 표시
        # font = get_font(None, 15)
        # text_surf = font.render(str(self.hp), True, BLACK)
        # text_rect = text_surf.get_rect(center=self.rect.center)
        # surface.blit(text_surf, text_rect)


class Player:
    """
    플레이어(게) 클래스.
    """

    def __init__(self, start_grid_x, start_grid_y):
        self.hp = PLAYER_START_HP
        self.grid_x = start_grid_x
        self.grid_y = start_grid_y

        self.target_x = start_grid_x
        self.target_y = start_grid_y

        self.is_moving = False
        self.move_timer = 0.0
        self.move_speed = PLAYER_MOVE_TIME

        self.is_invincible = False
        self.invincible_timer = 0.0

        self.can_move = True  # '명상' 스킬용

        # 플레이어 이미지
        self.image = load_image(IMAGE_PATH.get('PLAYER_SPRITE', 'crab_sprite.png'),alpha=1)
        self.image = pygame.transform.scale(self.image, (CELL_WIDTH, CELL_HEIGHT*2/3))

    def set_target(self, grid_x, grid_y):
        """이동 목표 지점을 설정합니다."""
        if not self.can_move:
            return

        self.target_x = grid_x
        self.target_y = grid_y
        if self.target_x != self.grid_x or self.target_y != self.grid_y:
            self.is_moving = True

    def update(self, dt, grid):
        """
        플레이어 로직 업데이트 (이동, 무적 시간).
        grid: [[Cell, ...], ...] 2차원 리스트
        """
        # 1. 무적 시간 업데이트
        if self.is_invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.is_invincible = False
                print("무적 상태 종료")

        # 2. 이동 업데이트
        if self.is_moving and self.can_move:
            self.move_timer -= dt
            if self.move_timer <= 0:
                self.move_timer = self.move_speed  # 타이머 리셋
                self.move_one_step()

                # 이동 후 현재 칸 상태 체크
                self.check_current_cell(grid)

    def move_one_step(self):
        """목표를 향해 1칸 이동합니다 (X축 먼저, 그 다음 Y축)."""
        if self.grid_x != self.target_x:
            # X축 이동
            if self.target_x > self.grid_x:
                self.grid_x += 1
            else:
                self.grid_x -= 1
        elif self.grid_y != self.target_y:
            # Y축 이동
            if self.target_y > self.grid_y:
                self.grid_y += 1
            else:
                self.grid_y -= 1
        else:
            # 목표 도착
            self.is_moving = False

    def check_current_cell(self, grid):
        """
        현재 밟고 있는 칸을 체크하여 데미지를 입는지 확인합니다.
        """
        if self.is_invincible:
            return

        current_cell = grid[self.grid_x][self.grid_y]

        if current_cell.hp == 0 or current_cell.is_dead:
            print("플레이어 피격!")
            self.take_damage(1, grid)

    def take_damage(self, amount, grid):
        """
        데미지를 입고, 무적 상태가 되며, 랜덤 텔레포트를 합니다.
        """
        if self.is_invincible:
            return

        self.hp -= amount
        print(f"플레이어 체력: {self.hp}")

        if self.hp > 0:
            self.is_invincible = True
            self.invincible_timer = PLAYER_INVINCIBLE_TIME
            self.teleport_randomly(grid)
        else:
            # 게임 오버 로직은 GameScreen에서 처리
            pass

    def teleport_randomly(self, grid):
        """체력이 1 이상인 임의의 칸으로 순간이동합니다."""
        safe_cells = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if grid[x][y].hp > 0 and not grid[x][y].is_dead:
                    safe_cells.append((x, y))

        if safe_cells:
            new_x, new_y = random.choice(safe_cells)
            self.grid_x = new_x
            self.grid_y = new_y
            self.target_x = new_x
            self.target_y = new_y
            self.is_moving = False
            print(f"랜덤 텔레포트! -> ({new_x}, {new_y})")
        else:
            # 안전한 칸이 없으면 (이론상 게임 오버)
            print("안전한 칸이 없어 텔레포트 실패!")
            # 중앙으로 이동 (임시)
            self.grid_x = GRID_WIDTH // 2
            self.grid_y = GRID_HEIGHT // 2

    def set_move_speed(self, speed):
        """이동 속도를 변경합니다 (신속 스킬용)."""
        self.move_speed = speed

    def set_can_move(self, can_move):
        """이동 가능 여부를 설정합니다 (명상 스킬용)."""
        self.can_move = can_move
        if not can_move:
            self.is_moving = False

    def heal(self, amount):
        """체력을 회복합니다."""
        self.hp += amount
        self.hp = min(self.hp, PLAYER_START_HP)  # 최대 체력 2

    def draw(self, surface):
        """플레이어를 그립니다."""
        screen_x, screen_y = get_screen_pos(self.grid_x, self.grid_y)

        if self.is_invincible:
            # 무적 상태일 때 반짝임 (간단하게 투명도 조절)
            alpha_image = self.image.copy()
            alpha = 128 + (127 * (self.invincible_timer / PLAYER_INVINCIBLE_TIME))  # 128~255
            alpha_image.set_alpha(alpha)
            surface.blit(alpha_image, (screen_x, screen_y))
        else:
            surface.blit(self.image, (screen_x, screen_y))