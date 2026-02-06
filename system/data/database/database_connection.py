import sqlite3
import os
import threading
from typing import Optional, List, Any, Dict

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()

    def __init__(self):
        DatabaseConnection._instance = self
        
        self.base_dir = os.getcwd()
        self.db_folder = os.path.join(self.base_dir, "user_data")
        self.db_path = os.path.join(self.db_folder, "blog_automation.db")
        
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        self._connection = None
        self._connect()
        self._create_tables()

    @classmethod
    def instance(cls) -> 'DatabaseConnection':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _connect(self):
        """내부용: DB 연결"""
        try:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row 
            print(f"[DB] 연결 성공: {self.db_path}")
        except Exception as e:
            print(f"[DB] 연결 실패: {e}")
            raise e

    # ---------------------------------------------------------
    # [Public] 외부 공개 메서드
    # ---------------------------------------------------------
    
    def execute_query(self, query: str, params: tuple = ()) -> None:
        """INSERT, UPDATE, DELETE (자동 커밋)"""
        if not self._connection: return
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            self._connection.commit()
        except Exception as e:
            print(f"[DB Error] 쿼리: {query}\n에러: {e}")

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """SELECT (여러 줄)"""
        if not self._connection: return []
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """SELECT (한 줄)"""
        if not self._connection: return None
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def close(self):
        if self._connection:
            self._connection.close()

    # ---------------------------------------------------------
    # [Internal] 테이블 생성 및 초기 데이터
    # ---------------------------------------------------------
    def _create_tables(self):
        # 1. 설정 테이블 (단일 값들: API Key, Token 등)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 2. 서이추 메시지 테이블 (Row 단위 관리)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS neighbor_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL
            )
        """)

        # 3. 댓글 메시지 테이블 (Row 단위 관리)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS comment_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL
            )
        """)
        
        self._init_default_data()

    def _init_default_data(self):
        # 서이추 메시지 초기값
        row = self.fetch_one("SELECT count(*) as cnt FROM neighbor_messages")
        if row and row['cnt'] == 0:
            defaults = [
                "안녕하세요! 관심사가 비슷해서 이웃 신청합니다 :)",
                "반갑습니다~ 포스팅 잘 보고 가요! 자주 소통해요.",
                "글이 너무 좋네요! 서로이웃 하고 싶어요 ^^",
                "우연히 들렀는데 배울 점이 많네요. 이웃 신청 받아주세요!",
                "소통하며 지내고 싶습니다. 서이추 부탁드려요~"
            ]
            for msg in defaults:
                self.execute_query("INSERT INTO neighbor_messages (message) VALUES (?)", (msg,))

        # 댓글 메시지 초기값
        row = self.fetch_one("SELECT count(*) as cnt FROM comment_messages")
        if row and row['cnt'] == 0:
            defaults = [
                "포스팅 잘 보고 갑니다!",
                "좋은 정보 감사합니다~",
                "공감 누르고 가요! 오늘도 좋은 하루 보내세요 :)",
                "글이 알차네요! 잘 읽었습니다.",
                "덕분에 좋은 내용 알아갑니다 ^^"
            ]
            for msg in defaults:
                self.execute_query("INSERT INTO comment_messages (message) VALUES (?)", (msg,))