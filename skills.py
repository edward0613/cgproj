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
            description="4x3 영역의 칸 체력을 1 더합니다.",
            target_type='area', target_size=(4, 3)
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

class Player_StrongConstruction(Skill):
    def __init__(self):
        super().__init__(
            name="강화건축", cost=5, delay=1.0,
            description="2x2 영역의 칸 체력을 2 더합니다.",
            target_type='area', target_size=(2, 2)
        )

    def activate(self, game_manager, target_cells, player):
        print(f"[Player] 강화건축 발동!")
        for cell in target_cells:
            cell.update_hp(2)

class Player_EmergencyEscape(Skill):
    """
    긴급대피: 마우스로 선택한 한 칸으로 즉시 순간이동.
    도착한 칸이 체력 0이거나 죽은 칸이면, 그 칸을 밟았을 때와 똑같이 처리.
    """
    def __init__(self):
        super().__init__(
            name="긴급대피",
            cost=3,
            delay=0.0,
            description="마우스로 선택한 칸 한 곳으로 즉시 순간이동합니다.",
            target_type='area',      # 🔹 한 칸을 타겟으로 잡기 위해 area 사용
            target_size=(1, 1)       # 🔹 1x1 범위 → 선택한 칸 하나만
        )

    def activate(self, game_manager, target_cells, player):
        print("[Player] 긴급대피 발동!")

        if not target_cells:
            # 이론상 여기로 올 일은 거의 없지만, 안전장치
            return

        # target_cells는 1x1 범위라서 첫 번째 칸이 우리가 선택한 칸
        target_cell = target_cells[0]
        tx, ty = target_cell.grid_x, target_cell.grid_y

        # 🔹 순간이동: 이동 중 애니메이션 없이 즉시 좌표만 갱신
        player.grid_x = tx
        player.grid_y = ty
        player.target_x = tx
        player.target_y = ty
        player.is_moving = False   # 강제로 이동 상태 해제

        # 🔹 도착한 칸이 체력 0 / 죽은 칸이면,
        #    "그 칸을 밟았을 때"와 똑같이 처리되도록 기존 함수 호출
        player.check_current_cell(game_manager.grid)

class Player_Breakwater(Skill):
    """
    방파제: 선택한 위치를 중심으로 가로 1x5 줄의 칸 체력을 1 회복.
    """
    def __init__(self):
        super().__init__(
            name="방파제", cost=3, delay=0.3,
            description="가로 1x5 칸의 체력을 1 회복합니다.",
            target_type='area', target_size=(5, 1)
        )

    def activate(self, game_manager, target_cells, player):
        print("[Player] 방파제 발동!")
        for cell in target_cells:
            cell.update_hp(1)

# --- 여우 (Fox) 스킬 목록 ---

# --- 여우 (Fox) 스킬 목록 ---

class Fox_Thorn(Skill):
    """
    가시 : 2x2 영역에 체력이 0인 칸은 바로 죽이고,
           나머지 칸은 체력 1 감소
    """
    def __init__(self):
        super().__init__(
            name="가시", cost=2, delay=1.0,
            description="2x2 영역에 체력이 0 이하인 칸은 죽이고, 나머지는 체력 1 감소시킵니다.",
            target_type='area', target_size=(2, 2), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            if cell.hp == 0:
                cell.kill_cell()
            else:
                cell.update_hp(-1)


class Fox_Arrow(Skill):
    """
    화살 : 범위 5x6, 칸 체력 1씩 감소,
           게가 맞으면 게의 체력 1 감소
    """
    def __init__(self):
        super().__init__(
            name="화살", cost=5, delay=1.0,
            description="5x6 영역의 칸 체력을 1 감소시킵니다. 게가 맞으면 체력 1 감소.",
            target_type='area', target_size=(5, 6), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)

        # 플레이어가 범위 안에 있으면 피해 1
        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)


