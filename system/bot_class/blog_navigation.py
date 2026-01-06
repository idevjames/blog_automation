import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep

class BlogNavigation:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def go_to_main(self):
        print("\n[이동] 블로그 메인 접속 중...")
        try:
            self.driver.get("https://section.blog.naver.com/BlogHome.naver")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, config.SELECTORS["body"])))
            smart_sleep(config.DELAY_RANGE["page_load"], "페이지 안정화")
            return True
        except:
            return "section.blog" in self.driver.current_url

    def move_to_next_page(self, target_page):
        try:
            page_nav = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["pagination"])
            for p in page_nav:
                if p.text.strip() == str(target_page):
                    self.driver.execute_script("arguments[0].click();", p)
                    smart_sleep(config.DELAY_RANGE["page_nav"], f"{target_page}페이지 이동")
                    return True
            return False
        except:
            return False