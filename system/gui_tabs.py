from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QComboBox, QScrollArea, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit)
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

        self.l_adv = QGroupBox("⚙️ 고급 설정 (⏳ 최소~최대초 사이에서 랜덤값)")
        adv_vbox = QVBoxLayout(self.l_adv)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFixedHeight(230)
        scr_content = QWidget(); self.scr_form = QFormLayout(scr_content)
        self.inputs = {}
        for k, v in config.LIKES_NEIGHBOR_CONFIG["delays"].items():
            self.main._add_config_row(self.scr_form, self.inputs, k, v)
        for k, v in config.LIKES_NEIGHBOR_CONFIG["conditions"].items():
            s = QLineEdit(str(v)); self.scr_form.addRow(f"🔍 {k}:", s); self.inputs[k] = s
        scroll.setWidget(scr_content); adv_vbox.addWidget(scroll)
        btn_save = QPushButton("💾 공감 수치 설정 저장"); btn_save.setObjectName("save_btn")
        btn_save.clicked.connect(self.main.save_like_settings)
        adv_vbox.addWidget(btn_save); layout.addWidget(self.l_adv)

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

        self.a_adv = QGroupBox("⚙️ 고급 설정 (⏳ 최소~최대초 사이에서 랜덤값)")
        adv_vbox = QVBoxLayout(self.a_adv)
        f_btn_lay = QHBoxLayout()
        btn_o_msg = QPushButton("📂 서이추 메시지 열기"); btn_o_msg.setObjectName("file_btn")
        btn_o_cmt = QPushButton("📂 댓글 관리 열기"); btn_o_cmt.setObjectName("file_btn")
        btn_o_msg.clicked.connect(lambda: self.main.open_txt_file(config.path_neighbor_msg))
        btn_o_cmt.clicked.connect(lambda: self.main.open_txt_file(config.path_comment_msg))
        f_btn_lay.addWidget(btn_o_msg); f_btn_lay.addWidget(btn_o_cmt); adv_vbox.addLayout(f_btn_lay)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFixedHeight(230)
        scr_content = QWidget(); self.scr_form = QFormLayout(scr_content)
        self.inputs = {}
        for k, v in config.ADD_NEIGHBOR_CONFIG["delays"].items():
            self.main._add_config_row(self.scr_form, self.inputs, k, v)
        for k, v in config.ADD_NEIGHBOR_CONFIG["conditions"].items():
            s = QLineEdit(str(v)); self.scr_form.addRow(f"🔍 {k}:", s); self.inputs[k] = s
        scroll.setWidget(scr_content); adv_vbox.addWidget(scroll)
        btn_save = QPushButton("💾 서이추 수치 설정 저장"); btn_save.setObjectName("save_btn")
        btn_save.clicked.connect(self.main.save_add_settings)
        adv_vbox.addWidget(btn_save); layout.addWidget(self.a_adv)

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
        self.comment_interval = QLineEdit(str(config.NEIGHBOR_COMMENT_CONFIG["conditions"].get("방문주기", 3)))
        form.addRow("🎯 목표 인원:", self.comment_cnt)
        form.addRow("📑 시작 페이지:", self.comment_pg)
        form.addRow("📅 댓글 주기(일):", self.comment_interval)
        layout.addWidget(self.c_base)
        
        # [신규] Gemini AI 설정 그룹
        self.c_ai = QGroupBox("🤖 Gemini AI 설정 (자동 댓글)")
        ai_layout = QFormLayout(self.c_ai)
        
        self.ai_key = QLineEdit(config.GEMINI_CONFIG.get("GEMINI_API_KEY", ""))
        self.ai_key.setPlaceholderText("Gemini API Key를 입력하세요")
        self.ai_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit) # 보안용
        
        self.ai_prompt = QTextEdit()
        self.ai_prompt.setPlainText(config.GEMINI_CONFIG.get("GEMINI_PROMPT", ""))
        self.ai_prompt.setFixedHeight(80)
        self.ai_prompt.setPlaceholderText("AI에게 시킬 명령어를 입력하세요")
        
        ai_layout.addRow("🔑 API Key:", self.ai_key)
        ai_layout.addRow("📝 프롬프트:", self.ai_prompt)
        layout.addWidget(self.c_ai)

        self.c_adv = QGroupBox("⚙️ 고급 설정 (⏳ neighbor_history.db 연동)")
        adv_vbox = QVBoxLayout(self.c_adv)
        btn_o_cmt_msg = QPushButton("📂 댓글 관리 열기"); btn_o_cmt_msg.setObjectName("file_btn")
        btn_o_cmt_msg.clicked.connect(lambda: self.main.open_txt_file(config.path_comment_msg))
        adv_vbox.addWidget(btn_o_cmt_msg)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFixedHeight(230)
        scr_content = QWidget(); self.scr_form = QFormLayout(scr_content)
        self.inputs = {}
        for k, v in config.NEIGHBOR_COMMENT_CONFIG["delays"].items():
            self.main._add_config_row(self.scr_form, self.inputs, k, v)
        for k, v in config.NEIGHBOR_COMMENT_CONFIG["conditions"].items():
            if k == "방문주기": continue
            s = QLineEdit(str(v)); self.scr_form.addRow(f"🔍 {k}:", s); self.inputs[k] = s
        scroll.setWidget(scr_content); adv_vbox.addWidget(scroll)
        btn_save = QPushButton("💾 AI 설정 & 댓글 수치 설정 저장"); btn_save.setObjectName("save_btn")
        btn_save.clicked.connect(self.main.save_comment_settings)
        adv_vbox.addWidget(btn_save); layout.addWidget(self.c_adv)

        btn_hbox = QHBoxLayout()
        self.btn_run = QPushButton("🚀 이웃 댓글 시작"); self.btn_run.setObjectName("action_btn"); self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.main.run_comment_task)
        self.btn_stop = QPushButton("🛑 작업 중단"); self.btn_stop.setObjectName("stop_btn"); self.btn_stop.setFixedHeight(50); self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btn_hbox.addWidget(self.btn_run, 2); btn_hbox.addWidget(self.btn_stop, 1)
        layout.addLayout(btn_hbox)