# system/bot_class/blog_likes_neighbor.py
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click

class BlogLikesNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)

    def run(self, target_count, start_page=1):
        """메인 실행 함수"""
        if not self._go_to_blog_main(start_page):
            print("❌ 블로그 홈 진입 실패")
            return

        print(f"\n[작업] {start_page}페이지부터 시작하여 공감 {target_count}개를 목표로 합니다.")
        
        clicked_total = 0
        current_page = start_page 
        
        # [수정] LIKES_NEIGHBOR_CONFIG 참조
        conf = config.LIKES_NEIGHBOR_CONFIG
        fail_limit = conf["conditions"].get("최대실패횟수", 5)
        fail_streak = 0 

        while clicked_total < target_count:
            if fail_streak >= fail_limit:
                print(f"\n❌ {fail_limit}회 연속 클릭 실패로 중단합니다.")
                break

            print(f"\n📄 {current_page}페이지 탐색 중...")
            # [수정] reason 필수 기입 및 전용 딜레이 참조
            smart_sleep(conf["delays"].get("페이지로딩", (1.0, 2.5)), f"{current_page}페이지 피드 데이터 로딩 중")

            selector = config.SELECTORS["feed_like_buttons"]
            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            if not buttons:
                print(" > [알림] 공감 버튼을 찾을 수 없습니다.")
                if fail_streak < 2: 
                     print(" > 페이지를 스킵하고 다음 페이지로 이동합니다.")
                     current_page += 1
                     self._move_next_page_direct(current_page)
                     continue
                else:
                     break

            print(f" > 발견된 버튼: {len(buttons)}개")

            for btn in buttons:
                if clicked_total >= target_count or fail_streak >= fail_limit:
                    break
                
                result = self._process_like_button(btn)
                
                if result == "SUCCESS":
                    clicked_total += 1
                    fail_streak = 0
                    print(f" > [{clicked_total}/{target_count}] ❤️ 공감 완료")
                    # [수정] reason 필수 기입 및 전용 딜레이 참조
                    smart_sleep(conf["delays"].get("작업간대기", (0.2, 0.5)), "공감 완료 후 다음 글 이동 전 대기")
                
                elif result == "ALREADY":
                    print(" > [패스] 이미 공감한 글입니다.")
                    continue
                
                else: # FAIL or ERROR
                    fail_streak += 1
                    print(f" > [실패] 클릭 실패 또는 오류 ({fail_streak}/{fail_limit})")
            
            if clicked_total < target_count and fail_streak < fail_limit:
                current_page += 1
                if not self._move_next_page_direct(current_page):
                    print(" > 더 이상 페이지가 없습니다.")
                    break
            else:
                break
        
        print(f"\n✅ 작업 종료. 총 {clicked_total}개 공감.")

    def _go_to_blog_main(self, page_num=1):
        try:
            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={page_num}"
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            try:
                selector = config.SELECTORS["feed_like_buttons"]
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            except:
                # [수정] reason 필수 기입 및 전용 딜레이 참조
                smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("페이지로딩", (1.0, 2.5)), "블로그 홈 진입 후 페이지 완전 로딩 대기")
            
            return True
        except:
            return False

    def _process_like_button(self, btn):
        conf_delay = config.LIKES_NEIGHBOR_CONFIG["delays"]
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            # [수정] reason 필수 기입 및 전용 딜레이 참조
            smart_sleep(conf_delay.get("클릭전대기", (0.1, 0.3)), "공감 버튼 클릭 전 망설임")

            initial_state = btn.get_attribute("aria-pressed") == "true"
            
            if initial_state:
                return "ALREADY"

            if not smart_click(self.driver, btn):
                return "FAIL"
            
            for _ in range(3):
                # [수정] reason 필수 기입 및 전용 딜레이 참조
                smart_sleep(conf_delay.get("확인대기", (0.3, 0.5)), "공감 버튼 클릭 결과 확인 중")
                current_state = btn.get_attribute("aria-pressed") == "true"
                if current_state:
                    return "SUCCESS"
            
            return "FAIL"
        except Exception as e:
            return "ERROR"

    def _move_next_page_direct(self, page_num):
        try:
            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={page_num}"
            self.driver.get(url)
            # [수정] reason 필수 기입 및 전용 딜레이 참조
            smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("페이지이동", (1.0, 2.5)), f"{page_num}페이지로 직접 이동 대기")
            return True
        except:
            return False