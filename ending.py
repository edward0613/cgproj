# ending.py
import subprocess

import pygame
import sys

import opening
from SpeechBubble import (
    EndingSpeechBubble,
    BubbleOwner,
    load_hanna_fonts,
)

pygame.init()

# ===== 기본 설정 =====
WIDTH, HEIGHT = opening.WIDTH, opening.HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crab & Fox Ending")

clock = pygame.time.Clock()

# ===== 폰트 (공통: 한나체) =====
font_main, font_small = load_hanna_fonts()


# ===== 이미지 / 리소스 관리 클래스 =====
class Assets:
    def __init__(self, width: int, height: int):
        # 육지 배경
        self.shore_bg = pygame.image.load("shore.png").convert()
        self.shore_bg = pygame.transform.scale(self.shore_bg, (width, height))

        # 게 이미지 (1/4 크기)
        crab_base_img = pygame.image.load("crab2.png").convert_alpha()
        cw, ch = crab_base_img.get_size()
        self.crab_base_img = pygame.transform.smoothscale(
            crab_base_img, (int(cw / 2), int(ch / 2))
        )

        # 여우 이미지 (1/2 크기)
        fox_img = pygame.image.load("fox2.png").convert_alpha()
        fw, fh = fox_img.get_size()
        self.fox_img = pygame.transform.smoothscale(
            fox_img, (int(fw / 1.5), int(fh / 1.5))
        )


