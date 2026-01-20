import sys
import os
import random
import sqlite3
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 경로 설정 (절대 건드리지 않음)
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
        # setup_comments.txt 내용이 반영된 config 참조
        self.conf = config.NEIGHBOR_COMMENT_CONFIG 
        self.selectors = config.SELECTORS
        self.worker = None

    def run(self, target_count, start_page):
        # 메시지 및 상세 딜레이 설정 로드
        comment_messages = self.conf.get("messages", ["잘 보고 갑니다!"])
        delays = self.conf.get("delays", {}) 
        conditions = self.conf.get("conditions", {})
        
        interval_days = conditions.get("방문주기", 3)
        max_fails = conditions.get("최대실패횟수", 3)
        
        success_count = 0
        fail_count = 0
        current_page = start_page

        print(f"\n🚀 이웃 댓글 자동화 시작 (목표: {target_count}명)")
        print(f"✨ 상세 딜레이 설정 적용 완료")

        while success_count < target_count:
            # 중단 신호 체크
            if self.worker and self.worker.is_stopped:
                print("\n🛑 [중단] 사용자에 의해 작업이 중단되었습니다.")
                break

            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={current_page}"
            self.driver.get(url)
            
            # [Delay 1] 피드 페이지 로딩
            smart_sleep(delays.get("피드_페이지_로딩", (2.5, 4.0)), "피드 목록 로딩 중")

            items = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["feed_item_inner"])
            if not items:
                print(f"   > [알림] {current_page}페이지에 게시글이 없습니다.")
                break

            for item in items:
                # 개별 처리 중단 체크
                if self.worker and self.worker.is_stopped: return
                if success_count >= target_count: break
                
                try:
                    # 이웃 정보 추출
                    author_el = item.find_element(By.CSS_SELECTOR, self.selectors["feed_author_link"])
                    blog_url = author_el.get_attribute("href")
                    blog_id = blog_url.split('/')[-1]
                    nickname = item.find_element(By.CSS_SELECTOR, self.selectors["feed_nickname"]).text.strip()
                    
                    # DB 주기 체크 (함수 분리 유지)
                    if not self._is_target_ready(blog_id, interval_days):
                        continue
                    
                    try:
                        reply_btn = item.find_element(By.CSS_SELECTOR, self.selectors["feed_reply_icon"])
                        smart_click(self.driver, reply_btn)
                        print("   > 🖱️ smart_click으로 댓글창 새 탭 열기 성공")
                        
                    except Exception as e:
                        print(f"   > ⚠️ 클릭 실패, 일반 진입 시도: {e}")
                        self.driver.execute_script(f"window.open('{blog_url}');")
                                            
                    # [Delay 2] 블로그 접속 대기
                    smart_sleep(delays.get("블로그_접속_대기", (3.0, 5.0)), f"@{nickname} 블로그 진입 대기")
                    
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # 댓글 작성 실행 (실패/성공 반환)
                    if self.execute_commenting(blog_id, nickname, comment_messages, delays):
                        success_count += 1
                        fail_count = 0
                        # [로그] GUI 카운팅용 포맷 (수정 금지)
                        print(f"> ✅ '{nickname}' 이웃에게 댓글작성 완료!")
                    else:
                        fail_count += 1
                    
                    # 탭 닫기 및 복귀
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                    # [Delay 9] 다음 이웃 대기
                    smart_sleep(delays.get("다음_이웃_대기", (2.0, 3.0)), "다음 이웃 이동 전 휴식")

                    if fail_count >= max_fails:
                        print(f"⚠️ 연속 {max_fails}회 실패로 작업을 중단합니다.")
                        return

                except Exception as e:
                    print(f"   > [오류] {e}")
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    fail_count += 1
                    continue
            current_page += 1
        
        print(f"\n✨ 목표 수량({target_count}) 달성! 작업을 종료합니다.")

    def execute_commenting(self, blog_id, nickname, messages, delays):
        """댓글 작성 상세 로직 (Gemini AI 연동 및 실패 시 대응 로직)"""
        try:
            # [Delay 3] 프레임 전환 대기
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            smart_sleep(delays.get("프레임_전환_대기", (0.5, 1.0)), "댓글 프레임 전환")
            
            # [Delay 4] 중복 체크 대기
            smart_sleep(delays.get("중복_체크_대기", (1.5, 2.0)), "기존 댓글 스캔 중")
            if self.check_already_commented():
                print(f"   > 🚫 스킵: 이미 내 댓글이 달려 있습니다.")
                return False 

            # --- [댓글 메시지 결정 로직] ---
            final_msg = ""
            
            # AI 사용 모드인 경우
            if config.GEMINI_CONFIG.get("USE_GEMINI") and config.GEMINI_CONFIG.get("GEMINI_API_KEY"):
                try:
                    from ai_helper import GeminiHelper
                    
                    # 1. 본문 텍스트 추출 시도
                    try:
                        content_el = self.driver.find_element(By.CSS_SELECTOR, self.selectors.get("post_content", ".se-main-container, #postViewArea"))
                        post_text = content_el.text.strip()
                    except:
                        # [조건 2] 본문 추출 자체가 안 되는 경우 실패로 간주하고 종료
                        print(f"   > ❌ 실패: 본문 영역을 찾을 수 없습니다. (취소)")
                        return False

                    # [조건 3] 본문 내용이 80자 미만인 경우 내용 없음으로 간주하고 종료
                    if len(post_text) < 80:
                        print(f"   > ❌ 취소: 본문 내용이 너무 짧습니다. (80자 미만)")
                        return False
                    
                    # 추출 성공 시 로그 출력 (축약형)
                    log_post = post_text[:50] + "\n[...중략...]\n" + post_text[-30:] if len(post_text) > 80 else post_text
                    print(f"[본문 추출 성공]\n{log_post}")
                    
                    # 2. Gemini AI 댓글 생성 요청
                    helper = GeminiHelper(config.GEMINI_CONFIG["GEMINI_API_KEY"])
                    ai_reply = helper.generate_comment(post_text, config.GEMINI_CONFIG.get("GEMINI_PROMPT", ""))
                    
                    if ai_reply:
                        final_msg = ai_reply
                        print(f"   > 🤖 AI 맞춤 댓글 생성 완료")
                    else:
                        # [조건 1] AI 댓글 생성 실패 시 기존 리스트 활용
                        print(f"   > ⚠️ AI 생성 실패: 기존 댓글 리스트를 활용합니다.")
                        final_msg = random.choice(messages)
                        
                except Exception as e:
                    # AI 로직 중 에러 발생 시 기존 리스트로 백업
                    print(f"   > ⚠️ AI 프로세스 에러 ({e}): 기존 댓글 리스트를 활용합니다.")
                    final_msg = random.choice(messages)
            else:
                # AI 미사용 설정 시 기본 리스트 활용
                final_msg = random.choice(messages)

            # 만약 어떤 이유로든 메시지가 비어있다면 백업
            if not final_msg:
                final_msg = random.choice(messages)
            # -------------------------------

            # [Delay 5] 입력창 찾기 대기
            smart_sleep(delays.get("입력창_찾기_대기", (1.0, 2.0)), "댓글 입력창 탐색")
            try:
                input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["comment_input_area"])))
            except:
                btn = self.driver.find_element(By.CSS_SELECTOR, self.selectors["comment_open_button"])
                smart_click(self.driver, btn)
                input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["comment_input_area"])))

            # [Delay 6] 입력창 클릭 대기
            smart_sleep(delays.get("입력창_클릭_대기", (0.5, 1.0)), "입력창 포커스 대기")
            smart_click(self.driver, input_area)
            
            # 최종 메시지 입력
            print(f"   > [댓글 작성] {final_msg}")
            human_typing(input_area, final_msg)
            
            # [Delay 7] 타이핑 후 대기 (검토 시간)
            smart_sleep(delays.get("타이핑_후_대기", (1.5, 2.5)), "입력 완료 후 검토")

            # 등록 버튼 클릭
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, self.selectors["comment_submit_button"])
            smart_click(self.driver, submit_btn)
            
            # [Delay 8] 등록 완료 대기
            smart_sleep(delays.get("등록_완료_대기", (2.5, 4.0)), "서버 등록 처리 대기")

            # DB 저장
            self.db.save_comment_success(blog_id, nickname)
            return True
            
        except Exception as e:
            print(f"   > ❌ 작성 에러: {e}")
            return False

    def check_already_commented(self):
        """내 댓글 존재 여부 확인"""
        try:
            my_name_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors["my_write_nickname"])
            my_name = my_name_element.text.strip()
            comment_authors = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["comment_list_nicknames"])
            for author in comment_authors:
                if author.text.strip() == my_name:
                    return True
            return False
        except:
            return False

    def _is_target_ready(self, blog_id, interval_days):
        """DB 방문 주기 확인 (지난 작업일로부터 interval_days 지났는지 체크)"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT last_comment_date FROM neighbor_comments WHERE blog_id = ?", (blog_id,))
            row = cursor.fetchone()
            conn.close()
            
            # 기록이 없으면(None) 작업 대상(True)
            if not row or not row[0]:
                return True
                
            last_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').date()
            diff_days = (datetime.now().date() - last_date).days
            
            if diff_days < interval_days:
                print(f"   > ⏳ 패스: {diff_days}일 전 작업 (설정: {interval_days}일)")
                return False
                
            return True
        except Exception as e:
            print(f"   > [DB 에러] {e}")
            return True # 에러나면 일단 진행