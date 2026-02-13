import re
import time
import random
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ai_helper import GeminiHelper
from bot_class.db_manager import BlogDB
import config
from ____utils import human_scroll_distance, human_scroll_element, smart_sleep, smart_click, human_typing

class BlogSmartNeighborManagement:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.worker = None
        self.db = BlogDB()
        self.temp_neighbor_stats = {}
        # cached_ranking_map: 1단계 분석 후 랭킹 정보를 담아두는 곳
        self.cached_ranking_map = {} 

    def check_stopped(self):
        """작업 중단 여부 확인"""
        if self.worker and self.worker.is_stopped:
            return True
        return False

    def _parse_relative_time(self, time_text):
        """
        네이버 알림 시간 텍스트를 현재 시스템 시간(캐나다/한국) 기준 datetime으로 변환
        - 날짜 포맷(YYYY.MM.DD)은 24시간 경과로 간주하여 None 반환
        """
        now = datetime.now()
        txt = time_text.strip()
        
        try:
            # 1. 날짜 포맷 처리 (예: 2026. 1. 27.)
            # 정규식으로 '숫자. 숫자. 숫자' 패턴 확인
            if re.search(r'\d{4}\.\s*\d{1,2}\.\s*\d{1,2}', txt):
                nums = re.findall(r'\d+', txt)
                if len(nums) >= 3:
                    # 시간 정보가 없으므로 00:00:00으로 설정
                    # -> 마지막 스캔 시간이 15:00였다면, 00:00 <= 15:00 이 되어 '과거'로 판단됨 (중복 방지)
                    return datetime(int(nums[0]), int(nums[1]), int(nums[2]))
                return None

            # 2. 상대 시간 처리
            if "방금 전" in txt:
                return now
            elif "분 전" in txt:
                minutes = int(re.sub(r'[^0-9]', '', txt))
                return now - timedelta(minutes=minutes)
            elif "시간 전" in txt:
                hours = int(re.sub(r'[^0-9]', '', txt))
                return now - timedelta(hours=hours)
            
            # '어제'는 나오지 않는다는 전제하에 로직 제거, 그 외 알 수 없는 포맷은 None
            return None
        except:
            return None

    def run(self, params=None):
        """스마트 이웃 관리 메인 루프 (Phase 1 -> Phase 2)"""
        config.sync_all_configs()
        
        # [Phase 1] 알림 분석 및 DB 동기화
        if not self._phase_1_analysis():
            return

        if self.check_stopped(): 
            return
        
        # [Phase 2] 스마트 답방 실행
        self._phase_2_action(params)

    def _phase_1_analysis(self):
        """[Phase 1] 알림 분석 (Strict Time Cutoff 적용)"""
        try:
            # 설정값 로드
            cond = config.SMART_NEIGHBOR_CONFIG.get("conditions", {})
            
            # 1. 마지막 스캔 시간 로드
            last_scan_time = self.db.get_last_scan_time()
            current_scan_start_time = datetime.now() # 이번 스캔 시작 시간
            
            print(f"\n🕒 [기준 시각] {last_scan_time.strftime('%Y-%m-%d %H:%M:%S')} 이후 알림만 수집합니다.")

            self.driver.get("https://m.blog.naver.com/News.naver")
            smart_sleep((2.0, 3.0), "알림 페이지 로딩")

            new_stats = {}
            is_scan_finished = False
            consecutive_empty_count = 0
            processed_count = 0

            print(f"\n📡 [1단계] 데이터 증분 수집 시작...")

            while not is_scan_finished: 
                if self.check_stopped(): return False
                
                # 1. 전체 카드 로드
                all_cards = self.driver.find_elements(By.CSS_SELECTOR, "li[class*='item']")
                
                # 2. 증분 처리
                new_batch = all_cards[processed_count:]

                # --- [분기 A] 새로운 배치가 없을 때 (스크롤 또는 종료 판단) ---
                if not new_batch:
                    # (1) UI 바닥 체크
                    try:
                        footer = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='scroll_top']")
                        if footer and footer[0].is_displayed():
                            print(f"\n🛑 [종료 사유] '맨 위로' 버튼(UI) 발견 -> 페이지 바닥 도착")
                            is_scan_finished = True
                            break
                    except: pass

                    # (2) 연속 실패 카운트
                    consecutive_empty_count += 1
                    if consecutive_empty_count >= 5:
                        print(f"\n⚠️ [종료 사유] 5회 연속 데이터 로드 실패 -> 강제 종료")
                        is_scan_finished = True
                        break

                    # (3) 스크롤 시도
                    scroll_dist = cond.get("스크롤보폭", 500)
                    load_delay = cond.get("데이터수집스크롤간격", (0.5, 0.8))
                    
                    human_scroll_distance(self.driver, scroll_dist)
                    smart_sleep(load_delay, "데이터 로딩 대기")
                    continue

                # --- [분기 B] 새로운 배치가 있을 때 ---
                consecutive_empty_count = 0 

                for card in new_batch:
                    processed_count += 1
                    
                    # 1. 시간 텍스트 추출
                    try:
                        time_el = card.find_element(By.CSS_SELECTOR, "span[class*='date']")
                        time_txt = time_el.text.strip()
                    except:
                        continue

                    # 2. 시간 파싱
                    item_time = self._parse_relative_time(time_txt)

                    if item_time is not None:
                        # [핵심] Strict Cutoff 로직
                        # 알림 시간이 마지막 스캔 시간보다 같거나 과거면 -> 이미 처리한 데이터(혹은 날짜 변환으로 인한 과거 처리) -> 종료
                        if item_time <= last_scan_time:
                            print(f"   🛑 [종료] 마지막 작업 시점 도달 ({time_txt}) -> 중복 방지")
                            is_scan_finished = True
                            break
                    else:
                        # 파싱 실패 시 안전하게 건너뛰거나 종료 (여기선 종료하여 안전 추구)
                        print(f"   🛑 [종료] 시간 형식 인식 불가 ({time_txt}) -> 안전 종료")
                        is_scan_finished = True
                        break
                    
                    # 3. 데이터 수집
                    try:
                        text_content = card.text
                        act_type = ""
                        if "공감" in text_content: act_type = "공감"
                        elif "댓글" in text_content: act_type = "댓글"
                        elif "답글" in text_content: act_type = "답글"

                        nick_el = card.find_element(By.TAG_NAME, "strong")
                        nick = nick_el.text.strip()
                        
                        if nick and act_type:
                            if nick not in new_stats:
                                new_stats[nick] = {'like': 0, 'comment': 0, 'reply': 0}
                            
                            if act_type == "댓글": new_stats[nick]['comment'] += 1
                            elif act_type == "답글": new_stats[nick]['reply'] += 1
                            elif act_type == "공감": new_stats[nick]['like'] += 1
                            
                            print(f"   > [수집] {nick} ({act_type}) - {time_txt}")
                    except Exception as e:
                        continue

                if is_scan_finished:
                    break

            # --- [데이터 정리 및 저장] ---
            if new_stats:
                self.db.update_neighbor_stats_only(new_stats)
                print(f"\n ✅ {len(new_stats)}명의 새로운 활동 데이터 저장 완료")
            else:
                print(f"\n ✅ 새로운 활동이 없습니다.")

            # 마지막 스캔 시간 갱신
            self.db.update_last_scan_time(current_scan_start_time)

            # 랭킹 산출 및 캐싱
            self._cache_and_emit_rankings()
            
            return True

        except Exception as e:
            print(f"⚠️ [1단계 오류] {e}")
            return False

    def _cache_and_emit_rankings(self):
        """DB 통계를 메모리에 캐싱하고 GUI로 전송"""
        stats = self.db.get_all_neighbor_stats()
        raw_ui_list = []
        self.cached_ranking_map = {}

        for s in stats:
            score = (s['total_comments'] * 10) + (s['total_reply'] * 3) + (s['total_likes'] * 1)
            self.cached_ranking_map[s['nickname']] = {
                'c': s['total_comments'], 
                'r': s['total_reply'], 
                'l': s['total_likes'],
                'score': score
            }
            raw_ui_list.append((s['nickname'], {
                'comment': s['total_comments'], 
                'reply': s['total_reply'], 
                'like': s['total_likes'], 
                'score': score
            }))
        
        ui_list = sorted(raw_ui_list, key=lambda x: x[1]['score'], reverse=True)
        if self.worker: 
            try: self.worker.ranking_signal.emit(ui_list)
            except: pass

    def _phase_2_action(self, params):
        """[Phase 2] 스마트 답방 실행 (기존 run 함수 로직 이동)"""
        try:
            # 설정값 사용 유지
            conf = config.SMART_NEIGHBOR_CONFIG
            target_comment_cnt = params.get('target_comment', 30) if params else 30
            start_page = params.get('start_pg', 1) if params else 1
            
            print(f"\n🚀 [2단계] 스마트 답방 시작 (목표 댓글: {target_comment_cnt}건)")
            
            current_page = start_page
            total_comments_done = 0 
            
            while total_comments_done < target_comment_cnt:
                if self.check_stopped(): 
                    break

                url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={current_page}"
                self.driver.get(url)
                
                # 기존 설정값 사용
                p_loading = conf.get("delays", {}).get("페이지로딩", (2.0, 3.5))
                smart_sleep(p_loading if isinstance(p_loading, tuple) else (2.0, 3.5), f"{current_page}페이지 로딩")
                
                items = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["feed_item_inner"])
                if not items:
                    print(f"⚠️ {current_page}페이지에 게시글이 없습니다. 작업을 종료합니다.")
                    break

                # [Plan] 행동 계획 수립
                action_plan = self._plan_page_actions(items)
                
                # [Execute] 계획 실행
                comments_in_page = self._execute_page_actions(action_plan)
                total_comments_done += comments_in_page
                
                print(f"   👉 현재 진행: 댓글달기 {total_comments_done}/{target_comment_cnt} 완료")
                
                current_page += 1
                smart_sleep((1.0, 1.5), "다음 페이지 이동 대기")

            print(f"\n✨ 목표 달성! 스마트 답방 종료 (총 댓글 {total_comments_done}건)")

        except Exception as e:
            print(f"⚠️ [2단계 오류] {e}")

    def _plan_page_actions(self, items):
        """피드 내 게시글 분석 및 우선순위 계획 수립"""
        plan_list = []
        sel = config.SELECTORS
        interval_days = config.SMART_NEIGHBOR_CONFIG["conditions"].get("댓글주기", 3)
        
        print(f"\n📋 [Action Plan] 페이지 분석 (우선순위 가이드)")
        print("-" * 85)

        for idx, item in enumerate(items):
            try:
                nickname = item.find_element(By.CSS_SELECTOR, sel["feed_nickname"]).text.strip()
                author_el = item.find_element(By.CSS_SELECTOR, sel["feed_author_link"])
                blog_id = author_el.get_attribute("href").split('/')[-1]
                
                rank_data = self.cached_ranking_map.get(nickname)
                action_type = "SKIP"
                
                if rank_data:
                    stats_str = f"{nickname}(댓{rank_data['c']}/답{rank_data['r']}/공{rank_data['l']})"
                    
                    if rank_data.get('c', 0) > 0:
                        if self.db.can_I_comment(blog_id, interval_days):
                            action_type = "AI_COMMENT" if config.GEMINI_CONFIG.get("USE_GEMINI") else "NORMAL_COMMENT"
                        else: 
                            print(f"   > [이미 댓글 작성] {nickname}의 게시글은 이미 {interval_days}일 이내에 댓글을 작성했습니다.")
                            action_type = "LIKE_ONLY"
                    elif rank_data.get('r', 0) > 0:
                        if self.db.can_I_comment(blog_id, interval_days):
                            action_type = "NORMAL_COMMENT"
                        else: 
                            print(f"   > [이미 댓글 작성] {nickname}의 게시글은 이미 {interval_days}일 이내에 댓글을 작성했습니다.")
                            action_type = "LIKE_ONLY"
                    else: action_type = "LIKE_ONLY"
                else:
                    stats_str = f"{nickname}(데이터없음)"
                    action_type = "LIKE_ONLY"
                
                print(f" - {stats_str.ljust(30)} : {action_type}")
                plan_list.append({'index': idx, 'nickname': nickname, 'blog_id': blog_id, 'action': action_type})
            except: 
                continue
        print("-" * 85)
        return plan_list

    def _execute_page_actions(self, plan_list):
        """계획된 피드 작업 실행"""
        sel = config.SELECTORS
        success_comments = 0
        comment_msgs = config.SMART_NEIGHBOR_CONFIG.get("messages", ["잘 보고 갑니다!"])
        items = self.driver.find_elements(By.CSS_SELECTOR, sel["feed_item_inner"])

        for plan in plan_list:
            if self.check_stopped(): 
                break
            idx, action, nick = plan['index'], plan['action'], plan['nickname']
            try: 
                # 인덱스 유효성 체크
                if idx < len(items):
                    current_item = items[idx]
                else:
                    continue
            except: 
                continue

            if action in ["AI_COMMENT", "NORMAL_COMMENT"]:
                if self._execute_comment_logic(current_item, plan['blog_id'], nick, comment_msgs, action):
                    success_comments += 1
                else:
                    if self._execute_like_logic(current_item):
                        print(f"✅ [스마트관리] 공감 성공 ❤️ ({nick})")
            elif action == "LIKE_ONLY":
                if self._execute_like_logic(current_item):
                    print(f"✅ [스마트관리] 공감 성공 ❤️ ({nick})")
            
            time.sleep(random.uniform(0.5, 1.0))
        return success_comments

    def _execute_comment_logic(self, item_el, blog_id, nickname, messages, requested_action):
        """댓글 작성 상세 로직 (AI 실패 시 일반 댓글 전환 포함)"""
        try:
            sel = config.SELECTORS
            use_ai = (requested_action == "AI_COMMENT")
            
            # 1. 블로그 진입 (댓글 아이콘 클릭 또는 새 창 열기)
            try:
                reply_btn = item_el.find_element(By.CSS_SELECTOR, sel["feed_reply_icon"])
                smart_click(self.driver, reply_btn)
            except:
                self.driver.execute_script(f"window.open('https://blog.naver.com/{blog_id}');")

            smart_sleep((2.0, 3.0), f"@{nickname} 블로그 진입")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # 2. 메인 프레임 전환 및 입력 영역 확인
            try:
                self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
                input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel["comment_input_area"])))

                msg = ""
                # 3. AI 댓글 생성 프로세스
                if use_ai:
                    api_key = config.GEMINI_CONFIG.get("GEMINI_API_KEY")
                    if not api_key:
                        print(f"   ℹ️ [전환] API 키 누락 -> 일반 댓글로 진행")
                        use_ai = False
                    else:
                        # 데이터 추출 단계 (개별 예외 처리로 안정성 확보)
                        try:
                            # 제목 추출 시도
                            try:
                                title_text = self.driver.find_element(By.CSS_SELECTOR, ".se-title-text").text.strip()
                            except:
                                title_text = "제목 없음"

                            # 본문 추출 시도 (.se-main-container 가 없는 경우 대비)
                            try:
                                full_text = self.driver.find_element(By.CSS_SELECTOR, ".se-main-container").text.strip()
                            except:
                                full_text = ""

                            # 본문 내용이 너무 적거나 추출에 실패한 경우
                            if len(full_text) < 50:
                                print(f"   ℹ️ [전환] 추출된 본문 정보 부족 -> 일반 댓글로 진행")
                                use_ai = False
                            else:
                                # 토큰 절약을 위해 제목 + 본문 앞부분만 조합
                                post_data = f"제목: {title_text}\n본문 요약: {full_text[:300]}"

                                msg = GeminiHelper(api_key).generate_comment(
                                    post_data, 
                                    config.GEMINI_CONFIG.get("GEMINI_PROMPT", "")
                                )
                                
                                if not msg:
                                    print(f"   ℹ️ [전환] AI 응답 생성 실패 -> 일반 댓글로 진행")
                                    use_ai = False
                        except Exception as e:
                            print(f"   ℹ️ [전환] 데이터 분석 중 오류({e}) -> 일반 댓글로 진행")
                            use_ai = False
                
                # 4. 최종 메시지 확정 (AI 실패 시 리스트에서 랜덤 선택)
                if not msg: 
                    msg = random.choice(messages)
                    use_ai = False

                # ==========================================================
                # [수정] 이모지 제거 (BMP 오류 방지)
                # 크롬 드라이버 충돌 방지를 위해 이모지를 제거합니다.
                # ==========================================================
                msg = ''.join(c for c in msg if c <= '\uFFFF')
                
                # 만약 이모지를 다 지웠더니 내용이 비어버리면 기본 메시지 사용
                if not msg.strip():
                    msg = random.choice(messages)
                # ==========================================================

                # 5. 댓글 입력 및 전송
                smart_click(self.driver, input_area)
                human_typing(input_area, msg)
                
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, sel["comment_submit_button"])
                smart_click(self.driver, submit_btn)
                
                print(f"✅ [스마트관리] {'AI' if use_ai else '일반'}댓글 성공 ({nickname})")
                print(f"   💬 내용: {msg}")

                self.db.save_comment_success(blog_id, nickname)
                smart_sleep((1.5, 2.5), "등록 완료 대기")
                
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return True

            except Exception as e:
                print(f"   ⚠️ 내부 처리 오류: {nickname} 블로그 작업 실패 ({e})")
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False

        except Exception as e:
            print(f"   ❌ 시스템 오류: {e}")
            return False

    def _execute_like_logic(self, item_el):
        """공감 클릭 로직"""
        try:
            sel = config.SELECTORS
            like_btn = item_el.find_element(By.CSS_SELECTOR, sel["feed_like_buttons"])
            if like_btn.get_attribute("aria-pressed") == "true": 
                return False
            human_scroll_element(self.driver, like_btn)
            smart_sleep((0.1, 0.3), "공감 버튼 클릭 전 실제 사람처럼 대기")
            smart_click(self.driver, like_btn)
            return True
        except: 
            return False