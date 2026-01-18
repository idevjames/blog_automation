import sys
import os
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 상위 폴더(system)의 모듈을 불러오기 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import config
from utils import smart_sleep, smart_click, human_typing

class BlogAddNeighbor:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)
        self.worker = None

    def run(self, active_directory_seq, directory_no, target_count, start_page=1):
        """메인 실행 함수"""
        self._print_start_info(active_directory_seq, directory_no, target_count, start_page)
        
        # [수정] ADD_NEIGHBOR_CONFIG 참조
        conf = config.ADD_NEIGHBOR_CONFIG
        max_likes, max_comments = self._load_conditions(conf)
        fail_limit = conf["conditions"].get("최대실패횟수", 10)
        
        current_success = 0
        consecutive_failures = 0
        page = start_page
        
        while current_success < target_count:
            # [추가 작업 1] 루프 시작 시 중단 신호 체크
            if self.worker and self.worker.is_stopped:
                print("\n🛑 [중단] 사용자에 의해 작업이 중단되었습니다.")
                break

            if self._should_stop_due_to_failures(consecutive_failures, fail_limit):
                break
            
            if not self._load_page(active_directory_seq, directory_no, page):
                break
            
            containers = self._get_blog_containers()
            if not containers:
                break
            
            main_window = self.driver.current_window_handle
            
            for container in containers:
                # [추가 작업 2] 블로그 개별 처리 전 중단 신호 체크
                if self.worker and self.worker.is_stopped:
                    return

                if self._should_stop_processing(current_success, target_count, consecutive_failures, fail_limit):
                    break
                
                blog_info = self._analyze_blog_info(container)
                self._print_blog_info(blog_info, current_success, target_count, consecutive_failures)
                
                if self._check_conditions(blog_info, max_likes, max_comments):
                    result = self._process_blog(container, main_window)
                else:
                    result = "ALREADY"
                
                current_success, consecutive_failures, should_exit = self._handle_result(
                    result, current_success, consecutive_failures
                )
                
                # 이웃 추가 제한에 도달한 경우 즉시 종료
                if should_exit:
                    print(f"\n🛑 이웃 추가 제한으로 인해 작업을 즉시 종료합니다.")
                    return
            
            page += 1
        
        self._print_finish_info(active_directory_seq, directory_no, page, current_success)
    
    def _print_start_info(self, active_directory_seq, directory_no, target_count, start_page):
        """작업 시작 정보 출력"""
        print(f"\n🚀 주제 [대분류:{active_directory_seq} / 상세:{directory_no}]")
        print(f"🚀 {start_page}페이지부터 시작하여 {target_count}명 신청을 진행합니다.")
    
    def _load_conditions(self, conf):
        """작업 조건 로드"""
        # [수정] ADD_NEIGHBOR_CONFIG 참조
        cond = conf["conditions"]
        max_l = cond.get("최대공감수제한", 100)
        max_c = cond.get("최대댓글수제한", 10)
        print(f"   (필터 조건: 공감 {max_l}개 이하 AND 댓글 {max_c}개 이하인 글만 방문)")
        return max_l, max_c
    
    def _should_stop_due_to_failures(self, consecutive_failures, fail_limit):
        """연속 실패로 인한 중단 여부 확인"""
        if consecutive_failures >= fail_limit:
            print(f"\n❌ [경고] {fail_limit}회 연속 실패로 작업을 조기 종료합니다.")
            return True
        return False
    
    def _load_page(self, active_directory_seq, directory_no, page):
        """페이지 로딩"""
        url = f"https://section.blog.naver.com/ThemePost.naver?directoryNo={directory_no}&activeDirectorySeq={active_directory_seq}&currentPage={page}"
        try:
            self.driver.get(url)
            # [수정] reason 필수 및 ADD_NEIGHBOR_CONFIG 참조
            smart_sleep(config.ADD_NEIGHBOR_CONFIG["delays"].get("목록페이지로딩", (1.0, 2.5)), f"{page}페이지 주제별 목록 로딩 대기")
            return True
        except:
            print("❌ 페이지 로딩 실패")
            return False
    
    def _get_blog_containers(self):
        """블로그 컨테이너 목록 가져오기"""
        selector = config.SELECTORS.get("theme_post_container", "div.info_post")
        containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
        if not containers:
            print(" > 더 이상 블로그가 없습니다 (마지막 페이지).")
        return containers
    
    def _should_stop_processing(self, current_success, target_count, consecutive_failures, fail_limit):
        """처리 중단 여부 확인"""
        return (current_success >= target_count or 
                consecutive_failures >= fail_limit)
    
    def _analyze_blog_info(self, container):
        """블로그 정보 분석"""
        nick_selector = config.SELECTORS.get("post_list_nickname", ".name_author")
        nick = self._get_child_text(container, nick_selector, "알수없음")
        
        likes_selector = config.SELECTORS.get("post_list_like_count", ".like em")
        likes_str = self._get_child_text(container, likes_selector, "0")
        
        comments_selector = config.SELECTORS.get("post_list_comment_count", ".reply em")
        comments_str = self._get_child_text(container, comments_selector, "0")
        
        likes = self._parse_number(likes_str)
        comments = self._parse_number(comments_str)
        
        return {
            "nickname": nick,
            "likes": likes,
            "comments": comments
        }
    
    def _check_element_exists(self, parent_element, selector):
        """요소 존재 여부 확인"""
        try:
            parent_element.find_element(By.CSS_SELECTOR, selector)
            return True
        except:
            return False
    
    def _print_blog_info(self, blog_info, current_success, target_count, consecutive_failures):
        """블로그 정보 출력"""
        print(f"\n[시도 {current_success}/{target_count}] [연속 오류 횟수: {consecutive_failures}] 블로거 : {blog_info['nickname']}")
        print(f"   > [분석] 공감: {blog_info['likes']} | 댓글: {blog_info['comments']}")
    
    def _check_conditions(self, blog_info, max_likes, max_comments):
        """블로그 조건 체크"""
        check_likes = (max_likes == 0) or (blog_info['likes'] <= max_likes)
        check_comments = (max_comments == 0) or (blog_info['comments'] <= max_comments)
        
        if check_likes and check_comments:
            print(f"   > ✅ 조건 충족! 블로그 방문을 시도합니다.")
            return True
        else:
            print(f"   > ⏭️ 조건 미달(인기 블로그 등)로 스킵합니다.")
            return False
    
    def _process_blog(self, container, main_window):
        """블로그 방문 및 처리"""
        try:
            selector = config.SELECTORS["theme_post_links"]
            link_element = container.find_element(By.CSS_SELECTOR, selector)
            result = self._process_one_blog(link_element, main_window)
            
            # 이웃 추가 제한에 도달한 경우 즉시 종료
            if result == "LIMIT_REACHED":
                return result
            
            return result
        except Exception as e:
            print(f"   > ⚠️ 링크 클릭 불가 또는 찾기 실패 ({e})")
            return "FAIL"
    
    def _handle_result(self, result, current_success, consecutive_failures):
        """결과 처리 및 상태 업데이트"""
        conf_delay = config.ADD_NEIGHBOR_CONFIG["delays"]
        if result == "LIMIT_REACHED":
            # 이웃 추가 제한에 도달 - 즉시 종료를 위해 특별한 값 반환
            return current_success, consecutive_failures, True  # (success, failures, should_exit)
        elif result == "SUCCESS":
            current_success += 1
            consecutive_failures = 0
            print(f"   > 🎉 이웃 신청 완료!")
            # [수정] reason 필수 및 ADD_NEIGHBOR_CONFIG 참조
            smart_sleep(conf_delay.get("블로그간대기", (0.2, 0.5)), "신청 성공 후 다음 블로그 방문 전 대기")
        elif result == "ALREADY":
            consecutive_failures = 0
        else:  # FAIL
            consecutive_failures += 1
            print(f"   > ⚠️ 실패 처리되었습니다.")
            # [수정] reason 필수 및 ADD_NEIGHBOR_CONFIG 참조
            smart_sleep(conf_delay.get("재시도대기", (0.5, 1.0)), "실패 후 안정화를 위한 재시도 대기")
        
        return current_success, consecutive_failures, False  # (success, failures, should_exit)
    
    def _check_limit_reached(self, text):
        """이웃 추가 제한 메시지 확인"""
        if not text:
            return False
        
        limit_keywords = [
            "더 이상 이웃을 추가할 수 없습니다",
            "1일동안 추가할 수 있는 이웃수",
            "추가할 수 있는 이웃수를 제한",
            "해당 그룹에 더 이상",
            "다른 그룹을 선택해주세요",
        ]
        
        for keyword in limit_keywords:
            if keyword in text:
                print(f"\n❌ [중단] 이웃 추가 제한에 도달했습니다.")
                print(f"   메시지: {text[:100]}...")
                return True
        
        return False
    
    def _print_finish_info(self, active_directory_seq, directory_no, page, current_success):
        """작업 완료 정보 출력"""
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

    # [수정] 결과 처리 로직 개선: 공감/댓글 실패가 서이추 성공 결과에 영향을 주지 않도록 변경
    def _process_one_blog(self, link_element, main_window):
        conf_delay = config.ADD_NEIGHBOR_CONFIG["delays"]
        try:
            # 링크 클릭 및 새 창 전환
            smart_click(self.driver, link_element)
            # [수정] reason 필수 및 ADD_NEIGHBOR_CONFIG 참조
            smart_sleep(conf_delay.get("팝업창대기", (1.0, 2.0)), "블로그 상세 페이지 로딩 대기")
            
            if len(self.driver.window_handles) == 1:
                return "FAIL"
            
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 1. 서로이웃 신청 흐름 실행
            result_status = self._try_add_neighbor_flow()
            
            # 2. 서이추 성공 시에만 공감/댓글 시도 (실패해도 서이추 결과는 유지)
            if result_status == "SUCCESS":
                try:
                    self._add_like_and_comment()
                except Exception as e:
                    print(f"   > [댓글 오류 무시] {e}")
            
            # 3. 창 닫기 및 복귀
            try:
                if self.driver.current_window_handle != main_window:
                    self.driver.close()
            except:
                pass

            self.driver.switch_to.window(main_window)
            return result_status

        except Exception as e:
            print(f"   > [치명적 오류] {e}")
            # 창 닫기 시도
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(main_window)
            except:
                pass
            return "FAIL"

    def _try_add_neighbor_flow(self):
        """이웃 추가 버튼 클릭부터 팝업 처리까지의 흐름"""
        conf_delay = config.ADD_NEIGHBOR_CONFIG["delays"]
        try:
            # 1. 버튼 찾기
            selector = config.SELECTORS["add_neighbor_btn"]
            btn = self._find_element_safe(selector)
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
            # [수정] reason 필수 및 전용 딜레이 참조
            smart_sleep(conf_delay.get("팝업창대기", (1.0, 2.0)), "이웃 신청 팝업 대기")
            
            # 4. 알림창(Alert) 확인 - 이미 신청 중인 경우 등
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                
                # 이웃 추가 제한 메시지 체크
                if self._check_limit_reached(alert_text):
                    return "LIMIT_REACHED"
                
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
        conf_delay = config.ADD_NEIGHBOR_CONFIG["delays"]
        try:
            # 팝업창 내부 텍스트에서 제한 메시지 체크
            page_text = self.driver.page_source
            if self._check_limit_reached(page_text):
                return "LIMIT_REACHED"
            
            # [수정] reason 필수 및 전용 딜레이 참조
            smart_sleep(conf_delay.get("팝업초기대기", (0.2, 0.5)), "팝업창 내용 로딩 대기")

            # [Step 1] 서로이웃 라디오 버튼 선택
            try:
                selector = config.SELECTORS["popup_radio_mutual_label"]
                radio_mutual = self.driver.find_element(By.CSS_SELECTOR, selector)
                smart_click(self.driver, radio_mutual)
                # [수정] reason 필수 및 전용 딜레이 참조
                smart_sleep(conf_delay.get("팝업작업대기", (0.2, 0.5)), "서로이웃 라디오 버튼 클릭 후 대기")
            except:
                print("   > [패스] '서로이웃' 신청 옵션이 없습니다. (이웃만 가능)")
                return "ALREADY"

            # [Step 2] 다음 버튼 클릭 (메시지 입력창 나오게 하기)
            try:
                selector = config.SELECTORS["popup_next_btn"]
                next_btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in next_btns:
                    if btn.is_displayed():
                        # 메시지 입력창이 아직 없으면 '다음' 클릭
                        if not self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["popup_message_input"]):
                            smart_click(self.driver, btn)
                            # [수정] reason 필수 및 전용 딜레이 참조
                            smart_sleep(conf_delay.get("메시지창전환대기", (1.5, 2.0)), "메시지 입력폼 전환 대기")
                            
                            # '다음' 클릭 후 알림창 체크
                            try:
                                alert = self.driver.switch_to.alert
                                txt = alert.text
                                alert.accept()
                                if self._check_limit_reached(txt):
                                    return "LIMIT_REACHED"
                                if "진행" in txt or "신청" in txt:
                                    print(f"   > [패스] 이미 신청 진행 중입니다.")
                                    return "ALREADY"
                            except: pass
                        break
            except: pass

            # [Step 3] 메시지 입력 (human_typing 적용)
            try:
                selector = config.SELECTORS["popup_message_input"]
                msg_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                msg_input.clear()
                rand_msg = random.choice(config.ADD_NEIGHBOR_CONFIG["messages"])
                print(f"   > 💬 서이추 메시지 타이핑: {rand_msg}")
                human_typing(msg_input, rand_msg) 
                smart_sleep(conf_delay.get("메시지입력후대기", (0.2, 0.5)), "메시지 작성 후 검토 대기")
            except: 
                print("   > [실패] 메시지 입력창을 찾을 수 없습니다.")
                return "FAIL"

            # [Step 4] 전송 버튼 클릭
            clicked = False
            try:
                selector = config.SELECTORS["popup_submit_btn"]
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in submit_btns:
                    if btn.is_displayed():
                        smart_click(self.driver, btn)
                        clicked = True
                        smart_sleep(conf_delay.get("전송후대기", (1.0, 2.0)), "최종 신청 전송 완료 대기")
                        try:
                            alert = self.driver.switch_to.alert
                            alert_text = alert.text
                            if self._check_limit_reached(alert_text):
                                alert.accept()
                                return "LIMIT_REACHED"
                            alert.accept()
                        except: pass
                        break
            except: pass
            
            if not clicked: 
                print("   > [실패] 전송 버튼을 누르지 못했습니다.")
                return "FAIL"

            return "SUCCESS"

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
    
    def _add_like_and_comment(self):
        """공감 및 댓글 일괄 처리 (human_typing 적용)"""
        conf_delay = config.ADD_NEIGHBOR_CONFIG["delays"]
        print("   > [작업] 공감 및 댓글 작성을 시작합니다.")
        
        try:
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            
            # 스크롤 수행
            scroll_ratio = conf_delay.get("스크롤최대비율", 0.8)
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_ratio});")
            smart_sleep(conf_delay.get("스크롤대기", (0.5, 1.0)), "공감/댓글 영역 노출을 위한 스크롤 대기")

            try:
                container = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["floating_container"])
            except:
                container = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["static_container"])

            # --- [STEP A] 공감하기 ---
            try:
                like_btn = container.find_element(By.CSS_SELECTOR, config.SELECTORS["like_button_face"])
                btn_class = like_btn.get_attribute("class") or ""
                if "off" in btn_class.split():
                    smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("클릭전대기", (0.1, 0.3)), "공감 클릭 전 대기")
                    smart_click(self.driver, like_btn)
                    print("   > 👍 공감 완료")
                    smart_sleep(config.LIKES_NEIGHBOR_CONFIG["delays"].get("작업간대기", (0.2, 0.5)), "공감 완료 후 휴식")
                else:
                    print("   > [패스] 이미 공감함")
            except Exception as e:
                print(f"   > [공감 실패] {e}")

            # --- [STEP B] 댓글 달기 ---
            try:
                comment_btn = container.find_element(By.CSS_SELECTOR, config.SELECTORS["post_view_comment_button"])
                smart_click(self.driver, comment_btn)
                input_sel = config.SELECTORS["comment_text_area"]
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, input_sel)))
                smart_sleep(conf_delay.get("댓글창대기", (1.5, 2.0)), "댓글 입력창 가시성 대기")

                # 실제 입력창 타이핑
                comment_input = self.driver.find_element(By.CSS_SELECTOR, input_sel)
                smart_click(self.driver, comment_input)
                
                comment_msg = random.choice(config.ADD_NEIGHBOR_CONFIG["comments"])
                print(f"   > 💬 댓글 타이핑: {comment_msg}")
                human_typing(comment_input, comment_msg) 
                
                smart_sleep(conf_delay.get("메시지입력후대기", (0.2, 0.5)), "댓글 입력 완료 후 대기")
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["comment_submit_button"])
                smart_click(self.driver, submit_btn)
                print("   > ✅ 댓글 등록 완료")
                smart_sleep(conf_delay.get("목록페이지로딩", (1.0, 2.5)), "댓글 등록 완료 후 안정화 대기")
            except Exception as e:
                print(f"   > [댓글 실패] {e}")

        except Exception as e:
            print(f"   > [통합 작업 에러] {e}")
        finally:
            self.driver.switch_to.default_content()