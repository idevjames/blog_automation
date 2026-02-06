import sys
from dataclasses import dataclass
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal

# -------------------------------------------------------
# [1] 컴포넌트 & 뷰 임포트
# -------------------------------------------------------
from present.component.session_bar import SessionBar 
from present.home.gui_home_view import HomeView
from present.add_neighbor.gui_add_neighbor_view import AddNeighborView

# -------------------------------------------------------
# [2] 뷰모델 임포트 (인자 없이 생성 가능)
# -------------------------------------------------------
from present.main.main_session_viewmodel import SessionViewModel
from present.home.home_viewmodel import HomeViewModel
from present.add_neighbor.add_neighbor_viewmodel import AddNeighborViewModel

# -------------------------------------------------------
# [3] 싱글턴 로거 임포트
# -------------------------------------------------------
from service.logger import Logger

class GUIMainWindow(QMainWindow):
    # 다른 스레드(서비스)에서 로그가 들어올 때 UI 갱신을 위해 신호 사용
    log_signal = pyqtSignal(str)

    @dataclass 
    class State:
        current_tab_index: int = 0
        tabs = ["🏠 HOME", "🤝 서이추 작업"] 
        window_title = "Blog Automation V2"

    def __init__(self):
        super().__init__()
        
        self.state = self.State()
        self.log_view = None
        
        # 1. 윈도우 기본 설정
        self.setWindowTitle(self.state.window_title)
        self.resize(800, 800)
        
        # 2. UI 구성 (로그창 포함)
        self.init_ui()
        
        # 3. 로거 연결 (싱글턴)
        # "로그가 발생하면 log_signal을 방출해라"
        Logger.instance().set_ui_callback(self.log_signal.emit)
        
        # "log_signal이 방출되면 _append_log 메서드를 실행해라" (메인 스레드 실행 보장)
        self.log_signal.connect(self._append_log)
        
        Logger.instance().log("GUI 초기화 완료.")

    def init_ui(self):
        # 전체 스타일 설정
        self.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4; font-family: 'Malgun Gothic';")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -----------------------------------------------------------
        # [1] 상단 세션 관리 바
        # -----------------------------------------------------------
        # ViewModel 내부에서 LoginSessionService.instance()를 호출하므로 인자 불필요
        self.session_vm = SessionViewModel()
        self.session_bar = SessionBar()
        
        # 바인딩
        self.session_bar.login_clicked.connect(self.session_vm.open_browser_and_login)
        self.session_vm.status_changed.connect(self.session_bar.update_view)
        
        main_layout.addWidget(self.session_bar)

        # -----------------------------------------------------------
        # [2] 작업 영역 (스플리터)
        # -----------------------------------------------------------
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.setHandleWidth(1)
        self.v_splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")
        
        work_area = QWidget()
        work_layout = QHBoxLayout(work_area)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(0)

        # 사이드바 (탭 메뉴)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(160)
        self.sidebar.addItems(self.state.tabs)
        self.sidebar.setStyleSheet("""
            QListWidget { background-color: #252526; border-right: 1px solid #333; outline: none; }
            QListWidget::item { height: 60px; border-bottom: 1px solid #2D2D2D; padding-left: 15px; }
            QListWidget::item:selected { background-color: #37373D; color: #2DB400; border-left: 4px solid #2DB400; font-weight: bold; }
            QListWidget::item:hover { background-color: #2A2A2D; }
        """)

        # 탭 내용을 담을 스택 위젯
        self.stack = QStackedWidget()
        self._create_tabs()

        work_layout.addWidget(self.sidebar)
        work_layout.addWidget(self.stack)
        
        self.v_splitter.addWidget(work_area)

        # -----------------------------------------------------------
        # [3] 하단 로그 창
        # -----------------------------------------------------------
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #121212; 
                border-top: 1px solid #333; 
                color: #A0A0A0; 
                font-family: Consolas, 'Malgun Gothic'; 
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.v_splitter.addWidget(self.log_view)

        # 초기 스플리터 비율 설정 (7:3)
        self.v_splitter.setStretchFactor(0, 7)
        self.v_splitter.setStretchFactor(1, 3)

        main_layout.addWidget(self.v_splitter)

        # 이벤트 연결
        self.sidebar.currentRowChanged.connect(self._on_tab_changed)
        self.sidebar.setCurrentRow(self.state.current_tab_index)

        self.session_vm.open_browser_and_login()

    def _create_tabs(self):
        """State에 정의된 탭 리스트를 기반으로 View 생성"""
        for i, tab_name in enumerate(self.state.tabs):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none; background: transparent;")
            
            if i == 0: 
                # [HOME 탭]
                # ViewModel 생성 (인자 없음 -> 내부에서 Repo.instance() 호출)
                vm = HomeViewModel()
                tab_content = HomeView(vm)
                
            elif i == 1:
                # [서이추 탭]
                # ViewModel 생성 (인자 없음 -> 내부에서 Service.instance() 호출)
                vm = AddNeighborViewModel()
                tab_content = AddNeighborView(vm)
                
            else:
                # [준비 중]
                dummy = QWidget()
                layout = QVBoxLayout(dummy)
                layout.addWidget(QLabel(f"🚧 {tab_name} 준비 중...", alignment=Qt.AlignmentFlag.AlignCenter))
                tab_content = dummy
            
            scroll.setWidget(tab_content)
            self.stack.addWidget(scroll)

    def _on_tab_changed(self, index):
        """사이드바 탭 변경 시 호출"""
        self.state.current_tab_index = index
        self.stack.setCurrentIndex(index)

    def _append_log(self, msg: str):
        """실제 UI에 로그를 찍는 메서드 (Main Thread)"""
        if self.log_view:
            self.log_view.append(f"▶ {msg}")
            cursor = self.log_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_view.setTextCursor(cursor)