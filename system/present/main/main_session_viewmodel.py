from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from service.login_session_service import LoginSessionService
from service.logger import Logger

# 백그라운드 작업 (로그인 대기)
class LoginWorker(QThread):
    finished = pyqtSignal(bool, str) # 성공여부, 메시지

    def __init__(self):
        super().__init__()
        self.service = LoginSessionService.instance()

    def run(self):
        try:
            # Service의 Blocking 함수 실행
            self.service.ensure_session()
            self.finished.emit(True, "로그인 세션이 확인되었습니다.")
        except Exception as e:
            self.finished.emit(False, str(e))

class SessionViewModel(QObject):
    # View에 전달할 데이터 신호 (is_active, text)
    status_changed = pyqtSignal(bool, str) 
    
    def __init__(self):
        super().__init__()
        self.service = LoginSessionService.instance()
        self.logger = Logger.instance()
        self.worker = None

        # 2초마다 브라우저 생존 확인
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_browser_health)
        self.monitor_timer.start(2000)

    def open_browser_and_login(self):
        """View에서 버튼을 누르면 이 함수가 호출됨"""
        if self.worker and self.worker.isRunning():
            self.logger.log("⚠️ 작업이 이미 진행 중입니다.")
            return

        # 브라우저가 살아있고 로그인도 되어있다면
        if self.service.is_browser_alive() and self.service._check_cookies():
             self.logger.log("✅ 이미 로그인이 완료된 상태입니다.")
             self._update_status(True)
             return

        self.logger.log("🚀 브라우저를 열고 로그인을 시도합니다...")
        self.status_changed.emit(False, "연결 중...") 

        # 스레드 시작
        self.worker = LoginWorker()
        self.worker.finished.connect(self._on_login_finished)
        self.worker.start()

    def _on_login_finished(self, success, msg):
        if success:
            self.logger.log(f"✅ {msg}")
            self._update_status(True)
        else:
            self.logger.log(f"❌ {msg}")
            self._update_status(False)

    def _check_browser_health(self):
        # 작업 중일 땐 감시 안 함
        if self.worker and self.worker.isRunning():
            return

        if self.service.is_browser_alive():
            self._update_status(True)
        else:
            self._update_status(False)

    def _update_status(self, is_alive):
        if is_alive:
            self.status_changed.emit(True, "연결됨 (로그인 완료)")
        else:
            self.status_changed.emit(False, "로그인 필요")