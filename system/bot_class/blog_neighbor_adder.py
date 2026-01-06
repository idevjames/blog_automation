import random
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    UnexpectedAlertPresentException, 
    NoAlertPresentException, 
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from system import config
from system.utils import smart_sleep, smart_click

class BlogNeighborAdder:
    def __init__(self, driver):
        self.driver = driver
        # settings.txt에서 설정한 번호 (예: 5=맛집, 12=IT 등)
        self.dir_no = config.NEIGHBOR_CONFIG.get("directory_no", 5)
        self.messages = config.NEIGHBOR_CONFIG.get("messages", [])

    def go_to_theme_list(self, page):
        """
        [수정됨] 사용자 요청 URL 형식 반영
        https://section.blog.naver.com/ThemePost.naver?directoryNo=XX&activeDirectorySeq=1&currentPage=YY
        """
        # activeDirectorySeq=1 로 고정하여 정확히 주제별 리스트로 진입
        url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={self.dir_no}&activeDirectorySeq=1&currentPage={page}"
        
        print(f"\n[이동] 주제별 목록(No.{self.dir_no}) {page}페이지 접속 중...")
        self.driver.get(url)
        
        # 페이지 로딩 대기
        smart_sleep(config.DELAY_RANGE.get("page_load", (2.0, 3.0)), "목록 로딩")

    def process_neighbors(self, current_success, total_target):
        added_count = 0
        # 주제별 리스트의 글 링크 Selector (a.desc_inner)
        link_sel = config.SELECTORS.get("theme_post_links", "a.desc_inner")
        
        # 링크 수집
        links = self.driver.find_elements(By.CSS_SELECTOR, link_sel)
        print(f"🔎 수집된 링크: {len(links)}개")
        
        if not links:
            return 0, True

        main_window = self.driver.current_window_handle

        for i, link_el in enumerate(links):
            if current_success + added_count >= total_target:
                break
            
            try:
                # 링크 주소 추출
                url = link_el.get_attribute("href")
                print(f"\n[{i+1}/{len(links)}] 진입: {url}")
                
                self.driver.get(url)
                smart_sleep(config.DELAY_RANGE.get("page_load", (1.5, 2.5)), "게시글 진입")
                
                # 프레임 전환 (필수)
                self._switch_to_frame("mainFrame")

                # === [핵심] 서이추 시도 ===
                if self._apply_neighbor():
                    print("   🎉 서이추 신청 성공! -> 공감/댓글 진행")
                    added_count += 1
                    
                    # 팝업 닫힌 후 본창/프레임 복귀
                    self.driver.switch_to.window(main_window)
                    self._switch_to_frame("mainFrame")
                    
                    self._do_like()
                    self._do_comment()
                else:
                    print("   ⏭️ 서이추 패스 (조건 미달/거절/이미이웃)")
            
            except Exception:
                # 에러 발생 시 로그 생략하고 다음으로
                continue
            
            finally:
                # 창 정리 (팝업 닫기)
                try:
                    while len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.close()
                    self.driver.switch_to.window(main_window)
                except:
                    pass

        return added_count, False

    def _switch_to_frame(self, frame_name):
        try:
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 3).until(EC.frame_to_be_available_and_switch_to_it(frame_name))
        except:
            pass

    def _apply_neighbor(self):
        """서이추 로직 (5초 타임아웃 & Alert 즉시 처리)"""
        try:
            # 1. 서이추 버튼 찾기
            btn_sel = config.SELECTORS.get("add_neighbor_btn")
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, btn_sel)
            except:
                print("   👋 이웃추가 버튼 없음")
                return False

            # 2. 버튼 클릭 (Alert 감지)
            try:
                smart_click(self.driver, btn)
            except UnexpectedAlertPresentException:
                try:
                    self.driver.switch_to.alert.accept()
                except: pass
                return False
            
            # 3. 팝업 대기 (최대 5초)
            try:
                WebDriverWait(self.driver, 5).until(lambda d: len(d.window_handles) > 1)
            except TimeoutException:
                # 팝업 안 뜸 -> Alert 확인
                try:
                    self.driver.switch_to.alert.accept()
                except: pass
                return False

            # 4. 팝업 핸들링
            main_win = self.driver.current_window_handle
            for h in self.driver.window_handles:
                if h != main_win:
                    self.driver.switch_to.window(h)
                    break
            
            try:
                # [팝업] 라디오 버튼
                radio_sel = config.SELECTORS.get("popup_radio_mutual_label")
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, radio_sel)))
                radio_label = self.driver.find_element(By.CSS_SELECTOR, radio_sel)
                smart_click(self.driver, radio_label)
                
                # [팝업] 다음 버튼
                next_sel = config.SELECTORS.get("popup_first_next_btn")
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, next_sel)
                    smart_click(self.driver, next_btn)
                    smart_sleep(config.DELAY_RANGE.get("popup_form_load", (0.5, 1.0)))
                except: pass

                # [팝업] 메시지 입력
                if self.messages:
                    msg_sel = config.SELECTORS.get("popup_message_input")
                    if msg_sel:
                        txt_area = self.driver.find_element(By.CSS_SELECTOR, msg_sel)
                        smart_click(self.driver, txt_area)
                        txt_area.clear()
                        txt_area.send_keys(random.choice(self.messages))
                        smart_sleep(config.DELAY_RANGE.get("popup_typing", (0.5, 1.0)))

                # [팝업] 확인 버튼
                submit_sel = config.SELECTORS.get("popup_submit_btn")
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, submit_sel)
                smart_click(self.driver, submit_btn)
                
                print("      [팝업] 신청 완료")
                smart_sleep(config.DELAY_RANGE.get("popup_submit", (1.0, 1.5)))
                
                return True

            except Exception:
                self.driver.close()
                self.driver.switch_to.window(main_win)
                return False

        except Exception:
            return False

    def _do_like(self):
        try:
            self._switch_to_frame("mainFrame")
            like_sel = ".u_likeit_button"
            
            wait = WebDriverWait(self.driver, 5)
            btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, like_sel)))
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.5)

            status = btn.get_attribute("aria-pressed")
            if status == "false":
                smart_click(self.driver, btn)
                print("      ❤️ 공감 완료")
                smart_sleep(config.DELAY_RANGE.get("between_actions", (1.0, 2.0)))
            else:
                print("      ❤️ 이미 공감됨")

        except Exception:
            pass

    def _do_comment(self):
        try:
            self._switch_to_frame("mainFrame")
            if not self.messages: return

            msg = random.choice(self.messages)
            wait = WebDriverWait(self.driver, 5)

            # 1. 댓글창 찾기 (없으면 버튼 클릭)
            try:
                cmt_input = self.driver.find_element(By.CSS_SELECTOR, ".u_cbox_text")
            except NoSuchElementException:
                try:
                    open_btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn_comment")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", open_btn)
                    smart_click(self.driver, open_btn)
                    time.sleep(1.0)
                except NoSuchElementException:
                    return

            # 2. 가이드 박스 클릭 (활성화)
            try:
                guide_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".u_cbox_guide")))
                smart_click(self.driver, guide_box)
                time.sleep(0.5)
            except: pass

            # 3. 입력 및 전송
            cmt_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".u_cbox_text")))
            cmt_input.send_keys(msg)
            smart_sleep(config.DELAY_RANGE.get("popup_typing", (0.5, 1.0)))
            
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, ".u_cbox_btn_upload")
            smart_click(self.driver, submit_btn)
            
            print(f"      💬 댓글: {msg}")
            smart_sleep(config.DELAY_RANGE.get("between_actions", (1.0, 2.0)))

        except Exception:
            pass