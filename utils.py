import pygame
import os
from config import GRID_START_X, GRID_START_Y, CELL_WIDTH, CELL_HEIGHT, GRID_WIDTH, GRID_HEIGHT

# 이미지 로딩 캐시
IMAGE_CACHE = {}


def load_image(path, use_colorkey=False, colorkey_color=None,alpha=None):
    """
    이미지를 로드하고 캐시합니다.
    크기 조절(scale)이나 투명도(colorkey) 처리가 필요할 경우 수정.
    """
    global IMAGE_CACHE
    if path in IMAGE_CACHE:
        return IMAGE_CACHE[path]

    if not os.path.exists(path):
        print(f"경고: 이미지 파일을 찾을 수 없습니다: {path}")
        # 파일을 찾을 수 없을 때, 지정된 크기의 회색 사각형 반환
        image = pygame.Surface((CELL_WIDTH, CELL_HEIGHT))
        image.fill((100, 100, 100))
        IMAGE_CACHE[path] = image
        return image

    try:
        if alpha is not None:
            image = pygame.image.load(path).convert_alpha()
            print(2345678)
        else:
            image = pygame.image.load(path).convert()

        if use_colorkey:
            if colorkey_color is None:
                colorkey_color = image.get_at((0, 0))
            image.set_colorkey(colorkey_color, pygame.RLEACCEL)

        # 알파 채널이 있는 PNG의 경우 convert_alpha() 사용


        IMAGE_CACHE[path] = image
        return image
    except pygame.error as e:
        print(f"이미지 로딩 오류 '{path}': {e}")
        image = pygame.Surface((CELL_WIDTH, CELL_HEIGHT))
        image.fill((100, 100, 100))  # 오류 시 회색 사각형
        IMAGE_CACHE[path] = image
        return image


# 폰트 로딩 캐시
FONT_CACHE = {}


def get_font(font_path, size):
    """지정된 경로와 크기의 폰트 객체를 로드하고 캐시합니다."""
    global FONT_CACHE
    key = (font_path, size)
    if key not in FONT_CACHE:
        try:
            FONT_CACHE[key] = pygame.font.Font(font_path, size)
        except Exception:
            # 오류 발생 시 Pygame 기본 폰트 사용
            FONT_CACHE[key] = pygame.font.Font(None, size)
    return FONT_CACHE[key]


def get_mouse_grid_pos(mouse_pos):
    """
    화면 픽셀 좌표(mouse_pos)를 그리드 좌표(x, y)로 변환합니다.
    그리드 밖이면 None을 반환합니다.
    """
    mx, my = mouse_pos
    # 그리드 영역 안인지 확인
    if (mx < GRID_START_X or mx >= GRID_START_X + (GRID_WIDTH * CELL_WIDTH) or
            my < GRID_START_Y or my >= GRID_START_Y + (GRID_HEIGHT * CELL_HEIGHT)):
        return None

    grid_x = (mx - GRID_START_X) // CELL_WIDTH
    grid_y = (my - GRID_START_Y) // CELL_HEIGHT

    return grid_x, grid_y


def get_screen_pos(grid_x, grid_y):
    """그리드 좌표를 화면 픽셀 좌표(좌상단)로 변환합니다."""
    screen_x = GRID_START_X + (grid_x * CELL_WIDTH)
    screen_y = GRID_START_Y + (grid_y * CELL_HEIGHT)
    return screen_x, screen_y


def calculate_target_area(center_grid_pos, size_x, size_y):
    """
    기획서의 복잡한 스킬 범위 계산 로직을 구현합니다.
    center_grid_pos: (x, y) 튜플
    size_x, size_y: 범위 크기 (예: 3, 3)
    반환: [(x1, y1), (x2, y2), ...] 형태의 그리드 좌표 리스트
    """
    if center_grid_pos is None:
        return []

    cx, cy = center_grid_pos
    area = []

    # 1. 홀수 x 홀수 (e.g., 3x3)
    if size_x % 2 != 0 and size_y % 2 != 0:
        offset_x = (size_x - 1) // 2
        offset_y = (size_y - 1) // 2
        start_x, end_x = cx - offset_x, cx + offset_x
        start_y, end_y = cy - offset_y, cy + offset_y

    # 2. 홀수 x 짝수 (e.g., 3x2)
    elif size_x % 2 != 0 and size_y % 2 != 0:
        offset_x = (size_x - 1) // 2
        offset_y_top = size_y // 2  # 위로 한 칸 더
        offset_y_bottom = (size_y // 2) - 1
        start_x, end_x = cx - offset_x, cx + offset_x
        start_y, end_y = cy - offset_y_top, cy + offset_y_bottom

    # 3. 짝수 x 홀수 (e.g., 2x3)
    elif size_x % 2 == 0 and size_y % 2 != 0:
        offset_x_left = size_x // 2  # 왼쪽으로 한 칸 더
        offset_x_right = (size_x // 2) - 1
        offset_y = (size_y - 1) // 2
        start_x, end_x = cx - offset_x_left, cx + offset_x_right
        start_y, end_y = cy - offset_y, cy + offset_y

    # 4. 짝수 x 짝수 (e.g., 2x4) - 기획서: 좌측 상단 기준
    elif size_x % 2 == 0 and size_y % 2 == 0:
        start_x, end_x = cx, cx + size_x - 1
        start_y, end_y = cy, cy + size_y - 1

    else:
        # 이 경우는 발생하지 않아야 함
        return []

    # 그리드 범위 내의 유효한 좌표만 리스트에 추가
    for x in range(start_x, end_x + 1):
        for y in range(start_y, end_y + 1):
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                area.append((x, y))

    return area


def calculate_cross_area(center_grid_pos):
    """십자가 모양 영역 계산 (상하좌우 1칸)"""
    if center_grid_pos is None:
        return []

    cx, cy = center_grid_pos
    area = []
    positions = [
        (cx, cy),  # 중앙
        (cx, cy - 1),  # 상
        (cx, cy + 1),  # 하
        (cx - 1, cy),  # 좌
        (cx + 1, cy)  # 우
    ]

    for x, y in positions:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            area.append((x, y))
    return area


def calculate_plus_area(center_grid_pos):
    """열 십(十) 모양 영역 계산 (가로 5칸, 세로 5칸)"""
    if center_grid_pos is None:
        return []

    cx, cy = center_grid_pos
    area = set()  # 중복 방지

    # 가로 5칸
    for x in range(cx - 2, cx + 3):
        if 0 <= x < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
            area.add((x, cy))

    # 세로 5칸
    for y in range(cy - 2, cy + 3):
        if 0 <= cx < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            area.add((cx, y))

    return list(area)