# ===== 엔딩 연출 클래스 =====
class Ending:
    def __init__(self, assets: Assets):
        self.assets = assets
        self.running = True
        self.phase = 1
        self.space_hint = True

        # 1단계: 검은 화면 → 밝아짐
        self.fade_alpha = 255
        self.fade_speed = 150

        # 여우 위치 (오른쪽)
        self.fox_rect = self.assets.fox_img.get_rect()
        self.fox_rect.midright = (WIDTH, HEIGHT // 2 + 100)

        # 게 초기 위치 (왼쪽, top-left 기준)
        cw, ch = self.assets.crab_base_img.get_size()
        start_tl_x = 100
        start_tl_y = HEIGHT // 2

        self.crab_center = [
            start_tl_x + cw / 2,
            start_tl_y + ch / 2,
        ]
        self.crab_angle = 0.0
        self.crab_scale = 1.0
        self.crab_visible = True

        # 2단계: 이동/회전/크기변화 파라미터
        self.move_duration = 2.0
        self.move_t = 0.0

        # 이전 코드와 "좌표는 그대로" 유지 (top-left 기준)
        end_tl_x = self.fox_rect.x + 250
        end_tl_y = self.fox_rect.y + 170

        self.move_start_scale = 1.0
        self.move_end_scale = 0.4

        self.move_start_center = (
            start_tl_x + cw * self.move_start_scale / 2,
            start_tl_y + ch * self.move_start_scale / 2,
        )
        self.move_end_center = (
            end_tl_x + cw * self.move_end_scale / 2,
            end_tl_y + ch * self.move_end_scale / 2,
        )

        self.angle_start = 0.0
        self.angle_end = 720.0

        # 3단계 말풍선/텍스트
        self.text_full = ""
        self.text_shown = 0.0
        self.text_speed = 24.0
        self.text_done = False

        self.bubble = None
        self.crab_owner = BubbleOwner()

        # 4단계: 축소
        self.shrink_duration = 1.5
        self.shrink_t = 0.0
        self.shrink_start_scale = self.move_end_scale

        # 5단계: 어두워짐
        self.end_fade_alpha = 0
        self.end_fade_target = 128
        self.end_fade_speed = 200

    # --- 게 이미지(회전/스케일) 얻기: 중심 기준 ---
    def get_crab_surf_and_rect(self):
        if not self.crab_visible:
            return None, None

        img = self.assets.crab_base_img

        # 스케일
        if self.crab_scale != 1.0:
            w0, h0 = img.get_size()
            new_w = max(1, int(w0 * self.crab_scale))
            new_h = max(1, int(h0 * self.crab_scale))
            img = pygame.transform.smoothscale(img, (new_w, new_h))

        # 회전
        if self.crab_angle != 0:
            img = pygame.transform.rotate(img, self.crab_angle)

        rect = img.get_rect(center=(self.crab_center[0], self.crab_center[1]))
        return img, rect

    # --- 단계 시작 ---
    def start_phase1(self):
        self.phase = 1
        self.space_hint = True
        self.fade_alpha = 255

    def start_phase2(self):
        self.phase = 2
        self.space_hint = True
        self.move_t = 0.0

    def start_phase3(self):
        self.phase = 3
        self.space_hint = True
        self.text_full = (
            "바다에서 살던 내가\n"
            "육지로 올라왔으니\n"
            "이런 일을 당해도 싸다.."
        )
        self.text_shown = 0.0
        self.text_speed = 24.0
        self.text_done = False

        # 말풍선: EndingSpeechBubble 사용 (화면 밖으로 안 나가게)
        self.bubble = EndingSpeechBubble(
            owner=self.crab_owner,
            text=self.text_full,
            direction="left",
            font=font_main,
            screen_width=WIDTH,
            screen_height=HEIGHT,
        )

    def start_phase4(self):
        self.phase = 4
        self.space_hint = True
        self.shrink_t = 0.0
        self.shrink_start_scale = self.crab_scale

    def start_phase5(self):
        self.phase = 5
        self.space_hint = False
        self.end_fade_alpha = 0

    # --- 스페이스 처리 ---
    def handle_space(self):
        if self.phase == 1:
            self.fade_alpha = 0
            self.start_phase2()

        elif self.phase == 2:
            self.crab_center[0] = self.move_end_center[0]
            self.crab_center[1] = self.move_end_center[1]
            self.crab_angle = self.angle_end
            self.crab_scale = self.move_end_scale
            self.start_phase3()

        elif self.phase == 3:
            if not self.text_done:
                self.text_shown = len(self.text_full)
                self.text_done = True
            else:
                self.start_phase4()

        elif self.phase == 4:
            self.crab_scale = 0.0
            self.crab_visible = False
            self.start_phase5()

        elif self.phase == 5:
            # 엔딩 상태에서 스페이스는 특별한 동작 없음
            pass

    # --- 업데이트 ---
    def update(self, dt):
        if self.phase == 1:
            if self.fade_alpha > 0:
                self.fade_alpha -= self.fade_speed * dt
                if self.fade_alpha < 0:
                    self.fade_alpha = 0

        elif self.phase == 2:
            # 회전 + 크기 작아지면서(1.0 → move_end_scale) 여우 쪽으로 이동
            self.move_t += dt / self.move_duration
            if self.move_t > 1.0:
                self.move_t = 1.0

            t = self.move_t

            cx = self.move_start_center[0] + (self.move_end_center[0] - self.move_start_center[0]) * t
            cy = self.move_start_center[1] + (self.move_end_center[1] - self.move_start_center[1]) * t
            self.crab_center[0] = cx
            self.crab_center[1] = cy

            self.crab_angle = self.angle_start + (self.angle_end - self.angle_start) * t
            self.crab_scale = self.move_start_scale + (self.move_end_scale - self.move_start_scale) * t

            if self.move_t >= 1.0:
                self.start_phase3()

        elif self.phase == 3:
            # 말풍선 텍스트 타이핑
            if not self.text_done:
                self.text_shown += self.text_speed * dt
                if self.text_shown >= len(self.text_full):
                    self.text_shown = len(self.text_full)
                    self.text_done = True

        elif self.phase == 4:
            # 게가 중심을 기준으로 작아지면서 사라지기
            self.shrink_t += dt / self.shrink_duration
            if self.shrink_t > 1.0:
                self.shrink_t = 1.0

            self.crab_scale = max(0.0, self.shrink_start_scale * (1.0 - self.shrink_t))

            if self.crab_scale <= 0.01:
                self.crab_visible = False
                self.start_phase5()

        elif self.phase == 5:
            # 화면 50% 어둡게
            if self.end_fade_alpha < self.end_fade_target:
                self.end_fade_alpha += self.end_fade_speed * dt
                if self.end_fade_alpha > self.end_fade_target:
                    self.end_fade_alpha = self.end_fade_target

    # --- 그리기 ---
    def draw(self, surface):
        # 배경(육지)
        surface.blit(self.assets.shore_bg, (0, 0))

        # 여우
        surface.blit(self.assets.fox_img, self.fox_rect)

        # 게
        crab_surf, crab_rect = self.get_crab_surf_and_rect()
        if crab_surf is not None and crab_rect is not None:
            surface.blit(crab_surf, crab_rect)

        # 3단계 말풍선
        if self.phase == 3 and self.bubble is not None and crab_rect is not None:
            # 말풍선 owner를 게 이미지 rect 기준으로 업데이트
            self.crab_owner.x = crab_rect.x
            self.crab_owner.y = crab_rect.y
            self.crab_owner.w = crab_rect.width
            self.crab_owner.h = crab_rect.height

            self.bubble.set_text(self.text_full)
            self.bubble.draw(surface, self.text_shown)

        # 1단계: 검은 페이드
        if self.phase == 1 and self.fade_alpha > 0:
            mask = pygame.Surface((WIDTH, HEIGHT))
            mask.set_alpha(int(self.fade_alpha))
            mask.fill((0, 0, 0))
            surface.blit(mask, (0, 0))

        # 5단계: 어두워지는 오버레이 + Q/R 표시
        if self.phase == 5:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(int(self.end_fade_alpha))
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))

            text = font_main.render("Q:재시작   R:종료", True, (255, 255, 255))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(text, rect)

        # 스페이스바 안내 (1~4단계)
        if self.space_hint and self.phase in (1, 2, 3, 4):
            hint = font_small.render("스페이스바를 누르세요", True, (255, 255, 255))
            hint_rect = hint.get_rect(midtop=(WIDTH // 2, 10))
            surface.blit(hint, hint_rect)


# ===== 앱 / 메인 루프 클래스 =====
class EndingApp:
    def __init__(self):
        self.screen = screen
        self.clock = clock

        self.assets = Assets(WIDTH, HEIGHT)
        self.ending = Ending(self.assets)

    def run(self):
        """return True이면 opening.py 다시 실행, False이면 그냥 종료"""
        restart_to_opening = False

        while self.ending.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.ending.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.ending.handle_space()

                    # 5단계에서 Q/R 처리
                    if self.ending.phase == 5:
                        if event.key == pygame.K_q:
                            # 오프닝으로 재시작
                            restart_to_opening = True
                            self.ending.running = False
                        elif event.key == pygame.K_r:
                            self.ending.running = False

            self.ending.update(dt)
            self.ending.draw(self.screen)
            pygame.display.flip()

        return restart_to_opening

# ===== 진입점 =====
def main():
    app = EndingApp()
    restart = app.run()

    pygame.quit()

    # 여기서는 프로세스 종료 코드만 돌려준다.
    # Q(재시작) → 1, R(종료) → 0
    if restart:
        return 1
    else:
        return 0


if __name__ == "__main__":
    code = main()
    sys.exit(code)

