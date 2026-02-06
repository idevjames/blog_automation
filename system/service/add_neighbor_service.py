import random
import time
from typing import Optional, Callable

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException

# 싱글턴 및 유틸
from service.login_session_service import LoginSessionService
from service.settings_repository import SettingsRepository
from service.logger import Logger
from utils import smart_sleep, smart_click, human_typing, human_scroll_to_ratio

class AddNeighborService:
    _instance: Optional['AddNeighborService'] = None

    def __init__(self):
        AddNeighborService._instance = self
        
        self.logger = Logger.instance()
        self.login_service = LoginSessionService.instance()
        self.repository = SettingsRepository.instance()
        
        self.driver: Optional[WebDriver] = None
        self.is_running: bool = False
        
        # [기본 딜레이 설정] - 튜플 (최소, 최대) 초 단위
        self.delays = {
            '목록페이지로딩': (1.0, 2.5),
            '팝업창대기': (1.0, 2.0),
            '팝업초기대기': (0.2, 0.5),
            '팝업작업대기': (0.2, 0.5),
            '메시지창전환대기': (1.5, 2.0),
            '메시지입력후대기': (0.2, 0.5),
            '전송후대기': (1.0, 2.0),
            '블로그간대기': (1.0, 2.0),
            '스크롤최대비율': 0.5,
            '스크롤대기': (0.5, 1.0),
            '댓글창대기': (1.5, 2.0),
            '재시도대기': (1.0, 2.0),
        }
        
        # 셀렉터
        self.sel = {
            "theme_post_container": "div.info_post",
            "post_nickname": ".name_author",
            "post_link": "a.desc_inner",
            "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add",
            "popup_radio_mutual": "label[for='each_buddy_add']",
            "popup_radio_mutual_legacy": "label[for='radiog_0']",
            "popup_next_btn": "a.btn_ok, a.button_next, .btn_confirm, a.btn_next",
            "popup_msg_input": "#message, textarea.txt_area",
            "popup_submit_btn": "a.btn_ok, a.button_next",
            "like_btn": "div.u_likeit_list_module .u_likeit_list_btn, .u_likeit_button",
            "comment_btn": ".btn_comment, a.area_comment",
            "comment_input": ".u_cbox_text.u_cbox_text_mention, .u_cbox_text",
            "comment_submit": "button.u_cbox_btn_upload, .u_cbox_btn_upload"
        }

    @classmethod
    def instance(cls) -> 'AddNeighborService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_delay(self, key):
        """설정된 튜플 딜레이 반환, 없으면 기본값 (1.0, 2.0)"""
        return self.delays.get(key, (1.0, 2.0))

    def run(self, seq: int, no: int, target_count: int, start_page: int = 1, progress_callback=None):
        self.driver = self.login_service.get_driver()
        if not self.driver:
            self.logger.log("❌ [오류] 브라우저가 연결되지 않았습니다.")
            return

        self.is_running = True
        
        n_msgs = self.repository.get_neighbor_messages()
        c_msgs = self.repository.get_comment_messages()

        curr_success = 0
        consecutive_fails = 0
        total_try = 0
        curr_page = start_page
        
        # [설정 로드] Repository에서 딜레이 값 업데이트
        if hasattr(self.repository, 'ADD_NEIGHBOR_CONFIG'):
             loaded_delays = self.repository.ADD_NEIGHBOR_CONFIG.get("delays", {})
             if loaded_delays:
                 self.delays.update(loaded_delays)

        self.logger.log(f"🚀 [서이추 시작] 목표: {target_count}명 / 시작페이지: {curr_page}")

        while curr_success < target_count and self.is_running:
            if consecutive_fails >= 10:
                self.logger.log(f"❌ [중단] 연속 실패 {consecutive_fails}회 도달. 종료합니다.")
                break

            if progress_callback:
                progress_callback(curr_page, total_try, curr_success, consecutive_fails)

            # 1. 페이지 이동
            self.logger.print(f"📄 {curr_page}페이지로 이동합니다...")
            if not self._navigate(seq, no, curr_page): 
                self.logger.log(f"❌ [이동 실패] {curr_page}페이지 로딩 실패")
                break
            
            # 2. 블로그 목록 수집
            containers = self._get_containers()
            if not containers:
                self.logger.print(f"ℹ️ {curr_page}페이지: 블로그 목록이 없습니다 (페이지 끝).")
                break
            
            self.logger.print(f"🔎 {len(containers)}개의 블로그를 발견했습니다.")
            
            main_win = self.driver.current_window_handle
            
            for cont in containers:
                if not self.is_running: 
                    self.logger.log("🛑 사용자에 의해 중단되었습니다.")
                    return
                
                if curr_success >= target_count: break

                total_try += 1
                nick = self._get_nick(cont)
                self.logger.print(f"▶ [{curr_success+1}/{target_count}] 방문 시도: {nick}")

                # [작업 수행]
                res = self._process_one(cont, main_win, n_msgs, c_msgs)
                
                # [결과 처리]
                if res == "LIMIT_REACHED":
                    self.logger.log("❌ [중단] 일일 이웃 추가 제한에 도달했습니다.")
                    self.is_running = False
                    return
                elif res == "SUCCESS":
                    curr_success += 1
                    consecutive_fails = 0
                    self.logger.print(f"   🎉 신청 성공! (누적 {curr_success}명)")
                    # 성공 후 대기 (튜플 확인 완료)
                    smart_sleep(self._get_delay('블로그간대기'), "성공 후 다음 작업 대기")
                elif res == "FAIL":
                    consecutive_fails += 1
                    self.logger.print("   ⚠️ 실패 (재시도 대기 중...)")
                    # 실패 시 대기 (튜플 확인 완료)
                    smart_sleep(self._get_delay('재시도대기'), "실패 후 안정화 대기")
                else: 
                    # ALREADY, SKIP 등
                    consecutive_fails = 0
                    smart_sleep((0.4, 0.6), "패스 후 짧은 대기")
                
                if progress_callback:
                    progress_callback(curr_page, total_try, curr_success, consecutive_fails)
            
            curr_page += 1
        
        self.logger.log(f"🏁 [작업 종료] 총 {curr_success}명 신청 성공.")
        self.is_running = False

    def stop(self):
        self.is_running = False

    # --- 내부 로직 ---

    def _navigate(self, seq, no, page):
        url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={no}&activeDirectorySeq={seq}&currentPage={page}"
        try:
            self.driver.get(url)
            # body 로딩 대기
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # 페이지 로딩 대기 (튜플 확인 완료)
            smart_sleep(self._get_delay('목록페이지로딩'), "페이지 로딩 대기")
            return True
        except Exception as e:
            self.logger.print(f"   ❌ 네비게이션 에러: {e}")
            return False

    def _get_containers(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.sel["theme_post_container"]))
            )
            return self.driver.find_elements(By.CSS_SELECTOR, self.sel["theme_post_container"])
        except:
            return []

    def _get_nick(self, cont):
        try: return cont.find_element(By.CSS_SELECTOR, self.sel["post_nickname"]).text
        except: return "(이름없음)"

    def _process_one(self, cont, main_win, n_msgs, c_msgs):
        try:
            # 1. 링크 클릭 전 준비
            link = cont.find_element(By.CSS_SELECTOR, self.sel["post_link"])
            
            current_handles = len(self.driver.window_handles)
            
            self.logger.print("   🔗 블로그 링크 클릭")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            
            # 스크롤 후 안정화 대기
            smart_sleep((0.4, 0.7), "링크 클릭 전 스크롤 대기")
            smart_click(self.driver, link)
            
            # 2. 새 창 열림 대기
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: len(d.window_handles) > current_handles
                )
            except TimeoutException:
                self.logger.print("   ⚠️ 새 창이 열리지 않았습니다. (클릭 실패 또는 로딩 지연)")
                return "FAIL"

            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 블로그 로딩 대기 (튜플 확인 완료)
            smart_sleep(self._get_delay('팝업창대기'), "블로그 진입 대기")
            
            # 3. 서이추 시도
            result_status = self._try_add_neighbor(n_msgs)
            
            # 4. 성공 시에만 공감/댓글
            if result_status == "SUCCESS": 
                self._try_engage(c_msgs)
            
            # 5. 창 닫기 및 복귀
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(main_win)
            except Exception as e:
                self.logger.print(f"   ⚠️ 창 닫기 중 에러 (무시): {e}")
                if main_win in self.driver.window_handles:
                    self.driver.switch_to.window(main_win)

            return result_status

        except Exception as e:
            self.logger.print(f"   ❌ [치명적 오류] {e}")
            try: 
                if len(self.driver.window_handles) > 1: self.driver.close()
                self.driver.switch_to.window(main_win)
            except: pass
            return "FAIL"

    def _try_add_neighbor(self, msgs):
        # A. iframe 전환
        try:
            WebDriverWait(self.driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
        except: pass

        # B. 버튼 찾기
        btn = self._find_element_safe(self.sel["add_neighbor_btn"])
        if not btn:
            self.logger.print("   ⏩ [패스] 이웃추가 버튼 없음 (이미 이웃/버튼 미노출)")
            return "ALREADY"

        txt = btn.text.strip()
        cls = btn.get_attribute("class") or ""
        if "서로이웃" in txt and ("off" not in cls and "_rosRestrictAll" in cls):
            self.logger.print("   ⏩ [패스] 이미 서로이웃 상태")
            return "ALREADY"

        # C. 버튼 클릭
        self.logger.print("   🖱️ 이웃추가 버튼 클릭")
        smart_click(self.driver, btn)
        # 팝업 대기 (튜플 확인 완료)
        smart_sleep(self._get_delay('팝업창대기'), "신청 팝업 로딩")

        # D. 알림창 체크
        alert_res = self._check_alert_and_limit()
        if alert_res == "LIMIT": return "LIMIT_REACHED"
        if alert_res == "ALREADY": return "ALREADY"

        # E. 팝업 핸들링
        if len(self.driver.window_handles) > 2:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.logger.print("   🪟 신청 팝업 진입")
            
            final_res = self._handle_popup_steps(msgs)
            
            try: self.driver.close()
            except: pass
            
            try: self.driver.switch_to.window(self.driver.window_handles[-1])
            except: pass
            
            return final_res
        else:
            self.logger.print("   ⚠️ 팝업창이 뜨지 않음 (단순 이웃추가 되었거나 실패)")
            return "FAIL"

    def _handle_popup_steps(self, msgs):
        try:
            # 팝업 로딩 (튜플 확인 완료)
            smart_sleep(self._get_delay('팝업초기대기'), "팝업 내용 로딩")

            # 1. 라디오 버튼
            try:
                radios = self.driver.find_elements(By.CSS_SELECTOR, self.sel["popup_radio_mutual"])
                if not radios:
                    radios = self.driver.find_elements(By.CSS_SELECTOR, self.sel["popup_radio_mutual_legacy"])
                
                if radios:
                    smart_click(self.driver, radios[0])
                    self.logger.print("   🔘 '서로이웃' 선택")
                    # 라디오 선택 대기 (튜플 확인 완료)
                    smart_sleep(self._get_delay('팝업작업대기'), "라디오 선택")
                else:
                    self.logger.print("   ⏩ [패스] 서로이웃 옵션 없음")
                    return "ALREADY"
            except:
                return "ALREADY"

            # 2. 다음 버튼
            try:
                if not self.driver.find_elements(By.CSS_SELECTOR, self.sel["popup_msg_input"]):
                    next_btns = self.driver.find_elements(By.CSS_SELECTOR, self.sel["popup_next_btn"])
                    for b in next_btns:
                        if b.is_displayed():
                            smart_click(self.driver, b)
                            self.logger.print("   ➡️ '다음' 클릭")
                            # 입력창 전환 대기 (튜플 확인 완료)
                            smart_sleep(self._get_delay('메시지창전환대기'), "입력창 전환")
                            break
            except: pass

            # 3. 메시지 입력
            try:
                area = self.driver.find_element(By.CSS_SELECTOR, self.sel["popup_msg_input"])
                area.clear()
                msg = random.choice(msgs) if msgs else "우리 서로이웃 해요~"
                self.logger.print(f"   ⌨️ 메시지 입력: {msg[:10]}...")
                human_typing(area, msg)
                # 입력 후 대기 (튜플 확인 완료)
                smart_sleep(self._get_delay('메시지입력후대기'), "입력 완료")
            except:
                self.logger.print("   ❌ 메시지 입력창 찾기 실패")
                return "FAIL"

            # 4. 전송
            try:
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR, self.sel["popup_submit_btn"])
                for b in submit_btns:
                    if b.is_displayed():
                        smart_click(self.driver, b)
                        self.logger.print("   📤 전송 버튼 클릭")
                        # 전송 후 대기 (튜플 확인 완료)
                        smart_sleep(self._get_delay('전송후대기'), "전송 완료 처리")
                        
                        if self._check_alert_and_limit() == "LIMIT": 
                            return "LIMIT_REACHED"
                        return "SUCCESS"
            except: pass
            
            return "FAIL"

        except Exception as e:
            self.logger.print(f"   ❌ 팝업 처리 중 에러: {e}")
            return "FAIL"

    def _try_engage(self, msgs):
        self.logger.print("   ❤️ 공감/댓글 작업 시작")
        try:
            self.driver.switch_to.default_content()
            try:
                WebDriverWait(self.driver, 3).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            except: pass

            # 스크롤 (float 확인 완료)
            human_scroll_to_ratio(self.driver, self._get_delay('스크롤최대비율'))
            # 스크롤 후 대기 (튜플 확인 완료)
            smart_sleep(self._get_delay('스크롤대기'), "스크롤 후 로딩")

            # 공감
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, self.sel["like_btn"])
                if "on" not in btn.get_attribute("class"):
                    smart_click(self.driver, btn)
                    self.logger.print("   👍 공감 완료")
                    # 공감 후 대기 (튜플 변경)
                    smart_sleep((0.4, 0.7), "공감 클릭 후 대기")
            except: pass

            # 댓글
            if msgs:
                try:
                    c_btn = self.driver.find_element(By.CSS_SELECTOR, self.sel["comment_btn"])
                    smart_click(self.driver, c_btn)
                    
                    WebDriverWait(self.driver, 3).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, self.sel["comment_input"]))
                    )
                    # 댓글창 로딩 대기 (튜플 확인 완료)
                    smart_sleep(self._get_delay('댓글창대기'), "댓글창 로딩 대기")
                    
                    area = self.driver.find_element(By.CSS_SELECTOR, self.sel["comment_input"])
                    smart_click(self.driver, area)
                    
                    msg = random.choice(msgs)
                    self.logger.print(f"   💬 댓글 입력: {msg}")
                    human_typing(area, msg)
                    
                    s_btn = self.driver.find_element(By.CSS_SELECTOR, self.sel["comment_submit"])
                    smart_click(self.driver, s_btn)
                    self.logger.print("   ✅ 댓글 등록 완료")
                    # 등록 완료 대기 (튜플 변경)
                    smart_sleep((1.5, 2.0), "댓글 등록 완료 대기")
                except: pass
                
        except Exception as e:
            self.logger.print(f"   ⚠️ 공감/댓글 실패 (무시): {e}")

    def _check_alert_and_limit(self):
        try:
            if EC.alert_is_present()(self.driver):
                alert = self.driver.switch_to.alert
                txt = alert.text
                alert.accept()
                
                limit_keywords = ["더 이상", "1일", "제한", "추가할 수 있는"]
                if any(k in txt for k in limit_keywords):
                    self.logger.print(f"   ❌ [제한 알림] {txt}")
                    return "LIMIT"
                
                if "진행" in txt or "이미" in txt or "신청" in txt:
                    self.logger.print(f"   ℹ️ [알림] {txt}")
                    return "ALREADY"
            return "NONE"
        except:
            return "NONE"

    def _find_element_safe(self, selector):
        try: return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("mainFrame")
                return self.driver.find_element(By.CSS_SELECTOR, selector)
            except: return None





