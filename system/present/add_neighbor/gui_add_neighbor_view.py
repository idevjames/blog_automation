from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from present.add_neighbor.add_neighbor_viewmodel import AddNeighborViewModel, AddNeighborState

class AddNeighborView(QWidget):
    THEME_CATEGORIES = {
        1: {"name": "엔터테인먼트/예술", "sub": {0: "전체", 5: "문학/책", 6: "영화", 8: "미술/디자인", 7: "공연/전시", 11: "음악", 9: "드라마", 12: "스타/연예인", 13: "만화/애니", 10: "방송"}},
        2: {"name": "생활/노하우/쇼핑", "sub": {0: "전체", 14: "일상/생각", 15: "육아/결혼", 16: "반려동물", 17: "좋은글/이미지", 18: "패션/미용", 19: "인테리어/DIY", 20: "요리/레시피", 21: "상품리뷰", 36: "원예/재배"}},
        3: {"name": "취미/여가/여행", "sub": {0: "전체", 22: "게임", 23: "스포츠", 24: "사진", 25: "자동차", 26: "취미", 27: "국내여행", 28: "세계여행", 29: "맛집"}},
        4: {"name": "지식/동향", "sub": {0: "전체", 30: "IT/컴퓨터", 31: "사회/정치", 32: "건강/의학", 33: "비지니스/경제", 35: "어학/외국어", 34: "교육/학문"}}
    }

    def __init__(self, view_model: AddNeighborViewModel):
        super().__init__()
        self.view_model = view_model
        self.init_ui()
        self.view_model.state_changed.connect(self.render)
        self.render(AddNeighborState())

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        # [1] 카드 위젯 (좌측 고정, 너비 420px)
        self.card_widget = QWidget()
        self.card_widget.setFixedWidth(420)
        self.card_widget.setStyleSheet("""
            QWidget { background-color: #252526; border-radius: 12px; border: 1px solid #3E3E42; }
            QLabel { color: #D4D4D4; border: none; background: transparent; }
        """)

        card_layout = QVBoxLayout(self.card_widget)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # 타이틀
        title = QLabel("🤝 서이추 자동화")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        card_layout.addWidget(title)

        # 설명
        desc = QLabel("주제, 인원, 페이지를 설정하고 작업을 시작하세요.\n진행 상황은 아래 대시보드에 실시간 표시됩니다.")
        desc.setStyleSheet("color: #888; font-size: 12px; line-height: 1.4;")
        card_layout.addWidget(desc)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #3E3E42;")
        card_layout.addWidget(line)

        # 입력 폼
        form = QFormLayout()
        form.setSpacing(15)

        self.combo_main = QComboBox()
        self.combo_main.setFixedHeight(35)
        self.combo_main.setStyleSheet(self._input_style())
        for k, v in self.THEME_CATEGORIES.items():
            self.combo_main.addItem(v["name"], userData=k)
        self.combo_main.currentIndexChanged.connect(self._on_change_main)
        form.addRow("대분류:", self.combo_main)

        self.combo_sub = QComboBox()
        self.combo_sub.setFixedHeight(35)
        self.combo_sub.setStyleSheet(self._input_style())
        form.addRow("소분류:", self.combo_sub)

        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(50)
        self.spin_count.setFixedHeight(35)
        self.spin_count.setStyleSheet(self._input_style())
        form.addRow("목표 인원:", self.spin_count)

        self.spin_page = QSpinBox()
        self.spin_page.setRange(1, 9999)
        self.spin_page.setValue(1)
        self.spin_page.setFixedHeight(35)
        self.spin_page.setStyleSheet(self._input_style())
        form.addRow("시작 페이지:", self.spin_page)

        card_layout.addLayout(form)

        # [대시보드] 통계 표시 영역
        self.stats_box = QWidget()
        self.stats_box.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        grid = QGridLayout(self.stats_box)
        grid.setContentsMargins(15, 15, 15, 15)
        grid.setSpacing(10)

        self.lbl_total = self._make_stat_val("0", "#FFFFFF")
        self.lbl_success = self._make_stat_val("0", "#2DB400")
        self.lbl_fail = self._make_stat_val("0", "#FF5555")
        self.lbl_page = self._make_stat_val("1", "#FFD700")

        grid.addWidget(self._make_stat_title("총 시도"), 0, 0)
        grid.addWidget(self.lbl_total, 1, 0)
        grid.addWidget(self._make_stat_title("성공"), 0, 1)
        grid.addWidget(self.lbl_success, 1, 1)
        grid.addWidget(self._make_stat_title("실패(연속)"), 2, 0)
        grid.addWidget(self.lbl_fail, 3, 0)
        grid.addWidget(self._make_stat_title("현재 페이지"), 2, 1)
        grid.addWidget(self.lbl_page, 3, 1)

        card_layout.addWidget(self.stats_box)

        # 버튼 영역 (병렬 배치)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_start = QPushButton("작업 시작")
        self.btn_start.setFixedHeight(45)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet(self._btn_style("#2DB400"))
        self.btn_start.clicked.connect(self._on_start)

        self.btn_stop = QPushButton("작업 중단")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet(self._btn_style("#FF5555"))
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False) # 초기엔 비활성

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        card_layout.addLayout(btn_layout)
        
        card_layout.addStretch(1)

        main_layout.addWidget(self.card_widget)
        main_layout.addStretch(1)

        self._on_change_main(0)

    def _make_stat_title(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #888; font-size: 11px; font-weight: normal;")
        return lbl

    def _make_stat_val(self, text, color):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        return lbl

    def _on_change_main(self, idx):
        self.combo_sub.clear()
        mid = self.combo_main.currentData()
        if mid is None: return
        for k, v in self.THEME_CATEGORIES[mid]["sub"].items():
            self.combo_sub.addItem(v, userData=k)

    def _on_start(self):
        mid = self.combo_main.currentData()
        sid = self.combo_sub.currentData()
        self.view_model.start_work(mid, sid, self.spin_count.value(), self.spin_page.value())

    def _on_stop(self):
        self.view_model.stop_work()

    def render(self, state: AddNeighborState):
        run = state.is_running
        
        self.btn_start.setEnabled(not run)
        self.btn_start.setStyleSheet(self._btn_style("#2DB400" if not run else "#444"))
        
        self.btn_stop.setEnabled(run)
        self.btn_stop.setStyleSheet(self._btn_style("#FF5555" if run else "#444"))

        self.combo_main.setEnabled(not run)
        self.combo_sub.setEnabled(not run)
        self.spin_count.setEnabled(not run)
        self.spin_page.setEnabled(not run)

        self.lbl_page.setText(str(state.current_page))
        self.lbl_total.setText(str(state.total_try))
        self.lbl_success.setText(str(state.success_count))
        self.lbl_fail.setText(str(state.fail_count))

        border = "2px solid #2DB400" if run else "1px solid #3E3E42"
        self.card_widget.setStyleSheet(f"QWidget {{ background-color: #252526; border-radius: 12px; border: {border}; }} QLabel {{ border: none; background: transparent; }}")

    def _input_style(self):
        return "QComboBox, QSpinBox { background-color: #333; border: 1px solid #444; border-radius: 4px; color: white; padding: 0 10px; } QComboBox::drop-down { border: none; } QSpinBox::up-button, QSpinBox::down-button { background: transparent; }"

    def _btn_style(self, color):
        return f"QPushButton {{ background-color: {color}; color: white; border-radius: 6px; font-weight: bold; }} QPushButton:hover {{ opacity: 0.9; }}"