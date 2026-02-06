from typing import Optional, List, Dict, Union
from data.database.database_connection import DatabaseConnection

class SettingsRepository:
    _instance: Optional['SettingsRepository'] = None

    KEY_GEMINI_API_KEY = "gemini_api_key"
    KEY_TELEGRAM_BOT_TOKEN = "telegram_bot_token"

    def __init__(self):
        SettingsRepository._instance = self
        self.gemini_active = False
        self.telegram_active = False

    @classmethod
    def instance(cls) -> 'SettingsRepository':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def db(self):
        return DatabaseConnection.instance()

    # --- 1. 일반 설정 (Key-Value) ---
    def _upsert_setting(self, key: str, value: str):
        self.db.execute_query('''
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        ''', (key, value))

    def _get_setting(self, key: str) -> str:
        row = self.db.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row['value'] if (row and row['value']) else ""

    # --- 2. Gemini & Telegram Config ---
    def get_gemini_config(self) -> Dict[str, Union[str, bool]]:
        val = self._get_setting(self.KEY_GEMINI_API_KEY)
        self.gemini_active = bool(val and val.strip())
        return {"value": val, "is_active": self.gemini_active}

    def save_gemini_config(self, api_key: str, is_active: bool):
        self.gemini_active = is_active
        self._upsert_setting(self.KEY_GEMINI_API_KEY, api_key)

    def get_telegram_config(self) -> Dict[str, Union[str, bool]]:
        val = self._get_setting(self.KEY_TELEGRAM_BOT_TOKEN)
        self.telegram_active = bool(val and val.strip())
        return {"value": val, "is_active": self.telegram_active}

    def save_telegram_config(self, token: str, is_active: bool):
        self.telegram_active = is_active
        self._upsert_setting(self.KEY_TELEGRAM_BOT_TOKEN, token)

    # --- 3. 서이추 메시지 (Row 단위) ---
    def get_neighbor_messages(self) -> List[str]:
        """테이블에서 메시지 목록 조회"""
        rows = self.db.fetch_all("SELECT message FROM neighbor_messages ORDER BY id ASC")
        return [row['message'] for row in rows]

    def save_neighbor_messages(self, messages: List[str]):
        """
        리스트 전체 저장:
        기존 데이터를 모두 지우고(DELETE) 새로 넣습니다(INSERT).
        (UI 목록과 DB 목록의 동기화를 위해 가장 확실한 방법)
        """
        # 1. 기존 데이터 삭제
        self.db.execute_query("DELETE FROM neighbor_messages")
        
        # 2. 새 데이터 입력
        for msg in messages:
            if msg.strip(): # 빈 문자열 제외
                self.db.execute_query(
                    "INSERT INTO neighbor_messages (message) VALUES (?)", 
                    (msg,)
                )

    # --- 4. 댓글 메시지 (Row 단위) ---
    def get_comment_messages(self) -> List[str]:
        rows = self.db.fetch_all("SELECT message FROM comment_messages ORDER BY id ASC")
        return [row['message'] for row in rows]

    def save_comment_messages(self, messages: List[str]):
        self.db.execute_query("DELETE FROM comment_messages")
        for msg in messages:
            if msg.strip():
                self.db.execute_query(
                    "INSERT INTO comment_messages (message) VALUES (?)", 
                    (msg,)
                )