# import random
# import time
# from typing import Optional, Callable, Tuple

# from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException

# # 싱글턴 및 유틸
# from service.login_session_service import LoginSessionService
# from service.settings_repository import SettingsRepository
# from service.logger import Logger
# from utils import smart_sleep, smart_click, human_typing, human_scroll_to_ratio, human_scroll_element
# from dataclasses import dataclass

# @dataclass
# class BlogSelectors:
#     theme_post_container: str = "div.info_post"
#     post_nickname: str = ".name_author"
#     post_link: str = "a.desc_inner"
    
#     # 서이추 버튼
#     add_neighbor_button: str = ".btn_add_buddy, .btn_add_neighbor, #blog-menubody .btn_neighbor, a.btn_add, #neighbor"
    
#     # 팝업 관련
#     popup_radio_mutual: str = "label[for='each_buddy_add']"
#     popup_radio_mutual_legacy: str = "label[for='radiog_0']"
#     popup_next_btn: str = "a.btn_ok, a.button_next, .btn_confirm, a.btn_next"
#     popup_msg_input: str = "#message, textarea.txt_area"
#     popup_submit_btn: str = "a.btn_ok, a.button_next"
    
#     # [수정] 보내주신 코드의 셀렉터 그대로 적용
#     like_btn: str = "a.u_likeit_button._face"
#     comment_btn: str = ".btn_comment, a.area_comment"
#     comment_input: str = ".u_cbox_text.u_cbox_text_mention, .u_cbox_text"
#     comment_submit: str = "button.u_cbox_btn_upload, .u_cbox_btn_upload"
    
