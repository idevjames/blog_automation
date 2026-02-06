from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

# 컴포넌트 & VM 임포트
from present.component.key_config_input import KeyConfigInput
from present.component.message_config_popup import MessageManagePopup
from present.home.home_viewmodel import HomeViewModel, HomeState

class HomeView(QWidget):
    def __init__(self, vm: HomeViewModel):
        super().__init__()
        self.vm = vm
        
        # 2. UI 구성
        self.init_ui()
        
        # 3. Data Binding (VM -> View)
        # VM의 데이터가 변하면 render 함수 실행
        self.vm.state_changed.connect(self.render)
        
        # 최초 1회 렌더링 (VM의 초기값으로)
        self.render(self.vm.state)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(25)

        # --- 1. Gemini 컴포넌트 ---
        self.gemini_input = KeyConfigInput(
            title="🔑 Gemini API Key",
            description="블로그 본문 생성 및 문맥 분석용",
            placeholder="Enter Gemini API Key..."
        )
        # Event Binding (View -> VM)
        self.gemini_input.config_changed.connect(self.vm.update_gemini_config)
        layout.addWidget(self.gemini_input)

        # --- 2. Telegram 컴포넌트 ---
        self.telegram_input = KeyConfigInput(
            title="📡 Telegram Bot Token",
            description="원격 제어 및 알림용",
            placeholder="Enter Bot Token..."
        )
        # Event Binding (View -> VM)
        self.telegram_input.config_changed.connect(self.vm.update_telegram_config)
        layout.addWidget(self.telegram_input)

# --- 구분선 (선택사항, 깔끔함을 위해 추가) ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)

        # --- 3. 메시지 관리 섹션 (세로 배치) ---
        msg_layout = QVBoxLayout()
        msg_layout.setSpacing(20) # 그룹 간 간격

        # [그룹 A] 서이추 메시지
        neighbor_group = QVBoxLayout()
        neighbor_group.setSpacing(8) # 텍스트와 버튼 사이 간격

        lbl_neighbor = QLabel("서로이웃추가 시 작성할 메세지 리스트입니다. \n랜덤으로 가져와서 사용되니 범용적으로 사용되도록 설정해주세요.")
        lbl_neighbor.setStyleSheet("color: #888; font-size: 12px;")
        
        self.btn_neighbor = QPushButton("🤝 서이추 신청 메시지 관리")
        self.btn_neighbor.setFixedHeight(45) # 높이만 고정, 너비는 꽉 차게
        self.btn_neighbor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_neighbor.setStyleSheet(self._outline_btn_style())
        self.btn_neighbor.clicked.connect(self._open_neighbor_popup)

        neighbor_group.addWidget(lbl_neighbor)
        neighbor_group.addWidget(self.btn_neighbor)

        # [그룹 B] 댓글 메시지
        comment_group = QVBoxLayout()
        comment_group.setSpacing(8)

        lbl_comment = QLabel("자동 댓글 작성 시 사용할 메세지 리스트입니다.\n랜덤으로 가져와서 사용되니 범용적으로 사용되도록 설정해주세요.")
        lbl_comment.setStyleSheet("color: #888; font-size: 12px;")

        self.btn_comment = QPushButton("💬 댓글 작성 메시지 관리")
        self.btn_comment.setFixedHeight(45)
        self.btn_comment.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_comment.setStyleSheet(self._outline_btn_style())
        self.btn_comment.clicked.connect(self._open_comment_popup)

        comment_group.addWidget(lbl_comment)
        comment_group.addWidget(self.btn_comment)

        # 전체 레이아웃에 추가
        msg_layout.addLayout(neighbor_group)
        msg_layout.addLayout(comment_group)
        
        layout.addLayout(msg_layout)

    def _outline_btn_style(self):
        """아웃라인 스타일 (테두리 강조)"""
        return """
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #D4D4D4;
                font-family: 'Malgun Gothic';
                font-size: 13px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                border: 1px solid #2DB400; /* 네이버 그린 */
                color: #2DB400;
                background-color: #252526;
            }
            QPushButton:pressed {
                background-color: #1E1E1E;
                border: 1px solid #1E5000;
            }
        """
    def _open_neighbor_popup(self):
        """서이추 메시지 관리 팝업"""
        # 팝업 생성 시 필요한 데이터와 함수를 직접 꽂아줍니다.
        popup = MessageManagePopup(
            title="🤝 서이추 신청 메시지 관리",
            initial_data=self.vm.state.neighbor_messages,  # 초기 데이터
            save_callback=self.vm.save_neighbor_messages   # 저장 시 호출할 VM 함수
        )
        popup.exec()

    def _open_comment_popup(self):
        """댓글 메시지 관리 팝업"""
        popup = MessageManagePopup(
            title="💬 댓글 메시지 관리",
            initial_data=self.vm.state.comment_messages,   # 초기 데이터
            save_callback=self.vm.save_comment_messages    # 저장 시 호출할 VM 함수
        )
        popup.exec()

    def render(self, state: HomeState):
        """ViewModel의 State를 UI에 반영"""
        # Gemini 상태 반영
        self.gemini_input.update_view(state.gemini_api_key, state.gemini_active)
        
        # Telegram 상태 반영
        self.telegram_input.update_view(state.telegram_token, state.telegram_active)