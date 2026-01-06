import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 상위 폴더 모듈 가져오기
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep

class NaverSessionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        self.profile_path = os.path.join(self.base_dir, "naver_profile")
        self.driver = self._init_driver()

    def _init_driver(self):
        options = Options()
        options.add_argument(f"user-data-dir={self.profile_path}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"]) # 로깅 제외
        options.add_experimental_option('useAutomationExtension', False)
        
        # [수정] 불필요한 시스템 로그 숨기기
        options.add_argument("--log-level=3") 
        options.add_argument("--silent")
        
        options.add_argument(f'user-agent={config.USER_AGENT}')

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def check_login_status(self):
        cookies = self.driver.get_cookies()
        return any(c['name'] == 'NID_AUT' for c in cookies) and any(c['name'] == 'NID_SES' for c in cookies)

    def ensure_login(self):
        self.driver.get("https://www.naver.com")
        smart_sleep((1.5, 2.5), "세션 확인")
        if self.check_login_status():
            return True
        
        self.driver.get("https://nid.naver.com/nidlogin.login")
        print("\n" + "="*50 + "\n로그인 후 엔터를 누르세요.\n" + "="*50)
        input()
        return self.check_login_status()