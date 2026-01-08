# system/bot_class/blog_add_neighbor.py
import sys
import os
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 상위 폴더(system)의 모듈을 불러오기 위한 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import config
from utils import smart_sleep, smart_click

class BlogAddNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    def run(self, active_directory_seq, directory_no, target_count, start_page=1):
        print(f"\n🚀 주제 [대분류:{active_directory_seq} / 상세:{directory_no}]")
        print(f"🚀 {start_page}페이지부터 시작하여 {target_count}명 신청을 진행합니다.")
        
        # 설정값 로드
        cond = getattr(config, "NEIGHBOR_CONDITION", {})
        max_l = cond.get("max_likes", 100)
        max_c = cond.get("max_comments", 10)
        
        print(f"   (필터 조건: 공감 {max_l}개 이하 AND 댓글 {max_c}개 이하인 글만 방문)")
        
        current_success = 0
        consecutive_failures = 0
        page = start_page
        
        while current_success < target_count:
            if consecutive_failures >= config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT:
                print(f"\n❌ [경고] {config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT}회 연속 실패로 작업을 조기 종료합니다.")
                break

            url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={directory_no}&activeDirectorySeq={active_directory_seq}&currentPage={page}"
            
            try:
                self.driver.get(url)
                smart_sleep(config.DELAY_RANGE["page_load"], f"{page}페이지 로딩")
            except:
                print("❌ 페이지 로딩 실패")
                break
            
            # 리스트 컨테이너 가져오기
            containers = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS.get("theme_post_container", "div.info_post"))
            
            if not containers:
                print(" > 더 이상 블로그가 없습니다 (마지막 페이지).")
                break
            
            main_window = self.driver.current_window_handle
            
            for i, container in enumerate(containers):
                if current_success >= target_count: break
                if consecutive_failures >= config.DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT: break
                
                # 1. 정보 분석
                nick = self._get_child_text(container, config.SELECTORS.get("post_list_nickname", ".name_author"), "알수없음")
                likes_str = self._get_child_text(container, config.SELECTORS.get("post_list_like_count", ".like em"), "0")
                comments_str = self._get_child_text(container, config.SELECTORS.get("post_list_comment_count", ".reply em"), "0")
                
                likes = self._parse_number(likes_str)
                comments = self._parse_number(comments_str)
                
                # [로그 형식 수정] 요청하신 헤더 스타일 적용
                print(f"\n[시도 {current_success}/{target_count}] [연속 오류 횟수: {consecutive_failures}] 블로거 : {nick}")
                print(f"   > [분석] 공감: {likes} | 댓글: {comments}")

                # 2. 조건 체크
                check_likes = (max_l == 0) or (likes <= max_l)
                check_comments = (max_c == 0) or (comments <= max_c)

                result = "ALREADY" # 기본값

                if check_likes and check_comments:
                    print(f"   > ✅ 조건 충족! 블로그 방문을 시도합니다.")
                    
                    try:
                        link_element = container.find_element(By.CSS_SELECTOR, config.SELECTORS["theme_post_links"])
                        # 방문 로직 수행
                        result = self._process_one_blog(link_element, main_window)
                    except Exception as e:
                        print(f"   > ⚠️ 링크 클릭 불가 또는 찾기 실패 ({e})")
                        result = "FAIL"
                else:
                    print(f"   > ⏭️ 조건 미달(인기 블로그 등)로 스킵합니다.")
                    result = "ALREADY"
                
                # 3. 결과 처리
                if result == "SUCCESS":
                    current_success += 1
                    consecutive_failures = 0
                    print(f"   > 🎉 이웃 신청 완료!")
                    smart_sleep(config.DELAY_RANGE["between_actions"])
                    
                elif result == "ALREADY":
                    # 상세 로그는 _process_one_blog 내부 또는 조건 체크에서 이미 출력됨
                    consecutive_failures = 0 
                
                else: # FAIL
                    consecutive_failures += 1
                    print(f"   > ⚠️ 실패 처리되었습니다.")

            page += 1


        print(f"\n 🏁 [대분류:{active_directory_seq} / 상세:{directory_no}] {page} 페이지에서 작업 종료. 총 {current_success}명 신청 성공")

    def _get_child_text(self, parent_element, selector, default_text):
        try:
            child = parent_element.find_element(By.CSS_SELECTOR, selector)
            return child.text.strip()
        except:
            return default_text

    def _parse_number(self, text):
        try:
            nums = re.findall(r'\d+', text.replace(',', ''))
            return int(nums[0]) if nums else 0
        except:
            return 0

    def _process_one_blog(self, link_element, main_window):
        try:
            smart_click(self.driver, link_element)
            smart_sleep(config.DELAY_RANGE["window_switch"])
            
            if len(self.driver.window_handles) == 1:
                return "FAIL"
            
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 이웃추가 흐름 실행
            result_status = self._try_add_neighbor_flow()
            
            # 메인 창이 아니면 닫기
            try:
                if self.driver.current_window_handle != main_window:
                    self.driver.close()
            except: pass

            self.driver.switch_to.window(main_window)
            return result_status

        except Exception as e:
            try:
                if len(self.driver.window_handles) > 1: self.driver.close()
                self.driver.switch_to.window(main_window)
            except: pass
            return "FAIL"

    def _try_add_neighbor_flow(self):
        """
        이웃 추가 버튼 클릭부터 팝업 처리까지의 흐름
        [로그 복구] 이미 이웃, 신청 중 등의 사유를 명확히 출력
        """
        try:
            # 1. 버튼 찾기
            btn = self._find_element_safe(config.SELECTORS["add_neighbor_btn"])
            if not btn:
                print("   > [패스] 이웃추가 버튼이 없습니다. (이미 이웃이거나 버튼 미노출)")
                return "FAIL"
                
            # 2. 버튼 텍스트/클래스 확인 (이미 이웃 여부)
            btn_text = btn.text.strip()
            btn_class = btn.get_attribute("class") or ""
            
            if "서로이웃" in btn_text and "_rosRestrictAll" in btn_class:
                print(f"   > [패스] 이미 '서로이웃' 상태입니다.")
                return "ALREADY"

            # 3. 버튼 클릭
            blog_window = self.driver.current_window_handle
            smart_click(self.driver, btn)
            smart_sleep(config.DELAY_RANGE["window_switch"], "팝업 대기")
            
            # 4. 알림창(Alert) 확인 - 이미 신청 중인 경우 등
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                
                if "진행" in alert_text or "이미 신청" in alert_text:
                    print(f"   > [패스] 이미 신청을 보낸 상태입니다. (알림: {alert_text})")
                    return "ALREADY"
                else:
                    print(f"   > [알림] 경고창 발생: {alert_text}")
                    return "FAIL"
            except:
                pass # 알림 없으면 정상 진행

            # 5. 팝업창 핸들링
            all_windows = self.driver.window_handles
            if len(all_windows) > 2: 
                self.driver.switch_to.window(all_windows[-1])
                final_result = self._handle_popup_steps()
                
                # 팝업 닫기
                try: self.driver.close() 
                except: pass
                
                # 블로그 창 복귀
                try: self.driver.switch_to.window(blog_window)
                except: pass
                
                return final_result
            else:
                print("   > [실패] 팝업창이 뜨지 않았습니다.")
                return "FAIL"

        except Exception as e:
            print(f"   > [에러] 로직 수행 중 오류: {e}")
            return "FAIL"

    def _handle_popup_steps(self):
        """팝업 내부 로직"""
        try:
            smart_sleep(config.DELAY_RANGE.get("popup_step_wait", (0.5, 1.0)))

            # [Step 1] 서로이웃 라디오 버튼 선택
            try:
                radio_mutual = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_radio_mutual_label"])
                smart_click(self.driver, radio_mutual)
            except:
                print("   > [패스] '서로이웃' 신청 옵션이 없습니다. (이웃만 가능)")
                return "ALREADY"

            # [Step 2] 다음 버튼 클릭 (메시지 입력창 나오게 하기)
            try:
                next_btns = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_next_btn"])
                for btn in next_btns:
                    if btn.is_displayed():
                        # 메시지 입력창이 아직 없으면 '다음' 클릭
                        if not self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"]):
                            smart_click(self.driver, btn)
                            smart_sleep(config.DELAY_RANGE.get("popup_form_load", (0.5, 1.0)))
                            
                            # '다음' 클릭 후 알림창 체크
                            try:
                                alert = self.driver.switch_to.alert
                                txt = alert.text
                                alert.accept()
                                if "진행" in txt or "신청" in txt:
                                    print(f"   > [패스] 이미 신청 진행 중입니다.")
                                    return "ALREADY"
                            except: pass
                        break
            except: pass

            # [Step 3] 메시지 입력
            try:
                msg_input = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"])
                msg_input.clear()
                rand_msg = random.choice(config.NEIGHBOR_CONFIG["messages"])
                msg_input.send_keys(rand_msg)
                print(f"   > 💬 메시지 작성: {rand_msg}") 
                smart_sleep(config.DELAY_RANGE.get("popup_typing", (0.2, 0.5)))
            except: 
                print("   > [실패] 메시지 입력창을 찾을 수 없습니다.")
                return "FAIL"

            # [Step 4] 전송 버튼 클릭
            clicked = False
            try:
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_submit_btn"])
                for btn in submit_btns:
                    if btn.is_displayed():
                        smart_click(self.driver, btn)
                        clicked = True
                        smart_sleep(config.DELAY_RANGE.get("popup_submit", (1.0, 1.5)))
                        break
            except: pass
            
            if not clicked: 
                print("   > [실패] 전송 버튼을 누르지 못했습니다.")
                return "FAIL"

            # [Step 5] 최종 확인
            if "신청" in self.driver.page_source:
                return "SUCCESS"
            
            return "FAIL"

        except Exception as e:
            print(f"   > [팝업 에러] {e}")
            return "FAIL"

    def _find_element_safe(self, selector):
        try: return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            try:
                self.driver.switch_to.frame("mainFrame")
                return self.driver.find_element(By.CSS_SELECTOR, selector)
            except: return None