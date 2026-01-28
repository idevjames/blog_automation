from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QLineEdit, QComboBox, QHBoxLayout, 
    QPushButton, QLabel, QCheckBox, QFrame, 
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt
import config
from bot_class.db_manager import BlogDB

class LikeTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)

        self.l_base = QGroupBox("📌 제어")
        form = QFormLayout(self.l_base)
        self.like_cnt = QLineEdit("50")
        self.like_pg = QLineEdit("1")
        form.addRow("목표 수:", self.like_cnt)
        form.addRow("시작 페이지:", self.like_pg)
        layout.addWidget(self.l_base)

        self.l_adv = QGroupBox("⚙️ 관리")
        vbox = QVBoxLayout(self.l_adv)
        btn_e = QPushButton("📂 딜레이/조건 설정 파일 열기")
        btn_e.setFixedHeight(30)
        btn_e.clicked.connect(lambda: self.main.open_txt_file(config.path_like_setup))
        vbox.addWidget(btn_e)
        layout.addWidget(self.l_adv)
        
        layout.addStretch()

        btns = QHBoxLayout()
        self.btn_run = QPushButton("🚀 실행 시작")
        self.btn_run.setObjectName("action_btn")
        self.btn_run.setFixedHeight(40)
        self.btn_run.clicked.connect(self.main.run_like_task)
        self.btn_stop = QPushButton("🛑 중단")
        self.btn_stop.setObjectName("stop_btn")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btns.addWidget(self.btn_run, 3)
        btns.addWidget(self.btn_stop, 1)
        layout.addLayout(btns)

class AddTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)

        self.a_base = QGroupBox("📌 제어")
        form = QFormLayout(self.a_base)
        self.combo_main = QComboBox()
        self.combo_sub = QComboBox()
        for cid, data in config.THEME_CATEGORIES.items():
            self.combo_main.addItem(data['name'], cid)
        self.combo_main.currentIndexChanged.connect(self.main.update_sub_combo)
        self.add_cnt = QLineEdit("20")
        self.add_pg = QLineEdit("1")
        form.addRow("대분류:", self.combo_main)
        form.addRow("상세주제:", self.combo_sub)
        form.addRow("목표 인원:", self.add_cnt)
        form.addRow("시작 페이지:", self.add_pg)
        layout.addWidget(self.a_base)

        self.a_adv = QGroupBox("⚙️ 관리")
        vbox = QVBoxLayout(self.a_adv)
        for t, p in [("📂 딜레이 설정", config.path_add_setup), 
                    ("📂 신청 메시지 목록", config.path_neighbor_msg), 
                    ("📂 서이추용 댓글 목록", config.path_comment_msg)]:
            btn = QPushButton(t)
            btn.setFixedHeight(25)
            btn.clicked.connect(lambda ch, path=p: self.main.open_txt_file(path))
            vbox.addWidget(btn)
        layout.addWidget(self.a_adv)
        
        layout.addStretch()

        btns = QHBoxLayout()
        self.btn_run = QPushButton("🚀 실행 시작")
        self.btn_run.setObjectName("action_btn")
        self.btn_run.setFixedHeight(40)
        self.btn_run.clicked.connect(self.main.run_add_task)
        self.btn_stop = QPushButton("🛑 중단")
        self.btn_stop.setObjectName("stop_btn")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        btns.addWidget(self.btn_run, 3)
        btns.addWidget(self.btn_stop, 1)
        layout.addLayout(btns)