#     # 컨테이너 (순차 탐색용)
#     floating_container: str = "#floating_bottom .wrap_postcomment"
#     static_container: str = ".wrap_postcomment"

# class AddNeighborService:
#     _instance: Optional['AddNeighborService'] = None

#     def __init__(self):
#         AddNeighborService._instance = self
        
#         self.logger = Logger.instance()
#         self.login_service = LoginSessionService.instance()
#         self.repository = SettingsRepository.instance()
        
#         self.driver: Optional[WebDriver] = None
#         self.is_running: bool = False
        
#         # 딜레이 설정
#         self.delays = {
#             '목록페이지로딩': (1.0, 2.5),
#             '팝업창대기': (1.5, 2.5),
#             '팝업초기대기': (0.5, 1.0),
#             '팝업작업대기': (0.3, 0.6),
#             '메시지창전환대기': (1.5, 2.0),
#             '메시지입력후대기': (0.5, 1.0),
#             '전송후대기': (1.5, 2.5),
#             '블로그간대기': (1.5, 3.0),
#             '스크롤최대비율': 0.5,
#             '스크롤대기': (0.8, 1.5),
#             '댓글창대기': (1.5, 2.5),
#             '재시도대기': (1.5, 3.0),
#         }
        
#         self.selectors = BlogSelectors()

