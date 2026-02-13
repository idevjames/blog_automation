import random
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from service.login_session_service import LoginSessionService
from service.settings_repository import SettingsRepository
from service.logger import Logger
from utils.smart_util import smart_sleep, smart_click, human_typing, human_scroll, find_element_smart

@dataclass
class AddNeighborDefines:
    delays: dict = field(default_factory=lambda: {
        '목록페이지로딩': (1.0, 2.5),
        '팝업창대기': (1.0, 2.0),
        '팝업초기대기': (0.2, 0.5),
        '팝업작업대기': (0.2, 0.5),
        '메시지창전환대기': (1.5, 2.0),
        '메시지입력후대기': (0.2, 0.5),
        '전송후대기': (1.0, 2.0),
        '블로그간대기': (0.2, 0.5),
        '재시도대기': (0.5, 1.0),
        '스크롤대기': (0.5, 1.0),
        '댓글창대기': (1.5, 2.0),
        '블로그진입': (2.0, 3.0),
    })
    
    conditions: dict = field(default_factory=lambda: {
        '최대실패횟수': 10,
        '스크롤최대비율': 0.5
    })

    selectors: dict = field(default_factory=lambda: {
        "theme_post_container": "div.info_post",
        "post_list_nickname": ".name_author",
        "theme_post_links": "a.desc_inner",
        "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add",
        "main_frame": "mainFrame",
        "popup_radio_mutual_label": "label[for='each_buddy_add']",
        "popup_next_btn": "a.btn_ok, a.button_next, .btn_confirm",
        "popup_message_input": "#message, textarea.txt_area",
        "popup_submit_btn": "a.btn_ok, a.button_next",
        "floating_container": "#floating_bottom .wrap_postcomment",
        "static_container": ".wrap_postcomment",
        "like_button_face": "a.u_likeit_button._face",
        "post_view_comment_button": "#floating_bottom .btn_comment",
        "comment_text_area": ".u_cbox_text",
        "comment_submit_button": "button.u_cbox_btn_upload"
    })

