import pygame
import random
from config import SOUND_PATH
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, GRAY,
    GRID_WIDTH, GRID_HEIGHT, GRID_START_X, GRID_START_Y,
    CELL_WIDTH, CELL_HEIGHT, IMAGE_PATH,
    NOTIFICATION_BAR_HEIGHT, BOTTOM_UI_HEIGHT,
    MAX_MONEY, MONEY_GAIN_INTERVAL,
    HIGHLIGHT_COLOR, FOX_ATTACK_WARN_COLOR, FOX_ATTACK_EXEC_COLOR, GRID_TOTAL_WIDTH, GRID_TOTAL_HEIGHT, FONT_PATH
)
from utils import load_image, get_mouse_grid_pos, get_screen_pos,get_font
from ui import Button, SkillToggleButton, NotificationBar, SkillHandUI, MoneyGauge
from components import Player, Cell
from skills import load_all_fox_skills


class BaseScreen:
    """모든 화면 클래스의 기본이 되는 클래스."""

    def __init__(self):
        pass

    def handle_events(self, events):
        raise NotImplementedError

    def update(self, dt):
        pass

    def draw(self, surface):
        raise NotImplementedError


class MenuScreen(BaseScreen):
    """메뉴 화면."""

    def __init__(self):
        super().__init__()
        self.background = load_image(IMAGE_PATH['MENU_BG'])
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # 버튼 생성
        button_width, button_height = 350, 160
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        button_img_path = IMAGE_PATH['MENU_BUTTON']

        self.start_button = Button(
            center_x,
            SCREEN_HEIGHT // 2 + 130,
            button_width,
            button_height,
            text="게임 시작",
            image_path=button_img_path,
            font_size=36,
            alpha=True,  # 투명 PNG면 True로 두면 좋음(네 load_image 구현에 맞춰서)
            text_color = BLACK,
            text_offset_y = 7,
            press_scale=0.93,
            hover_scale=0.97
        )

        self.tutorial_button = Button(
            center_x,
            SCREEN_HEIGHT // 2 + 280,
            button_width // 2 - 10,
            button_height // 2 + 10,
            text="튜토리얼",
            image_path=button_img_path,
            font_size=22,
            alpha=True,
            text_color=BLACK,
            text_offset_y=5,
            press_scale=0.93,
            hover_scale=0.97
        )

        self.exit_button = Button(
            SCREEN_WIDTH // 2 + 10,
            SCREEN_HEIGHT // 2 + 280,
            button_width // 2 - 10,
            button_height // 2 + 10,
            text="게임 종료",
            image_path=button_img_path,
            font_size=22,
            alpha=True,
            text_color=BLACK,
            text_offset_y=5,
            press_scale=0.93,
            hover_scale=0.97
        )

        self.buttons = [self.start_button, self.tutorial_button, self.exit_button]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                if self.start_button.handle_event(event) == 'clicked':
                    return 'START_GAME'
                if self.tutorial_button.handle_event(event) == 'clicked':
                    return 'TUTORIAL'
                if self.exit_button.handle_event(event) == 'clicked':
                    return 'EXIT'
            else:
                # 호버 효과를 위해 다른 이벤트도 전달
                for button in self.buttons:
                    button.handle_event(event)
        return None

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        for button in self.buttons:
            button.draw(surface)


