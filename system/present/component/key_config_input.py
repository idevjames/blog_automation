from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal

class KeyConfigInput(QWidget):
    # 사용자 수정 시 신호: (값, 활성여부)
    config_changed = pyqtSignal(str, bool)

    def __init__(self, title, description, placeholder=""):
        super().__init__()
        self.title_text = title
        self.desc_text = description
        self.placeholder_text = placeholder
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 제목
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("font-weight: bold; color: #BBBBBB; font-size: 13px;")
        
        # 입력 행
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.checkbox = QCheckBox()
        self.status_label = QLabel("비활성")
        self.status_label.setFixedWidth(55)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder_text)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_field.setStyleSheet("""
            QLineEdit { background-color: #2D2D2D; border: 1px solid #444; border-radius: 4px; padding: 5px; color: white; }
            QLineEdit:focus { border: 1px solid #2DB400; }
        """)

        row.addWidget(self.checkbox, 0)
        row.addWidget(self.status_label, 0)
        row.addWidget(self.input_field, 1)
        
        # 설명
        self.desc_label = QLabel(self.desc_text)
        self.desc_label.setStyleSheet("color: #777777; font-size: 11px;")
        
        layout.addWidget(self.title_label)
        layout.addLayout(row)
        layout.addWidget(self.desc_label)

        # 이벤트 -> 신호 전달
        self.input_field.returnPressed.connect(self._emit_change)
        self.checkbox.clicked.connect(self._emit_change)

    def _emit_change(self):
        # 부모에게 현재 상태 보고
        self.config_changed.emit(self.input_field.text().strip(), self.checkbox.isChecked())

    def update_view(self, value: str, is_active: bool):
        """VM 데이터로 UI 동기화"""
        if self.input_field.text() != value:
            self.input_field.setText(value)
        
        self.checkbox.setEnabled(bool(value)) # 값이 있어야 활성 가능
        self.checkbox.setChecked(is_active)
        
        if is_active:
            self.status_label.setText("활성")
            self.status_label.setStyleSheet("color: #2DB400;")
        else:
            self.status_label.setText("비활성")
            self.status_label.setStyleSheet("color: #888888;")