#     @classmethod
#     def instance(cls) -> 'AddNeighborService':
#         if cls._instance is None:
#             cls._instance = cls()
#         return cls._instance

#     def _get_delay(self, key):
#         return self.delays.get(key, (1.0, 2.0))

#     def run(self, seq: int, no: int, target_count: int, start_page: int = 1, progress_callback=None):
#         self.driver = self.login_service.get_driver()
#         if not self.driver:
#             self.logger.log("❌ [오류] 브라우저가 연결되지 않았습니다.")
#             return

#         self.is_running = True
        
#         n_msgs = self.repository.get_neighbor_messages()
#         c_msgs = self.repository.get_comment_messages()

#         curr_success = 0
#         consecutive_fails = 0
#         total_try = 0
#         curr_page = start_page
        
#         if hasattr(self.repository, 'ADD_NEIGHBOR_CONFIG'):
#              loaded_delays = self.repository.ADD_NEIGHBOR_CONFIG.get("delays", {})
#              if loaded_delays: self.delays.update(loaded_delays)

#         self.logger.log(f"🚀 [서이추 시작] 목표: {target_count}명 / 시작페이지: {curr_page}")

#         while curr_success < target_count and self.is_running:
#             if consecutive_fails >= 10:
#                 self.logger.log(f"❌ [중단] 연속 실패 {consecutive_fails}회 도달. 종료합니다.")
#                 break

