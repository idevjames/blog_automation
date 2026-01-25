from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QComboBox, QHBoxLayout, 
                             QPushButton, QLabel, QCheckBox, QFrame, QScrollArea)
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
        self.btn_run = QPushButton("🚀 이웃 공감 시작"); 
        self.btn_run.setObjectName("action_btn"); 
        self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.main.run_like_task)
        self.btn_stop = QPushButton("🛑 작업 중단"); 
        self.btn_stop.setObjectName("stop_btn"); 
        self.btn_stop.setFixedHeight(50); 
        self.btn_stop.setEnabled(False)
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
        
class SmartNeighborManagementTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        conf = config.SMART_NEIGHBOR_CONFIG

        # 1. 핵심 제어 영역 (단순화됨)
        self.s_base = QGroupBox("📌 스마트 관리 목표")
        form = QFormLayout(self.s_base)
        
        # [수정] 목표를 '댓글 목표' 하나로 통일
        self.target_comment = QLineEdit(str(conf["conditions"].get("댓글목표", 20)))
        self.start_pg = QLineEdit(str(conf["conditions"].get("시작페이지", 1)))
        self.comment_interval = QLineEdit(str(conf["conditions"].get("댓글주기", 1)))
        
        form.addRow("💬 댓글 목표(AI/일반):", self.target_comment)
        form.addRow("📑 시작 페이지:", self.start_pg)
        form.addRow("📅 댓글 주기(일):", self.comment_interval)
        layout.addWidget(self.s_base)

        self.inputs = {
            "댓글목표": self.target_comment,
            "시작페이지": self.start_pg,
            "방문주기": self.comment_interval
        }

        # 2. 설정 관리 (기존 동일)
        self.s_adv = QGroupBox("⚙️ 설정 관리")
        adv_vbox = QVBoxLayout(self.s_adv)
        
        status_hbox = QHBoxLayout()
        self.ai_toggle = QCheckBox("🤖 Gemini AI 자동 댓글")
        self.ai_toggle.setStyleSheet("font-weight: bold;")
        self.ai_toggle.setChecked(config.GEMINI_CONFIG.get("USE_GEMINI", False))
        self.ai_toggle.stateChanged.connect(self.main.save_smart_settings)
        
        self.ai_status_msg = QLabel("비활성화 상태")
        self.ai_status_msg.setStyleSheet("color: #C13535;")
        
        status_hbox.addWidget(self.ai_toggle)
        status_hbox.addWidget(self.ai_status_msg)
        status_hbox.addStretch()
        adv_vbox.addLayout(status_hbox)

        btn_hbox = QHBoxLayout()
        btn_smart_edit = QPushButton("📂 상세 설정 수정")
        btn_smart_edit.clicked.connect(lambda: self.main.open_txt_file(config.path_smart_neighbor_management_setup))
        btn_ai_edit = QPushButton("📂 AI 키 수정")
        btn_ai_edit.clicked.connect(lambda: self.main.open_txt_file(config.path_gemini_setup))
        
        btn_hbox.addWidget(btn_smart_edit)
        btn_hbox.addWidget(btn_ai_edit)
        adv_vbox.addLayout(btn_hbox)
        layout.addWidget(self.s_adv)

        # 3. 랭킹 (기존 동일)
        self.s_ranking = QGroupBox("🏆 이웃 활동 지수 랭킹 (전체)")
        ranking_layout = QVBoxLayout(self.s_ranking)
        
        header = QFrame()
        header.setStyleSheet("background-color: #333; font-weight: bold; border-radius: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.addWidget(QLabel("순위"), 1)
        h_layout.addWidget(QLabel("닉네임"), 3)
        h_layout.addWidget(QLabel("댓글(+5)"), 2)
        h_layout.addWidget(QLabel("공감(+1)"), 2)
        h_layout.addWidget(QLabel("총점"), 2)
        ranking_layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #252526; border: none;")
        self.scroll_content = QWidget()
        self.ranking_vbox = QVBoxLayout(self.scroll_content)
        self.ranking_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        ranking_layout.addWidget(self.scroll)
        layout.addWidget(self.s_ranking)

        # 4. 실행 버튼
        act_hbox = QHBoxLayout()
        self.btn_run = QPushButton("🚀 스마트 관리 시작")
        self.btn_run.setObjectName("action_btn")
        self.btn_run.setFixedHeight(45)
        self.btn_run.clicked.connect(self.main.run_smart_neighbor_management_task)
        
        self.btn_stop = QPushButton("🛑 중단")
        self.btn_stop.setObjectName("stop_btn")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        
        act_hbox.addWidget(self.btn_run, 2)
        act_hbox.addWidget(self.btn_stop, 1)
        layout.addLayout(act_hbox)
        
        self.refresh_ai_ui_status()

    # (나머지 메서드 update_ranking_ui, refresh_ai_ui_status 등은 기존 유지)
    def refresh_ai_ui_status(self):
        is_checked = self.ai_toggle.isChecked()
        api_key = config.GEMINI_CONFIG.get("GEMINI_API_KEY", "").strip()
        prompt = config.GEMINI_CONFIG.get("GEMINI_PROMPT", "").strip()
        if not is_checked:
            self.ai_toggle.setStyleSheet("font-weight: bold; color: #C13535;")
            self.ai_status_msg.setText("● AI 기능이 비활성화 상태입니다.")
            self.ai_status_msg.setStyleSheet("color: #C13535; font-size: 11px; margin-left: 20px;")
        else:
            if not api_key or not prompt:
                self.ai_toggle.setStyleSheet("font-weight: bold; color: #C13535;")
                self.ai_status_msg.setText("● 필수 설정 누락")
                self.ai_status_msg.setStyleSheet("color: #C13535; font-size: 11px; margin-left: 20px; font-weight: bold;")
            else:
                self.ai_toggle.setStyleSheet("font-weight: bold; color: #2DB400;")
                self.ai_status_msg.setText("● AI 기능 정상")
                self.ai_status_msg.setStyleSheet("color: #2DB400; font-size: 11px; margin-left: 20px;")

    def update_ranking_ui(self, neighbor_data):
        for i in reversed(range(self.ranking_vbox.count())): 
            self.ranking_vbox.itemAt(i).widget().setParent(None)
        if not neighbor_data:
            self.ranking_vbox.addWidget(QLabel("데이터가 없습니다."))
            return
        for i, (nick, data) in enumerate(neighbor_data, 1):
            row = QFrame()
            row.setStyleSheet("border-bottom: 1px solid #333; padding: 0px; margin: 0px;")
            row.setFixedHeight(22)
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(5, 0, 5, 0); r_layout.setSpacing(10)
            lbl_rank = QLabel(f"{i}위"); lbl_rank.setFixedWidth(35)
            lbl_nick = QLabel(f"<b>{nick}</b>")
            lbl_comm = QLabel(f"💬{data['comment']}"); lbl_comm.setFixedWidth(50)
            lbl_like = QLabel(f"❤️{data['like']}"); lbl_like.setFixedWidth(50)
            lbl_score = QLabel(f"<span style='color:#2DB400;'>{data['score']}</span>")
            lbl_score.setFixedWidth(45)
            lbl_score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            r_layout.addWidget(lbl_rank); r_layout.addWidget(lbl_nick, stretch=1)
            r_layout.addWidget(lbl_comm); r_layout.addWidget(lbl_like); r_layout.addWidget(lbl_score)
            self.ranking_vbox.addWidget(row)