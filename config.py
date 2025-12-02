import pygame

# 화면 설정 (요청에 따라 전체화면 기준이 될 기본 해상도)
# 사용자의 모니터 해상도에 맞게 조정될 수 있음
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
FPS = 60

# 그리드 설정
GRID_WIDTH = 24
GRID_HEIGHT = 16

# UI 영역 설정
NOTIFICATION_BAR_HEIGHT = 100
BOTTOM_UI_HEIGHT = 150

# 그리드 영역 계산
# (SCREEN_HEIGHT에서 상단 알림창과 하단 UI 영역을 뺀 높이)
GRID_AREA_HEIGHT = SCREEN_HEIGHT - NOTIFICATION_BAR_HEIGHT - BOTTOM_UI_HEIGHT

# 셀 크기 (그리드 영역을 기준으로 자동 계산)
# 정사각형 셀을 유지하기 위해 더 작은 쪽을 기준으로 계산
CELL_WIDTH = min(SCREEN_WIDTH // GRID_WIDTH, GRID_AREA_HEIGHT // GRID_HEIGHT)
CELL_HEIGHT = CELL_WIDTH

# 그리드 전체 크기
GRID_TOTAL_WIDTH = CELL_WIDTH * GRID_WIDTH
GRID_TOTAL_HEIGHT = CELL_HEIGHT * GRID_HEIGHT

# 그리드 시작 위치 (화면 중앙 정렬)
GRID_START_X = (SCREEN_WIDTH - GRID_TOTAL_WIDTH) // 2
GRID_START_Y = NOTIFICATION_BAR_HEIGHT + (GRID_AREA_HEIGHT - GRID_TOTAL_HEIGHT) // 2

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
HIGHLIGHT_COLOR = (255, 255, 0, 100) # 플레이어 스킬 하이라이트 (노란색, 반투명)
FOX_ATTACK_WARN_COLOR = (255, 0, 0, 150) # 여우 공격 경고 (빨간색, 반투명)
FOX_ATTACK_EXEC_COLOR = (0, 255, 0, 150) # 여우 공격 실행 (초록색, 반투명)

# 플레이어 설정
PLAYER_START_HP = 2
PLAYER_MOVE_TIME = 0.3  # 1칸 이동 시간 (초)
PLAYER_SWIFT_MOVE_TIME = 0.2 # 신속 스킬 사용 시
PLAYER_INVINCIBLE_TIME = 1.0 # 피격 후 무적 시간 (초)

# 게임 시스템 설정
MAX_MONEY = 12
MONEY_GAIN_INTERVAL = 1.0 # 돈 1원 획득 시간 (초)

# 파일 경로
FONT_PATH = "CookieRunBold.ttf" # 기본 폰트 사용. 특별한 폰트 사용 시 "path/to/font.ttf"
IMAGE_PATH = {
    'SHORE_BG': 'shore.png',
    'SQUARE_UI': 'square.png',
    'FOX_ICON': 'fox1.png',
    'MENU_BG': 'menuscreen.png',
    'CELL_0': 'cell0.png',
    'CELL_1': 'cell1.png',
    'CELL_2': 'cell2.png',
    'CELL_3': 'cell3.png',
    'CELL_4': 'cell4.png',
    'CELL_5': 'cell5.png',
    # ... (체력별 이미지)
    'CELL_DEAD': 'dead.png',
    'PLAYER_SPRITE': 'crab1.png',
    'MENU_BUTTON': 'buttonimg.png',
    'GAME_BG': 'backscreen4.png',
    'CRAB': 'crab.png'
}
SOUND_PATH = {
    "GAME_BGM": "Crab and Fox Chase.mp3"
}