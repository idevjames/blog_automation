import sys
import os
import random
import sqlite3
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 경로 설정 유지
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import config
from utils import smart_sleep, smart_click, human_typing
from db_manager import BlogDB

class BlogCommenter:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.db = BlogDB()
        self.conf = config.NEIGHBOR_COMMENT_CONFIG
        self.selectors = config.SELECTORS
        self.worker = None

    def check_already_commented(self):
        """현재 글에 내 닉네임이나 ID로 된 댓글이 이미 있는지 확인"""
        try:
            # 내 정보 가져오기 (댓글창 상단 내 닉네임)
            my_name_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors["my_write_nickname"])
            my_name = my_name_element.text.strip()
            
            # 현재 로드된 모든 댓글 작성자 닉네임 스캔
            comment_authors = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["comment_list_nicknames"])
            for author in comment_authors:
                if author.text.strip() == my_name:
                    return True
            return False
        except:
            return False

    def run(self, target_count, start_page):
        # 메시지 리스트 로드
        comment_messages = self.conf.get("messages", [])
        if not comment_messages:
            print("⚠️ [경고] COMMENT_MESSAGES가 비어있습니다. 기본 문구를 사용합니다.")
            comment_messages = ["포스팅 잘 보고 갑니다! ㅎㅎ", "유익한 정보 감사합니다!"]
        
        success_count = 0
        fail_count = 0
        current_page = start_page
        
        delays = self.conf.get("delays", {})
        conditions = self.conf.get("conditions", {})
        interval_days = conditions.get("방문주기", 3)
        max_fails = conditions.get("최대실패횟수", 3)

        print(f"\n🚀 이웃 댓글 자동화 시작 (목표: {target_count}명)")
        print(f"✨ 설정: {interval_days}일 주기, 최대 {max_fails}회 실패 허용")

        while success_count < target_count:
            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={current_page}"
            self.driver.get(url)
            smart_sleep((2.5, 3.5), "피드 페이지 로드 대기")

            items = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["feed_item_inner"])
            if not items:
                print(f"   > [알림] {current_page}페이지에 게시글이 없습니다.")
                break

            for idx, item in enumerate(items, 1):
                if self.worker and self.worker.is_stopped: return
                if success_count >= target_count: break
                
                if fail_count >= max_fails:
                    print(f"⚠️ [중단] 연속 {max_fails}회 실패로 작업을 종료합니다.")
                    return

                try:
                    # 정보 추출
                    author_el = item.find_element(By.CSS_SELECTOR, self.selectors["feed_author_link"])
                    blog_url = author_el.get_attribute("href")
                    blog_id = blog_url.split('/')[-1]
                    nickname = item.find_element(By.CSS_SELECTOR, self.selectors["feed_nickname"]).text
                    
                    print(f"\n🔎 [{idx}번] {nickname} (@{blog_id})")

                    # 1. DB 주기 체크
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT last_comment_date FROM neighbor_comments WHERE blog_id = ?", (blog_id,))
                    row = cursor.fetchone()
                    conn.close()

                    if row and row[0]:
                        last_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').date()
                        diff = (datetime.now().date() - last_date).days
                        if diff < interval_days:
                            print(f"   > ⏳ 패스: {diff}일 전 작업함 (설정 주기 {interval_days}일)")
                            continue
                    
                    # 2. 댓글창 진입
                    try:
                        comment_icon = item.find_element(By.CSS_SELECTOR, self.selectors["feed_reply_icon"])
                        smart_click(self.driver, comment_icon.find_element(By.XPATH, "./.."))
                    except:
                        self.driver.execute_script(f"window.open('{blog_url}');")

                    smart_sleep((3.0, 4.0), "새 탭 로딩 대기")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # 3. 댓글 작성 실행
                    if self.execute_commenting(blog_id, nickname, comment_messages, delays):
                        success_count += 1
                        fail_count = 0
                        # [수정] 성공 로그 카운트 표시 강화
                        print(f"   > ✅ 성공: {nickname}에게 댓글 작성 완료!")
                        print(f"   > 💬 이웃 댓글 카운트: [ {success_count} / {target_count} ]")
                        
                        # GUI 연동을 위한 worker 업데이트 (있을 경우만)
                        if self.worker:
                            self.worker.progress_signal.emit(success_count)
                    else:
                        fail_count += 1
                    
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    smart_sleep(delays.get("블로그간대기", (1.5, 2.5)), "다음 이웃 이동 전 대기")

                except Exception as e:
                    print(f"   > ❌ 처리 실패: {e}")
                    fail_count += 1
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    continue
            current_page += 1
        
        print(f"\n✨ 목표 수량({target_count}) 달성! 작업을 종료합니다.")

    def execute_commenting(self, blog_id, nickname, messages, delays):
        try:
            # 프레임 전환
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, self.selectors["main_frame"])))

            # 중복 체크
            smart_sleep((1.5, 2.0), "기존 댓글 스캔 중")
            if self.check_already_commented():
                print(f"   > 🚫 스킵: 이미 내 댓글이 달려 있습니다.")
                return False 

            # 입력창 탐색
            try:
                input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["comment_input_area"])))
            except:
                btn = self.driver.find_element(By.CSS_SELECTOR, self.selectors["comment_open_button"])
                smart_click(self.driver, btn)
                input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["comment_input_area"])))

            # 입력 및 전송
            smart_click(self.driver, input_area)
            smart_sleep((0.5, 1.0), "입력창 활성화 대기")
            
            msg = random.choice(messages)
            # [수정] 줄이지 않고 전체 메시지 출력
            print(f"   > ✍️ 타이핑 중: {msg}")
            
            # 사람처럼 한 글자씩 입력
            human_typing(input_area, msg)
            
            smart_sleep(delays.get("입력후대기", (1.0, 1.5)), "입력 완료 후 대기")

            # 등록 버튼 클릭
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, self.selectors["comment_submit_button"])
            smart_click(self.driver, submit_btn)
            smart_sleep(delays.get("전송후대기", (2.5, 4.0)), "서버 전송 및 등록 확인")

            # DB 저장
            self.db.save_comment_success(blog_id, nickname)
            return True
        except Exception as e:
            print(f"   > ❌ 작성 에러 상세: {e}")
            return False