class SkillSelectScreen(BaseScreen):
    """스킬 선택 화면."""

    def __init__(self, all_player_skills):
        super().__init__()
        try:
            self.background = load_image(IMAGE_PATH['SHORE_BG'])
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except KeyError:
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(GRAY)
            print("스킬 선택 배경 'shore.png'를 찾을 수 없습니다.")

        self.skills = all_player_skills
        self.skill_buttons = []

        # 알림창
        self.notification_bar = NotificationBar(
            SCREEN_WIDTH * 0.1, 20, SCREEN_WIDTH * 0.8, 60, font_size=24
        )
        self.notification_text = "5개의 스킬을 선택하세요."

        # 스킬 버튼 배치
        # 스킬 버튼 배치
        button_width, button_height = 180, 100
        padding = 20
        max_cols = 6  # 한 줄에 최대 6개
        start_y = 120

        # 6열 그리드 전체 너비를 한 번만 계산해서 화면 가운데 정렬
        grid_width = max_cols * button_width + (max_cols - 1) * padding
        base_x = (SCREEN_WIDTH - grid_width) // 2

        for i, skill in enumerate(self.skills):
            row = i // max_cols  # 몇 번째 줄인지 (0, 1, 2, ...)
            col = i % max_cols  # 그 줄에서 몇 번째 열인지 (0~5)

            x = base_x + col * (button_width + padding)
            y = start_y + row * (button_height + padding)

            self.skill_buttons.append(
                SkillToggleButton(x, y, button_width, button_height, skill)
            )

        # 선택 완료 버튼
        self.confirm_button = Button(
            SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 60, "선택 완료"
        )

    def handle_events(self, events):
        # 1) 매 프레임 hover 업데이트
        mouse_pos = pygame.mouse.get_pos()

        self.confirm_button.is_hovered = self.confirm_button.rect.collidepoint(mouse_pos)
        for b in self.skill_buttons:
            b.is_hovered = b.rect.collidepoint(mouse_pos)

        # 2) 클릭 처리 (토글/선택)
        for event in events:
            # 확인 버튼 클릭
            confirm = self.confirm_button.handle_event(event)
            if confirm == 'clicked':
                selected = [b.skill for b in self.skill_buttons if b.is_active]
                if len(selected) == 5:
                    return ('GAME_START', selected)
                else:
                    self.notification_text = f"정확히 5개의 스킬을 선택해야 합니다. (현재 {len(selected)}개)"

            # 스킬 버튼 클릭 처리 (토글)
            for b in self.skill_buttons:
                b.handle_event(event)

        # 3) 알림창 텍스트 결정 (이벤트 필요 없음)
        #    ★ 여기서 hover 된 스킬 찾기
        hovered_skill = None
        for b in self.skill_buttons:
            if b.is_hovered:
                hovered_skill = b.skill
                break

        if hovered_skill:
            # 마우스가 스킬 위에 있기만 하면 설명 표시
            self.notification_text = hovered_skill.description

        elif self.confirm_button.is_hovered:
            self.notification_text = "선택을 완료합니다."

        else:
            # hover 없을 때 기본 메시지
            count = sum(1 for b in self.skill_buttons if b.is_active)
            if count != 5:
                self.notification_text = f"{count} / 5 개 선택됨. 5개를 선택하세요."
            else:
                self.notification_text = "5개 선택 완료! '선택 완료' 버튼을 누르세요."

        return None

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        self.notification_bar.draw(surface, self.notification_text, show_fox_icon=False)

        for button in self.skill_buttons:
            button.draw(surface)

        self.confirm_button.draw(surface)


