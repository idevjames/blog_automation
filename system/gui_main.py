import sys
import os
import time
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QLineEdit, QTextEdit, QTabWidget, 
                             QHBoxLayout, QGroupBox, QFormLayout, QComboBox, 
                             QScrollArea, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QObject
from PyQt6.QtGui import QTextCursor

# 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from bot_class.session_manager import NaverSessionManager
from bot_class.blog_likes_neighbor import BlogLikesNeighbor
from bot_class.blog_add_neighbor import BlogAddNeighbor

class GuiLogger(QObject):
    log_signal = pyqtSignal(str)
    def write(self, text):
        if text.strip(): self.log_signal.emit(text.strip())
    def flush(self): pass

class SessionWatcher(QThread):
    status_signal = pyqtSignal(int)
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.main_window.session and self.main_window.session.driver:
                    _ = self.main_window.session.driver.window_handles
                    if self.main_window.session.check_login_status():
                        self.status_signal.emit(2)
                    else:
                        self.status_signal.emit(1)
                else:
                    self.status_signal.emit(0)
            except:
                self.status_signal.emit(0)
            time.sleep(2)

class ActionWorker(QThread):
    finished_signal = pyqtSignal(object) 
    log_signal = pyqtSignal(str)         

    def __init__(self, action_type, session=None, params=None):
        super().__init__()
        self.action_type = action_type
        self.session = session
        self.params = params
        self.is_stopped = False

    def run(self):
        try:
            if self.action_type in ["like_task", "add_task"]:
                driver = self.session.driver
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            if self.action_type == "init_session":
                session = NaverSessionManager()
                session.ensure_login()
                self.finished_signal.emit(session)
            elif self.action_type == "like_task":
                bot = BlogLikesNeighbor(self.session.driver)
                bot.worker = self
                bot.run(self.params['cnt'], self.params['pg'])
                self.finished_signal.emit("✅ 이웃 공감 작업 종료")
            elif self.action_type == "add_task":
                bot = BlogAddNeighbor(self.session.driver)
                bot.worker = self
                bot.run(self.params['main_id'], self.params['sub_id'], self.params['cnt'], self.params['pg'])
                self.finished_signal.emit("✅ 서이추 신청 작업 종료")
        except Exception as e:
            self.log_signal.emit(f"❌ 오류: {str(e)}")
            self.finished_signal.emit(None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 블로그 자동화 v2.1")
        self.setFixedSize(650, 950)
        self.session = None
        self.watcher = None
        
        # --- [추가] 실시간 누적 성공 횟수 변수 ---
        self.total_like_success = 0
        self.total_add_success = 0
        
        self.gui_logger = GuiLogger()
        self.gui_logger.log_signal.connect(self.append_log)
        sys.stdout = self.gui_logger
        
        self.init_ui()
        QTimer.singleShot(100, lambda: self.start_action("init_session"))

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QWidget { background-color: #1E1E1E; color: #D4D4D4; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; }
            QGroupBox { font-weight: bold; border: 1px solid #333333; margin-top: 10px; color: #AAAAAA; padding-top: 10px; }
            QTabWidget::pane { border: 1px solid #333333; background: #252526; }
            QTabBar::tab { background: #2D2D2D; color: #888888; padding: 10px; min-width: 120px; }
            QTabBar::tab:selected { background: #252526; color: #2DB400; border-bottom: 2px solid #2DB400; }
            QLineEdit, QComboBox { background-color: #3C3C3C; border: 1px solid #555555; color: white; padding: 4px; }
            QPushButton#action_btn { background-color: #2DB400; color: white; font-weight: bold; font-size: 15px; border-radius: 6px; }
            QPushButton#stop_btn { background-color: #C13535; color: white; font-weight: bold; font-size: 15px; border-radius: 6px; }
            QPushButton#save_btn { background-color: #3E4E3F; color: #2DB400; font-weight: bold; border: 1px solid #2DB400; }
            QPushButton#file_btn { background-color: #444; color: #EEE; border: 1px solid #666; font-size: 11px; }
        """)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        top_bar = QHBoxLayout()
        self.status_dot = QLabel(); self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background-color: #808080; border-radius: 6px;")
        self.status_label = QLabel("브라우저 연결 대기 중...")
        self.btn_reconnect = QPushButton("브라우저 재실행"); self.btn_reconnect.setFixedSize(110, 30)
        self.btn_reconnect.clicked.connect(lambda: self.start_action("init_session"))
        top_bar.addWidget(self.status_dot); top_bar.addWidget(self.status_label); top_bar.addStretch(); top_bar.addWidget(self.btn_reconnect)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        
        # --- [1] 이웃 새글 공감 탭 ---
        like_tab = QWidget(); like_layout = QVBoxLayout(like_tab)
        self.l_base = QGroupBox("📌 핵심 제어")
        l_form = QFormLayout(self.l_base)
        self.like_cnt = QLineEdit("50"); self.like_pg = QLineEdit("1")
        l_form.addRow("🎯 목표 수:", self.like_cnt); l_form.addRow("📑 시작 페이지:", self.like_pg)
        like_layout.addWidget(self.l_base)

        self.l_adv = QGroupBox("⚙️ 고급 설정 (⏳ 최소~최대초 사이에서 랜덤값)")
        l_adv_vbox = QVBoxLayout(self.l_adv)
        l_scroll = QScrollArea(); l_scroll.setWidgetResizable(True); l_scroll.setFixedHeight(250)
        l_scr_content = QWidget(); l_scr_form = QFormLayout(l_scr_content)
        self.like_inputs = {}
        for k, v in config.LIKES_NEIGHBOR_CONFIG["delays"].items():
            self._add_config_row(l_scr_form, self.like_inputs, k, v)
        for k, v in config.LIKES_NEIGHBOR_CONFIG["conditions"].items():
            s = QLineEdit(str(v)); l_scr_form.addRow(f"🔍 {k}:", s); self.like_inputs[k] = s
        l_scroll.setWidget(l_scr_content); l_adv_vbox.addWidget(l_scroll)
        btn_save_like = QPushButton("💾 공감 수치 설정 저장"); btn_save_like.setObjectName("save_btn")
        btn_save_like.setFixedHeight(35); btn_save_like.clicked.connect(self.save_like_settings)
        l_adv_vbox.addWidget(btn_save_like); like_layout.addWidget(self.l_adv)

        l_btn_hbox = QHBoxLayout()
        self.btn_run_like = QPushButton("🚀 이웃 공감 시작"); self.btn_run_like.setObjectName("action_btn"); self.btn_run_like.setFixedHeight(50)
        self.btn_run_like.clicked.connect(self.run_like_task)
        self.btn_stop_like = QPushButton("🛑 작업 중단"); self.btn_stop_like.setObjectName("stop_btn"); self.btn_stop_like.setFixedHeight(50); self.btn_stop_like.setEnabled(False)
        self.btn_stop_like.clicked.connect(self.stop_task)
        l_btn_hbox.addWidget(self.btn_run_like, 2); l_btn_hbox.addWidget(self.btn_stop_like, 1)
        like_layout.addLayout(l_btn_hbox)

        # --- [2] 서로이웃 신청 탭 ---
        add_tab = QWidget(); add_layout = QVBoxLayout(add_tab)
        self.a_base = QGroupBox("📌 핵심 제어")
        a_form = QFormLayout(self.a_base)
        self.combo_main = QComboBox(); self.combo_sub = QComboBox()
        for cid, cdata in config.THEME_CATEGORIES.items(): self.combo_main.addItem(cdata['name'], cid)
        self.combo_main.currentIndexChanged.connect(self.update_sub_combo); self.update_sub_combo()
        self.add_cnt = QLineEdit("20"); self.add_pg = QLineEdit("1")
        a_form.addRow("📁 대분류:", self.combo_main); a_form.addRow("🏷️ 상세주제:", self.combo_sub)
        a_form.addRow("🎯 목표 인원:", self.add_cnt); a_form.addRow("📑 시작 페이지:", self.add_pg)
        add_layout.addWidget(self.a_base)

        self.a_adv = QGroupBox("⚙️ 고급 설정 (⏳ 최소~최대초 사이에서 랜덤값)")
        a_adv_vbox = QVBoxLayout(self.a_adv)
        f_btn_lay = QHBoxLayout()
        btn_o_msg = QPushButton("📂 서이추 메시지 열기"); btn_o_msg.setObjectName("file_btn")
        btn_o_cmt = QPushButton("📂 댓글 관리 열기"); btn_o_cmt.setObjectName("file_btn")
        btn_o_msg.clicked.connect(lambda: self.open_txt_file(config.path_neighbor_msg))
        btn_o_cmt.clicked.connect(lambda: self.open_txt_file(config.path_comment_msg))
        f_btn_lay.addWidget(btn_o_msg); f_btn_lay.addWidget(btn_o_cmt); a_adv_vbox.addLayout(f_btn_lay)

        a_scroll = QScrollArea(); a_scroll.setWidgetResizable(True); a_scroll.setFixedHeight(250)
        a_scr_content = QWidget(); a_scr_form = QFormLayout(a_scr_content)
        self.add_inputs = {}
        for k, v in config.ADD_NEIGHBOR_CONFIG["delays"].items():
            self._add_config_row(a_scr_form, self.add_inputs, k, v)
        for k, v in config.ADD_NEIGHBOR_CONFIG["conditions"].items():
            s = QLineEdit(str(v)); a_scr_form.addRow(f"🔍 {k}:", s); self.add_inputs[k] = s
        a_scroll.setWidget(a_scr_content); a_adv_vbox.addWidget(a_scroll)
        btn_save_add = QPushButton("💾 서이추 수치 설정 저장"); btn_save_add.setObjectName("save_btn")
        btn_save_add.setFixedHeight(35); btn_save_add.clicked.connect(self.save_add_settings)
        a_adv_vbox.addWidget(btn_save_add); add_layout.addWidget(self.a_adv)

        a_btn_hbox = QHBoxLayout()
        self.btn_run_add = QPushButton("🚀 서로이웃 신청 시작"); self.btn_run_add.setObjectName("action_btn"); self.btn_run_add.setFixedHeight(50)
        self.btn_run_add.clicked.connect(self.run_add_task)
        self.btn_stop_add = QPushButton("🛑 작업 중단"); self.btn_stop_add.setObjectName("stop_btn"); self.btn_stop_add.setFixedHeight(50); self.btn_stop_add.setEnabled(False)
        self.btn_stop_add.clicked.connect(self.stop_task)
        a_btn_hbox.addWidget(self.btn_run_add, 2); a_btn_hbox.addWidget(self.btn_stop_add, 1)
        add_layout.addLayout(a_btn_hbox)

        self.tabs.addTab(like_tab, "❤️ 이웃 공감"); self.tabs.addTab(add_tab, "🤝 서이추 신청")
        main_layout.addWidget(self.tabs)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text); self.setCentralWidget(central_widget)

    # --- [수정] 탭 이름 실시간 업데이트 함수 ---
    def update_tab_labels(self):
        self.tabs.setTabText(0, f"❤️ 이웃 공감 (+{self.total_like_success})")
        self.tabs.setTabText(1, f"🤝 서이추 신청 (+{self.total_add_success})")

    def append_log(self, text):
        self.log_text.append(text); self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # --- [추가] 로그 분석을 통한 실시간 카운트 업 ---
        if "❤️ 공감 완료" in text:
            self.total_like_success += 1
            self.update_tab_labels()
        elif "🎉 이웃 신청 완료!" in text:
            self.total_add_success += 1
            self.update_tab_labels()
            
        QApplication.processEvents()

    def update_status_ui(self, status):
        colors = {0: "#ff4444", 1: "#FFFF00", 2: "#2db400"}
        texts = {0: "연결 끊김", 1: "로그인 필요", 2: "✅ 로그인 정상"}
        self.status_dot.setStyleSheet(f"background-color: {colors.get(status)}; border-radius: 6px;")
        self.status_label.setText(texts.get(status))

    def _add_config_row(self, form, input_dict, k, v):
        if isinstance(v, (tuple, list)):
            h = QHBoxLayout(); min_in = QLineEdit(str(v[0])); max_in = QLineEdit(str(v[1]))
            h.addWidget(min_in); h.addWidget(QLabel("~")); h.addWidget(max_in); h.addWidget(QLabel("초"))
            form.addRow(f"⏳ {k}:", h); input_dict[k] = (min_in, max_in)
        else:
            s = QLineEdit(str(v)); form.addRow(f"🎲 {k}:", s); input_dict[k] = s

    def open_txt_file(self, path):
        try:
            if sys.platform == 'win32': os.startfile(path)
            else: subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        except Exception as e: self.append_log(f"❌ 파일 열기 실패: {e}")

    def sync_ui_to_config(self, inputs, target_cfg):
        for k, f in inputs.items():
            if isinstance(f, tuple):
                target_cfg["delays"][k] = (float(f[0].text()), float(f[1].text()))
            else:
                val = f.text()
                if k in target_cfg["delays"]: target_cfg["delays"][k] = float(val) if '.' in val else int(val)
                else: target_cfg["conditions"][k] = int(val) if val.isdigit() else val

    def _write_txt(self, path, prefix, target_cfg):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            lines = [f"{prefix}_DELAYS = {{"]
            for k, v in target_cfg["delays"].items():
                val = f"'{v}'" if isinstance(v, str) else v
                lines.append(f"    '{k}': {val},")
            lines.append("}\n")
            lines.append(f"{prefix}_CONDITIONS = {{")
            for k, v in target_cfg["conditions"].items():
                val = f"'{v}'" if isinstance(v, str) else v
                lines.append(f"    '{k}': {val},")
            lines.append("}")
            with open(path, 'w', encoding='utf-8') as f: f.write("\n".join(lines))
            self.append_log(f"✅ 설정 저장 완료: {os.path.basename(path)}")
        except Exception as e: self.append_log(f"❌ 저장 실패: {e}")

    def save_like_settings(self):
        self.sync_ui_to_config(self.like_inputs, config.LIKES_NEIGHBOR_CONFIG)
        self._write_txt(config.path_like_setup, "LIKE_NEIGHBORS", config.LIKES_NEIGHBOR_CONFIG)

    def save_add_settings(self):
        self.sync_ui_to_config(self.add_inputs, config.ADD_NEIGHBOR_CONFIG)
        self._write_txt(config.path_add_setup, "ADD_NEIGHBORS", config.ADD_NEIGHBOR_CONFIG)

    def run_like_task(self):
        self.save_like_settings()
        self.start_action("like_task", {'cnt': int(self.like_cnt.text() or 5), 'pg': int(self.like_pg.text() or 1)})

    def run_add_task(self):
        self.save_add_settings()
        self.start_action("add_task", {'main_id': self.combo_main.currentData(), 'sub_id': self.combo_sub.currentData(), 'cnt': int(self.add_cnt.text() or 20), 'pg': int(self.add_pg.text() or 1)})

    def stop_task(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.is_stopped = True 
            self.append_log("\n🛑 작업 중단 요청됨... (현재 단계 마무리 후 멈춥니다)")

    def update_sub_combo(self):
        self.combo_sub.clear(); cid = self.combo_main.currentData()
        if cid in config.THEME_CATEGORIES:
            for sid, sname in config.THEME_CATEGORIES[cid]['sub'].items(): self.combo_sub.addItem(sname, sid)

    def start_action(self, action_type, params=None):
        if action_type != "init_session" and (not self.session or not self.session.driver):
            self.append_log("❌ 브라우저 준비 필요"); return
        
        self.tabs.tabBar().setEnabled(False)
        self.l_base.setEnabled(False); self.l_adv.setEnabled(False)
        self.a_base.setEnabled(False); self.a_adv.setEnabled(False)
        
        self.btn_run_like.setEnabled(False); self.btn_run_add.setEnabled(False)
        self.btn_stop_like.setEnabled(True); self.btn_stop_add.setEnabled(True)
        
        self.worker = ActionWorker(action_type, self.session, params)
        self.worker.log_signal.connect(self.append_log); self.worker.finished_signal.connect(self.on_action_finished); self.worker.start()

    def on_action_finished(self, result):
        if isinstance(result, NaverSessionManager): 
            self.session = result
            if not self.watcher: self.watcher = SessionWatcher(self); self.status_signal = self.watcher.status_signal; self.watcher.status_signal.connect(self.update_status_ui); self.watcher.start()
        elif result: self.append_log(str(result))
        
        self.tabs.tabBar().setEnabled(True)
        self.l_base.setEnabled(True); self.l_adv.setEnabled(True)
        self.a_base.setEnabled(True); self.a_adv.setEnabled(True)
        
        self.btn_run_like.setEnabled(True); self.btn_run_add.setEnabled(True)
        self.btn_stop_like.setEnabled(False); self.btn_stop_add.setEnabled(False)

    def closeEvent(self, event):
        if self.watcher: self.watcher.running = False; self.watcher.wait()
        if self.session and self.session.driver: self.session.driver.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())