# ending.py
import pygame
import sys

import opening  # WIDTH, HEIGHT, font_main, font_small 재사용
from SpeechBubble import MakeSpeechBubble

pygame.init()

# ===== 기본 설정 / 공용 자원 =====
WIDTH, HEIGHT = opening.WIDTH, opening.HEIGHT
font_main = opening.font_main
font_small = opening.font_small


# ===== 말풍선 Owner (x,y,w,h만 필요) =====
class BubbleOwner:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0


# ===== 말풍선용 안전 버전 (화면 안으로 강제) =====
class SafeSpeechBubble(MakeSpeechBubble):
    def _compute_geometry(self):
        # 기본 위치 계산 (부모의 로직 그대로 사용)
        bubble_x, bubble_y, tail_tip_x, tail_tip_y = super()._compute_geometry()

        # 화면 크기 정보가 있다면, 여기서 클램프
        if self.screen_width is not None and self.screen_height is not None:
            if bubble_x < 0:
                bubble_x = 0
            if bubble_x + self.bubble_w > self.screen_width:
                bubble_x = self.screen_width - self.bubble_w
            if bubble_y < 0:
                bubble_y = 0
            if bubble_y + self.bubble_h > self.screen_height:
                bubble_y = self.screen_height - self.bubble_h

        return bubble_x, bubble_y, tail_tip_x, tail_tip_y


# ===== 이미지 / 리소스 관리 클래스 =====
class Assets:
    def __init__(self, width: int, height: int):
        # 육지 배경
        self.shore_bg = pygame.image.load("shore2.jpeg").convert()
        self.shore_bg = pygame.transform.scale(self.shore_bg, (width, height))

        # 게 이미지 (1/4 크기)
        crab_base_img = pygame.image.load("crab2.png").convert_alpha()
        cw, ch = crab_base_img.get_size()
        self.crab_base_img = pygame.transform.smoothscale(
            crab_base_img, (int(cw / 4), int(ch / 4))
        )

        # 여우 이미지 (1/2 크기)
        fox_img = pygame.image.load("fox2.png").convert_alpha()
        fw, fh = fox_img.get_size()
        self.fox_img = pygame.transform.smoothscale(
            fox_img, (int(fw / 2), int(fh / 2))
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
        self.fox_rect.midright = (WIDTH - 120, HEIGHT // 2 + 40)

        # 게 초기 위치 (왼쪽, top-left 기준)
        start_tl_x = 150
        start_tl_y = HEIGHT // 2 + 60

        cw, ch = self.assets.crab_base_img.get_size()
        self.crab_center = [
            start_tl_x + cw / 2,
            start_tl_y + ch / 2,
        ]
        self.crab_angle = 0.0
        self.crab_scale = 1.0
        self.crab_visible = True

        # 2단계: 이동/회전/크기변화
        self.move_duration = 2.0
        self.move_t = 0.0

        end_tl_x = self.fox_rect.x + 120
        end_tl_y = self.fox_rect.y + 170

        self.move_start_scale = 1.0
        self.move_end_scale = 0.7

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

    def get_crab_surf_and_rect(self):
        if not self.crab_visible:
            return None, None

        img = self.assets.crab_base_img

        if self.crab_scale != 1.0:
            w0, h0 = img.get_size()
            new_w = max(1, int(w0 * self.crab_scale))
            new_h = max(1, int(h0 * self.crab_scale))
            img = pygame.transform.smoothscale(img, (new_w, new_h))

        if self.crab_angle != 0:
            img = pygame.transform.rotate(img, self.crab_angle)

        rect = img.get_rect(center=(self.crab_center[0], self.crab_center[1]))
        return img, rect

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

        # 화면 안에 들어오도록 SafeSpeechBubble 사용
        self.bubble = SafeSpeechBubble(
            self.crab_owner,
            self.text_full,
            direction="left",
            padding=20,
            line_height=28,
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
            pass

    def update(self, dt):
        if self.phase == 1:
            if self.fade_alpha > 0:
                self.fade_alpha -= self.fade_speed * dt
                if self.fade_alpha < 0:
                    self.fade_alpha = 0

        elif self.phase == 2:
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
            if not self.text_done:
                self.text_shown += self.text_speed * dt
                if self.text_shown >= len(self.text_full):
                    self.text_shown = len(self.text_full)
                    self.text_done = True

        elif self.phase == 4:
            self.shrink_t += dt / self.shrink_duration
            if self.shrink_t > 1.0:
                self.shrink_t = 1.0

            self.crab_scale = max(0.0, self.shrink_start_scale * (1.0 - self.shrink_t))

            if self.crab_scale <= 0.01:
                self.crab_visible = False
                self.start_phase5()

        elif self.phase == 5:
            if self.end_fade_alpha < self.end_fade_target:
                self.end_fade_alpha += self.end_fade_speed * dt
                if self.end_fade_alpha > self.end_fade_target:
                    self.end_fade_alpha = self.end_fade_target

    def draw(self, surface):
        surface.blit(self.assets.shore_bg, (0, 0))
        surface.blit(self.assets.fox_img, self.fox_rect)

        crab_surf, crab_rect = self.get_crab_surf_and_rect()
        if crab_surf is not None and crab_rect is not None:
            surface.blit(crab_surf, crab_rect)

        if self.phase == 3 and self.bubble is not None and crab_rect is not None:
            self.crab_owner.x = crab_rect.x
            self.crab_owner.y = crab_rect.y
            self.crab_owner.w = crab_rect.width
            self.crab_owner.h = crab_rect.height

            self.bubble.set_text(self.text_full)
            self.bubble.draw(surface, self.text_shown)

        if self.phase == 1 and self.fade_alpha > 0:
            mask = pygame.Surface((WIDTH, HEIGHT))
            mask.set_alpha(int(self.fade_alpha))
            mask.fill((0, 0, 0))
            surface.blit(mask, (0, 0))

        if self.phase == 5:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(int(self.end_fade_alpha))
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))

            text = font_main.render("Q:재시작   R:종료", True, (255, 255, 255))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(text, rect)

        if self.space_hint and self.phase in (1, 2, 3, 4):
            hint = font_small.render("스페이스바를 누르세요", True, (255, 255, 255))
            hint_rect = hint.get_rect(midtop=(WIDTH // 2, 10))
            surface.blit(hint, hint_rect)


# ===== 앱 / 메인 루프 클래스 =====
class EndingApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Crab & Fox Ending")
        self.clock = pygame.time.Clock()

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

                    if self.ending.phase == 5:
                        if event.key == pygame.K_q:
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

    if restart:
        # 여기서는 pygame을 끄지 않고 바로 opening으로 넘어간다
        opening.main()
    else:
        # 완전히 종료할 때만 pygame.quit() 호출
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
