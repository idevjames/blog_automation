import sys
import os
import time
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QLabel, QTextEdit, QTabWidget, QHBoxLayout, 
                             QFormLayout, QLineEdit, QMessageBox, QPushButton)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QObject
from PyQt6.QtGui import QTextCursor

import config
from bot_class.session_manager import NaverSessionManager
from bot_class.blog_likes_neighbor import BlogLikesNeighbor
from bot_class.blog_add_neighbor import BlogAddNeighbor
from bot_class.blog_comment_neighbor import BlogCommentNeighbor

# 위에서 정의한 위젯 클래스들을 불러옵니다.
from gui_tabs import LikeTab, AddTab, CommentTab

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
            if self.action_type in ["like_task", "add_task", "comment_task"]:
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
            elif self.action_type == "comment_task":
                bot = BlogCommentNeighbor(self.session.driver)
                bot.worker = self
                bot.run(self.params['cnt'], self.params['pg'])
                self.finished_signal.emit("✅ 이웃 댓글 작업 종료")
        except Exception as e:
            self.log_signal.emit(f"❌ 오류: {str(e)}")
            self.finished_signal.emit(None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 블로그 자동화 v3.0 (모듈화 완료)")
        self.setMinimumSize(1000, 700) # 가로를 넓게, 세로는 적당히 조정
        self.resize(1100, 800)         # 초기 실행 크기
        self.session = None
        self.watcher = None
        
        self.total_like_success = 0
        self.total_add_success = 0
        self.total_comment_success = 0
        
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
            QLineEdit, QComboBox, QTextEdit { background-color: #3C3C3C; border: 1px solid #555555; color: white; padding: 4px; }
            QPushButton#action_btn { background-color: #2DB400; color: white; font-weight: bold; font-size: 15px; border-radius: 6px; }
            QPushButton#stop_btn { background-color: #C13535; color: white; font-weight: bold; font-size: 15px; border-radius: 6px; }
            QPushButton#save_btn { background-color: #3E4E3F; color: #2DB400; font-weight: bold; border: 1px solid #2DB400; }
            QPushButton#file_btn { background-color: #444; color: #EEE; border: 1px solid #666; font-size: 11px; }
        """)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        top_bar = QHBoxLayout()
        self.status_dot = QLabel(); self.status_dot.setFixedSize(12, 12); self.status_dot.setStyleSheet("background-color: #808080; border-radius: 6px;")
        self.status_label = QLabel("브라우저 연결 대기 중...")
        btn_reconnect = QPushButton("브라우저 재실행"); btn_reconnect.setFixedSize(110, 30); btn_reconnect.clicked.connect(lambda: self.start_action("init_session"))
        top_bar.addWidget(self.status_dot); top_bar.addWidget(self.status_label); top_bar.addStretch(); top_bar.addWidget(btn_reconnect)
        main_layout.addLayout(top_bar)
        
        content_layout = QHBoxLayout() # 가로 레이아웃 생성

        self.tabs = QTabWidget()
        
        # 분리된 탭 위젯들 생성
        self.tabs = QTabWidget()
        self.like_tab = LikeTab(self)
        self.add_tab = AddTab(self)
        self.comment_tab = CommentTab(self)
        self.tabs.addTab(self.like_tab, "❤️ 이웃 공감")
        self.tabs.addTab(self.add_tab, "🤝 서이추 신청")
        self.tabs.addTab(self.comment_tab, "💬 이웃 댓글")
        
        content_layout.addWidget(self.tabs, stretch=0)
        
        # 3. 우측 로그창 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # 우측 로그창이 남는 공간을 모두 차지하도록 가중치를 1로 설정
        content_layout.addWidget(self.log_text, stretch=1)
        
        # 메인 레이아웃에 가로 콘텐츠 레이아웃 추가
        main_layout.addLayout(content_layout)
        # --------------------------------------------------------

        self.setCentralWidget(central_widget)
        self.update_sub_combo()

    def update_tab_labels(self):
        self.tabs.setTabText(0, f"❤️ 이웃 공감 (+{self.total_like_success})")
        self.tabs.setTabText(1, f"🤝 서이추 신청 (+{self.total_add_success})")
        self.tabs.setTabText(2, f"💬 이웃 댓글 (+{self.total_comment_success})")

    def append_log(self, text):
        self.log_text.append(text); self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        if "❤️ 공감 완료" in text: self.total_like_success += 1; self.update_tab_labels()
        elif "🎉 이웃 신청 완료!" in text: self.total_add_success += 1; self.update_tab_labels()
        elif "이웃에게 댓글작성 완료!" in text: self.total_comment_success += 1; self.update_tab_labels()
        QApplication.processEvents()

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
            if isinstance(f, tuple): target_cfg["delays"][k] = (float(f[0].text()), float(f[1].text()))
            else:
                val = f.text()
                if k in target_cfg["delays"]: target_cfg["delays"][k] = float(val) if '.' in val else int(val)
                else: target_cfg["conditions"][k] = int(val) if val.isdigit() else val

    def _write_txt(self, path, prefix, target_cfg):
        try:
            lines = [f"{prefix}_DELAYS = {{"]
            for k, v in target_cfg["delays"].items(): lines.append(f"    '{k}': {v},")
            lines.append("}\n"); lines.append(f"{prefix}_CONDITIONS = {{")
            for k, v in target_cfg["conditions"].items(): lines.append(f"    '{k}': {v},")
            lines.append("}")
            with open(path, 'w', encoding='utf-8') as f: f.write("\n".join(lines))
            self.append_log(f"✅ 설정 저장 완료: {os.path.basename(path)}")
        except Exception as e: self.append_log(f"❌ 저장 실패: {e}")

    def save_like_settings(self):
        self.sync_ui_to_config(self.like_tab.inputs, config.LIKES_NEIGHBOR_CONFIG)
        self._write_txt(config.path_like_setup, "LIKE_NEIGHBORS", config.LIKES_NEIGHBOR_CONFIG)

    def save_add_settings(self):
        self.sync_ui_to_config(self.add_tab.inputs, config.ADD_NEIGHBOR_CONFIG)
        self._write_txt(config.path_add_setup, "ADD_NEIGHBORS", config.ADD_NEIGHBOR_CONFIG)

    def save_comment_settings(self):
        
        # 1. AI 설정 값 가져오기
        api_key = self.comment_tab.ai_key.text().strip()
        prompt = self.comment_tab.ai_prompt.toPlainText().strip()
        use_ai = True if api_key else False
        
        # 2. config 객체 실시간 업데이트
        config.GEMINI_CONFIG["GEMINI_API_KEY"] = api_key
        config.GEMINI_CONFIG["GEMINI_PROMPT"] = prompt
        config.GEMINI_CONFIG["USE_GEMINI"] = use_ai
        
        # 3. setup_gemini.txt 파일로 저장
        try:
            content = [
                f"GEMINI_API_KEY = '{api_key}'",
                f"GEMINI_PROMPT = \"\"\"{prompt}\"\"\"",
                f"USE_GEMINI = {use_ai}"
            ]
            with open(config.path_gemini_setup, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            self.append_log(f"✅ AI 설정이 {os.path.basename(config.path_gemini_setup)}에 저장되었습니다.")
        except Exception as e:
            self.append_log(f"❌ AI 설정 저장 실패: {e}")
        config.NEIGHBOR_COMMENT_CONFIG["conditions"]["방문주기"] = int(self.comment_tab.comment_interval.text())
        self.sync_ui_to_config(self.comment_tab.inputs, config.NEIGHBOR_COMMENT_CONFIG)
        self._write_txt(config.path_comment_setup, "COMMENT", config.NEIGHBOR_COMMENT_CONFIG)

    def run_like_task(self): 
        config.sync_all_configs() # 실행 직전 파일에서 설정을 새로 읽어옴
        self.start_action("like_task", {
            'cnt': int(self.like_tab.like_cnt.text()), 
            'pg': int(self.like_tab.like_pg.text())
        })

    def run_add_task(self): 
        config.sync_all_configs() # 실행 직전 파일에서 설정을 새로 읽어옴
        self.start_action("add_task", {
            'main_id': self.add_tab.combo_main.currentData(), 
            'sub_id': self.add_tab.combo_sub.currentData(), 
            'cnt': int(self.add_tab.add_cnt.text()), 
            'pg': int(self.add_tab.add_pg.text())
        })

    def run_comment_task(self):
        config.sync_all_configs() # 실행 직전 파일에서 설정을 새로 읽어옴
        # UI에서 입력받은 방문주기 값 반영
        try:
            config.NEIGHBOR_COMMENT_CONFIG["conditions"]["방문주기"] = int(self.comment_tab.comment_interval.text())
        except: pass
        
        self.start_action("comment_task", {
            'cnt': int(self.comment_tab.comment_cnt.text()), 
            'pg': int(self.comment_tab.comment_pg.text())
        })
    def stop_task(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.is_stopped = True
            self.append_log("\n🛑 중단 요청됨... (현재 단계 마무리 후 정지)")

    def update_sub_combo(self):
        self.add_tab.combo_sub.clear(); cid = self.add_tab.combo_main.currentData()
        if cid in config.THEME_CATEGORIES:
            for sid, sname in config.THEME_CATEGORIES[cid]['sub'].items(): self.add_tab.combo_sub.addItem(sname, sid)

    def start_action(self, action_type, params=None):
        if action_type != "init_session" and (not self.session or not self.session.driver):
            self.append_log("❌ 브라우저 준비 필요"); return
        self.toggle_ui(False)
        self.worker = ActionWorker(action_type, self.session, params)
        self.worker.log_signal.connect(self.append_log); self.worker.finished_signal.connect(self.on_action_finished); self.worker.start()

    def toggle_ui(self, enabled):
        self.tabs.tabBar().setEnabled(enabled)
        self.like_tab.l_base.setEnabled(enabled); self.like_tab.l_adv.setEnabled(enabled)
        self.add_tab.a_base.setEnabled(enabled); self.add_tab.a_adv.setEnabled(enabled)
        self.comment_tab.c_base.setEnabled(enabled); self.comment_tab.c_adv.setEnabled(enabled)
        self.like_tab.btn_run.setEnabled(enabled); self.add_tab.btn_run.setEnabled(enabled); self.comment_tab.btn_run.setEnabled(enabled)
        self.like_tab.btn_stop.setEnabled(not enabled); self.add_tab.btn_stop.setEnabled(not enabled); self.comment_tab.btn_stop.setEnabled(not enabled)

    def update_status_ui(self, status):
        colors = {0: "#ff4444", 1: "#FFFF00", 2: "#2db400"}
        texts = {0: "연결 끊김", 1: "로그인 필요", 2: "✅ 로그인 정상"}
        self.status_dot.setStyleSheet(f"background-color: {colors.get(status)}; border-radius: 6px;")
        self.status_label.setText(texts.get(status))

    def on_action_finished(self, result):
        if isinstance(result, NaverSessionManager): 
            self.session = result
            if not self.watcher: self.watcher = SessionWatcher(self); self.watcher.status_signal.connect(self.update_status_ui); self.watcher.start()
        elif result: self.append_log(str(result))
        self.toggle_ui(True)

    def closeEvent(self, event):
        if self.watcher: self.watcher.running = False; self.watcher.wait()
        if self.session and self.session.driver: self.session.driver.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())