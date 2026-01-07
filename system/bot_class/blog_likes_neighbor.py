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

    def run(self, target_count):
        """메인 실행 함수"""
        if not self._go_to_blog_main():
            print("❌ 블로그 홈 진입 실패")
            return

        print(f"\n[작업] 목표 공감 수: {target_count}개")
        clicked_total = 0
        current_page = 1
        fail_streak = 0 

        while clicked_total < target_count:
            if fail_streak >= config.DEFAULT_LIKE_FAILURE_COUNT:
                print(f"\n❌ {config.DEFAULT_LIKE_FAILURE_COUNT}회 연속 클릭 실패로 중단합니다.")
                break

            print(f"\n📄 {current_page}페이지 탐색 중...")
            smart_sleep(config.DELAY_RANGE["page_load"], "데이터 로딩")

            buttons = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["feed_like_buttons"])
            
            if not buttons:
                print(" > [알림] 공감 버튼을 찾을 수 없습니다.")
                break

            print(f" > 발견된 버튼: {len(buttons)}개")

            for btn in buttons:
                if clicked_total >= target_count:
                    break
                if fail_streak >= config.DEFAULT_LIKE_FAILURE_COUNT:
                    break
                
                result = self._process_like_button(btn)
                
                if result == "SUCCESS":
                    clicked_total += 1
                    fail_streak = 0
                    print(f" > [{clicked_total}/{target_count}] ❤️ 공감 완료")
                    smart_sleep(config.DELAY_RANGE["between_actions"])
                
                elif result == "ALREADY":
                    # [수정] 이미 공감한 경우 출력
                    print(" > [패스] 이미 공감한 글입니다.")
                    continue
                
                else: # FAIL or ERROR
                    fail_streak += 1
                    print(f" > [실패] 클릭 실패 또는 오류 ({fail_streak}/{config.DEFAULT_LIKE_FAILURE_COUNT})")
            
            # 페이지 이동 로직
            if clicked_total < target_count and fail_streak < config.DEFAULT_LIKE_FAILURE_COUNT:
                current_page += 1
                if not self._move_next_page(current_page):
                    print(" > 더 이상 페이지가 없습니다.")
                    break
            else:
                break
        
        print(f"\n✅ 작업 종료. 총 {clicked_total}개 공감.")

    def _go_to_blog_main(self):
        try:
            self.driver.get("https://section.blog.naver.com/BlogHome.naver")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return True
        except:
            return False

    def _process_like_button(self, btn):
        try:
            # 화면 중앙으로 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            smart_sleep(config.DELAY_RANGE.get("before_click", (0.5, 0.5)))

            # 이미 눌렸는지 확인 (aria-pressed 속성 활용)
            if btn.get_attribute("aria-pressed") == "true":
                return "ALREADY"

            # 물리 클릭 시도
            if not smart_click(self.driver, btn):
                return "FAIL"
            
            # 클릭 결과 검증 (약 1.5초간)
            for _ in range(3):
                smart_sleep(config.DELAY_RANGE.get("verify_interval", (0.5, 0.5)))
                if btn.get_attribute("aria-pressed") == "true":
                    return "SUCCESS"
            
            return "FAIL"
        except Exception as e:
            return "ERROR"

    def _move_next_page(self, page_num):
        try:
            pages = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["pagination"])
            for p in pages:
                if p.text.strip() == str(page_num):
                    smart_click(self.driver, p)
                    smart_sleep(config.DELAY_RANGE["page_nav"], f"{page_num}페이지 이동")
                    return True
            return False
        except:
            return False