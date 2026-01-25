import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from db_manager import BlogDB
import config
from utils import human_scroll, smart_sleep, smart_click, human_typing

class BlogSmartNeighborManagement:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.worker = None
        self.db = BlogDB()
        self.temp_neighbor_stats = {}
        self.current_checkpoints = []
        
        # 랭킹 데이터 캐싱 {닉네임: {'score':..., 'desc_str':...}}
        self.cached_ranking_map = {} 

    def check_stopped(self):
        """작업 중단 여부 확인"""
        if self.worker and self.worker.is_stopped:
            return True
        return False

    def _get_item_fingerprint(self, card):
        """
        알림 카드 파싱 및 지문 생성
        - 닉네임 / 타입(공감,댓글,답글) / 내용(제목) 분리 추출
        """
        try:
            # 1. 타입 분석
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

            # 2. 닉네임 및 내용 분석
            try:
                title_area = card.find_element(By.CSS_SELECTOR, ".title__KPI3G")
                strong_tags = title_area.find_elements(By.TAG_NAME, "strong")
                
                nick = strong_tags[0].text.strip()
                content = ""
                if len(strong_tags) > 1:
                    content = strong_tags[1].text.strip()
                else:
                    content = "제목없음"
            except:
                return None, None, None, None

            # 3. 고유 ID 생성
            safe_content = content[:30].replace(" ", "")
            fingerprint = f"{nick}_{act_type}_{safe_content}"
            
            return nick, act_type, content, fingerprint

        except Exception as e:
            return None, None, None, None

    def run(self, params=None):
        """
        [Phase 1] 알림 데이터 수집 및 랭킹 분석
        [Phase 2] 피드 순회 -> 계획 수립(Plan) -> 로그 출력 -> 실행(Execute)
        """
        config.sync_all_configs()
        conf = config.SMART_NEIGHBOR_CONFIG
        
        # --- [Phase 1] 알림 데이터 수집 및 랭킹 분석 ---
        if not self._phase_1_analysis():
            return

        # --- [Phase 2] 스마트 답방 실행 ---
        if self.check_stopped(): return
        
        try:
            target_comment_cnt = params.get('target_comment', 30)
            start_page = params.get('start_pg', 1)
            
            print(f"\n🚀 [2단계] 스마트 답방 시작 (목표 댓글: {target_comment_cnt}건)")
            
            current_page = start_page
            total_comments_done = 0 
            
            while total_comments_done < target_comment_cnt:
                if self.check_stopped(): break
                
                url = f"https://section.blog.naver.com/BlogHome.naver?currentPage={current_page}"
                self.driver.get(url)
                
                # [오류 수정] 튜플 타입 체크 보강
                p_loading = conf.get("delays", {}).get("페이지로딩", (2.0, 3.5))
                smart_sleep(p_loading if isinstance(p_loading, tuple) else (2.0, 3.5), f"{current_page}페이지 로딩")
                
                items = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["feed_item_inner"])
                if not items:
                    print(f"⚠️ {current_page}페이지에 게시글이 없습니다. 작업을 종료합니다.")
                    break

                # 3. [Plan] 행동 계획 수립 및 출력
                action_plan = self._plan_page_actions(items)
                
                # 4. [Execute] 계획 실행
                comments_in_page = self._execute_page_actions(action_plan)
                total_comments_done += comments_in_page
                
                print(f"   👉 현재 진행: 댓글달기 {total_comments_done}/{target_comment_cnt} 완료")
                
                current_page += 1
                s_interval = conf.get("delays", {}).get("스크롤간격", (1.0, 1.5))
                smart_sleep(s_interval if isinstance(s_interval, tuple) else (1.0, 1.5), "다음 페이지 이동 대기")

            print(f"\n✨ 목표 달성! 스마트 답방 종료 (총 댓글 {total_comments_done}건)")

        except Exception as e:
            print(f"⚠️ [2단계 오류] {e}")

    def _phase_1_analysis(self):
        """
        [수정] 알림창 크롤링 (완전 자동 버전)
        - 10개 단위 고속 분석
        - Enter 입력 없이 자동으로 DB 저장 및 2단계 진입
        """
        try:
            config.sync_all_configs()
            conf = config.SMART_NEIGHBOR_CONFIG
            sel = config.SELECTORS
            
            card_selector = "li.item__INKiv" 
            btn_selector = sel.get("scroll_top_btn", ".scroll_top_button__uyAEr")
            
            w_comment = conf["weights"].get("댓글점수", 10)
            w_reply = conf["weights"].get("답글점수", 3) 
            w_like = conf["weights"].get("공감점수", 1)

            last_ids = self.db.get_last_checkpoints()
            print(f"\n[🔍 DB 로드된 중단점]: {last_ids}")
            
            self.driver.get("https://m.blog.naver.com/News.naver")
            p_loading = conf.get("delays", {}).get("페이지로딩", (2.0, 3.5))
            smart_sleep(p_loading if isinstance(p_loading, tuple) else (2.0, 3.5), "알림 페이지 진입")

            print("\n" + "="*60)
            print(" 🚀 [1단계] 알림 고속 분석 및 자동 저장 시작")
            print("="*60)

            analyzed_idx = 0 
            new_count = 0
            stats_summary = {'like': 0, 'comment': 0, 'reply': 0}
            
            is_ended = False
            scroll_count = 0

            while not is_ended:
                if self.check_stopped(): return False

                all_cards = self.driver.find_elements(By.CSS_SELECTOR, card_selector)
                target_batch = all_cards[analyzed_idx : analyzed_idx + 10]
                
                if target_batch:
                    batch_new_found = 0
                    for card in target_batch:
                        nick, act_type, content, fingerprint = self._get_item_fingerprint(card)
                        
                        if not nick:
                            analyzed_idx += 1
                            continue

                        if fingerprint in last_ids:
                            print(f"\n📍 [완료] 중단점 도달: {nick}님")
                            is_ended = True
                            break

                        # 체크포인트 최대 3개 저장
                        if len(self.current_checkpoints) < 3: 
                            self.current_checkpoints.append({
                                'id': fingerprint, 
                                'nick': nick,
                                'type': act_type,
                                'content': content
                            })

                        # 통계 집계
                        if nick not in self.temp_neighbor_stats:
                            self.temp_neighbor_stats[nick] = {'like': 0, 'comment': 0, 'reply': 0}

                        if act_type == "댓글":
                            self.temp_neighbor_stats[nick]['comment'] += 1
                            stats_summary['comment'] += 1
                        elif act_type == "답글":
                            self.temp_neighbor_stats[nick]['reply'] += 1
                            stats_summary['reply'] += 1
                        elif act_type == "공감":
                            self.temp_neighbor_stats[nick]['like'] += 1
                            stats_summary['like'] += 1
                        
                        new_count += 1
                        batch_new_found += 1
                        analyzed_idx += 1 

                    if batch_new_found > 0:
                        print(f"   📊 스캔 중... (현재 +{batch_new_found} / 누적 {new_count})")

                if is_ended: break

                try:
                    btn_sel = sel.get("scroll_top_btn", ".scroll_top_button__uyAEr")
                    if self.driver.find_element(By.CSS_SELECTOR, btn_sel).is_displayed():
                        print("\n🛑 [완료] 페이지 바닥 도달")
                        is_ended = True
                        break
                except: pass

                scroll_count += 1
                step = conf["conditions"].get('스크롤보폭', 700)
                human_scroll(self.driver, step)
                s_interval = conf.get("delays", {}).get("스크롤간격", (0.8, 1.5))
                smart_sleep(s_interval if isinstance(s_interval, tuple) else (0.8, 1.5), f"스크롤 {scroll_count}회")

            # --- [자동 저장 및 Phase 2 진입] ---
            if not self.check_stopped() and (new_count > 0 or is_ended):
                print("\n" + "="*60)
                print(f" ✅ 분석 완료: 신규 {new_count}개 수집")
                print(f" 💾 데이터를 DB에 자동으로 저장합니다...")
                
                # 저장 승인 input() 제거됨
                self.db.update_sync_data(self.temp_neighbor_stats, self.current_checkpoints)
                
                # 랭킹 갱신 및 캐싱
                all_stats = self.db.get_all_neighbor_stats()
                temp_list = []
                for s in all_stats:
                    n = s['nickname']
                    c = s['total_comments']
                    r = s['total_reply']
                    l = s['total_likes']
                    score = (c * w_comment) + (r * w_reply) + (l * w_like)
                    temp_list.append({'nick': n, 'c': c, 'r': r, 'l': l, 'score': score})
                
                temp_list.sort(key=lambda x: x['score'], reverse=True)
                self.cached_ranking_map = {}
                ui_list = []
                for rank, item in enumerate(temp_list, 1):
                    # Phase 2 로그 포맷 고정
                    desc = f"[{item['nick']} {rank}위/댓{item['c']}/답{item['r']}/공{item['l']}/총{item['score']}점]"
                    self.cached_ranking_map[item['nick']] = {'score': item['score'], 'desc_str': desc, 'c': item['c'], 'r': item['r'], 'l': item['l']}
                    
                    ui_list.append((item['nick'], {'comment': item['c'], 'reply': item['r'], 'like': item['l'], 'score': item['score']}))
                
                if self.worker: self.worker.ranking_signal.emit(ui_list)
                print(" ✅ DB 저장 및 랭킹 최신화 완료. 2단계를 시작합니다.")
                print("="*60)
                return True
                
            return False

        except Exception as e:
            print(f"⚠️ [1단계 오류] {e}")
            return False

    def _plan_page_actions(self, items):
        """페이지 내 게시글들에 대한 행동 계획 수립"""
        plan_list = []
        sel = config.SELECTORS
        interval_days = config.NEIGHBOR_COMMENT_CONFIG["conditions"].get("방문주기", 3)
        
        print(f"\n📋 [Action Plan] 페이지 분석")
        print("-" * 80)

        for idx, item in enumerate(items):
            try:
                nickname = item.find_element(By.CSS_SELECTOR, sel["feed_nickname"]).text.strip()
                author_el = item.find_element(By.CSS_SELECTOR, sel["feed_author_link"])
                blog_url = author_el.get_attribute("href")
                blog_id = blog_url.split('/')[-1]
                
                rank_data = self.cached_ranking_map.get(nickname)
                action_type = "SKIP"
                log_prefix = f"[{nickname} 데이터없음]"
                
                if rank_data:
                    log_prefix = rank_data['desc_str']
                    # [우선순위 로직]
                    # 1순위: 댓글 이력 있음 -> AI/일반 댓글
                    if rank_data.get('c', 0) > 0:
                        if self.db.can_I_comment(blog_id, interval_days):
                            action_type = "AI_COMMENT" if config.GEMINI_CONFIG.get("USE_GEMINI") else "NORMAL_COMMENT"
                        else: action_type = "LIKE_ONLY"
                    # 2순위: 답글 이력만 있음 -> 일반 댓글
                    elif rank_data.get('r', 0) > 0:
                        if self.db.can_I_comment(blog_id, interval_days):
                            action_type = "NORMAL_COMMENT"
                        else: action_type = "LIKE_ONLY"
                    else: action_type = "LIKE_ONLY"
                else:
                    action_type = "LIKE_ONLY"
                
                # 상세 로그 출력
                print(f"{log_prefix} - {action_type}")
                
                plan_list.append({'index': idx, 'nickname': nickname, 'blog_id': blog_id, 'blog_url': blog_url, 'action': action_type})

            except: continue
        
        print("-" * 80)
        return plan_list

    def _execute_page_actions(self, plan_list):
        """계획된 행동 실행"""
        sel = config.SELECTORS
        success_comments = 0
        comment_msgs = config.NEIGHBOR_COMMENT_CONFIG.get("messages", ["잘 보고 갑니다!"])
        items = self.driver.find_elements(By.CSS_SELECTOR, sel["feed_item_inner"])

        for plan in plan_list:
            if self.check_stopped(): break
            idx, action, nick = plan['index'], plan['action'], plan['nickname']
            
            try: current_item = items[idx]
            except: continue

            if action in ["AI_COMMENT", "NORMAL_COMMENT"]:
                use_ai = (action == "AI_COMMENT")
                if self._execute_comment_logic(current_item, plan['blog_url'], plan['blog_id'], nick, comment_msgs, use_ai):
                    success_comments += 1
                else:
                    if self._execute_like_logic(current_item):
                        print(f"✅ [스마트관리] 공감 성공 ❤️ ({nick})")

            elif action == "LIKE_ONLY":
                if self._execute_like_logic(current_item):
                    print(f"✅ [스마트관리] 공감 성공 ❤️ ({nick})")
            
            time.sleep(random.uniform(0.8, 1.5))
        return success_comments

    def _execute_comment_logic(self, item_el, blog_url, blog_id, nickname, messages, use_ai):
        try:
            sel = config.SELECTORS
            delays = config.NEIGHBOR_COMMENT_CONFIG["delays"]

            try:
                reply_btn = item_el.find_element(By.CSS_SELECTOR, sel["feed_reply_icon"])
                smart_click(self.driver, reply_btn)
            except:
                self.driver.execute_script(f"window.open('{blog_url}');")

            smart_sleep(delays.get("블로그_접속_대기", (2.0, 3.0)), "블로그 진입")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            try:
                self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
                try:
                    input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel["comment_input_area"])))
                except:
                    smart_click(self.driver, self.driver.find_element(By.CSS_SELECTOR, sel["comment_open_button"]))
                    input_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel["comment_input_area"])))

                msg = ""
                if use_ai and config.GEMINI_CONFIG.get("GEMINI_API_KEY"):
                    try:
                        post_text = self.driver.find_element(By.CSS_SELECTOR, sel.get("post_content", ".se-main-container")).text.strip()
                        if len(post_text) > 50:
                            from ai_helper import GeminiHelper
                            msg = GeminiHelper(config.GEMINI_CONFIG["GEMINI_API_KEY"]).generate_comment(post_text, config.GEMINI_CONFIG.get("GEMINI_PROMPT", ""))
                    except: pass
                
                if not msg: msg = random.choice(messages)

                smart_click(self.driver, input_area)
                human_typing(input_area, msg)
                smart_sleep((0.3, 0.7), "작성 후 검토")
                
                smart_click(self.driver, self.driver.find_element(By.CSS_SELECTOR, sel["comment_submit_button"]))
                
                # [댓글 내용 로그 출력]
                print(f"✅ [스마트관리] {'AI' if use_ai else '일반'}댓글 성공 ({nickname})")
                print(f"   💬 내용: {msg}")

                smart_sleep((1.5, 2.5), "등록 완료 대기")
                self.db.save_comment_success(blog_id, nickname)
                
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return True

            except Exception as e:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
                
        except: return False

    def _execute_like_logic(self, item_el):
        try:
            sel = config.SELECTORS
            like_btn = item_el.find_element(By.CSS_SELECTOR, sel["feed_like_buttons"])
            if like_btn.get_attribute("aria-pressed") == "true":
                return False
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_btn)
            time.sleep(0.3)
            smart_click(self.driver, like_btn)
            return True
        except:
            return False