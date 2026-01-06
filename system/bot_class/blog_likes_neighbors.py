import time
from selenium.webdriver.common.by import By
from system import config
from system.utils import smart_sleep, smart_click

class BlogLikesNeighbors:
    def __init__(self, driver):
        self.driver = driver

    def go_to_blog_main(self):
        """블로그 홈(이웃새글)으로 이동"""
        try:
            print("\n[이동] 블로그 홈(이웃새글) 접속 중...")
            self.driver.get("https://section.blog.naver.com/BlogHome.naver")
            smart_sleep(config.DELAY_RANGE.get("page_load", (2.0, 3.0)), "페이지 로딩")
            return True
        except Exception as e:
            print(f"[에러] 이동 실패: {e}")
            return False

    def click_neighbor_likes(self, target_count):
        """
        목표 개수만큼 공감 클릭
        **주의: JS 클릭(강제 클릭)은 사용하지 않음 (사람처럼 보이기 위함)**
        """
        print(f"🚀 목표 공감 개수: {target_count}개")
        
        current_count = 0
        scroll_attempts = 0
        consecutive_fails = 0
        limit_fail = config.DEFAULT_FAILURE_COUNT

        like_selector = config.SELECTORS.get("like_buttons", ".u_likeit_button")

        while current_count < target_count:
            # 실패 누적이 한계치 넘으면 종료
            if consecutive_fails >= limit_fail:
                print(f"\n❌ {limit_fail}회 연속 공감 대상을 못 찾거나 클릭 실패. 작업을 중단합니다.")
                break

            # 1. 현재 화면의 공감 버튼 수집
            buttons = self.driver.find_elements(By.CSS_SELECTOR, like_selector)
            
            clicked_in_this_scroll = False

            for btn in buttons:
                if current_count >= target_count:
                    break
                
                try:
                    # '공감 안 누른 상태'인 버튼만 타겟
                    if btn.get_attribute("aria-pressed") == "false":
                        
                        # === Smart Click (물리 클릭) 시도 ===
                        if smart_click(self.driver, btn):
                            # 클릭 직후 잠시 대기 (서버 반영 시간)
                            time.sleep(1.0) 

                            # 검증: 진짜 눌렸는지 확인
                            if btn.get_attribute("aria-pressed") == "true":
                                current_count += 1
                                print(f"   ❤️  공감 성공 ({current_count}/{target_count})")
                                clicked_in_this_scroll = True
                                consecutive_fails = 0
                                
                                # 다음 행동 전 딜레이
                                smart_sleep(config.DELAY_RANGE.get("between_actions", (1.0, 2.0)))
                            else:
                                # 물리 클릭을 했는데도 반영이 안 된 경우 (렉 걸림 등)
                                print("   ⚠️ 클릭했으나 반영 안 됨 (JS 강제클릭 안함)")
                                # 실패로 간주하고 넘어감
                        else:
                            # smart_click 함수 내부에서 에러난 경우
                            print("   ⚠️ 클릭 동작 실패 (좌표 계산 불가 등)")
                except Exception:
                    continue

            if current_count >= target_count:
                break
            
            # 이번 스크롤에서 하나도 클릭 못했다면 실패 카운트 증가
            if not clicked_in_this_scroll:
                consecutive_fails += 1

            # 2. 스크롤 다운
            self.driver.execute_script("window.scrollBy(0, 2000);")
            smart_sleep(config.DELAY_RANGE.get("page_load", (1.5, 2.0)), "스크롤")
            
            scroll_attempts += 1
            if scroll_attempts > 30:
                print("   ⚠️ 스크롤 한계 도달 (피드 끝).")
                break

        print(f"\n🏁 작업 종료. 총 {current_count}개 공감 완료.")