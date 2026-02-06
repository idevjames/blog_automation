from dataclasses import dataclass, field
from typing import List
from PyQt6.QtCore import QObject, pyqtSignal

from service.settings_repository import SettingsRepository
from service.logger import Logger

@dataclass
class HomeState:
    gemini_api_key: str = ""
    gemini_active: bool = False
    telegram_token: str = ""
    telegram_active: bool = False
    neighbor_messages: List[str] = field(default_factory=list)
    comment_messages: List[str] = field(default_factory=list)

class HomeViewModel(QObject):
    state_changed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.settings_repository = SettingsRepository.instance()
        self.logger = Logger.instance()
        self._state = HomeState()
        self.load_data()

    @property
    def state(self):
        return self._state

    def load_data(self):
        try:
            if not self.settings_repository: return

            # 설정값 로드
            gemini = self.settings_repository.get_gemini_config()
            self._state.gemini_api_key = gemini['value']
            self._state.gemini_active = gemini['is_active']

            tele = self.settings_repository.get_telegram_config()
            self._state.telegram_token = tele['value']
            self._state.telegram_active = tele['is_active']

            # 메시지 리스트 로드 (Repo의 명시적 메서드 호출)
            self._state.neighbor_messages = self.settings_repository.get_neighbor_messages()
            self._state.comment_messages = self.settings_repository.get_comment_messages()

            self.state_changed.emit(self._state)

        except Exception as e:
            self._handle_error(f"데이터 로드 실패: {str(e)}")

    # --- API 설정 관련 (기존 동일) ---
    def update_gemini_config(self, key: str, is_active: bool):
        self._state.gemini_api_key = key
        self._state.gemini_active = is_active
        try:
            if self.settings_repository:
                self.settings_repository.save_gemini_config(key, is_active)
            self.state_changed.emit(self._state)
        except Exception as e:
            self._handle_error(f"Gemini 저장 실패: {str(e)}")

    def update_telegram_config(self, token: str, is_active: bool):
        self._state.telegram_token = token
        self._state.telegram_active = is_active
        try:
            if self.settings_repository:
                self.settings_repository.save_telegram_config(token, is_active)
            self.state_changed.emit(self._state)
        except Exception as e:
            self._handle_error(f"Telegram 저장 실패: {str(e)}")

    # --- [수정] 명시적으로 분리된 메시지 저장 함수들 ---

    def save_neighbor_messages(self, new_list: List[str]):
        """서이추 메시지 리스트 통째로 저장"""
        try:
            if self.settings_repository:
                self.settings_repository.save_neighbor_messages(new_list)
            
            # State 갱신 및 UI 알림
            self._state.neighbor_messages = new_list
            self.state_changed.emit(self._state)
            self.logger.log("서이추 메시지 리스트가 저장되었습니다.")
            
        except Exception as e:
            self._handle_error(f"서이추 메시지 저장 실패: {str(e)}")

    def save_comment_messages(self, new_list: List[str]):
        """댓글 메시지 리스트 통째로 저장"""
        try:
            if self.settings_repository:
                self.settings_repository.save_comment_messages(new_list)
            
            # State 갱신 및 UI 알림
            self._state.comment_messages = new_list
            self.state_changed.emit(self._state)
            self.logger.log("댓글 메시지 리스트가 저장되었습니다.")
            
        except Exception as e:
            self._handle_error(f"댓글 메시지 저장 실패: {str(e)}")

    def _handle_error(self, msg):
        self.logger.log(msg)
        self.error_occurred.emit(msg)