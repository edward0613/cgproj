from utils import calculate_target_area, calculate_cross_area, calculate_plus_area
from config import PLAYER_MOVE_TIME, PLAYER_SWIFT_MOVE_TIME


class Skill:
    """
    모든 스킬의 기본(base) 클래스.
    """

    def __init__(self, name, cost, delay, description, target_type, target_size=None, owner='player'):
        self.name = name
        self.cost = cost
        self.delay = delay  # 스킬 발동까지 걸리는 시간 (초)
        self.description = description
        self.target_type = target_type  # 'area', 'self', 'all'
        self.target_size = target_size  # (x, y) 튜플, e.g., (3, 3)
        self.owner = owner  # 'player' or 'fox'

    def get_target_area(self, center_grid_pos, player=None):
        """
        스킬의 대상 영역을 계산하여 그리드 좌표 리스트로 반환합니다.
        player: '명상' 같이 플레이어 위치 기준 스킬에 필요.
        """
        if self.target_type == 'all':
            # 전체 영역 (추후 그리드 크기 참조 필요)
            return []  # 'all'은 하이라이트가 없으므로 빈 리스트

        elif self.target_type == 'self':
            if player:
                # '명상'의 3x3 범위
                if self.name == '명상' and player.hp == 2:
                    return calculate_target_area((player.grid_x, player.grid_y), 3, 3)
                else:  # 체력 1일땐 자기 자신만
                    return [(player.grid_x, player.grid_y)]
            return []

        elif self.target_type == 'area':
            if self.target_size:
                return calculate_target_area(center_grid_pos, self.target_size[0], self.target_size[1])
            elif self.name in ['십자가', 'Player_십자가']:
                return calculate_cross_area(center_grid_pos)
            elif self.name == '집중타격':
                return calculate_plus_area(center_grid_pos)

        return []

    def activate(self, game_manager, target_cells, player):
        """
        스킬 효과를 발동시킵니다.
        game_manager: 게임의 현재 상태 (그리드, 플레이어 등)에 접근
        target_cells: [Cell, Cell, ...] 효과를 적용할 셀 객체 리스트
        player: 플레이어 객체
        """
        # 이 메서드는 각 하위 스킬 클래스에서 오버라이드(재정의)됩니다.
        print(f"[{self.owner}] 스킬 '{self.name}' 발동!")
        pass


# --- 게 (Player) 스킬 목록 ---

