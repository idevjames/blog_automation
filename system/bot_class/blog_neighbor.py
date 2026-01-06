import sys
import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click

class BlogNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def go_to_theme_list(self, page=1):
        dir_no = config.NEIGHBOR_CONFIG["directory_no"]
        url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={dir_no}&activeDirectorySeq=1&currentPage={page}"
        print(f"\n[이동] 주제별 목록({dir_no}번) {page}페이지 접속 중...")
        self.driver.get(url)
        smart_sleep(config.DELAY_RANGE["page_load"], "목록 로딩")

    def process_neighbors(self, current_total_success, target_goal):
        links = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["theme_post_links"])
        print(f" > 현재 페이지 블로그 목록: {len(links)}개")
        
        main_window = self.driver.current_window_handle
        local_success_count = 0

        for index, link in enumerate(links):
            if current_total_success + local_success_count >= target_goal:
                return local_success_count, True

            print(f"\n[{index+1}/{len(links)}] 블로그 방문... (현재 성공: {current_total_success + local_success_count}/{target_goal})")
            
            try:
                smart_click(self.driver, link)
                smart_sleep(config.DELAY_RANGE["window_switch"], "새 창 열림 대기")

                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    if self._action_add_neighbor():
                        local_success_count += 1
                        print(f" > ✨ 현재까지 성공: {current_total_success + local_success_count}명")
                else:
                    print(" > [오류] 새 창이 열리지 않았습니다.")

            except Exception as e:
                print(f" > [에러] 처리 중 문제 발생: {e}")
            finally:
                if self.driver.current_window_handle != main_window:
                    try:
                        self.driver.close()
                    except:
                        pass
                self.driver.switch_to.window(main_window)
                smart_sleep(config.DELAY_RANGE["between_actions"])

        return local_success_count, False

    def _action_add_neighbor(self):
        try:
            btn = None
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["add_neighbor_btn"])
            except:
                try:
                    self.driver.switch_to.frame(config.SELECTORS["blog_iframe"])
                    btn = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["add_neighbor_btn"])
                except:
                    pass

            if not btn:
                print(" > [패스] 이웃추가 버튼 없음.")
                return False

            if "서로이웃" in btn.text and "신청" not in btn.text:
                 print(f" > [패스] 이미 서로이웃 상태.")
                 return False

            print(" > [시도] 이웃추가 버튼 클릭")
            blog_window = self.driver.current_window_handle 
            
            smart_click(self.driver, btn)
            smart_sleep(config.DELAY_RANGE["window_switch"], "팝업 대기")

            all_windows = self.driver.window_handles
            if len(all_windows) > 2:
                self.driver.switch_to.window(all_windows[-1])
                
                result = self._fill_popup_form()
                
                if self.driver.current_window_handle != blog_window:
                    try:
                        self.driver.close()
                    except:
                        pass
                self.driver.switch_to.window(blog_window)
                return result
            else:
                print(" > [알림] 팝업 안 뜸.")
                return False

        except Exception as e:
            print(f" > [경고] 오류: {e}")
            return False

    def _fill_popup_form(self):
        """팝업 흐름 제어 (config 참조)"""
        try:
            smart_sleep(config.DELAY_RANGE["popup_step_wait"])

            # 1. 서로이웃 라벨
            try:
                mutual_label = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_radio_mutual_label"])
                smart_click(self.driver, mutual_label)
                smart_sleep(config.DELAY_RANGE["popup_interaction"])
            except:
                print(" > [실패] '서로이웃' 불가.")
                return False

            # 2. 1단계 다음 버튼
            try:
                first_next_btn = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_first_next_btn"])
                if first_next_btn.is_displayed():
                    smart_click(self.driver, first_next_btn)
                    smart_sleep(config.DELAY_RANGE["popup_form_load"], "폼 전환")
            except:
                pass

            # 3. 메시지 입력 (랜덤)
            try:
                msg_box = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"])
                smart_click(self.driver, msg_box)
                msg_box.clear()
                
                random_msg = random.choice(config.NEIGHBOR_CONFIG["messages"])
                msg_box.send_keys(random_msg)
                print(f" > [입력] 메시지: {random_msg[:15]}...") 
                smart_sleep(config.DELAY_RANGE["popup_typing"])
                
            except Exception:
                print(" > [에러] 메시지 입력 불가.")
                return False

            # 4. 최종 제출
            try:
                final_submit_btn = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_submit_btn"])
                smart_click(self.driver, final_submit_btn)
                smart_sleep(config.DELAY_RANGE["popup_submit"], "전송 완료")
                print(" > [완료] ✅ 서로이웃 신청 성공!")
                return True
            except:
                print(" > [에러] 제출 버튼 실패.")
                return False

        except Exception:
            return False