from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal

class SessionBar(QWidget):
    # [출력] 외부(Window)로 "나 눌렸어!"라고 알리는 신호
    login_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        # 버튼 클릭 시 내부 로직 없이 신호만 발송
        self.btn_login.clicked.connect(self.login_clicked.emit)

    def init_ui(self):
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("background-color: #FF5555; border-radius: 6px;")

        self.status_label = QLabel("로그인 필요")
        self.status_label.setStyleSheet("color: #FF5555; font-weight: bold; margin-left: 5px;")

        self.btn_login = QPushButton("브라우저 열기 / 로그인")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet(self._btn_style_red())

        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        layout.addWidget(self.btn_login)

    # [입력] 외부에서 상태를 주면 그림만 그림
    def update_view(self, is_connected: bool, text: str):
        self.status_label.setText(text)
        if is_connected:
            self.status_indicator.setStyleSheet("background-color: #2DB400; border-radius: 6px;")
            self.status_label.setStyleSheet("color: #2DB400; font-weight: bold; margin-left: 5px;")
            self.btn_login.setText("브라우저 확인")
            self.btn_login.setStyleSheet(self._btn_style_green())
        else:
            self.status_indicator.setStyleSheet("background-color: #FF5555; border-radius: 6px;")
            self.status_label.setStyleSheet("color: #FF5555; font-weight: bold; margin-left: 5px;")
            self.btn_login.setText("브라우저 열기 / 로그인")
            self.btn_login.setStyleSheet(self._btn_style_red())

    def _btn_style_red(self):
        return """
            QPushButton { background-color: #333; color: white; border: 1px solid #555; border-radius: 4px; padding: 5px 15px; }
            QPushButton:hover { background-color: #444; border: 1px solid #FF5555; }
        """
    def _btn_style_green(self):
        return """
            QPushButton { background-color: #1E3A1E; color: #88FF88; border: 1px solid #2DB400; border-radius: 4px; padding: 5px 15px; }
            QPushButton:hover { background-color: #254525; }
        """