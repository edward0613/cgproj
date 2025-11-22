import pygame
import sys
import math

pygame.init()

# ===== 기본 설정 =====
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crab & Fox Opening")

clock = pygame.time.Clock()

# ===== 폰트 =====
font_main = pygame.font.SysFont("malgungothic", 28)
font_small = pygame.font.SysFont("malgungothic", 20)

# ===== 이미지 로드 =====
sea_bg = pygame.image.load("sea.jpeg").convert()
sea_bg = pygame.transform.scale(sea_bg, (WIDTH, HEIGHT))

shore_bg = pygame.image.load("shore.jpeg").convert()
shore_bg = pygame.transform.scale(shore_bg, (WIDTH, HEIGHT))

# 게 이미지 (1/4 크기)
crab_img = pygame.image.load("crab1.png").convert_alpha()
w_crab, h_crab = crab_img.get_size()
crab_img = pygame.transform.scale(crab_img, (int(w_crab / 4), int(h_crab / 4)))

# 여우 이미지 (1/4 크기)
fox_img = pygame.image.load("fox1.png").convert_alpha()
w_fox, h_fox = fox_img.get_size()
fox_img = pygame.transform.scale(fox_img, (int(w_fox / 4), int(h_fox / 4)))


# ===== 말풍선 그리기 함수 (수정됨) =====
def draw_speech_bubble(
    surface,
    char_x,
    char_y,
    char_w,
    char_h,
    full_lines,     # 전체 텍스트 줄 리스트(크기 계산용, 고정)
    render_lines,   # 현재까지 보여줄 텍스트 줄 리스트(타자 효과용)
    direction="right",
):

    if not full_lines:
        return

    padding = 12
    line_height = 28

    # 전체 텍스트 길이에 따라 말풍선 크기 "한 번만" 결정
    bubble_w = max(font_main.size(line)[0] for line in full_lines) + padding * 2
    bubble_h = line_height * len(full_lines) + padding * 2

    # 캐릭터 기준 말풍선 위치 계산
    if direction == "right":
        # 캐릭터 오른쪽 위에 딱 붙게
        bubble_x = char_x + char_w
        bubble_y = char_y - bubble_h - 30
        tail_tip_x = char_x + char_w
        tail_tip_y = char_y
    else:  # "left"
        # 캐릭터 왼쪽 위에 딱 붙게
        bubble_x = char_x - bubble_w - 10
        bubble_y = char_y - bubble_h - 30
        tail_tip_x = char_x
        tail_tip_y = char_y

    bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)

    # 말풍선 몸통
    pygame.draw.rect(surface, (255, 255, 255), bubble_rect, border_radius=14)
    pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 3, border_radius=14)

    base_y = bubble_y + bubble_h  # 말풍선 아래쪽에서 나옴

    if direction == "right":
        base_x1 = bubble_x + 15
        base_x2 = bubble_x + 45
    else:  # left
        base_x1 = bubble_x + bubble_w - 15
        base_x2 = bubble_x + bubble_w - 45

    tail_points = [
        (base_x1, base_y),
        (base_x2, base_y),
        (tail_tip_x, tail_tip_y),
    ]

    pygame.draw.polygon(surface, (255, 255, 255), tail_points)
    pygame.draw.polygon(surface, (0, 0, 0), tail_points, 3)

    # 텍스트 그리기 (여기서는 "현재까지 보여줄 텍스트"만 사용)
    ty = bubble_y + padding

    # render_lines 길이를 full_lines 길이에 맞게 맞춰줌 (없는 줄은 빈 문자열)
    padded_render = list(render_lines) + [""] * (len(full_lines) - len(render_lines))

    for line in padded_render[: len(full_lines)]:
        surf = font_main.render(line, True, (0, 0, 0))
        surface.blit(surf, (bubble_x + padding, ty))
        ty += line_height


