from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QComboBox, QHBoxLayout, 
                             QPushButton, QLabel, QCheckBox)
from PyQt6.QtCore import Qt
import config

class LikeTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.l_base = QGroupBox("📌 핵심 제어")
        form = QFormLayout(self.l_base)
        self.like_cnt = QLineEdit("50")
        self.like_pg = QLineEdit("1")
        form.addRow("🎯 목표 수:", self.like_cnt)
        form.addRow("📑 시작 페이지:", self.like_pg)
        layout.addWidget(self.l_base)

        # [수정] 고급 설정 영역 단순화
        self.l_adv = QGroupBox("⚙️ 설정 관리")
        adv_vbox = QVBoxLayout(self.l_adv)
        btn_edit = QPushButton("📂 공감 상세 설정(딜레이/조건) 수정하기")
        btn_edit.setFixedHeight(45)
        btn_edit.clicked.connect(lambda: self.main.open_txt_file(config.path_like_setup))
        adv_vbox.addWidget(btn_edit)
        layout.addWidget(self.l_adv)

        layout.addStretch()

        btn_hbox = QHBoxLayout()
        self.btn_run = QPushButton("🚀 이웃 공감 시작"); self.btn_run.setObjectName("action_btn"); self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.main.run_like_task)
        self.btn_stop = QPushButton("🛑 작업 중단"); self.btn_stop.setObjectName("stop_btn"); self.btn_stop.setFixedHeight(50); self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btn_hbox.addWidget(self.btn_run, 2); btn_hbox.addWidget(self.btn_stop, 1)
        layout.addLayout(btn_hbox)

class AddTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.a_base = QGroupBox("📌 핵심 제어")
        form = QFormLayout(self.a_base)
        self.combo_main = QComboBox(); self.combo_sub = QComboBox()
        for cid, cdata in config.THEME_CATEGORIES.items(): self.combo_main.addItem(cdata['name'], cid)
        self.combo_main.currentIndexChanged.connect(self.main.update_sub_combo)
        self.add_cnt = QLineEdit("20"); self.add_pg = QLineEdit("1")
        form.addRow("📁 대분류:", self.combo_main); form.addRow("🏷️ 상세주제:", self.combo_sub)
        form.addRow("🎯 목표 인원:", self.add_cnt); form.addRow("📑 시작 페이지:", self.add_pg)
        layout.addWidget(self.a_base)

        # [수정] 고급 설정 영역 단순화
        self.a_adv = QGroupBox("⚙️ 설정 관리")
        adv_vbox = QVBoxLayout(self.a_adv)
        
        btn_paths = [
            ("📂 서이추 상세 설정(딜레이/조건) 수정", config.path_add_setup),
            ("📂 서이추 신청 메시지 목록 수정", config.path_neighbor_msg),
            ("📂 서이추용 댓글 목록 수정", config.path_comment_msg)
        ]
        for text, path in btn_paths:
            btn = QPushButton(text)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, p=path: self.main.open_txt_file(p))
            adv_vbox.addWidget(btn)
            
        layout.addWidget(self.a_adv)
        layout.addStretch()

        btn_hbox = QHBoxLayout()
        self.btn_run = QPushButton("🚀 서로이웃 신청 시작"); self.btn_run.setObjectName("action_btn"); self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.main.run_add_task)
        self.btn_stop = QPushButton("🛑 작업 중단"); self.btn_stop.setObjectName("stop_btn"); self.btn_stop.setFixedHeight(50); self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btn_hbox.addWidget(self.btn_run, 2); btn_hbox.addWidget(self.btn_stop, 1)
        layout.addLayout(btn_hbox)

class CommentTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.c_base = QGroupBox("📌 핵심 제어")
        form = QFormLayout(self.c_base)
        self.comment_cnt = QLineEdit("30")
        self.comment_pg = QLineEdit("1")
        self.comment_interval = QLineEdit("3")
        form.addRow("🎯 목표 인원:", self.comment_cnt)
        form.addRow("📑 시작 페이지:", self.comment_pg)
        form.addRow("📅 댓글 주기(일):", self.comment_interval)
        layout.addWidget(self.c_base)
        
        # [수정] 고급 설정 영역 단순화 (AI 설정 포함)
        self.c_adv = QGroupBox("⚙️ 설정 관리")
        adv_vbox = QVBoxLayout(self.c_adv)
        
        btn_paths = [
            ("📂 댓글 상세 설정(딜레이/조건) 수정", config.path_comment_setup),
            ("📂 AI(Gemini) API키 및 프롬프트 수정", config.path_gemini_setup),
            ("📂 댓글 내용 목록 수정", config.path_comment_msg)
        ]
        for text, path in btn_paths:
            btn = QPushButton(text)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, p=path: self.main.open_txt_file(p))
            adv_vbox.addWidget(btn)
            
        layout.addWidget(self.c_adv)
        layout.addStretch()

        btn_hbox = QHBoxLayout()
        self.btn_run = QPushButton("🚀 이웃 댓글 시작"); self.btn_run.setObjectName("action_btn"); self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.main.run_comment_task)
        self.btn_stop = QPushButton("🛑 작업 중단"); self.btn_stop.setObjectName("stop_btn"); self.btn_stop.setFixedHeight(50); self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btn_hbox.addWidget(self.btn_run, 2); btn_hbox.addWidget(self.btn_stop, 1)
        layout.addLayout(btn_hbox)