class SmartNeighborManagementTab(QWidget):
    def __init__(self, parent_main):
        super().__init__()
        self.main = parent_main
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        
        conf = config.SMART_NEIGHBOR_CONFIG
        self.s_base = QGroupBox("📌 제어")
        form = QFormLayout(self.s_base)
        self.target_comment = QLineEdit(str(conf["conditions"].get("댓글목표", 20)))
        self.start_pg = QLineEdit(str(conf["conditions"].get("시작페이지", 1)))
        self.comment_interval = QLineEdit(str(conf["conditions"].get("댓글주기", 1)))
        form.addRow("댓글 목표:", self.target_comment)
        form.addRow("시작 페이지:", self.start_pg)
        form.addRow("주기(일):", self.comment_interval)
        layout.addWidget(self.s_base)
        
        self.inputs = {
            "댓글목표": self.target_comment, 
            "시작페이지": self.start_pg, 
            "방문주기": self.comment_interval
        }

        self.s_adv = QGroupBox("⚙️ AI/설정")
        vbox = QVBoxLayout(self.s_adv)
        hb = QHBoxLayout()
        self.ai_toggle = QCheckBox("🤖 Gemini AI 사용")
        self.ai_toggle.setChecked(config.GEMINI_CONFIG.get("USE_GEMINI", False))
        self.ai_toggle.stateChanged.connect(self.main.save_smart_settings)
        self.ai_status_msg = QLabel()
        hb.addWidget(self.ai_toggle)
        hb.addWidget(self.ai_status_msg)
        hb.addStretch()
        vbox.addLayout(hb)
        
        btns = QHBoxLayout()
        for t, p in [("📂 상세설명", config.path_smart_neighbor_management_setup), 
                    ("📂 AI 키", config.path_gemini_setup), 
                    ("📂 댓글목록", config.path_comment_msg)]:
            btn = QPushButton(t)
            btn.setFixedHeight(25)
            btn.clicked.connect(lambda ch, path=p: self.main.open_txt_file(path))
            btns.addWidget(btn)
        vbox.addLayout(btns)

        btn_reset = QPushButton("🗑️ 이웃점수DB초기화")
        btn_reset.setFixedHeight(25)
        # 붉은색 스타일로 경고 느낌 추가
        btn_reset.setStyleSheet("color: #FF6666; border: 1px solid #FF6666;") 
        btn_reset.clicked.connect(self.reset_db)
        vbox.addWidget(btn_reset)

        layout.addWidget(self.s_adv)

        self.s_ranking = QGroupBox("🏆 랭킹")
        rl = QVBoxLayout(self.s_ranking)
        
        # 헤더 섹션
        header = QFrame()
        header.setStyleSheet("background-color: #333; font-weight: bold; border-radius: 4px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(5, 2, 5, 2)
        hl.addWidget(QLabel("순위"), 1)
        hl.addWidget(QLabel("닉네임"), 3)
        hl.addWidget(QLabel("댓글"), 1)
        hl.addWidget(QLabel("답글"), 1)
        hl.addWidget(QLabel("공감"), 1)
        hl.addWidget(QLabel("점수"), 1)
        rl.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: #252526; border: none;")
        self.scroll_content = QWidget()
        self.ranking_vbox = QVBoxLayout(self.scroll_content)
        self.ranking_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        rl.addWidget(self.scroll)
        layout.addWidget(self.s_ranking)

        act = QHBoxLayout()
        self.btn_run = QPushButton("🚀 시작")
        self.btn_run.setObjectName("action_btn")
        self.btn_run.setFixedHeight(40)
        self.btn_run.clicked.connect(self.main.run_smart_neighbor_management_task)
        self.btn_stop = QPushButton("🛑 중단")
        self.btn_stop.setObjectName("stop_btn")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.main.stop_task)
        act.addWidget(self.btn_run, 3)
        act.addWidget(self.btn_stop, 1)
        layout.addLayout(act)
        self.refresh_ai_ui_status()

    def refresh_ai_ui_status(self):
        on = self.ai_toggle.isChecked()
        self.ai_status_msg.setText("● ON" if on else "● OFF")
        self.ai_status_msg.setStyleSheet(f"color: {'#2DB400' if on else '#C13535'}; font-size: 10px;")

    def update_ranking_ui(self, data):
        for i in reversed(range(self.ranking_vbox.count())):
            self.ranking_vbox.itemAt(i).widget().setParent(None)
        if not data: return
        for i, (nick, d) in enumerate(data, 1):
            row = QFrame()
            row.setFixedHeight(22)
            row.setStyleSheet("border-bottom: 1px solid #333;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(5, 0, 5, 0)
            rl.addWidget(QLabel(f"{i}위"), 1)
            rl.addWidget(QLabel(f"<b>{nick}</b>"), 3)
            rl.addWidget(QLabel(str(d.get('comment', 0))), 1)
            rl.addWidget(QLabel(str(d.get('reply', 0))), 1) # 답글 필드 추가
            rl.addWidget(QLabel(str(d.get('like', 0))), 1)
            rl.addWidget(QLabel(f"<span style='color:#2DB400;'>{d.get('score', 0)}</span>"), 1)
            self.ranking_vbox.addWidget(row)

    def reset_db(self):
        """이웃 점수 및 스캔 기록 초기화"""
        reply = QMessageBox.question(
            self, '초기화 경고', 
            '이웃 점수 통계와 마지막 스캔 시점을 모두 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = BlogDB()
            if db.reset_smart_data():
                self.update_ranking_ui([]) # 랭킹 화면 비우기
                QMessageBox.information(self, '완료', '이웃 점수 DB가 초기화되었습니다.')
            else:
                QMessageBox.critical(self, '오류', 'DB 초기화 중 문제가 발생했습니다.')