# ===== 오프닝 클래스 =====
class Opening:
    def __init__(self):
        self.phase = 1          # 1~10 단계
        self.running = True
        self.space_hint = True  # "스페이스바를 누르세요" 출력 여부

        # 건너뛰기 버튼 (왼쪽 상단)
        self.skip_text = font_small.render("건너뛰기", True, (255, 255, 255))
        self.skip_rect = self.skip_text.get_rect(topleft=(10, 10))

        # 페이드용 서피스
        self.fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.fade_surface.fill((0, 0, 0, 255))
        self.fade_alpha = 255

        # 텍스트 관련 변수
        self.text_full = ""
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False
        self.delay = 0.0

        # 캐릭터 위치
        self.crab_x = WIDTH // 2
        self.crab_y = HEIGHT // 2
        self.fox_x = WIDTH // 2
        self.fox_y = HEIGHT // 2

        # 1단계 시작
        self.start_phase1()

    # ----- 각 단계 초기화 -----
    def start_phase1(self):
        self.phase = 1
        self.space_hint = True
        self.radius = 0
        self.max_radius = int(math.hypot(WIDTH, HEIGHT))
        self.reveal_speed = self.max_radius / 1.5

    def start_phase2(self):
        self.phase = 2
        self.space_hint = True

        self.crab_y = HEIGHT - crab_img.get_height() - 40
        self.crab_target_x = WIDTH - crab_img.get_width() - 40
        self.crab_x = WIDTH + 100
        self.crab_speed = 400

    def start_phase3(self):
        self.phase = 3
        self.space_hint = True

        self.text_full = "바다 속에서만 사니까\n너무 지루한데"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False
        self.delay = 1.0

    def start_phase4(self):
        self.phase = 4
        self.space_hint = True

        self.text_full = "육지로 한번 나가볼까"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False

    def start_phase5(self):
        self.phase = 5
        self.space_hint = True

        self.dark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dark_surface.fill((0, 0, 0, 255))
        self.dark_alpha = 0

        self.crab_move_duration = 2.0
        self.crab_move_t = 0.0
        self.crab_start_pos = (self.crab_x, self.crab_y)
        self.crab_end_pos = (WIDTH * 0.2, HEIGHT * 0.2)

    def start_phase6(self):
        self.phase = 6
        self.space_hint = True

        self.crab_x = 60
        self.crab_y = HEIGHT - crab_img.get_height() - 40
        self.fade_alpha = 255

    def start_phase7(self):
        self.phase = 7
        self.space_hint = True

        self.fox_y = HEIGHT - fox_img.get_height() - 40
        self.fox_target_x = WIDTH - fox_img.get_width() - 60
        self.fox_x = WIDTH + 120
        self.fox_speed = 500

    def start_phase8(self):
        self.phase = 8
        self.space_hint = True

        self.text_full = "마침 배고픈데 잘됐다\n잡아먹어야겠어"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False

    def start_phase9(self):
        self.phase = 9
        self.space_hint = True

        self.text_full = "!?!?!?!?!?"
        self.text_shown = 0.0
        self.text_speed = 40.0
        self.text_done = False

    def start_phase10(self):
        self.phase = 10
        self.space_hint = False
        self.fade_alpha = 0

    # ----- 스페이스바: 항상 '다음 단계' -----
    def handle_space(self):
        if self.phase == 1:
            self.start_phase2()

        elif self.phase == 2:
            self.crab_x = self.crab_target_x
            self.start_phase3()

        elif self.phase in (3, 4, 8, 9):
            if not self.text_done:
                self.text_shown = len(self.text_full)
                self.text_done = True
            else:
                if self.phase == 3:
                    self.start_phase4()
                elif self.phase == 4:
                    self.start_phase5()
                elif self.phase == 8:
                    self.start_phase9()
                elif self.phase == 9:
                    self.start_phase10()

        elif self.phase == 5:
            self.dark_alpha = 255
            self.crab_x, self.crab_y = self.crab_end_pos
            self.start_phase6()

        elif self.phase == 6:
            self.fade_alpha = 0
            self.start_phase7()

        elif self.phase == 7:
            self.fox_x = self.fox_target_x
            self.start_phase8()

        elif self.phase == 10:
            self.running = False

    # ----- 건너뛰기 버튼: 언제 누르든 바로 10번 단계로 -----
    def handle_skip(self):
        self.start_phase10()

    # ----- 단계별 업데이트 -----
    def update(self, dt):
        if self.phase == 1:
            self.radius += self.reveal_speed * dt
            if self.radius >= self.max_radius:
                self.start_phase2()

        elif self.phase == 2:
            if self.crab_x > self.crab_target_x:
                self.crab_x -= self.crab_speed * dt
                if self.crab_x <= self.crab_target_x:
                    self.crab_x = self.crab_target_x

        elif self.phase == 3:
            if self.delay > 0:
                self.delay -= dt
            else:
                if not self.text_done:
                    self.text_shown += self.text_speed * dt
                    if self.text_shown >= len(self.text_full):
                        self.text_shown = len(self.text_full)
                        self.text_done = True

        elif self.phase == 4:
            if not self.text_done:
                self.text_shown += self.text_speed * dt
                if self.text_shown >= len(self.text_full):
                    self.text_shown = len(self.text_full)
                    self.text_done = True

        elif self.phase == 5:
            self.crab_move_t += dt
            t = min(1.0, self.crab_move_t / self.crab_move_duration)
            sx, sy = self.crab_start_pos
            ex, ey = self.crab_end_pos
            self.crab_x = sx + (ex - sx) * t
            self.crab_y = sy + (ey - sy) * t

            self.dark_alpha = min(255, self.dark_alpha + 120 * dt)
            if t >= 1.0 and self.dark_alpha >= 255:
                self.start_phase6()

        elif self.phase == 6:
            self.fade_alpha = max(0, self.fade_alpha - 120 * dt)
            if self.fade_alpha <= 0:
                self.start_phase7()

        elif self.phase == 7:
            if self.fox_x > self.fox_target_x:
                self.fox_x -= self.fox_speed * dt
                if self.fox_x <= self.fox_target_x:
                    self.fox_x = self.fox_target_x

        elif self.phase == 8:
            if not self.text_done:
                self.text_shown += self.text_speed * dt
                if self.text_shown >= len(self.text_full):
                    self.text_shown = len(self.text_full)
                    self.text_done = True

        elif self.phase == 9:
            if not self.text_done:
                self.text_shown += self.text_speed * dt
                if self.text_shown >= len(self.text_full):
                    self.text_shown = len(self.text_full)
                    self.text_done = True

        elif self.phase == 10:
            self.fade_alpha = min(255, self.fade_alpha + 120 * dt)
            if self.fade_alpha >= 255:
                self.running = False

    # ----- 화면 그리기 -----
    def draw(self, surface):
        # 배경
        if self.phase in (1, 2, 3, 4, 5):
            surface.blit(sea_bg, (0, 0))
        else:
            surface.blit(shore_bg, (0, 0))

        # 게
        if self.phase >= 2:
            surface.blit(crab_img, (self.crab_x, self.crab_y))

        # 여우
        if self.phase >= 7:
            surface.blit(fox_img, (self.fox_x, self.fox_y))

        # ===== 말풍선 (텍스트 단계인 3,4,8,9에서만 – 수정됨) =====
        if self.phase in (3, 4, 8, 9):
            # 전체 텍스트 기준 줄 나누기 (크기 계산용)
            full_lines = self.text_full.split("\n")

            # 현재까지 보여줄 텍스트
            shown_text = self.text_full[: int(self.text_shown)]
            shown_parts = shown_text.split("\n")

            # full_lines 개수에 맞게 줄 맞추기
            render_lines = []
            for i, line in enumerate(full_lines):
                if i < len(shown_parts):
                    render_lines.append(shown_parts[i])
                else:
                    render_lines.append("")

            # 3,4: 게의 왼쪽 위
            if self.phase in (3, 4):
                draw_speech_bubble(
                    surface,
                    self.crab_x,
                    self.crab_y,
                    crab_img.get_width(),
                    crab_img.get_height(),
                    full_lines,
                    render_lines,
                    direction="left",
                )

            # 8: 여우의 왼쪽 위
            elif self.phase == 8:
                draw_speech_bubble(
                    surface,
                    self.fox_x,
                    self.fox_y,
                    fox_img.get_width(),
                    fox_img.get_height(),
                    full_lines,
                    render_lines,
                    direction="left",
                )

            # 9: 게의 오른쪽 위
            elif self.phase == 9:
                draw_speech_bubble(
                    surface,
                    self.crab_x,
                    self.crab_y,
                    crab_img.get_width(),
                    crab_img.get_height(),
                    full_lines,
                    render_lines,
                    direction="right",
                )

        # 1단계: 원형 밝아지는 마스크
        if self.phase == 1:
            mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 255))
            pygame.draw.circle(
                mask,
                (0, 0, 0, 0),
                (WIDTH // 2, HEIGHT // 2),
                int(self.radius),
            )
            surface.blit(mask, (0, 0))

        # 5단계: 어두워지는 오버레이
        if self.phase == 5:
            self.dark_surface.set_alpha(int(self.dark_alpha))
            surface.blit(self.dark_surface, (0, 0))

        # 6, 10단계: 페이드(검은 오버레이)
        if self.phase in (6, 10):
            self.fade_surface.set_alpha(int(self.fade_alpha))
            surface.blit(self.fade_surface, (0, 0))

        # 스페이스바 안내
        if self.space_hint and self.phase != 10:
            hint = font_small.render("스페이스바를 누르세요", True, (255, 255, 255))
            hint_rect = hint.get_rect(midtop=(WIDTH // 2, 10))
            surface.blit(hint, hint_rect)

        # 건너뛰기 버튼
        bg_rect = self.skip_rect.inflate(10, 6)
        pygame.draw.rect(surface, (0, 0, 0), bg_rect, border_radius=6)
        surface.blit(self.skip_text, self.skip_rect)


# ===== 메인 루프 =====
def main():
    opening = Opening()

    while opening.running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                opening.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    opening.handle_space()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if opening.skip_rect.collidepoint(event.pos):
                    opening.handle_skip()

        opening.update(dt)
        opening.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
