import threading
from typing import Callable, Optional

class Logger:
    _instance: Optional['Logger'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.ui_callback: Optional[Callable[[str], None]] = None
        self.tg_callback: Optional[Callable[[str], None]] = None

    @classmethod
    def instance(cls) -> 'Logger':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_ui_callback(self, callback: Callable[[str], None]):
        """GUI 로그창 출력용 (Main Window에서 연결)"""
        self.ui_callback = callback

    def set_tg_callback(self, callback: Callable[[str], None]):
        """텔레그램 전송용 (Bot에서 연결)"""
        self.tg_callback = callback

    def print(self, message: str):
        """
        [일반 로그] 터미널 + GUI
        - 작업 진행 과정, 단순 정보 등 (Debug/Info 성격)
        """
        # 1. 터미널 출력
        print(f"{message}")
        
        # 2. GUI 출력
        if self.ui_callback:
            try: self.ui_callback(message)
            except: pass

    def log(self, message: str):
        """
        [중요 로그] 터미널 + GUI + 텔레그램
        - 작업 시작/종료, 에러, 제한 도달 등 알림이 필요한 경우 (Notice/Error 성격)
        """
        # 1. 일반 출력 (터미널+GUI) 포함
        self.print(f"✴️✴️ {message}")

        # 2. 텔레그램 전송
        if self.tg_callback:
            try: self.tg_callback(message)
            except: pass