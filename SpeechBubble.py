# SpeechBubble.py
import pygame

class MakeSpeechBubble:
    def __init__(
        self,
        owner,
        text: str,
        direction: str = "right",
        padding: int = 20,
        line_height: int = 28,
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
        font         : pygame.font.Font 객체 (없으면 기본 폰트 사용)
        screen_width : (선택) 화면 너비, 필요 시 서브클래스에서 사용
        screen_height: (선택) 화면 높이, 필요 시 서브클래스에서 사용
        """
        self.owner = owner
        self.direction = direction
        self.padding = padding
        self.line_height = line_height
        self.font = font or pygame.font.Font("BMHANNAPro.ttf", 28)
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
        (기본: clamp 없이, 그냥 owner 기준으로만 계산)
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
