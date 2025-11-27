import pygame
from config import WHITE, BLACK, GRAY,GREEN, FONT_PATH, IMAGE_PATH,BLUE
from utils import get_font, load_image


class Button:
    """
    클릭 가능한 기본 버튼 클래스. 텍스트 또는 이미지를 표시할 수 있습니다.
    """

    def __init__(self, x, y, width, height, text=None, image_path=None, font_size=30,alpha=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = None
        if image_path:
            self.image = load_image(image_path,alpha=alpha)
            self.image = pygame.transform.scale(self.image, (width, height))

        self.font = get_font(FONT_PATH, font_size)
        self.is_hovered = False

    def handle_event(self, event):
        """이벤트(주로 마우스)를 처리합니다. 클릭 시 'clicked'를 반환합니다."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return 'clicked'
        return None

    def draw(self, surface):
        """버튼을 화면에 그립니다."""
        color = GRAY if self.is_hovered else (100, 100, 100)

        if self.image:
            surface.blit(self.image, self.rect.topleft)
            # 호버 시 약간 밝게 처리 (옵션)
            if self.is_hovered:
                hover_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                hover_surface.fill((255, 255, 255, 50))  # 50/255 투명도의 흰색
                surface.blit(hover_surface, self.rect.topleft)
        else:
            pygame.draw.rect(surface, color, self.rect, border_radius=10)

        if self.text:
            text_surf = self.font.render(self.text, True, WHITE)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)


class SkillToggleButton(Button):
    """
    스킬 선택 화면용 토글 버튼 클래스. (활성화/비활성화 상태)
    """

    def __init__(self, x, y, width, height, skill, font_size=20,alpha=1):
        self.skill = skill
        # 이미지는 square.jpeg, 텍스트는 스킬 이름
        super().__init__(x, y, width, height, text=skill.name,
                         image_path=IMAGE_PATH.get('SQUARE_UI'), font_size=font_size,alpha=alpha)
        self.is_active = False

    def handle_event(self, event):
        """클릭 시 'toggled'를 반환하여 상태를 변경하도록 합니다."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.toggle()  # 스스로 상태 변경
                return 'toggled'
        return None

    def toggle(self):
        self.is_active = not self.is_active

    def draw(self, surface):
        """활성화 상태에 따라 다르게 그립니다."""
        # 기본 버튼 그리기 (이미지 + 텍스트)
        super().draw(surface)

        if self.is_active:
            # 활성화 시: 초록색 테두리
            pygame.draw.rect(surface, GREEN, self.rect, 5, border_radius=10)
        elif self.is_hovered:
            # 호버 시: 흰색 테두리
            pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)


class NotificationBar:
    """
    상단 알림창 UI.
    """

    def __init__(self, x, y, width, height, bg_color=WHITE, text_color=BLACK, font_size=30):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = get_font(FONT_PATH, font_size)
        self.fox_icon = None
        try:
            icon_image = load_image(IMAGE_PATH['FOX_ICON'])
            self.fox_icon = pygame.transform.scale(icon_image, (height - 10, height - 10))  # 아이콘 크기 조절
        except KeyError:
            print("알림창: fox1.png 이미지를 찾을 수 없습니다.")

    def draw(self, surface, text, show_fox_icon=False):
        """
        알림창을 그립니다.
        show_fox_icon: 본게임(True)인지 스킬선택(False)인지 구분
        """
        # 모서리가 둥근 흰색 사각형
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=15)

        text_x = self.rect.x + 20
        text_centery = self.rect.centery

        if show_fox_icon and self.fox_icon:
            # 여우 아이콘 그리기
            icon_rect = self.fox_icon.get_rect(centery=self.rect.centery, left=self.rect.x + 10)
            surface.blit(self.fox_icon, icon_rect)
            # 텍스트 위치를 아이콘 오른쪽으로
            text_x = icon_rect.right + 15

        text_surf = self.font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(centery=text_centery, left=text_x)
        surface.blit(text_surf, text_rect)


class SkillHandUI:
    """
    본게임 하단 스킬 핸드 UI.
    """

    def __init__(self, x, y, width, height, font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = get_font(FONT_PATH, font_size)
        self.skill_rects = []
        self.skill_image = load_image(IMAGE_PATH.get('SQUARE_UI'))

        # 4개의 스킬 슬롯 위치 계산
        slot_width = width // 5  # 4개 + 약간의 여백
        slot_height = height - 10
        self.skill_image = pygame.transform.scale(self.skill_image, (slot_width, slot_height))

        start_x = x + (width - slot_width * 4) // 5
        spacing = (width - slot_width * 4) // 5

        for i in range(4):
            slot_x = start_x + (slot_width + spacing) * i
            self.skill_rects.append(pygame.Rect(slot_x, y + 5, slot_width, slot_height))

    def draw(self, surface, hand_skills):
        """핸드에 있는 4개의 스킬을 그립니다."""
        key_labels = ['Q', 'W', 'E', 'R']

        for i, skill in enumerate(hand_skills):
            if i >= 4: break  # 핸드는 4장만 표시

            rect = self.skill_rects[i]

            # 스킬 이미지 배경
            surface.blit(self.skill_image, rect.topleft)

            # 1. 스킬 이름
            name_surf = self.font.render(skill.name, True, WHITE)
            name_rect = name_surf.get_rect(centerx=rect.centerx, top=rect.top + 10)
            surface.blit(name_surf, name_rect)

            # 2. 스킬 코스트
            cost_surf = self.font.render(f"Cost: {skill.cost}", True, WHITE)
            cost_rect = cost_surf.get_rect(centerx=rect.centerx, bottom=rect.bottom - 10)
            surface.blit(cost_surf, cost_rect)

            # 3. 키 라벨 (Q, W, E, R)
            key_font = get_font(FONT_PATH, 24)
            key_surf = key_font.render(key_labels[i], True, BLACK)
            key_rect = key_surf.get_rect(center=(rect.left - 15, rect.centery))
            pygame.draw.circle(surface, WHITE, key_rect.center, 12)
            surface.blit(key_surf, key_rect)


class MoneyGauge:
    """
    돈 게이지 UI.
    """

    def __init__(self, x, y, width, height, max_money, font_size=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_money = max_money
        self.font = get_font(FONT_PATH, font_size)

    def draw(self, surface, current_money):
        # 게이지 바 배경
        pygame.draw.rect(surface, GRAY, self.rect, border_radius=5)

        # 현재 돈
        fill_ratio = current_money / self.max_money
        fill_width = int(self.rect.width * fill_ratio)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, BLUE, fill_rect, border_radius=5)

        # 텍스트
        text_surf = self.font.render(f"Money: {current_money} / {self.max_money}", True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)