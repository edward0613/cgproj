import pygame
import sys
import ctypes
import subprocess
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from screens import MenuScreen, SkillSelectScreen, GameScreen
from skills import load_all_player_skills

SW_RESTORE = 9

def bring_window_to_front():
    try:
        hwnd = pygame.display.get_wm_info()["window"]

        # 1) 다른 프로세스 포그라운드 허용
        ctypes.windll.user32.AllowSetForegroundWindow(-1)

        # 2) 창을 정상 상태로 복구
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)

        # 3) 창을 맨 앞으로
        ctypes.windll.user32.SetForegroundWindow(hwnd)

        # 4) 포커스 강제 (때때로 필요)
        ctypes.windll.user32.SetFocus(hwnd)

    except Exception as e:
        print("bring_window_to_front 실패:", e)

class Game:
    """메인 게임 클래스.
    게임의 전반적인 흐름, 상태 관리, 화면 전환을 담당"""

    def __init__(self):
        pygame.init()
        pygame.font.init()  # 폰트 모듈 초기화

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("갯벌에서 살아남기")
        self.clock = pygame.time.Clock()

        # 모든 플레이어 스킬 로드
        self.all_player_skills = load_all_player_skills()

        # 게임 상태 및 화면 관리
        self.game_state = 'MENU'
        self.screens = {
            'MENU': MenuScreen(),
            'SKILL_SELECT': SkillSelectScreen(self.all_player_skills),
            'IN_GAME': None  # 게임 시작 시 동적으로 생성
        }
        self.current_screen = self.screens['MENU']
        self.opening_proc = None

    def return_to_menu(self):#메뉴로 이동
        if self.game_state == 'MENU':
            self.quit_game()
            return
        """ESC 등을 눌렀을 때 메뉴 화면으로 되돌아가는 함수"""
        print("ESC → 메뉴 화면으로 이동")

        self.game_state = 'MENU'
        self.screens = {
            'MENU': MenuScreen(),
            'SKILL_SELECT': SkillSelectScreen(self.all_player_skills),
            'IN_GAME': None
        }
        self.current_screen = self.screens['MENU']

    def run(self):#게임 실행
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit_game()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # 전체 종료 대신 메뉴로 돌아가기
                    pygame.mixer.music.stop()
                    self.return_to_menu()

            # 이벤트 처리 결과
            result = self.current_screen.handle_events(events)
            self.handle_transition(result)

            dt = self.clock.tick(FPS) / 1000.0
            update_result = self.current_screen.update(dt)
            self.handle_transition(update_result)

            # 화면 그리기
            self.current_screen.draw(self.screen)
            pygame.display.flip()

    def handle_transition(self, result):#게임상태 전환

        if result is None:
            return

        if result == 'EXIT':
            self.quit_game()

        elif result == 'TUTORIAL':
            print("튜토리얼 시작")
            from screens import TutorialScreen  # screens.py 안에 넣었다면 필요
            self.game_state = 'TUTORIAL'
            self.current_screen = TutorialScreen()

        elif result == 'START_GAME':
            print("오프닝 실행...")

            try:
                pygame.event.clear()
                pygame.display.iconify()
                proc = subprocess.Popen([sys.executable, "opening.py"])
                proc.wait()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                bring_window_to_front()
            except FileNotFoundError:
                print("'opening.py'를 찾을 수 없습니다. 오프닝 건너뜀.")
            except Exception as e:
                print(f"오프닝 실행 중 오류: {e}")
            except FileNotFoundError:
                print("'opening.py'를 찾을 수 없습니다. 오프닝 건너뜀.")
            except Exception as e:
                print(f"오프닝 실행 중 오류: {e}")

            # 오프닝 끝나면 스킬 선택 화면으로 전환
            self.game_state = 'SKILL_SELECT'

            # screens['SKILL_SELECT']를 새로 생성
            self.screens['SKILL_SELECT'] = SkillSelectScreen(self.all_player_skills)
            self.current_screen = self.screens['SKILL_SELECT']

        elif isinstance(result, tuple) and result[0] == 'GAME_START':
            # 스킬 선택 완료. ('GAME_START', [선택한 스킬 객체 리스트])
            selected_skills = result[1]
            print(f"게임 시작! 선택한 스킬: {[skill.name for skill in selected_skills]}")

            # 새로운 GameScreen 인스턴스 생성
            self.screens['IN_GAME'] = GameScreen(selected_skills)
            self.game_state = 'IN_GAME'
            self.current_screen = self.screens['IN_GAME']

        elif result == 'GAME_OVER':
            print("게임 오버! 엔딩 실행...")

            try:
                pygame.event.clear()
                pygame.display.iconify()
                proc = subprocess.Popen([sys.executable, "ending.py"])
                proc.wait()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                bring_window_to_front()

                if proc.returncode == 1:
                    print("엔딩에서 Q 입력 → 게임 재시작")
                    self.game_state = 'MENU'
                    self.screens = {
                        'MENU': MenuScreen(),
                        'SKILL_SELECT': SkillSelectScreen(self.all_player_skills),
                        'IN_GAME': None
                    }

                    self.current_screen = self.screens['MENU']

                else:
                    print("엔딩에서 종료 선택 → 게임 완전 종료")
                    self.quit_game()

            except Exception as e:
                print(f"엔딩 실행 중 오류 발생: {e}")
                self.quit_game()

        elif result == 'BACK_TO_MENU':
            print("튜토리얼 종료 → 메뉴로 돌아감")
            self.return_to_menu()

    def quit_game(self):#종료
        """게임 종료"""
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()