#             if progress_callback:
#                 progress_callback(curr_page, total_try, curr_success, consecutive_fails)

#             self.logger.print(f"📄 {curr_page}페이지로 이동합니다...")
#             if not self._navigate(seq, no, curr_page): 
#                 self.logger.log(f"❌ [이동 실패] {curr_page}페이지 로딩 실패")
#                 break
            
#             containers = self._get_containers()
#             if not containers:
#                 self.logger.print(f"ℹ️ {curr_page}페이지: 블로그 목록이 없습니다 (페이지 끝).")
#                 break
            
#             self.logger.print(f"🔎 {len(containers)}개의 블로그를 발견했습니다.")
#             main_win = self.driver.current_window_handle
            
#             for cont in containers:
#                 if not self.is_running: 
#                     self.logger.log("🛑 사용자에 의해 중단되었습니다.")
#                     return
                
#                 if curr_success >= target_count: break

#                 total_try += 1
#                 nick = self._get_nick(cont)
#                 self.logger.print(f"▶ [{curr_success+1}/{target_count}] 방문 시도: {nick}")

#                 res = self._process_one(cont, main_win, n_msgs, c_msgs)
                
#                 if res == "LIMIT_REACHED":
#                     self.logger.log("❌ [중단] 일일 이웃 추가 제한에 도달했습니다.")
#                     self.is_running = False
#                     return
#                 elif res == "SUCCESS":
#                     curr_success += 1
#                     consecutive_fails = 0
#                     self.logger.print(f"   🎉 신청 성공! (누적 {curr_success}명)")
#                     smart_sleep(self._get_delay('블로그간대기'), "성공 후 다음 작업 대기")
#                 elif res == "FAIL":
#                     consecutive_fails += 1
#                     self.logger.print("   ⚠️ 실패 (재시도 대기 중...)")
#                     smart_sleep(self._get_delay('재시도대기'), "실패 후 안정화 대기")
#                 else: 
#                     consecutive_fails = 0
#                     smart_sleep((0.5, 0.8), "패스 후 짧은 대기")
                
