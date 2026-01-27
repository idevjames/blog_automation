import sqlite3
import os
from datetime import datetime
import config

class BlogDB:
    def __init__(self):
        # 실행 파일 위치 기준 DB 경로 설정
        self.db_path = config.path_db
        self._init_db()

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 이웃 댓글 관리 테이블 (기존 유지)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS neighbor_comments (
                    blog_id TEXT PRIMARY KEY,
                    nickname TEXT,
                    last_comment_date TEXT,
                    total_count INTEGER DEFAULT 0
                )
            ''')

            # 2. 알림 중단점 관리 (수정됨)
            # id: nickname_type_content 조합의 고유키
            # save_date 제거, 컬럼 분리 저장
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_checkpoints (
                    id TEXT PRIMARY KEY,
                    nickname TEXT,
                    type TEXT,
                    content TEXT
                )
            ''')

            # 3. 이웃 활동 통계 (수정됨)
            # last_update 제거, 답글(reply) 컬럼 추가
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS neighbor_stats (
                    nickname TEXT PRIMARY KEY,
                    total_likes INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_reply INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def can_I_comment(self, blog_id, interval_days):
        """설정한 방문 주기(Days)가 지났는지 확인"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_comment_date FROM neighbor_comments WHERE blog_id = ?", (blog_id,))
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return True
            
            last_date_obj = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').date()
            days_passed = (datetime.now().date() - last_date_obj).days
            return days_passed >= interval_days

    def save_comment_success(self, blog_id, nickname):
        """댓글 작성 성공 시 DB 업데이트"""
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO neighbor_comments (blog_id, nickname, last_comment_date, total_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(blog_id) DO UPDATE SET 
                    last_comment_date = ?, 
                    total_count = total_count + 1
            ''', (blog_id, nickname, now_str, now_str))
            conn.commit()

    def get_last_checkpoints_details(self, limit=50):
        """중단점의 상세 데이터(ID, 닉네임, 타입, 내용) 리스트를 가져옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 결과를 딕셔너리 형태로 받기 위해 row_factory 설정
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id, nickname as nick, type, content FROM sync_checkpoints")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ [DB] 중단점 상세 로드 오류: {e}")
            return []

    def get_all_neighbor_stats(self):
        """모든 이웃 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM neighbor_stats")
            # 딕셔너리 형태로 반환
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_sync_data(self, stats_map, checkpoints_list):
        """분석된 통계 업데이트 및 중단점 갈아치우기"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. 중단점 테이블 초기화 (항상 최신 3개만 유지하기 위해 싹 비움)
                cursor.execute("DELETE FROM sync_checkpoints")
                
                # 2. 새로운 중단점(최대 3개) 삽입
                for cp in checkpoints_list:
                    cursor.execute('''
                        INSERT INTO sync_checkpoints (id, nickname, type, content)
                        VALUES (?, ?, ?, ?)
                    ''', (cp['id'], cp['nick'], cp['type'], cp['content']))

                # 3. 이웃 통계 업데이트 (누적 합산)
                for nick, counts in stats_map.items():
                    likes = counts.get('like', 0)
                    comments = counts.get('comment', 0)
                    replies = counts.get('reply', 0)

                    if likes == 0 and comments == 0 and replies == 0:
                        continue

                    cursor.execute('''
                        INSERT INTO neighbor_stats (nickname, total_likes, total_comments, total_reply)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(nickname) DO UPDATE SET 
                            total_likes = total_likes + ?,
                            total_comments = total_comments + ?,
                            total_reply = total_reply + ?
                    ''', (nick, likes, comments, replies, likes, comments, replies))
                
                conn.commit()
            return True
        except Exception as e:
            print(f"❌ [DB] 데이터 업데이트 오류: {e}")
            return False