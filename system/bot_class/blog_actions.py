import time
import sys
import os
from selenium.webdriver.common.by import By

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click

class BlogActions:
    def __init__(self, driver):
        self.driver = driver

    def find_like_buttons(self):
        return self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["like_buttons"])

    def perform_like(self, btn):
        try:
            # 1. 시야 확보 및 대기 (성공 로직 0.5초)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            smart_sleep(config.DELAY_RANGE["before_click"])

            # 2. 이미 눌렸는지 확인
            if btn.get_attribute("aria-pressed") == "true":
                print(" > [알림] 이미 공감한 포스팅입니다.")
                return "ALREADY"

            # 3. 스마트 물리 클릭
            smart_click(self.driver, btn)
            
            # 4. 검증 루프 (성공 로직 1초씩 3번)
            is_success = False
            for _ in range(3):
                smart_sleep(config.DELAY_RANGE["verify_interval"])
                if btn.get_attribute("aria-pressed") == "true":
                    is_success = True
                    break
            
            if is_success:
                return "SUCCESS"
            else:
                # 5. 재시도 로직
                print(" > ⚠️ 재시도 중...")
                smart_click(self.driver, btn)
                smart_sleep(config.DELAY_RANGE["retry_wait"])
                return "SUCCESS" if btn.get_attribute("aria-pressed") == "true" else "FAIL"

        except Exception as e:
            print(f" > [에러] 버튼 처리 중 오류: {e}")
            return "ERROR"