class GameScreen(BaseScreen):
    """
    메인 게임 화면.
    GameManager를 포함하여 실제 게임 로직과 UI를 연결합니다.
    """

    def __init__(self, selected_skills):
        super().__init__()
        self.game_manager = GameManager(selected_skills)
        try:
            pygame.mixer.music.load(SOUND_PATH["GAME_BGM"])
            pygame.mixer.music.play(-1)  # -1 = 무한 반복
            pygame.mixer.music.set_volume(0.6)  # 필요하면 볼륨 조절 (0.0~1.0)
        except Exception as e:
            print("BGM 로드 실패:", e)

        self.background = load_image(IMAGE_PATH['GAME_BG'])
        self.background = pygame.transform.scale(
            self.background,
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        # UI 요소 초기화
        self.notification_bar = NotificationBar(
            (SCREEN_WIDTH - SCREEN_WIDTH * 0.9) // 2,
            (NOTIFICATION_BAR_HEIGHT - 80) // 2,
            SCREEN_WIDTH * 0.9, 80, font_size=28
        )

        # 하단 UI 영역
        bottom_ui_x = (SCREEN_WIDTH - GRID_TOTAL_WIDTH) // 2
        bottom_ui_y = GRID_START_Y + GRID_TOTAL_HEIGHT
        bottom_ui_width = GRID_TOTAL_WIDTH

        # 돈 게이지 (하단 UI 상단)
        self.money_gauge = MoneyGauge(
            bottom_ui_x, bottom_ui_y + 10,
                         bottom_ui_width // 3, 30,
            MAX_MONEY
        )

        # 스킬 핸드 (돈 게이지 아래)
        self.skill_hand_ui = SkillHandUI(
            bottom_ui_x, bottom_ui_y + 50,
            bottom_ui_width, BOTTOM_UI_HEIGHT - 60
        )

        # 반투명 하이라이트를 위한 Surface
        self.highlight_surface = pygame.Surface((CELL_WIDTH, CELL_HEIGHT), pygame.SRCALPHA)

        self.is_fading_out = False
        self.fade_alpha = 0  # 0(완전 투명) ~ 255(완전 검정)
        self.fade_speed = 300

        self.fade_hold_duration = 1.5  # 1.5초 정도 유지 (원하면 2.0, 3.0으로 늘려도 됨)
        self.fade_hold_timer = 0.0

    def handle_events(self, events):
        for event in events:
            self.game_manager.handle_event(event)
        return None

    def update(self, dt):
        # 이미 페이드 중이면, 검게 만들기만 진행
        if self.is_fading_out:
            # 아직 완전히 까매지지 않았으면 alpha 올리기
            if self.fade_alpha < 255:
                self.fade_alpha += self.fade_speed * dt
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
            else:
                # 이미 완전 검정이면, 유지 시간 카운트
                self.fade_hold_timer += dt
                if self.fade_hold_timer >= self.fade_hold_duration:
                    # 충분히 기다렸으면 이제 진짜 GAME_OVER
                    return 'GAME_OVER'

            return None

        # 평소처럼 게임 로직 업데이트
        result = self.game_manager.update(dt)

        # GameManager가 GAME_OVER 신호를 주면,
        # 바로 넘기지 말고 여기서 페이드아웃 시작
        if result == 'GAME_OVER':
            print("플레이어 사망 감지 → 페이드아웃 시작")
            pygame.mixer.music.stop()
            self.is_fading_out = True
            self.fade_alpha = 0
            # 아직 GAME_OVER 리턴하지 않음
            return None

        return None

    def draw(self, surface):
        surface.blit(self.background, (0, 0))  # 배경

        # 1. 그리드 (모든 셀) 그리기
        self.game_manager.draw_grid(surface)

        # 2. 플레이어 스킬 하이라이트 그리기
        self.draw_player_highlight(surface)

        # 3. 여우 스킬 하이라이트 (공격 예고) 그리기
        self.draw_fox_highlights(surface)

        # 4. 플레이어 그리기
        self.game_manager.player.draw(surface)

        # 5. UI 그리기
        self.notification_bar.draw(
            surface,
            self.game_manager.notification_text,
            show_fox_icon=True
        )
        self.money_gauge.draw(surface, self.game_manager.money)
        self.skill_hand_ui.draw(surface, self.game_manager.skill_hand)

        if self.is_fading_out:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(int(self.fade_alpha))
            surface.blit(fade_surface, (0, 0))

    def draw_player_highlight(self, surface):
        """플레이어가 선택 중인 스킬 범위를 그립니다."""
        if self.game_manager.active_skill_highlight:
            skill, cells_pos = self.game_manager.active_skill_highlight
            self.highlight_surface.fill(HIGHLIGHT_COLOR)

            for grid_x, grid_y in cells_pos:
                screen_x, screen_y = get_screen_pos(grid_x, grid_y)
                surface.blit(self.highlight_surface, (screen_x, screen_y))

    def draw_fox_highlights(self, surface):
        """활성화된 여우의 공격 범위를 그립니다."""
        for attack in self.game_manager.active_fox_attacks:
            skill = attack['skill']
            cells_pos = attack['cells_pos']
            timer = attack['timer']

            # 딜레이가 0이거나 'all' 타입(추적자)이면 그리지 않음
            if skill.delay == 0 or skill.target_type == 'all':
                continue

            # 깜빡임 효과 (0.2초마다 색 변경)
            is_warn_phase = (timer // 0.2) % 2 == 1

            if timer > 0.1:  # 딜레이 시간 중 (0.1초는 실행 표시용)
                if is_warn_phase:
                    color = FOX_ATTACK_WARN_COLOR
                else:
                    color = (0, 0, 0, 0)  # 투명 (깜빡임)
            else:  # 딜레이 거의 끝 (실행 임박)
                color = FOX_ATTACK_EXEC_COLOR  # 초록색

            self.highlight_surface.fill(color)

            for grid_x, grid_y in cells_pos:
                screen_x, screen_y = get_screen_pos(grid_x, grid_y)
                surface.blit(self.highlight_surface, (screen_x, screen_y))

            # (옵션) 스킬 이름 표시 - 첫 번째 칸 위에
            if cells_pos:
                font = get_font(FONT_PATH, 18)
                text_surf = font.render(skill.name, True, WHITE)
                pos = get_screen_pos(cells_pos[0][0], cells_pos[0][1])
                text_rect = text_surf.get_rect(centerx=pos[0] + CELL_WIDTH // 2, bottom=pos[1] - 5)
                surface.blit(text_surf, text_rect)


class GameManager:
    """
    메인 게임의 모든 로직을 관리하는 클래스 (Controller 역할).
    GameScreen에 의해 소유됩니다.
    """

    def __init__(self, selected_skills):
        self.grid = [[Cell(x, y) for y in range(GRID_HEIGHT)] for x in range(GRID_WIDTH)]
        self.player = Player(GRID_WIDTH // 2, GRID_HEIGHT // 2)

        self.money = 0
        self.money_timer = 0.0

        self.skill_deck = selected_skills
        self.skill_hand = []
        self.fill_hand()  # 핸드 채우기

        self.notification_text = "게임 시작! 여우의 공격을 피하세요."

        # 플레이어 스킬 사용 관련
        self.active_skill_highlight = None  # (skill, [(x,y), ...])
        self.last_skill_press = {'key': None, 'pos': None}  # (키, 그리드좌표)

        # 여우 스킬 관련
        self.fox_skills = load_all_fox_skills()
        self.active_fox_attacks = []  # [{'skill': Skill, 'cells_pos': [...], 'timer': float}, ...]
        self.fox_ai_timer = 0.0  # 여우가 다음 스킬을 쓰는 쿨타임

        # 시간제 버프/디버프
        self.timed_effects = []  # [{'name': str, 'timer': float, 'on_expire': function}, ...]

    def fill_hand(self):
        """덱에서 스킬을 뽑아 핸드를 4장으로 채웁니다."""
        while len(self.skill_hand) < 4 and self.skill_deck:
            self.skill_hand.append(self.skill_deck.pop(0))

    def handle_event(self, event):
        """입력 이벤트를 처리합니다."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 좌클릭
                grid_pos = get_mouse_grid_pos(event.pos)
                if grid_pos:
                    self.player.set_target(grid_pos[0], grid_pos[1])

        elif event.type == pygame.KEYDOWN:
            key_map = {
                pygame.K_q: 0,
                pygame.K_w: 1,
                pygame.K_e: 2,
                pygame.K_r: 3
            }
            if event.key in key_map:
                hand_index = key_map[event.key]
                grid_pos = get_mouse_grid_pos(pygame.mouse.get_pos())
                if grid_pos:
                    self.handle_skill_press(hand_index, grid_pos, event.key)

    def handle_skill_press(self, hand_index, grid_pos, key):
        """
        QWER 스킬 키 입력을 처리합니다. (1회: 하이라이트, 2회: 사용)
        """
        if hand_index >= len(self.skill_hand):
            return  # 핸드에 스킬이 없음

        skill = self.skill_hand[hand_index]

        # '명상' 스킬은 플레이어 위치 기준
        if skill.name == '명상':
            target_area_pos = skill.get_target_area(None, player=self.player)
        else:
            target_area_pos = skill.get_target_area(grid_pos, player=self.player)

        # 1. 두 번째 클릭 (같은 키, 같은 위치)
        if (self.last_skill_press['key'] == key and
                self.last_skill_press['pos'] == grid_pos and
                self.active_skill_highlight is not None):

            if self.money >= skill.cost:
                self.money -= skill.cost
                self.activate_skill(skill, target_area_pos)
                self.rotate_deck(hand_index)

                self.active_skill_highlight = None
                self.last_skill_press = {'key': None, 'pos': None}
            else:
                self.notification_text = f"돈이 부족합니다! (필요: {skill.cost})"

        # 2. 첫 번째 클릭 (또는 다른 위치/키 클릭)
        else:
            self.active_skill_highlight = (skill, target_area_pos)
            self.last_skill_press = {'key': key, 'pos': grid_pos}

    def activate_skill(self, skill, target_area_pos):
        """플레이어 스킬을 발동시킵니다."""
        target_cells = [self.grid[x][y] for x, y in target_area_pos if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT]

        skill.activate(self, target_cells, self.player)
        self.notification_text = f"[{skill.name}] 스킬 사용!"

    def rotate_deck(self, hand_index):
        """사용한 스킬을 덱 맨 뒤로 보내고 새 스킬을 뽑습니다."""
        used_skill = self.skill_hand.pop(hand_index)
        self.skill_deck.append(used_skill)

        if self.skill_deck:
            new_skill = self.skill_deck.pop(0)
            self.skill_hand.insert(hand_index, new_skill)

    def update(self, dt):
        """게임 로직을 매 프레임 업데이트합니다."""
        # 1. 플레이어 업데이트
        self.player.update(dt, self.grid)
        if self.player.hp <= 0:
            return 'GAME_OVER'


        # 2. 돈 획득
        self.money_timer += dt
        if self.money_timer >= MONEY_GAIN_INTERVAL:
            self.money_timer -= MONEY_GAIN_INTERVAL
            if self.money < MAX_MONEY:
                self.money += 1

        # 3. 시간제 효과 업데이트 (신속, 명상 등)
        for effect in self.timed_effects[:]:  # 복사본 순회
            effect['timer'] -= dt
            if effect['timer'] <= 0:
                if effect['on_expire']:
                    effect['on_expire']()  # 만료 함수 실행
                self.timed_effects.remove(effect)
                # 만료 함수에서 플레이어가 죽었을 가능성 고려
                if self.player.hp <= 0:
                    return 'GAME_OVER'

        # 4. 여우 AI 업데이트
        self.update_fox_ai(dt)

        # 5. 여우 공격 딜레이 업데이트
        for attack in self.active_fox_attacks[:]:
            attack['timer'] -= dt
            if attack['timer'] <= 0:
                # 딜레이 종료, 스킬 발동!
                skill = attack['skill']
                target_cells = [self.grid[x][y] for x, y in attack['cells_pos']]
                skill.activate(self, target_cells, self.player)
                self.notification_text = f"[여우] {skill.name} 발동!"
                self.active_fox_attacks.remove(attack)

                # 스킬 발동으로 플레이어가 죽었는지 즉시 검사
                if self.player.hp <= 0:
                    return 'GAME_OVER'

        # (안전장치) 프레임 마지막에 한 번 더 검사
        if self.player.hp <= 0:
            return 'GAME_OVER'

        return None

    def update_fox_ai(self, dt):
        self.fox_ai_timer -= dt
        if self.fox_ai_timer <= 0:
            # 5~10초 사이 랜덤 쿨타임
            self.fox_ai_timer = random.uniform(1.0, 3.0)

            # 랜덤 스킬 선택
            skill_to_use = random.choice(self.fox_skills)

            # 랜덤 타겟 위치 (플레이어 근처 또는 랜덤)
            target_pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))

            target_area_pos = skill_to_use.get_target_area(target_pos, player=self.player)

            # 활성 공격 목록에 추가
            self.active_fox_attacks.append({
                'skill': skill_to_use,
                'cells_pos': target_area_pos,
                'timer': skill_to_use.delay
            })

            if skill_to_use.delay > 0:
                self.notification_text = f"[여우] {skill_to_use.name} 시전...!"

            print(f"여우 AI: {skill_to_use.name} 사용 (대상: {target_pos})")

    def add_timed_effect(self, name, duration, on_expire=None):
        """시간제 효과(버프/디버프)를 추가합니다."""
        self.timed_effects.append({
            'name': name,
            'timer': duration,
            'on_expire': on_expire
        })

    def draw_grid(self, surface):
        """모든 셀을 그립니다."""
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                self.grid[x][y].draw(surface)