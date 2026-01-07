# system/bot_class/blog_add_neighbor.py
import sys
import os
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click

class BlogAddNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5) # 대기 시간 조금 단축 (빠른 판단을 위해)

    def run(self, active_directory_seq, directory_no, target_count):
        """
        active_directory_seq: 대분류 ID
        directory_no: 상세 주제 ID
        target_count: 목표 성공 횟수
        """
        print(f"\n🚀 주제 [대분류:{active_directory_seq} / 상세:{directory_no}] 에서 {target_count}명 신청을 시작합니다.")
        
        current_success = 0
        consecutive_failures = 0  # 연속 실패 카운트 (시스템 보호용)
        page = 1
        
        while current_success < target_count:
            # 연속 실패가 임계치를 넘으면 봇 보호를 위해 중단
            if consecutive_failures >= config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT:
                print(f"\n❌ [경고] {config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT}회 연속으로 신청에 실패했습니다. (로직 보호 작동)")
                print("   잠시 후 다시 시도하거나, 설정을 확인해주세요. 작업을 조기 종료합니다.")
                break

            url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={directory_no}&activeDirectorySeq={active_directory_seq}&currentPage={page}"
            
            try:
                self.driver.get(url)
                smart_sleep(config.DELAY_RANGE["page_load"], f"{page}페이지 로딩")
            except:
                print("❌ 페이지 로딩 실패")
                break
            
            # 링크 수집
            links = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["theme_post_links"])
            if not links:
                print(" > 더 이상 블로그가 없습니다 (마지막 페이지).")
                break
                
            print(f" > {page}페이지 발견된 블로그: {len(links)}개")
            
            main_window = self.driver.current_window_handle
            
            for i, link in enumerate(links):
                if current_success >= target_count:
                    break
                if consecutive_failures >= config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT:
                    break
                
                print(f"\n[{i+1}/{len(links)}] 블로그 방문 시도... (현재 성공: {current_success}명)")
                
                # --- [핵심 로직] ---
                # 성공하면 True, 실패/스킵하면 False
                result = self._process_one_blog(link, main_window)
                
                if result:
                    current_success += 1
                    consecutive_failures = 0 # 성공하면 실패 카운트 리셋
                    print(f" > 🎉 신청 완료! (총 {current_success}/{target_count})")
                    smart_sleep(config.DELAY_RANGE["between_actions"])
                else:
                    consecutive_failures += 1
                    print(f" > ⚠️ 실패/스킵 처리되었습니다. (연속 실패: {consecutive_failures})")
                    # 실패했어도 바로 다음 사람으로 넘어갑니다. (재시도 안 함)
                # -------------------
            
            page += 1

        print(f"\n🏁 작업 종료. 총 {current_success}명 신청 성공.")

    def _process_one_blog(self, link_element, main_window):
        """
        단일 블로그에 대해: 방문 -> 이웃추가 버튼 -> 팝업 처리 -> 결과 확인
        하나라도 삐끗하면 즉시 False 반환 (창 닫기 포함)
        """
        try:
            # 1. 블로그 새 창 열기
            smart_click(self.driver, link_element)
            smart_sleep(config.DELAY_RANGE["window_switch"])
            
            if len(self.driver.window_handles) == 1:
                print("   [실패] 새 창이 열리지 않음")
                return False
            
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 2. 이웃추가 시도
            is_success = self._try_add_neighbor_flow()
            
            # 3. 창 닫기 및 복귀
            if self.driver.current_window_handle != main_window:
                self.driver.close()
            self.driver.switch_to.window(main_window)
            
            return is_success

        except Exception as e:
            print(f"   [에러] 프로세스 중 예외 발생: {e}")
            # 에러 발생 시 안전하게 창 닫기 시도
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(main_window)
            except:
                pass
            return False

    def _try_add_neighbor_flow(self):
        """
        실제 이웃 추가 로직 (버튼 찾기 -> 팝업 -> 성공확인)
        성공 시 True, 그 외 모든 경우 False
        """
        try:
            # 1. '이웃추가' 버튼 찾기 (iframe 대응)
            btn = self._find_element_safe(config.SELECTORS["add_neighbor_btn"])
            
            if not btn:
                print("   [패스] 이웃추가 버튼을 찾을 수 없습니다.")
                return False
                
            btn_text = btn.text.strip()
            # 이미 '서로이웃' 상태인 경우 등의 텍스트 필터링
            if "서로이웃" in btn_text and "신청" not in btn_text and "해요" not in btn_text: 
                # 버튼 텍스트가 '서로이웃'이면 이미 맺어진 상태일 확률 높음
                print("   [패스] 이미 서로이웃 관계입니다.")
                return False

            # 2. 버튼 클릭 (팝업 오픈)
            blog_window = self.driver.current_window_handle
            smart_click(self.driver, btn)
            smart_sleep(config.DELAY_RANGE["window_switch"], "팝업 대기")
            
            # 3. 팝업창 제어
            all_windows = self.driver.window_handles
            if len(all_windows) > 2: # 메인, 블로그, 팝업
                self.driver.switch_to.window(all_windows[-1])
                
                # 팝업 내부 로직 수행
                result = self._handle_popup_steps()
                
                # 팝업 닫기 (성공했든 실패했든 팝업창은 닫고 블로그창으로 돌아가야 함)
                try:
                    self.driver.close() 
                except: 
                    pass
                self.driver.switch_to.window(blog_window)
                
                return result
            else:
                # 팝업이 안 뜨고 alert(경고창)이 뜨는 경우 (예: 차단, 제한 등)
                try:
                    alert = self.driver.switch_to.alert
                    print(f"   [알림] 팝업 대신 경고창 발생: {alert.text}")
                    alert.accept()
                except:
                    print("   [실패] 팝업이 뜨지 않았습니다.")
                return False

        except Exception as e:
            print(f"   [로직 에러] {e}")
            return False

    def _handle_popup_steps(self):
        """
        팝업 내부 단계별 진행:
        라디오버튼 선택 -> (다음) -> 메시지 입력 -> (확인) -> 최종 텍스트 검증
        """
        try:
            smart_sleep(config.DELAY_RANGE.get("popup_step_wait", (0.5, 1.0)))

            # [Step 1] 서로이웃 라디오 버튼 선택
            # 이 단계에서 서로이웃 버튼이 없거나 비활성화면 실패 처리
            try:
                radio_mutual = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_radio_mutual_label"])
                smart_click(self.driver, radio_mutual)
                smart_sleep(config.DELAY_RANGE.get("popup_interaction", (0.3, 0.5)))
            except:
                print("   [실패] '서로이웃' 선택 불가 (이웃만 가능하거나 차단됨)")
                return False

            # [Step 2] '다음' 버튼 처리 (중간 단계가 있는 경우)
            # 바로 메시지창이 뜨는 경우도 있으므로 없으면 넘어감 (Exception 아님)
            try:
                next_btns = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_next_btn"])
                for btn in next_btns:
                    if btn.is_displayed() and ("다음" in btn.text or "확인" in btn.text):
                        # 메시지 입력창이 아직 안 떴을 때만 누름
                        if not self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"]):
                            smart_click(self.driver, btn)
                            smart_sleep(config.DELAY_RANGE.get("popup_form_load", (0.5, 1.0)))
                        break
            except:
                pass

            # [Step 3] 메시지 입력
            try:
                msg_input = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"])
                msg_input.clear()
                rand_msg = random.choice(config.NEIGHBOR_CONFIG["messages"])
                msg_input.send_keys(rand_msg)
                smart_sleep(config.DELAY_RANGE.get("popup_typing", (0.5, 1.0)))
            except:
                print("   [실패] 메시지 입력창을 찾을 수 없습니다.")
                return False

            # [Step 4] 최종 전송/확인 버튼 클릭
            clicked_submit = False
            try:
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_submit_btn"])
                for btn in submit_btns:
                    if btn.is_displayed():
                        smart_click(self.driver, btn)
                        clicked_submit = True
                        smart_sleep(config.DELAY_RANGE.get("popup_submit", (1.0, 1.5)))
                        break
            except:
                pass

            if not clicked_submit:
                print("   [실패] 전송 버튼을 누르지 못했습니다.")
                return False

            # [Step 5] ★ 최종 성공 검증 (사용자가 가장 중요하게 생각하는 부분)
            # "신청하였습니다" 같은 텍스트가 페이지 소스에 포함되어 있는지 확인
            page_source = self.driver.page_source
            if "신청하였습니다" in page_source or "신청을 완료" in page_source:
                return True
            else:
                # 팝업이 닫혀버렸는데 에러가 없으면 성공일 수도 있지만, 
                # 확실한 텍스트 확인이 안되면 실패로 간주하라는 요청에 따름
                # 다만 네이버는 성공 시 보통 팝업 내용이 바뀜.
                print("   [미확인] 성공 메시지를 확인하지 못했습니다.")
                return False

        except Exception as e:
            print(f"   [팝업 에러] {e}")
            return False

    def _find_element_safe(self, selector):
        """Iframe 내외부를 오가며 요소 찾기"""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            try:
                self.driver.switch_to.frame("mainFrame")
                return self.driver.find_element(By.CSS_SELECTOR, selector)
            except:
                return None