from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# 싱글턴 임포트
from service.add_neighbor_service import AddNeighborService
from service.logger import Logger

@dataclass
class AddNeighborState:
    is_running: bool = False
    current_page: int = 0
    total_try: int = 0
    success_count: int = 0
    fail_count: int = 0

class AddNeighborWorker(QThread):
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int, int, int) # Page, Total, Success, Fail

    def __init__(self, seq, no, count, page):
        super().__init__()
        self.args = (seq, no, count, page)
        # Worker 안에서도 서비스 싱글턴 호출
        self.service = AddNeighborService.instance()

    def run(self):
        # Service run에 콜백 함수 전달
        self.service.run(*self.args, progress_callback=self._report)
        self.finished_signal.emit()

    def _report(self, page, total, success, fail):
        self.progress_signal.emit(page, total, success, fail)

class AddNeighborViewModel(QObject):
    state_changed = pyqtSignal(AddNeighborState)

    def __init__(self):
        super().__init__()
        # [의존성 주입] Init에서 모두 할당
        self.logger = Logger.instance()
        self.service = AddNeighborService.instance()
        
        self._state = AddNeighborState()
        self.worker = None

    def start_work(self, seq, no, count, page):
        if self.worker and self.worker.isRunning(): return
        
        # 시작 로그는 Service 내부에서 .log()로 처리하므로 여기선 생략 가능
        # 또는 UI 반응을 위해 .print() 정도만 수행
        self.logger.print("⏳ 작업 스레드를 생성합니다...")
        
        # 상태 초기화
        self._update_state(is_running=True, current_page=page, total_try=0, success_count=0, fail_count=0)

        self.worker = AddNeighborWorker(seq, no, count, page)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.start()

    def stop_work(self):
        self.service.stop()
        self.logger.log("🛑 중단 요청을 보냈습니다. (진행 중인 작업 후 종료)")

    def _on_progress(self, page, total, success, fail):
        self._update_state(
            current_page=page, 
            total_try=total, 
            success_count=success, 
            fail_count=fail
        )

    def _on_finished(self):
        self._update_state(is_running=False)
        # 종료 로그는 Service에서 찍음

    def _update_state(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self._state, k, v)
        self.state_changed.emit(self._state)