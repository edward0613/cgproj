# SpeechBubble.py
import pygame
import os
from config import FONT_PATH

# ===== 폰트 로더 (넥슨 배민 한나체 Pro 공용) =====
def load_hanna_fonts():
    """
    프로젝트 기준:
    ./fonts/BMHANNAPro.ttf  경로에 폰트 파일이 있다고 가정.
    pygame.init() 이후에 호출해야 함.
    """
    base_dir = os.path.dirname(__file__)

    # 필요하면 사이즈는 여기서만 바꿔주면 opening/ending 둘 다 적용됨
    font_main = pygame.font.Font(FONT_PATH, 32)
    font_small = pygame.font.Font(FONT_PATH, 22)
    return font_main, font_small


class MakeSpeechBubble:
    def __init__(
        self,
        owner,
        text: str,
        direction: str = "right",
        padding: int = 12,
        line_height: int = 35,
        font: pygame.font.Font | None = None,
        screen_width: int | None = None,
        screen_height: int | None = None,
    ):
        """
        owner        : x, y, w, h 속성을 가진 객체 (캐릭터나 버블 오너)
        text         : 말풍선 전체 텍스트 (예: "문장1\n문장2")
        direction    : "right" → 캐릭터 오른쪽 위, "left" → 왼쪽 위
        padding      : 말풍선 안쪽 여백
        line_height  : 줄 간격
        font         : pygame.font.Font 객체 (없으면 기본 한나체 28pt 사용)
        screen_width : (선택) 화면 너비, EndingSpeechBubble 등에서 사용 가능
        screen_height: (선택) 화면 높이
        """
        self.owner = owner
        self.direction = direction
        self.padding = padding
        self.line_height = line_height
        # 폰트 없으면 기본값 (말풍선에 쓸 폰트)
        self.font = font or pygame.font.SysFont("malgungothic", 28)
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.set_text(text)

    def set_text(self, text: str):
        """텍스트를 바꾸면 말풍선 크기를 다시 계산"""
        self.text = text
        self.full_lines = self.text.split("\n")
        if not self.full_lines:
            self.full_lines = [""]

        # 전체 텍스트 기준으로 말풍선 크기 고정
        self.bubble_w = max(self.font.size(line)[0] for line in self.full_lines) + self.padding * 2
        self.bubble_h = self.line_height * len(self.full_lines) + self.padding * 2

    def _compute_geometry(self):
        """
        캐릭터 위치와 방향에 따라 말풍선 위치 + 꼬리 위치 계산.
        (기본: clamp 없음, 그냥 owner 기준으로만 계산)
        """
        char_x, char_y = self.owner.x, self.owner.y
        char_w, char_h = self.owner.w, self.owner.h

        if self.direction == "right":
            bubble_x = char_x + char_w
            bubble_y = char_y - self.bubble_h - 30
            tail_tip_x = char_x + char_w
            tail_tip_y = char_y
        else:  # "left"
            bubble_x = char_x - self.bubble_w - 10
            bubble_y = char_y - self.bubble_h - 30
            tail_tip_x = char_x
            tail_tip_y = char_y

        return bubble_x, bubble_y, tail_tip_x, tail_tip_y

    def draw(self, surface: pygame.Surface, shown_chars: float):
        """
        shown_chars: 현재까지 보여줄 글자 수 (타자 치듯이 한 글자씩 늘어나게 할 때 사용)
        """
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

        render_lines = []
        for i, line in enumerate(self.full_lines):
            if i < len(shown_parts):
                render_lines.append(shown_parts[i])
            else:
                render_lines.append("")

        ty = bubble_y + self.padding
        for line in render_lines:
            surf = self.font.render(line, True, (0, 0, 0))
            surface.blit(surf, (bubble_x + self.padding, ty))
            ty += self.line_height


# ===== Opening / Ending에서 상속해서 쓰는 전용 말풍선 클래스 =====

class OpeningSpeechBubble(MakeSpeechBubble):
    """
    오프닝에서 사용하는 말풍선.
    지금은 MakeSpeechBubble과 동작 동일하지만,
    나중에 오프닝 전용 스타일(색, 테두리 등)을 바꾸고 싶으면 여기서 오버라이드하면 됨.
    """
    pass


class EndingSpeechBubble(MakeSpeechBubble):
    """
    엔딩에서 사용하는 말풍선.
    기본 MakeSpeechBubble에 '화면 안으로 강제(clamp)' 기능을 추가.
    """

    def _compute_geometry(self):
        bubble_x, bubble_y, tail_tip_x, tail_tip_y = super()._compute_geometry()

        if self.screen_width is not None and self.screen_height is not None:
            # 화면 안으로 클램프
            if bubble_x < 0:
                bubble_x = 0
            if bubble_x + self.bubble_w > self.screen_width:
                bubble_x = self.screen_width - self.bubble_w
            if bubble_y < 0:
                bubble_y = 0
            if bubble_y + self.bubble_h > self.screen_height:
                bubble_y = self.screen_height - self.bubble_h

        return bubble_x, bubble_y, tail_tip_x, tail_tip_y


# ===== 엔딩에서 사용할 owner용 간단 클래스 =====
class BubbleOwner:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
