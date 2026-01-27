# system/bot_class/blog_likes_neighbor.py
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click, human_scroll_element

class BlogLikesNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)

    # [수정] start_page 인자 추가
    def run(self, target_count, start_page=1):
        """메인 실행 함수"""
        # [수정] 시작 페이지로 바로 이동
        if not self._go_to_blog_main(start_page):
            print("❌ 블로그 홈 진입 실패")
            return

        print(f"\n[작업] {start_page}페이지부터 시작하여 공감 {target_count}개를 목표로 합니다.")
        
        clicked_total = 0
        current_page = start_page # [수정] 현재 페이지 설정
        
        # [수정] LIKES_NEIGHBOR_CONFIG 참조
        conf = config.LIKES_NEIGHBOR_CONFIG
        fail_limit = conf["conditions"].get("최대실패횟수", 5)
        fail_streak = 0 

        while clicked_total < target_count:
            # [추가 작업 1] 중단 신호 체크
            if hasattr(self, 'worker') and self.worker.is_stopped:
                print("\n🛑 [중단] 사용자에 의해 작업이 중단되었습니다.")
                break

            if fail_streak >= fail_limit:
                print(f"\n❌ {fail_limit}회 연속 클릭 실패로 중단합니다.")
                break

            print(f"\n📄 {current_page}페이지 탐색 중...")
            # [수정] reason 필수 및 config 참조
            smart_sleep(conf["delays"].get("페이지로딩", (1.0, 2.5)), f"{current_page}페이지 피드 데이터 로딩 대기")

            selector = config.SELECTORS["feed_like_buttons"]
            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            if not buttons:
                print(" > [알림] 공감 버튼을 찾을 수 없습니다.")
                # 페이지 로딩 직후 버튼이 없는 경우, 다음 페이지로 넘어가보기
                # (마지막 페이지인지 체크 로직은 버튼 유무로 간접 판단)
                if fail_streak < 2: # 한두 번은 봐줌
                     print(" > 페이지를 스킵하고 다음 페이지로 이동합니다.")
                     current_page += 1
                     self._move_next_page_direct(current_page)
                     continue
                else:
                     break

            print(f" > 발견된 버튼: {len(buttons)}개")

            for btn in buttons:
                # [추가 작업 2] 버튼 반복 중 중단 신호 체크
                if hasattr(self, 'worker') and self.worker.is_stopped:
                    return

                if clicked_total >= target_count:
                    break
                if fail_streak >= fail_limit:
                    break
                
                # [프로세스 리트라이 로직 시작]
                # 개별 버튼에 대해 최대 3회까지 시도 (Backoff 적용)
                process_success = False
                for attempt in range(1, 4):
                    result = self._process_like_button(btn)
                    
                    if result == "SUCCESS":
                        clicked_total += 1
                        fail_streak = 0
                        print(f" > [{clicked_total}/{target_count}] ❤️ 공감 완료")
                        process_success = True
                        break # 리트라이 루프 탈출
                        
                    elif result == "ALREADY":
                        print(" > [패스] 이미 공감한 글입니다.")
                        process_success = True # 이미 된 것이므로 성공으로 간주하고 루프 탈출
                        break
                    
                    else: # FAIL or ERROR
                        # 실패 시 점점 길게 대기 (1초 -> 2초 -> 3초)
                        backoff = float(attempt)
                        print(f"   > [재시도] 클릭 미반영... {attempt}회차 대기 ({backoff}초)")
                        
                        # 중단 체크가 가능한 분할 대기
                        for _ in range(int(backoff * 2)):
                            if hasattr(self, 'worker') and self.worker.is_stopped: return
                            import time
                            time.sleep(0.5)
                
                # 3회 시도 후에도 최종 실패한 경우
                if not process_success:
                    fail_streak += 1
                    print(f" > [실패] 3회 시도 모두 실패 ({fail_streak}/{fail_limit})")
                else:
                    # 최종 성공(또는 이미 공감) 시에만 다음 작업을 위한 휴식
                    smart_sleep(conf["delays"].get("작업간대기", (0.2, 0.5)), "다음 공감 버튼 클릭 전 휴식")
            
            # 페이지 이동 로직
            if clicked_total < target_count and fail_streak < fail_limit:
                current_page += 1
                # [수정] 기존 버튼 클릭 방식 대신 URL 이동 방식(direct) 사용 권장
                if not self._move_next_page_direct(current_page):
                    print(" > 더 이상 페이지가 없습니다.")
                    break
            else:
                break
        
        print(f"\n✅ 작업 종료. 총 {clicked_total}개 공감.")

    # [수정] page_num을 받아 URL로 직접 이동
    def _go_to_blog_main(self, page_num=1):
        try:
            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={page_num}"
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 첫 페이지 로드 시 콘텐츠가 완전히 로드될 때까지 추가 대기
            # 공감 버튼이 나타날 때까지 기다리거나, 최소 대기 시간 확보
            try:
                # 공감 버튼이 나타날 때까지 최대 5초 대기
                selector = config.SELECTORS["feed_like_buttons"]
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            except:
                # 버튼이 없어도 페이지는 로드된 것으로 간주 (추가 대기만)
                # [수정] reason 필수 및 config 참조
                smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("페이지로딩", (1.0, 2.5)), "첫 페이지 콘텐츠 완전히 로드될 때까지 대기")
            
            return True
        except:
            return False

    def _process_like_button(self, btn):
        conf_delay = config.LIKES_NEIGHBOR_CONFIG["delays"]
        try:
            human_scroll_element(self.driver, btn)
            # [수정] reason 필수 및 config 참조
            smart_sleep(conf_delay.get("클릭전대기", (0.1, 0.3)), "공감 버튼 클릭 전 실제 사람처럼 대기")

            # 클릭하기 전 상태 저장 (방금 공감한 것과 원래 공감했던 것 구별)
            initial_state = btn.get_attribute("aria-pressed") == "true"
            
            # 진짜 이미 공감했던 글 (처음부터 true였던 경우)
            if initial_state:
                return "ALREADY"

            # 공감을 누르기 전 상태가 false였으므로, 클릭 시도
            if not smart_click(self.driver, btn):
                return "FAIL"
            
            # 클릭 후 확인: 원래 false였는데 true가 되면 SUCCESS
            # (이 경우는 방금 공감한 것이므로 로그 없이 처리됨)
            for _ in range(3):
                # [수정] reason 필수 및 config 참조
                smart_sleep(conf_delay.get("확인대기", (0.3, 0.5)), "공감 처리 결과가 서버에 반영되는지 확인 중")
                current_state = btn.get_attribute("aria-pressed") == "true"
                if current_state:
                    # 원래 false였고 지금 true가 되었으므로 방금 공감 성공
                    # initial_state가 false였으므로 이건 방금 공감한 것임
                    return "SUCCESS"
            
            return "FAIL"
        except Exception as e:
            return "ERROR"

    # [수정] URL 파라미터로 페이지 이동 (안정성 향상)
    def _move_next_page_direct(self, page_num):
        try:
            url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={page_num}"
            self.driver.get(url)
            # [수정] reason 필수 및 config 참조
            smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("페이지이동", (1.0, 2.5)), f"{page_num}페이지로 직접 이동 후 대기")
            return True
        except:
            return False