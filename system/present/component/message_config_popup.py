from typing import List, Callable
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

class MessageManagePopup(QDialog):
    def __init__(self, title: str, initial_data: List[str], save_callback: Callable[[List[str]], None]):
        """
        :param title: 팝업창 제목
        :param initial_data: 편집할 초기 문자열 리스트
        :param save_callback: 저장 버튼 클릭 시 실행할 함수 (인자로 수정된 리스트를 넘김)
        """
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(1000, 600)
        
        # 외부 의존성 없이 받은 데이터만 가지고 놈 (Deep Copy)
        self.temp_list = list(initial_data)
        self.save_callback = save_callback
        
        self.init_ui()
        self.render_local()

    def init_ui(self):
        self.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4;")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #2D2D2D; border: 1px solid #444; border-radius: 4px; padding: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #383838; }
            QListWidget::item:selected { background-color: #37373D; color: #2DB400; }
        """)
        layout.addWidget(self.list_widget)

        # 입력 영역
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("메시지 입력...")
        self.input_field.setStyleSheet("background-color: #2D2D2D; border: 1px solid #444; padding: 8px; color: white;")
        
        self.btn_add = QPushButton("추가")
        self.btn_add.setFixedSize(60, 35)
        self.btn_add.setStyleSheet("background-color: #333; border: 1px solid #555; color: white;")
        self.btn_add.clicked.connect(self._on_local_add)
        self.input_field.returnPressed.connect(self._on_local_add)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_add)
        layout.addLayout(input_layout)

        # 삭제 버튼
        self.btn_delete = QPushButton("선택 항목 삭제")
        self.btn_delete.setStyleSheet("background-color: #4A2020; color: #FFAAAA; border: 1px solid #603030; padding: 8px;")
        self.btn_delete.clicked.connect(self._on_local_delete)
        layout.addWidget(self.btn_delete)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)

        # 하단 버튼 (취소 / 저장)
        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setFixedSize(80, 35)
        self.btn_cancel.setStyleSheet("background-color: #444; color: white; border: none; border-radius: 4px;")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("완료 (저장)")
        self.btn_save.setFixedSize(120, 35)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #2DB400; color: white; border: none; border-radius: 4px; font-weight: bold;}
            QPushButton:hover { background-color: #35D600; }
        """)
        self.btn_save.clicked.connect(self._on_sync_save)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def render_local(self):
        """임시 리스트 UI 갱신"""
        self.list_widget.clear()
        self.list_widget.addItems(self.temp_list)

    def _on_local_add(self):
        text = self.input_field.text().strip()
        if not text: return
        if text in self.temp_list:
            QMessageBox.warning(self, "중복", "이미 목록에 있는 메시지입니다.")
            return

        self.temp_list.append(text)
        self.input_field.clear()
        self.render_local()

    def _on_local_delete(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.temp_list.pop(row)
            self.render_local()
        else:
            QMessageBox.warning(self, "알림", "삭제할 항목을 선택해주세요.")

    def _on_sync_save(self):
        """
        저장 버튼 클릭 시:
        1. 생성자에서 받은 콜백 함수(ViewModel의 메서드)를 실행
        2. 인자로 수정된 리스트 전달
        3. 팝업 닫기
        """
        if self.save_callback:
            self.save_callback(self.temp_list)
        self.accept()