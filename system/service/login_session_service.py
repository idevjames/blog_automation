import os
import time
import platform
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from utils.smart_util import smart_sleep

class LoginSessionService:
    _instance: Optional['LoginSessionService'] = None

    def __init__(self):
        LoginSessionService._instance = self

        self.driver: Optional[WebDriver] = None
        self.base_dir = os.getcwd()
        self.profile_path = os.path.join(self.base_dir, "user_data", "naver_profile")
        self._ensure_directory()

    @classmethod
    def instance(cls) -> 'LoginSessionService':
        if cls._instance is None:
            raise Exception("LoginSessionService 초기화되지 않았습니다. main.py를 확인하세요.")
        return cls._instance

    def _ensure_directory(self):
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)

    def _get_user_agent(self):
        system_name = platform.system()
        if system_name == 'Darwin': 
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        else:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def open_browser(self):
        if self.is_browser_alive():
            return

        try:
            options = Options()
            options.add_argument(f"user-data-dir={self.profile_path}")
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            ua = self._get_user_agent()
            options.add_argument(f'user-agent={ua}')
            options.add_argument("--window-size=800,600")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

            current_ua = self.driver.execute_script("return navigator.userAgent;")
            print(f"🌍 Browser User-Agent: {current_ua}")
            
        except Exception as e:
            raise Exception(f"브라우저 실행 실패: {str(e)}")

    def ensure_session(self):
        """로그인 세션 확인 및 대기 (Blocking Method)"""
        if not self.driver:
            self.open_browser()

        try:
            self.driver.get("https://www.naver.com")
            smart_sleep((1.5, 2.5), "네이버 메인 진입")

            if self._check_cookies():
                return True 

            self.driver.get("https://nid.naver.com/nidlogin.login")
            smart_sleep((1.0, 2.0), "로그인 페이지 이동")
            
            max_wait = 300
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if not self.is_browser_alive():
                    raise Exception("로그인 대기 중 브라우저가 종료되었습니다.")
                
                if self._check_cookies():
                    smart_sleep((1.5, 2.5), "로그인 성공 감지")
                    if "nid.naver.com" in self.driver.current_url:
                        self.driver.get("https://blog.naver.com")
                    return True
                
                smart_sleep((2.0, 3.0), "로그인 대기 중...")
            
            raise Exception("로그인 시간 초과 (5분)")

        except Exception as e:
            raise e 

    def _check_cookies(self) -> bool:
        try:
            if not self.driver: return False
            cookies = self.driver.get_cookies()
            nid_aut = any(c.get('name') == 'NID_AUT' for c in cookies)
            nid_ses = any(c.get('name') == 'NID_SES' for c in cookies)
            return nid_aut and nid_ses
        except:
            return False

    def is_browser_alive(self) -> bool:
        if self.driver is None:
            return False
        try:
            _ = self.driver.title 
            return True
        except:
            self.driver = None
            return False
        
    def get_driver(self) -> Optional[WebDriver]:
        """
        현재 실행 중인 브라우저 드라이버 인스턴스를 반환합니다.
        다른 서비스(AddNeighborService 등)에서 이 브라우저를 제어하기 위해 사용합니다.
        """
        return self.driver

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None