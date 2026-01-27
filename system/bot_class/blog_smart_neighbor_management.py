import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ai_helper import GeminiHelper
from bot_class.db_manager import BlogDB
import config
from utils import human_scroll_distance, human_scroll_element, smart_sleep, smart_click, human_typing

class BlogSmartNeighborManagement:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.worker = None
        self.db = BlogDB()
        self.temp_neighbor_stats = {}
        self.current_checkpoints = []
        self.cached_ranking_map = {} 

    def check_stopped(self):
        """작업 중단 여부 확인"""
        if self.worker and self.worker.is_stopped:
            return True
        return False

    def _get_item_fingerprint(self, card):
        """알림 카드 파싱 및 지문 생성"""
        try:
            try:
                icon_area = card.find_element(By.CSS_SELECTOR, ".icon_area__qMg6z")
                type_text = icon_area.text.strip()
            except:
                return None, None, None, None

            act_type = ""
            if "공감" in type_text: act_type = "공감"
            elif "댓글" in type_text: act_type = "댓글"
            elif "답글" in type_text: act_type = "답글"
            else: return None, None, None, None

            try:
                title_area = card.find_element(By.CSS_SELECTOR, ".title__KPI3G")
                strong_tags = title_area.find_elements(By.TAG_NAME, "strong")
                nick = strong_tags[0].text.strip()
                content = strong_tags[1].text.strip() if len(strong_tags) > 1 else "제목없음"
            except:
                return None, None, None, None

            safe_content = content[:30].replace(" ", "")
            fingerprint = f"{nick}_{act_type}_{safe_content}"
            return nick, act_type, content, fingerprint
        except Exception as e:
            return None, None, None, None

    def run(self, params=None):
        """스마트 이웃 관리 메인 루프"""
        config.sync_all_configs()
        conf = config.SMART_NEIGHBOR_CONFIG
        
        # [Phase 1] 알림 분석 및 DB 동기화
        if not self._phase_1_analysis():
            return

        if self.check_stopped(): 
            return
        
        try:
            target_comment_cnt = params.get('target_comment', 30)
            start_page = params.get('start_pg', 1)
            print(f"\n🚀 [2단계] 스마트 답방 시작 (목표 댓글: {target_comment_cnt}건)")
            
            current_page = start_page
            total_comments_done = 0 
            
            while total_comments_done < target_comment_cnt:
                if self.check_stopped(): 
                    break

                url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={current_page}"
                self.driver.get(url)
                
                p_loading = conf.get("delays", {}).get("페이지로딩", (2.0, 3.5))
                smart_sleep(p_loading if isinstance(p_loading, tuple) else (2.0, 3.5), f"{current_page}페이지 로딩")
                
                items = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["feed_item_inner"])
                if not items:
                    print(f"⚠️ {current_page}페이지에 게시글이 없습니다. 작업을 종료합니다.")
                    break

                # [Plan] 행동 계획 수립 (상세 로그 출력 포함)
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

    def _phase_1_analysis(self):
        """[Phase 1] 알림 분석 (중단점 또는 UI 바닥 감지 시 종료)"""
        try:
            config.sync_all_configs()
            cond = config.SMART_NEIGHBOR_CONFIG.get("conditions", {})
            
            # 1. DB에서 중단점 3개 다 가져오기
            old_checkpoints = self.db.get_last_checkpoints_details()
            last_ids = [cp['id'] for cp in old_checkpoints] if old_checkpoints else []
            
            print(f"\n[🔍 DB 로드된 중단점]: {len(last_ids)}개 로드됨 ({last_ids})")
            
            self.driver.get("https://m.blog.naver.com/News.naver")
            smart_sleep((2.0, 3.0), "알림 페이지 로딩")

            self.current_checkpoints = [] 
            self.temp_neighbor_stats = {} 
            
            last_processed_index = 0
            new_count = 0
            consecutive_empty_count = 0 # 연속으로 데이터 못 찾은 횟수 (Safety Net)
            
            # [핵심] 스캔 종료 여부를 판단하는 깃발
            is_scan_finished = False 

            print(f"\n📡 [1단계] 데이터 증분 수집 시작...")

            while not is_scan_finished: 
                if self.check_stopped(): return False
                
                # 1. 전체 카드 로드
                all_cards = self.driver.find_elements(By.CSS_SELECTOR, "li.item__INKiv")
                total_len = len(all_cards)

                # 2. 증분 처리 (이미 처리한 인덱스 이후부터)
                new_batch = all_cards[last_processed_index:]

                # ---------------------------------------------------------
                # [분기 A] 새로운 배치가 없을 때 (스크롤 또는 종료 판단)
                # ---------------------------------------------------------
                if not new_batch:
                    # (1) UI 바닥 체크: '맨 위로' 버튼이 있는지 확인
                    try:
                        footer_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.scroll_top__YuIw9")
                        if footer_buttons and footer_buttons[0].is_displayed():
                            print(f"\n🛑 [종료 사유] '맨 위로' 버튼(UI) 발견 -> 페이지 바닥 도착")
                            is_scan_finished = True
                            break
                    except: pass

                    # (2) UI가 안 보이면 연속 실패 카운트 증가
                    consecutive_empty_count += 1
                    
                    # (3) 5회 연속 실패 시 강제 종료 (네트워크 이슈 등)
                    if consecutive_empty_count >= 5:
                        print(f"\n⚠️ [종료 사유] 5회 연속 데이터 로드 실패 -> 강제 종료 (네트워크 지연 등)")
                        is_scan_finished = True
                        break

                    # (4) 아직 기회가 남았으면 스크롤 시도
                    scroll_dist = cond.get("스크롤보폭", 500)
                    load_delay = cond.get("데이터수집스크롤간격", (0.5, 0.8))
                    
                    human_scroll_distance(self.driver, scroll_dist)
                    smart_sleep(load_delay, "데이터 로딩 대기")
                    continue

                # ---------------------------------------------------------
                # [분기 B] 새로운 배치가 있을 때 (데이터 분석)
                # ---------------------------------------------------------
                consecutive_empty_count = 0 # 데이터 찾았으므로 카운트 리셋

                for card in new_batch:
                    nick, act_type, content, fingerprint = self._get_item_fingerprint(card)
                    
                    if nick:
                        # [조건 1] 중단점(Checkpoint) 발견 시 종료
                        if last_ids and fingerprint in last_ids:
                            print(f"\n🛑 [종료 사유] 기존 중단점 도달: {nick}님 ({fingerprint})")
                            print(f"   -> 더 이상 과거 데이터는 수집하지 않습니다.")
                            is_scan_finished = True
                            break # for문 탈출

                        # 데이터 수집
                        self.current_checkpoints.append({
                            'id': fingerprint, 'nick': nick, 'type': act_type, 'content': content
                        })

                        if nick not in self.temp_neighbor_stats:
                            self.temp_neighbor_stats[nick] = {'like': 0, 'comment': 0, 'reply': 0}
                        if act_type == "댓글": self.temp_neighbor_stats[nick]['comment'] += 1
                        elif act_type == "답글": self.temp_neighbor_stats[nick]['reply'] += 1
                        elif act_type == "공감": self.temp_neighbor_stats[nick]['like'] += 1
                        
                        new_count += 1
                        print(f"   > [수집] {new_count}번째 활동: {nick} ({act_type})", end='\r')
                    
                    last_processed_index += 1

                # 중단점을 만나서 for문을 나왔다면 while문도 종료
                if is_scan_finished:
                    break

            # ---------------------------------------------------------
            # [데이터 정리 및 DB 저장 로직]
            # ---------------------------------------------------------
            
            # [케이스 1] 새로운 데이터가 하나도 없을 때
            if new_count == 0:
                print(f"\n ✅ 새로운 활동이 없습니다. (현재 최신 상태)")
            
            # [케이스 2] 새로운 데이터가 있을 때
            else:
                # 1. 새로 찾은 거(앞) + 기존 거(뒤) 합쳐서 -> 앞에서 3개 자름
                final_checkpoints = (self.current_checkpoints + old_checkpoints)[:3]
                
                # 2. DB 업데이트
                self.db.update_sync_data(self.temp_neighbor_stats, final_checkpoints)
                print(f"\n ✅ {new_count}건의 활동 데이터 반영 및 중단점 갱신 완료")

            # [3단계] 랭킹 산출 (항상 실행)
            stats = self.db.get_all_neighbor_stats()
            raw_ui_list = []
            
            for s in stats:
                score = (s['total_comments'] * 10) + (s['total_reply'] * 3) + (s['total_likes'] * 1)
                self.cached_ranking_map[s['nickname']] = {
                    'c': s['total_comments'], 'r': s['total_reply'], 'l': s['total_likes']
                }
                raw_ui_list.append((s['nickname'], {'comment': s['total_comments'], 'reply': s['total_reply'], 'like': s['total_likes'], 'score': score}))
            
            ui_list = sorted(raw_ui_list, key=lambda x: x[1]['score'], reverse=True)
            if self.worker: self.worker.ranking_signal.emit(ui_list)
            
            return True

        except Exception as e:
            print(f"⚠️ [1단계 오류] {e}")
            return False

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
                current_item = items[idx]
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