#                 if progress_callback:
#                     progress_callback(curr_page, total_try, curr_success, consecutive_fails)
            
#             curr_page += 1
        
#         self.logger.log(f"🏁 [작업 종료] 총 {curr_success}명 신청 성공.")
#         self.is_running = False

#     def stop(self):
#         self.is_running = False

#     # --- 내부 로직 ---

#     def _navigate(self, seq, no, page):
#         url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={no}&activeDirectorySeq={seq}&currentPage={page}"
#         try:
#             self.driver.get(url)
#             WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
#             smart_sleep(self._get_delay('목록페이지로딩'), "목록 페이지 로딩")
#             return True
#         except Exception as e:
#             self.logger.print(f"   ❌ 네비게이션 에러: {e}")
#             return False

#     def _get_containers(self):
#         try:
#             WebDriverWait(self.driver, 5).until(
#                 EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.selectors.theme_post_container))
#             )
#             return self.driver.find_elements(By.CSS_SELECTOR, self.selectors.theme_post_container)
#         except: return []

#     def _get_nick(self, cont):
#         try: return cont.find_element(By.CSS_SELECTOR, self.selectors.post_nickname).text
#         except: return "(이름없음)"

#     def _process_one(self, cont, main_win, n_msgs, c_msgs):
#         try:
#             link = cont.find_element(By.CSS_SELECTOR, self.selectors.post_link)
#             current_handles = len(self.driver.window_handles)
            
#             self.logger.print("   🔗 블로그 링크 클릭")
#             self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
#             smart_sleep((0.3, 0.6), "링크 클릭 전 안정화")
            
#             if not smart_click(self.driver, link): return "FAIL"
            
#             try:
#                 WebDriverWait(self.driver, 5).until(lambda d: len(d.window_handles) > current_handles)
#             except TimeoutException:
#                 self.logger.print("   ⚠️ 새 창이 열리지 않았습니다.")
#                 return "FAIL"

#             self.driver.switch_to.window(self.driver.window_handles[-1])
#             smart_sleep(self._get_delay('팝업창대기'), "블로그 진입 로딩")
            
#             # 1. 서이추 시도
#             result_status = self._try_add_neighbor(n_msgs)
            
#             # 2. 성공 시에만 공감/댓글
#             if result_status == "SUCCESS": 
#                 self._try_engage(c_msgs)
            
#             # 3. 창 닫기 및 복귀
#             try:
#                 if len(self.driver.window_handles) > 1:
#                     self.driver.close()
#                 self.driver.switch_to.window(main_win)
#             except: 
#                 if main_win in self.driver.window_handles:
#                      self.driver.switch_to.window(main_win)

#             return result_status

#         except Exception as e:
#             self.logger.print(f"   ❌ [치명적 오류] {e}")
#             try: 
#                 if len(self.driver.window_handles) > 1: self.driver.close()
#                 self.driver.switch_to.window(main_win)
#             except: pass
#             return "FAIL"

#     def _try_add_neighbor(self, msgs):
#         # 보이는 버튼 찾기
#         btn = self._find_visible_neighbor_btn()
        
#         if not btn:
#             self.logger.print("   ⏩ [패스] 이웃추가 버튼을 찾을 수 없음 (또는 이미 이웃)")
#             return "ALREADY"

#         txt = btn.text.strip()
#         cls = btn.get_attribute("class") or ""
#         if "서로이웃" in txt and ("off" not in cls and "_rosRestrictAll" in cls):
#             self.logger.print("   ⏩ [패스] 이미 서로이웃")
#             return "ALREADY"