class Player_Construction(Skill):
    def __init__(self):
        super().__init__(
            name="건축", cost=3, delay=0.5,
            description="3x3 영역의 칸 체력을 1 더합니다.",
            target_type='area', target_size=(3, 3)
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 건축 발동! 대상 {len(target_cells)}칸")
        for cell in target_cells:
            cell.update_hp(1)


class Player_Swiftness(Skill):
    def __init__(self):
        super().__init__(
            name="신속", cost=2, delay=0.0,
            description="2초간 이동 간격을 0.2초로 만듭니다.",
            target_type='all'  # 전체 대상 (하이라이트 없음)
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 신속 발동!")
        player.set_move_speed(PLAYER_SWIFT_MOVE_TIME)
        # TODO: 2초 후에 원래 속도(PLAYER_MOVE_TIME)로 되돌리는 로직 필요
        # (GameManager에서 '활성 효과' 리스트로 관리)
        game_manager.add_timed_effect('swiftness', 2.0,
                                      on_expire=lambda: player.set_move_speed(PLAYER_MOVE_TIME))


class Player_Reconstruction(Skill):
    def __init__(self):
        super().__init__(
            name="재건축", cost=6, delay=0.5,
            description="4x4 영역 내 죽은 칸을 체력 1, 최대체력 1로 부활시킵니다.",
            target_type='area', target_size=(4, 4)
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 재건축 발동!")
        for cell in target_cells:
            if cell.is_dead:
                cell.revive_cell()


class Player_ConstructionWork(Skill):
    def __init__(self):
        super().__init__(
            name="공사", cost=4, delay=0.0,
            description="5x4 영역 내 칸들의 최대체력을 1 증가시킵니다.",
            target_type='area', target_size=(5, 4)
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 공사 발동!")
        for cell in target_cells:
            cell.set_max_hp(1)


class Player_Meditation(Skill):
    def __init__(self):
        super().__init__(
            name="명상", cost=2, delay=0.0,
            description="체력 1: 2초간 이동 불가, 체력 1 회복. 체력 2: 3x3 칸 체력 +1",
            target_type='self'
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 명상 발동!")
        if player.hp == 1:
            player.set_can_move(False)
            # TODO: 2초 후 이동 가능 + 체력 회복 로직 필요
            game_manager.add_timed_effect('meditation_heal', 2.0,
                                          on_expire=lambda: (player.set_can_move(True), player.heal(1)))
        elif player.hp == 2:
            # target_cells는 get_target_area에서 계산된 3x3 영역
            for cell in target_cells:
                cell.update_hp(1)


class Player_Cross(Skill):
    def __init__(self):
        super().__init__(
            name="십자가", cost=2, delay=0.0,
            description="마우스 위치 중심 십자가 영역 칸 체력 +1",
            target_type='area'  # get_target_area에서 '십자가' 이름으로 분기
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 십자가 발동!")
        for cell in target_cells:
            cell.update_hp(1)


# --- 여우 (Fox) 스킬 목록 ---

class Fox_Thorn(Skill):
    def __init__(self):
        super().__init__(
            name="가시", cost=4, delay=1.0,
            description="2x2 영역, 체력 0인 칸을 죽은 칸으로 만듦",
            target_type='area', target_size=(2, 2), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            if cell.hp == 0:
                cell.kill_cell()


class Fox_Arrow(Skill):
    def __init__(self):
        super().__init__(
            name="화살", cost=5, delay=1.0,  # (딜레이는 임의로 1초 지정)
            description="3x5 영역, 칸 체력 1 감소",
            target_type='area', target_size=(3, 5), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)
        # 플레이어가 맞았는지 체크
        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)


class Fox_Tracker(Skill):
    def __init__(self):
        super().__init__(
            name="추적자", cost=2, delay=0.0,
            description="2초간 게의 위치 공개",
            target_type='all', owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        # TODO: 2초간 게 위치 공개 (UI 효과)
        game_manager.add_timed_effect('tracker_reveal', 2.0)


class Fox_Peek(Skill):
    def __init__(self):
        super().__init__(
            name="들춰보기", cost=3, delay=0.7,
            description="2x3 영역, 1초간 체력 -1 했다가 +1",
            target_type='area', target_size=(2, 3), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)

        # TODO: 1초 후 체력 +1 복구
        def restore_hp():
            for cell in target_cells:
                cell.update_hp(1)

        game_manager.add_timed_effect('peek_restore', 1.0, on_expire=restore_hp)


class Fox_FocusHit(Skill):
    def __init__(self):
        super().__init__(
            name="집중타격", cost=5, delay=0.7,
            description="열 십(十) 모양, 칸 체력 2 감소",
            target_type='area', owner='fox'  # get_target_area에서 이름으로 분기
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-2)
        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)  # (데미지 1로 임의 지정)


class Fox_DirectLight(Skill):
    def __init__(self):
        super().__init__(
            name="직사광선", cost=4, delay=0.3,
            description="세로 1x8, 칸 체력 1 감소. 체력 0인 칸은 죽은 칸 처리.",
            target_type='area', target_size=(1, 8), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)
            if cell.hp == 0:
                cell.kill_cell()
        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)


class Fox_Cross(Skill):
    def __init__(self):
        super().__init__(
            name="십자가", cost=2, delay=0.5,
            description="십자가 모양, 칸 체력 1 감소",
            target_type='area', owner='fox'  # get_target_area에서 이름으로 분기
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)
        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)


# --- 스킬 로드 함수 ---

def load_all_player_skills():
    """플레이어가 선택할 수 있는 모든 스킬 리스트를 반환합니다."""
    return [
        Player_Construction(),
        Player_Swiftness(),
        Player_Reconstruction(),
        Player_ConstructionWork(),
        Player_Meditation(),
        Player_Cross(),
        # (새로운 스킬 추가)
    ]


def load_all_fox_skills():
    """여우가 사용할 수 있는 모든 스킬 리스트를 반환합니다."""
    return [
        Fox_Thorn(),
        Fox_Arrow(),
        Fox_Tracker(),
        Fox_Peek(),
        Fox_FocusHit(),
        Fox_DirectLight(),
        Fox_Cross(),
    ]