class AddNeighborService:
    _instance: Optional['AddNeighborService'] = None

    def __init__(self):
        self.logger = Logger.instance()
        self.login_service = LoginSessionService.instance()
        self.repo = SettingsRepository.instance()
        self.driver: Optional[WebDriver] = None
        self.is_running: bool = False
        
        # 환경 변수 객체 고정
        self.defines = AddNeighborDefines()

    @classmethod
    def instance(cls) -> 'AddNeighborService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def stop(self):
        """외부에서 작업을 중단시키고 싶을 때 호출"""
        self.logger.log("🛑 중단 요청을 받았습니다. 현재 작업중인 블로그까지만 수행하고 멈춥니다.")
        self.is_running = False

    def run(self, seq: int, no: int, target_count: int, start_page: int = 1, progress_callback: Optional[Callable] = None):
        self.driver = self.login_service.get_driver()
        if not self.driver: return

        self.is_running = True
        success_count = 0
        failure_count = 0
        consecutive_fails = 0
        current_page = start_page

        while success_count < target_count and self.is_running:
            if consecutive_fails >= self.defines.conditions['최대실패횟수']:
                self.logger.log(f"🛑 {consecutive_fails}회 연속 실패로 종료.")
                break

            # 1. 네비게이션 (화면 로드)
            if not self.navigate_to_page(seq, no, current_page): 
                consecutive_fails += 1
                failure_count += 1
                break

            # 2. 화면 분석
            containers = self.analyze_list_screen()
            if not containers:
                self.logger.print(f"ℹ️ {current_page}페이지 분석 결과 블로그 없음.")
                break

            # 3. 분석된 화면에 대하여 n개 수행
            main_win = self.driver.current_window_handle
            for container in containers:
                if not self.is_running or success_count >= target_count:
                    break

                # 블로그 개별 수행 함수 호출
                if not self.process_blog_entry(container, main_win) == "SUCCESS":
                    consecutive_fails += 1
                    failure_count += 1
                    break
                
                
                
                consecutive_fails = 0
                success_count += 1
                smart_sleep(self.defines.delays['작업간대기'], "블로그 진입 완료 다음 작업 대기")
                # add_neighbor_btn_clicked = 
                if blog_entry_result == "SUCCESS":
                    success_count += 1
                    consecutive_fails = 0
                    smart_sleep(self.defines.delays['작업간대기'], "다음 블로그 준비")
                else:
                    consecutive_fails += 1
                
                if progress_callback:
                    total_try = success_count + failure_count
                    progress_callback(current_page, total_try, success_count, failure_count)

            current_page += 1

        self.is_running = False
        self.logger.log(f"🏁 작업 종료. 성공: {success_count}")

    # =========================================================================
    # 쪼개진 기능 함수들
    # =========================================================================

    def navigate_to_page(self, seq: int, no: int, page: int) -> bool:
        """1. 네비게이션: 해당 주제 및 페이지로 이동"""
        url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={no}&activeDirectorySeq={seq}&currentPage={page}"
        try:
            self.driver.get(url)
            # body 요소가 보일 때까지 대기하여 로드 보장
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            smart_sleep(self.defines.delays['목록페이지로딩'], "페이지 화면 로드")
            return True
        except Exception as e:
            self.logger.print(f"❌ 네비게이션 에러: {e}")
            return False

    def analyze_list_screen(self) -> List:
        """2. 화면분석: 현재 페이지의 블로그 컨테이너들을 수집"""
        try:
            selector = self.defines.selectors["theme_post_container"]
            # 컨테이너들이 나타날 때까지 대기
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.logger.print(f"🔎 화면 분석 완료: {len(containers)}개 발견")
            return containers
        except:
            return []

    def process_blog_entry(self, container, main_win) -> str:
        """3. n개 수행: 기존 형상을 유지하며 상세 분석 로그만 추가"""
        try:
            # [형상 유지] 닉네임 분석
            nick_el = container.find_element(By.CSS_SELECTOR, self.defines.selectors["post_list_nickname"])
            nick = nick_el.text
            self.logger.print(f"▶ 방문 시도: {nick}")

            # [형상 유지] 링크 요소 분석
            link_el = container.find_element(By.CSS_SELECTOR, self.defines.selectors["theme_post_links"])

            # [형상 유지] ActionChain 물리 클릭 수행
            current_windows = len(self.driver.window_handles)
            self.logger.print(f"   🔎 클릭 전 핸들 수: {current_windows}")

            if smart_click(self.driver, link_el):
                # [형상 유지] 새 창이 뜰 때까지 대기
                # 에러가 발생했던 지점: 여기서 TimeoutException 발생 시 핸들 추적이 끊김
                WebDriverWait(self.driver, 5).until(lambda d: len(d.window_handles) > current_windows)
                
                # [분석 로그] 성공 시
                self.logger.print(f"   🔎 새 창 감지 성공. 핸들 전환 시도.")
                
                self.driver.switch_to.window(self.driver.window_handles[-1])
                smart_sleep(self.defines.delays['블로그진입'], "블로그 진입 완료")
                
                # [작업 후 창 닫고 복귀]
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(main_win)
                return "SUCCESS"
            
            return "FAIL"

        except Exception as e:
            # [분석 로그] 에러 발생 시점의 스냅샷
            self.logger.print(f"   ❌ [분석] 에러 발생: {type(e).__name__}")
            try:
                self.logger.print(f"   🔎 [분석] 에러 시점 핸들 수: {len(self.driver.window_handles)}")
            except: pass
            
            # [형상 유지] 예외 처리 로직
            if len(self.driver.window_handles) > 1:
                # 메인 창이 아닌 경우에만 닫기 시도 (이미 닫혔을 가능성 대비)
                try:
                    if self.driver.current_window_handle != main_win:
                        self.driver.close()
                except: pass
            
            return "FAIL"