#         self.logger.print("   🖱️ 이웃추가 버튼 클릭")
#         human_scroll_element(self.driver, btn)
#         smart_sleep((0.3, 0.5), "버튼 정렬 후 대기")
        
#         if not smart_click(self.driver, btn):
#             self.logger.print("   ⚠️ 물리 클릭 실패")
#             return "FAIL"
            
#         smart_sleep(self._get_delay('팝업창대기'), "신청 팝업 로딩")

#         alert_res = self._check_alert_and_limit()
#         if alert_res == "LIMIT": return "LIMIT_REACHED"
#         if alert_res == "ALREADY": return "ALREADY"

#         if len(self.driver.window_handles) > 2:
#             self.driver.switch_to.window(self.driver.window_handles[-1])
#             self.logger.print("   🪟 신청 팝업 진입")
            
#             final_res = self._handle_popup_steps(msgs)
            
#             try: self.driver.close()
#             except: pass
            
#             try: self.driver.switch_to.window(self.driver.window_handles[-1])
#             except: pass
            
#             return final_res
#         else:
#             self.logger.print("   ⚠️ 팝업 미노출 (단순이웃됨/실패)")
#             return "FAIL"
    
#     def _find_visible_neighbor_btn(self):
#         selector = self.selectors.add_neighbor_button
        
#         # 1. 현재 프레임
#         btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
#         for b in btns:
#             if b.is_displayed() and b.size['width'] > 0:
#                 return b
        
#         # 2. mainFrame
#         try:
#             self.driver.switch_to.default_content()
#             WebDriverWait(self.driver, 2).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
#             btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
#             for b in btns:
#                 if b.is_displayed() and b.size['width'] > 0:
#                     return b
#         except: pass
        
#         return None

#     def _handle_popup_steps(self, msgs):
#         try:
#             smart_sleep(self._get_delay('팝업초기대기'), "팝업 내용 로딩")

#             # 1. 라디오 버튼
#             try:
#                 radios = self.driver.find_elements(By.CSS_SELECTOR, self.selectors.popup_radio_mutual)
#                 if not radios:
#                     radios = self.driver.find_elements(By.CSS_SELECTOR, self.selectors.popup_radio_mutual_legacy)
                
#                 if radios:
#                     smart_click(self.driver, radios[0])
#                     self.logger.print("   🔘 '서로이웃' 선택")
#                     smart_sleep(self._get_delay('팝업작업대기'), "라디오 선택")
#                 else:
#                     self.logger.print("   ⏩ [패스] 서로이웃 옵션 없음")
#                     return "ALREADY"
#             except:
#                 return "ALREADY"

#             # 2. 다음 버튼
#             try:
#                 if not self.driver.find_elements(By.CSS_SELECTOR, self.selectors.popup_msg_input):
#                     next_btns = self.driver.find_elements(By.CSS_SELECTOR, self.selectors.popup_next_btn)
#                     for b in next_btns:
#                         if b.is_displayed():
#                             smart_click(self.driver, b)
#                             self.logger.print("   ➡️ '다음' 클릭")
#                             smart_sleep(self._get_delay('메시지창전환대기'), "입력창 전환")
#                             break
#             except: pass

#             # 3. 메시지 입력
#             try:
#                 area = self.driver.find_element(By.CSS_SELECTOR, self.selectors.popup_msg_input)
#                 area.clear()
#                 msg = random.choice(msgs) if msgs else "우리 서로이웃 해요~"
#                 self.logger.print(f"   ⌨️ 메시지 입력: {msg[:10]}...")
                
#                 smart_click(self.driver, area)
#                 human_typing(area, msg)
#                 smart_sleep(self._get_delay('메시지입력후대기'), "입력 완료")
#             except:
#                 self.logger.print("   ❌ 메시지 입력창 에러")
#                 return "FAIL"

#             # 4. 전송 버튼
#             try:
#                 submit_btns = self.driver.find_elements(By.CSS_SELECTOR, self.selectors.popup_submit_btn)
#                 for b in submit_btns:
#                     if b.is_displayed():
#                         smart_click(self.driver, b)
#                         self.logger.print("   📤 전송 버튼 클릭")
#                         smart_sleep(self._get_delay('전송후대기'), "전송 완료")
                        
