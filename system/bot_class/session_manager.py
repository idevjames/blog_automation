# system/bot_class/session_manager.py
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 상위 폴더 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep

class NaverSessionManager:
    def __init__(self):
        # 절대 경로로 프로필 폴더 지정 (system/naver_profile)
        self.base_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        self.profile_path = os.path.join(self.base_dir, "naver_profile")
        
        # 폴더가 없으면 생성 (권한 문제 방지)
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)
            
        self.driver = self._init_driver()

    def _init_driver(self):
        options = Options()
        # 사용자 데이터 디렉토리 설정 (로그인 정보 저장소)
        options.add_argument(f"user-data-dir={self.profile_path}")
        
        # 자동화 탐지 방지 옵션
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={config.USER_AGENT}')
        
        # 창 크기 최대화 (요소 가림 방지)
        options.add_argument("--window-size=1024,768")

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def check_login_status(self):
        """쿠키를 통해 로그인 여부 확인"""
        try:
            cookies = self.driver.get_cookies()
            nid_aut = any(c.get('name') == 'NID_AUT' for c in cookies)
            nid_ses = any(c.get('name') == 'NID_SES' for c in cookies)
            return nid_aut and nid_ses
        except:
            return False

    def ensure_login(self):
        print("\n[시스템] 로그인 상태를 확인합니다...")
        try:
            self.driver.get("https://www.naver.com")
        except:
            print("❌ 브라우저 연결 실패. 다시 실행해주세요.")
            return False
            
        smart_sleep((1.0, 2.0), "로그인 상태 확인 중")
        
        if self.check_login_status():
            print("✅ 기존 로그인 세션이 확인되었습니다.")
            return True
        
        print("ℹ️ 로그인 정보가 없습니다. 로그인 페이지로 이동합니다.")
        self.driver.get("https://nid.naver.com/nidlogin.login")
        
        print("\n" + "="*60)
        print(" [로그인 요청] 브라우저에서 로그인을 완료해주세요.")
        print(" ⚠️ '로그인 상태 유지'를 체크하면 다음번엔 자동 로그인됩니다.")
        print(" (로그인이 완료되면 자동으로 감지하여 넘어갑니다)")
        print("="*60)
        
        # [수정] input() 제거 -> 자동 감지 루프 (최대 5분 대기)
        max_wait = 300  # 5분
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if self.check_login_status():
                print("\n✅ 로그인 감지 성공! 세션을 저장하고 작업을 시작합니다.")
                smart_sleep((1.0, 2.0), "로그인 후 안정화")
                return True
            
            # 2초마다 체크 (로그 덜 찍히게)
            time.sleep(2)
            
        print("\n❌ 로그인 시간 초과 (5분). 프로그램을 다시 실행해주세요.")
        return False