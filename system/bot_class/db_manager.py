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

            # [2] 스캔 중단점 관리 (변경됨: Key-Value 구조)
            # 체크포인트 키(key)와 시간값(value)만 저장
            try:
                cursor.execute("SELECT value FROM sync_checkpoints LIMIT 0")
            except sqlite3.OperationalError:
                # 컬럼이 없다는 에러가 나면 과감히 삭제 (데이터는 어차피 호환 안 됨)
                cursor.execute("DROP TABLE IF EXISTS sync_checkpoints")

            # [2] 스캔 중단점 관리 (Key-Value 구조로 재생성)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_checkpoints (
                    key TEXT PRIMARY KEY,
                    value TEXT
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

    def get_last_scan_time(self):
        """sync_checkpoints에서 마지막 스캔 시간을 가져옴"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM sync_checkpoints WHERE key = 'last_scan_time'")
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                except:
                    return datetime.min
            return datetime.min # 기록 없으면 아주 옛날(최초 실행)

    def update_last_scan_time(self, dt_obj):
        """현재 스캔 시작 시간을 sync_checkpoints에 저장"""
        time_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 기존 값이 있으면 업데이트, 없으면 삽입
            cursor.execute('''
                INSERT INTO sync_checkpoints (key, value) VALUES ('last_scan_time', ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
            ''', (time_str, time_str))
            conn.commit()

    def update_neighbor_stats_only(self, stats_map):
        """수집된 통계를 DB에 누적 업데이트 (UPSERT)"""
        if not stats_map: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for nick, counts in stats_map.items():
                    likes = counts.get('like', 0)
                    comments = counts.get('comment', 0)
                    replies = counts.get('reply', 0)
                    
                    cursor.execute('''
                        INSERT INTO neighbor_stats (nickname, total_likes, total_comments, total_reply)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(nickname) DO UPDATE SET 
                            total_likes = total_likes + ?,
                            total_comments = total_comments + ?,
                            total_reply = total_reply + ?
                    ''', (nick, likes, comments, replies, likes, comments, replies))
                conn.commit()
        except Exception as e:
            print(f"❌ [DB 에러] 통계 업데이트 실패: {e}")

    def get_all_neighbor_stats(self):
        """랭킹 산정을 위한 통계 전체 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM neighbor_stats")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def reset_smart_data(self):
        """[추가] 스마트 이웃 관리 데이터(중단점, 통계) 완전 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. 스캔 시점 초기화
                cursor.execute("DELETE FROM sync_checkpoints")
                # 2. 통계 데이터 초기화
                cursor.execute("DELETE FROM neighbor_stats")
                conn.commit()
            return True
        except Exception as e:
            print(f"❌ DB 초기화 실패: {e}")
            return False