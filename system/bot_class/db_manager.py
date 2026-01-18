import sqlite3
import os
from datetime import datetime

class BlogDB:
    def __init__(self):
        # 실행 파일의 위치를 기준으로 DB 경로 설정
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neighbor_history.db")
        self._init_db()

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # blog_id: 이웃 아이디 (PK)
            # nickname: 이웃 닉네임
            # last_comment_date: 마지막으로 댓글을 성공한 날짜/시간 (TEXT)
            # total_count: 누적 댓글 성공 횟수
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS neighbor_comments (
                    blog_id TEXT PRIMARY KEY,
                    nickname TEXT,
                    last_comment_date TEXT,
                    total_count INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def can_I_comment(self, blog_id, interval_days):
        """설정한 방문 주기(Days)가 지났는지 확인"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_comment_date FROM neighbor_comments WHERE blog_id = ?", (blog_id,))
            row = cursor.fetchone()
            
            # 1. 기록이 없으면 첫 방문이므로 무조건 가능
            if not row or not row[0]:
                return True
            
            # 2. 날짜 계산 (시간 제외한 '날짜' 기준으로만 계산)
            last_date_obj = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').date()
            today_obj = datetime.now().date()
            
            days_passed = (today_obj - last_date_obj).days
            
            # 설정한 주기보다 지났거나 같으면 True 반환 (예: 주기 3일인데 3일 지났으면 가능)
            return days_passed >= interval_days

    def save_comment_success(self, blog_id, nickname):
        """댓글 작성 성공 시 DB 업데이트"""
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 기록이 있으면 업데이트, 없으면 삽입 (UPSERT)
            cursor.execute('''
                INSERT INTO neighbor_comments (blog_id, nickname, last_comment_date, total_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(blog_id) DO UPDATE SET 
                    last_comment_date = ?, 
                    total_count = total_count + 1
            ''', (blog_id, nickname, now_str, now_str))
            conn.commit()