class Fox_Tracker(Skill):
    """
    추적자 : 3초간 게의 위치 여우한테 노출 (UI/연출용 플래그)
    """
    def __init__(self):
        super().__init__(
            name="추적자", cost=2, delay=0.0,
            description="3초간 게의 위치가 노출됩니다.",
            target_type='all', owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        game_manager.add_timed_effect('tracker_reveal', 3.0)


class Fox_Peek(Skill):
    """
    들춰보기 : 5x5 영역에 1초간 체력을 -1 했다가 +1
               (잠깐 약해졌다가 원상복구)
    """
    def __init__(self):
        super().__init__(
            name="들춰보기", cost=3, delay=0.7,
            description="5x5 영역의 칸을 1초간 체력 -1 했다가 +1로 되돌립니다.",
            target_type='area', target_size=(5, 5), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        # 즉시 -1
        for cell in target_cells:
            cell.update_hp(-1)

        # 1초 후 +1로 되돌리기
        def restore_hp():
            for cell in target_cells:
                cell.update_hp(1)

        game_manager.add_timed_effect('peek_restore', 1.0, on_expire=restore_hp)


class Fox_FocusHit(Skill):
    """
    집중타격 : 열 십 모양에
              - 가운데 교차점: 체력 2 감소
              - 나머지 칸들: 체력 1 감소
              - 이미 체력이 0인 칸은 죽은 칸 처리
    (범위 모양은 calculate_plus_area(center) 사용)
    """
    def __init__(self):
        super().__init__(
            name="집중타격", cost=5, delay=0.7,
            description="열 십 모양. 중심은 체력 2 감소, 나머지는 1 감소. 체력 0은 죽은 칸 처리.",
            target_type='area', owner='fox'  # get_target_area에서 이름으로 plus 모양 계산
        )

    def activate(self, game_manager, target_cells, player):
        if not target_cells:
            return

        # 중심 칸 찾기:
        # 이 plus 모양에서 가장 이웃(상하좌우)을 많이 가진 칸이 교차점이라고 보고 선택
        pos_to_cell = {(c.grid_x, c.grid_y): c for c in target_cells}
        best_pos = None
        best_neighbor_count = -1

        for (x, y), cell in pos_to_cell.items():
            cnt = 0
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if (x + dx, y + dy) in pos_to_cell:
                    cnt += 1
            if cnt > best_neighbor_count:
                best_neighbor_count = cnt
                best_pos = (x, y)

        # 중심 칸과 나머지 칸들을 나눔
        center_cell = pos_to_cell.get(best_pos)
        other_cells = [c for (pos, c) in pos_to_cell.items() if pos != best_pos]

        # 중심 칸: 체력 2 감소
        if center_cell is not None:
            if center_cell.hp == 0:
                center_cell.kill_cell()
            else:center_cell.update_hp(-2)


        # 나머지 칸: 체력 1 감소, 0이면 죽은 칸 처리
        for cell in other_cells:
            if cell.hp == 0:
                cell.kill_cell()
            else:cell.update_hp(-1)

        # 플레이어가 범위 안에 있으면 피해 1
        if (player.grid_x, player.grid_y) in pos_to_cell:
            player.take_damage(1, game_manager.grid)


class Fox_DirectLight(Skill):
    """
    직사광선 : 1x10 칸 체력 1 감소, 체력이 0인 칸은 죽은 칸 처리
    """
    def __init__(self):
        super().__init__(
            name="직사광선", cost=4, delay=0.3,
            description="세로 1x10 영역의 칸 체력을 1 감소시키고, 0이 되면 죽입니다.",
            target_type='area', target_size=(1, 10), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            if cell.hp == 0:
                cell.kill_cell()
            else:cell.update_hp(-1)




class Fox_Cross(Skill):
    """
    십자가 : 가로 5, 세로 5인 십자가 모양 칸 체력을 1 감소
    (범위 모양은 calculate_cross_area(center) 사용)
    """
    def __init__(self):
        super().__init__(
            name="십자가", cost=2, delay=0.5,
            description="가로 5, 세로 5의 십자가 모양 칸 체력을 1 감소시킵니다.",
            target_type='area', owner='fox'  # get_target_area에서 이름으로 cross 모양 계산
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)

        if (player.grid_x, player.grid_y) in [(c.grid_x, c.grid_y) for c in target_cells]:
            player.take_damage(1, game_manager.grid)


class Fox_Sandstorm(Skill):
    def __init__(self):
        super().__init__(
            name="모래폭풍", cost=5, delay=1.0,
            description="4x4 영역의 칸 체력을 1 감소시키고, 0이 되면 죽입니다.",
            target_type='area', target_size=(4, 4), owner='fox'
        )

    def activate(self, game_manager, target_cells, player):
        for cell in target_cells:
            cell.update_hp(-1)
            if cell.hp == 0:
                cell.kill_cell()



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
        Player_StrongConstruction(),
        Player_EmergencyEscape(),
        Player_Breakwater()
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
        Fox_Sandstorm()  # 새로 추가된 스킬
    ]