#                         if self._check_alert_and_limit() == "LIMIT": 
#                             return "LIMIT_REACHED"
#                         return "SUCCESS"
#             except: pass
            
#             return "FAIL"

#         except Exception as e:
#             self.logger.print(f"   ❌ 팝업 에러: {e}")
#             return "FAIL"

#     def _try_engage(self, msgs):
#         """보내주신 정상 동작 코드(_add_like_and_comment) 로직 이식"""
#         self.logger.print("   ❤️ 공감/댓글 작업 시작")
#         try:
#             self.driver.switch_to.default_content()
#             try:
#                 WebDriverWait(self.driver, 3).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
#             except: pass

#             # [핵심] 보내주신 코드처럼 ratio 스크롤만 수행 (요소 정렬 X)
#             human_scroll_to_ratio(self.driver, self._get_delay('스크롤최대비율'))
#             smart_sleep(self._get_delay('스크롤대기'), "스크롤 후 로딩")

#             # [핵심] 보내주신 코드의 컨테이너 우선순위 탐색 로직 (floating -> static)
#             container = None
#             try:
#                 container = self.driver.find_element(By.CSS_SELECTOR, self.selectors.floating_container)
#             except:
#                 try:
#                     container = self.driver.find_element(By.CSS_SELECTOR, self.selectors.static_container)
#                 except: pass

#             if not container:
#                 self.logger.print("   ⚠️ 공감/댓글 컨테이너를 찾지 못함")
#                 return

#             # --- 공감 ---
#             try:
#                 btn = container.find_element(By.CSS_SELECTOR, self.selectors.like_btn)
#                 # [핵심] human_scroll_element 제거하고 바로 클릭 시도 (플로팅 요소 호환)
#                 if "off" in btn.get_attribute("class"):
#                     smart_click(self.driver, btn)
#                     self.logger.print("   👍 공감 완료")
#                     smart_sleep((0.5, 1.0), "공감 후 대기")
#                 else:
#                     self.logger.print("   ⏩ [패스] 이미 공감함")
#             except: pass

#             # --- 댓글 ---
#             if msgs:
#                 try:
#                     c_btn = container.find_element(By.CSS_SELECTOR, self.selectors.comment_btn)
#                     smart_click(self.driver, c_btn)
                    
#                     WebDriverWait(self.driver, 3).until(
#                         EC.visibility_of_element_located((By.CSS_SELECTOR, self.selectors.comment_input))
#                     )
#                     smart_sleep(self._get_delay('댓글창대기'), "댓글창 로딩")
                    
#                     area = self.driver.find_element(By.CSS_SELECTOR, self.selectors.comment_input)
#                     smart_click(self.driver, area)
                    
#                     msg = random.choice(msgs)
#                     self.logger.print(f"   💬 댓글 입력: {msg[:10]}...")
#                     human_typing(area, msg)
                    
#                     s_btn = self.driver.find_element(By.CSS_SELECTOR, self.selectors.comment_submit)
#                     smart_click(self.driver, s_btn)
#                     self.logger.print("   ✅ 댓글 등록 완료")
#                     smart_sleep((1.5, 2.5), "댓글 등록 완료")
#                 except Exception as e:
#                     self.logger.print(f"   ⚠️ 댓글 작성 실패: {e}")
                
#         except Exception as e:
#             self.logger.print(f"   ⚠️ 공감/댓글 진입 에러: {e}")

#     def _check_alert_and_limit(self):
#         try:
#             if EC.alert_is_present()(self.driver):
#                 alert = self.driver.switch_to.alert
#                 txt = alert.text
#                 alert.accept()
                
#                 limit_keywords = ["더 이상", "1일", "제한", "추가할 수 있는"]
#                 if any(k in txt for k in limit_keywords):
#                     self.logger.print(f"   ❌ [제한 알림] {txt}")
#                     return "LIMIT"
                
#                 if "진행" in txt or "이미" in txt or "신청" in txt:
#                     self.logger.print(f"   ℹ️ [알림] {txt}")
#                     return "ALREADY"
#             return "NONE"
#         except:
#             return "NONE"

#     def _find_element_safe(self, selector):
#         try: return self.driver.find_element(By.CSS_SELECTOR, selector)
#         except:
#             try:
#                 self.driver.switch_to.default_content()
#                 self.driver.switch_to.frame("mainFrame")
#                 return self.driver.find_element(By.CSS_SELECTOR, selector)
#             except: return None