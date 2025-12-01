import pygame
import sys
import subprocess
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from screens import MenuScreen, SkillSelectScreen, GameScreen
from skills import load_all_player_skills


class Game:
    """
    메인 게임 클래스.
    게임의 전반적인 흐름, 상태 관리, 화면 전환을 담당합니다.
    """

    def __init__(self):
        pygame.init()
        pygame.font.init()  # 폰트 모듈 초기화

        # Pygame 2.0.0 이상에서는 pygame.FULLSCREEN | pygame.SCALED 사용 가능
        # 여기서는 우선 FULLSCREEN 플래그만 사용합니다.
        # try:
        #     self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        # except pygame.error:
        #     print("전체 화면 모드를 지원하지 않아, 창 모드로 실행합니다.")
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

    def run(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.quit_game()

            # 이벤트 처리 결과
            result = self.current_screen.handle_events(events)
            self.handle_transition(result)

            # 업데이트 결과도 transition으로 넘기기!!! ← 중요
            dt = self.clock.tick(FPS) / 1000.0
            update_result = self.current_screen.update(dt)
            self.handle_transition(update_result)

            # 화면 그리기
            self.current_screen.draw(self.screen)
            pygame.display.flip()

    def handle_transition(self, result):
        """
        화면으로부터 받은 결과(result)를 바탕으로 게임 상태를 전환합니다.
        """
        if result is None:
            return

        if result == 'EXIT':
            self.quit_game()

        elif result == 'TUTORIAL':
            print("튜토리얼 시작 (미구현)")
            # self.game_state = 'TUTORIAL'
            # self.current_screen = self.screens['TUTORIAL']




        elif result == 'START_GAME':

            print("오프닝 실행...")

            try:

                # 🔥 게임 창 이벤트 모두 삭제 (충돌 방지)

                pygame.event.clear()

                # 🔥 게임 창 최소화 → opening.py 주 화면

                pygame.display.iconify()

                # 🔥 opening 실행

                proc = subprocess.Popen([sys.executable, "opening.py"])

                proc.wait()

                # 🔥 opening 종료 후 게임 창 복구

                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


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

                # 🔥 game.py 창의 모든 이벤트 제거 → 클릭 충돌 차단

                pygame.event.clear()

                # 🔥 게임 창을 최소화시켜 사용자 클릭을 못하게 함

                pygame.display.iconify()

                # 🔥 ending.py 실행

                proc = subprocess.Popen([sys.executable, "ending.py"])

                proc.wait()

                # 🔥 ending.py 종료 후 게임 창 복원

                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

                # 🔥 결과에 따라 재시작/종료 처리

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

    def quit_game(self):
        """게임을 종료합니다."""
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()