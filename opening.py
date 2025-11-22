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
crab_img_raw = pygame.image.load("crab1.png").convert_alpha()
w_crab, h_crab = crab_img_raw.get_size()
crab_img = pygame.transform.scale(crab_img_raw, (int(w_crab / 4), int(h_crab / 4)))

# 여우 이미지 (1/4 크기)
fox_img_raw = pygame.image.load("fox1.png").convert_alpha()
w_fox, h_fox = fox_img_raw.get_size()
fox_img = pygame.transform.scale(fox_img_raw, (int(w_fox / 4), int(h_fox / 4)))


# ===== 캐릭터 클래스 =====
class Character:
    def __init__(self, image: pygame.Surface, x: float = 0, y: float = 0):
        self.image = image
        self.x = x
        self.y = y

    @property
    def w(self):
        return self.image.get_width()

    @property
    def h(self):
        return self.image.get_height()

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, (self.x, self.y))


# ===== 말풍선 클래스 =====
class SpeechBubble:
    def __init__(
        self,
        owner: Character,
        text: str,
        direction: str = "right",
        padding: int = 12,
        line_height: int = 28,
    ):
        """
        owner      : 말풍선을 붙일 캐릭터(Character)
        text       : 전체 텍스트 (예: "문장1\n문장2")
        direction  : "right" → 캐릭터 오른쪽 위, "left" → 캐릭터 왼쪽 위
        padding    : 말풍선 안쪽 여백
        line_height: 한 줄 높이
        """
        self.owner = owner
        self.direction = direction
        self.padding = padding
        self.line_height = line_height
        self.set_text(text)

    def set_text(self, text: str):
        """텍스트를 바꾸면 한 번만 크기를 다시 계산"""
        self.text = text
        self.full_lines = self.text.split("\n")
        if not self.full_lines:
            self.full_lines = [""]

        # 전체 텍스트 기준으로 말풍선 크기 고정
        self.bubble_w = max(font_main.size(line)[0] for line in self.full_lines) + self.padding * 2
        self.bubble_h = self.line_height * len(self.full_lines) + self.padding * 2

    def _compute_geometry(self):
        """캐릭터 위치와 방향에 따라 말풍선 위치 + 꼬리 위치 계산"""
        char_x, char_y = self.owner.x, self.owner.y
        char_w, char_h = self.owner.w, self.owner.h

        if self.direction == "right":
            bubble_x = char_x + char_w
            bubble_y = char_y - self.bubble_h - 30
            tail_tip_x = char_x + char_w
            tail_tip_y = char_y
        else:
            bubble_x = char_x - self.bubble_w - 10
            bubble_y = char_y - self.bubble_h - 30
            tail_tip_x = char_x
            tail_tip_y = char_y

        return bubble_x, bubble_y, tail_tip_x, tail_tip_y

    def draw(self, surface: pygame.Surface, shown_chars: float):
        """shown_chars: 현재까지 보여줄 글자 수 (타자 효과용)"""
        if not self.full_lines:
            return

        bubble_x, bubble_y, tail_tip_x, tail_tip_y = self._compute_geometry()

        bubble_rect = pygame.Rect(bubble_x, bubble_y, self.bubble_w, self.bubble_h)

        # 말풍선 몸통
        pygame.draw.rect(surface, (255, 255, 255), bubble_rect, border_radius=14)
        pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 3, border_radius=14)

        # 꼬리
        base_y = bubble_y + self.bubble_h
        if self.direction == "right":
            base_x1 = bubble_x + 15
            base_x2 = bubble_x + 45
        else:
            base_x1 = bubble_x + self.bubble_w - 15
            base_x2 = bubble_x + self.bubble_w - 45

        tail_points = [
            (base_x1, base_y),
            (base_x2, base_y),
            (tail_tip_x, tail_tip_y),
        ]

        pygame.draw.polygon(surface, (255, 255, 255), tail_points)
        pygame.draw.polygon(surface, (0, 0, 0), tail_points, 3)

        # 텍스트 (현재까지 나온 부분만)
        partial_text = self.text[: int(shown_chars)]
        shown_parts = partial_text.split("\n")

        # full_lines 개수에 맞게 줄 정렬
        render_lines = []
        for i, line in enumerate(self.full_lines):
            if i < len(shown_parts):
                render_lines.append(shown_parts[i])
            else:
                render_lines.append("")

        ty = bubble_y + self.padding
        for line in render_lines:
            surf = font_main.render(line, True, (0, 0, 0))
            surface.blit(surf, (bubble_x + self.padding, ty))
            ty += self.line_height


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

        # 캐릭터 객체
        self.crab = Character(crab_img, WIDTH // 2, HEIGHT // 2)
        self.fox = Character(fox_img, WIDTH // 2, HEIGHT // 2)

        # 말풍선 객체 (필요할 때 생성)
        self.bubble: SpeechBubble | None = None

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

        self.crab.y = HEIGHT - self.crab.h - 40
        self.crab_target_x = WIDTH - self.crab.w - 40
        self.crab.x = WIDTH + 100
        self.crab_speed = 400

    def start_phase3(self):
        self.phase = 3
        self.space_hint = True

        self.text_full = "바다 속에서만 사니까\n너무 지루한데"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False
        self.delay = 1.0

        # 게 왼쪽 위 말풍선
        self.bubble = SpeechBubble(self.crab, self.text_full, direction="left")

    def start_phase4(self):
        self.phase = 4
        self.space_hint = True

        self.text_full = "육지로 한번 나가볼까"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False

        # 같은 게 말풍선, 텍스트만 변경
        if self.bubble is None:
            self.bubble = SpeechBubble(self.crab, self.text_full, direction="left")
        else:
            self.bubble.direction = "left"
            self.bubble.set_text(self.text_full)

    def start_phase5(self):
        self.phase = 5
        self.space_hint = True

        self.dark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dark_surface.fill((0, 0, 0, 255))
        self.dark_alpha = 0

        self.crab_move_duration = 2.0
        self.crab_move_t = 0.0
        self.crab_start_pos = (self.crab.x, self.crab.y)
        self.crab_end_pos = (WIDTH * 0.2, HEIGHT * 0.2)

    def start_phase6(self):
        self.phase = 6
        self.space_hint = True

        self.crab.x = 60
        self.crab.y = HEIGHT - self.crab.h - 40
        self.fade_alpha = 255

    def start_phase7(self):
        self.phase = 7
        self.space_hint = True

        self.fox.y = HEIGHT - self.fox.h - 40
        self.fox_target_x = WIDTH - self.fox.w - 60
        self.fox.x = WIDTH + 120
        self.fox_speed = 500

    def start_phase8(self):
        self.phase = 8
        self.space_hint = True

        self.text_full = "마침 배고픈데 잘됐다\n잡아먹어야겠어"
        self.text_shown = 0.0
        self.text_speed = 20.0
        self.text_done = False

        # 여우 왼쪽 위 말풍선
        self.bubble = SpeechBubble(self.fox, self.text_full, direction="left")

    def start_phase9(self):
        self.phase = 9
        self.space_hint = True

        self.text_full = "!?!?!?!?!?"
        self.text_shown = 0.0
        self.text_speed = 40.0
        self.text_done = False

        # 게 오른쪽 위 말풍선
        self.bubble = SpeechBubble(self.crab, self.text_full, direction="right")

    def start_phase10(self):
        self.phase = 10
        self.space_hint = False
        self.fade_alpha = 0

    # ----- 스페이스바: 항상 '다음 단계' -----
    def handle_space(self):
        if self.phase == 1:
            self.start_phase2()

        elif self.phase == 2:
            self.crab.x = self.crab_target_x
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
            self.crab.x, self.crab.y = self.crab_end_pos
            self.start_phase6()

        elif self.phase == 6:
            self.fade_alpha = 0
            self.start_phase7()

        elif self.phase == 7:
            self.fox.x = self.fox_target_x
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
            if self.crab.x > self.crab_target_x:
                self.crab.x -= self.crab_speed * dt
                if self.crab.x <= self.crab_target_x:
                    self.crab.x = self.crab_target_x

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
            self.crab.x = sx + (ex - sx) * t
            self.crab.y = sy + (ey - sy) * t

            self.dark_alpha = min(255, self.dark_alpha + 120 * dt)
            if t >= 1.0 and self.dark_alpha >= 255:
                self.start_phase6()

        elif self.phase == 6:
            self.fade_alpha = max(0, self.fade_alpha - 120 * dt)
            if self.fade_alpha <= 0:
                self.start_phase7()

        elif self.phase == 7:
            if self.fox.x > self.fox_target_x:
                self.fox.x -= self.fox_speed * dt
                if self.fox.x <= self.fox_target_x:
                    self.fox.x = self.fox_target_x

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
            self.crab.draw(surface)

        # 여우
        if self.phase >= 7:
            self.fox.draw(surface)

        # 말풍선 (3,4,8,9 단계에서만)
        if self.phase in (3, 4, 8, 9) and self.bubble is not None:
            self.bubble.draw(surface, self.text_shown)

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
