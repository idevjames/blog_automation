import sys
import os
from selenium.webdriver.support.ui import WebDriverWait
from .blog_navigation import BlogNavigation
from .blog_actions import BlogActions

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep

class NaverBlogBot:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.nav = BlogNavigation(self.driver, self.wait)
        self.action = BlogActions(self.driver)

    def go_to_blog_main(self):
        return self.nav.go_to_main()

    def click_neighbor_likes(self, target_count):
        print(f"\n[작업] 최대 {target_count}개의 공감을 시도합니다. (페이징 방식)")
        clicked_total = 0
        current_page = 1
        fail_streak = 0 

        while clicked_total < target_count:
            if fail_streak >= config.DEFAULT_FAILURE_COUNT:
                print(f"\n❌ [중단] {config.DEFAULT_FAILURE_COUNT}회 연속 클릭 실패! 작업을 중단합니다.")
                break

            print(f"\n📄 현재 {current_page}페이지 분석 중...")
            smart_sleep(config.DELAY_RANGE["page_load"], "페이지 데이터 로드 대기")

            buttons = self.action.find_like_buttons()
            if not buttons:
                print(" > [알림] 현재 페이지에서 공감 버튼을 찾을 수 없습니다.")
                break

            print(f" > 발견된 후보 버튼: {len(buttons)}개")

            for btn in buttons:
                if clicked_total >= target_count or fail_streak >= config.DEFAULT_FAILURE_COUNT:
                    break
                
                result = self.action.perform_like(btn)
                
                if result == "SUCCESS":
                    clicked_total += 1
                    fail_streak = 0 
                    print(f" > [{clicked_total}/{target_count}] ✅ 공감 성공 확인!")
                    smart_sleep(config.DELAY_RANGE["between_actions"], "다음 작업을 위한 휴식")
                elif result == "ALREADY":
                    continue
                elif result in ["FAIL", "ERROR"]:
                    fail_streak += 1
                    print(f" > ⚠️ 클릭 실패 ({fail_streak}/{config.DEFAULT_FAILURE_COUNT})")
                    smart_sleep((2.0, 3.0))

            if clicked_total < target_count and fail_streak < config.DEFAULT_FAILURE_COUNT:
                current_page += 1
                if not self.nav.move_to_next_page(current_page):
                    break
            else:
                break

        print(f"\n✅ 최종 완료: 총 {clicked_total}개 처리됨.")
        return clicked_total