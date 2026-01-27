import sys
import os
import time
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QLabel, QTextEdit, QHBoxLayout, QPushButton, 
    QStackedWidget, QButtonGroup, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QObject, Qt
from PyQt6.QtGui import QTextCursor

import config
from bot_class.session_manager import NaverSessionManager
from bot_class.blog_likes_neighbor import BlogLikesNeighbor
from bot_class.blog_add_neighbor import BlogAddNeighbor
from bot_class.blog_smart_neighbor_management import BlogSmartNeighborManagement

from gui_tabs import LikeTab, AddTab, SmartNeighborManagementTab

class GuiLogger(QObject):
    log_signal = pyqtSignal(str)
    
    def write(self, text):
        if text.strip():
            self.log_signal.emit(text.strip())
            
    def flush(self):
        pass

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
    ranking_signal = pyqtSignal(list)
    
    def __init__(self, action_type, session=None, params=None):
        super().__init__()
        self.action_type = action_type
        self.session = session
        self.params = params
        self.is_stopped = False
        
    def run(self):
        try:
            if self.action_type in ["like_task", "add_task", "smart_neighbor_management_task"]:
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
            elif self.action_type == "smart_neighbor_management_task":
                bot = BlogSmartNeighborManagement(self.session.driver)
                bot.worker = self
                bot.run(self.params)
                self.finished_signal.emit("✅ 스마트 이웃 관리 작업 종료")
        except Exception as e:
            self.log_signal.emit(f"❌ 오류: {str(e)}")
            self.finished_signal.emit(None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 블로그 자동화 v3.0")
        self.setMinimumSize(1000, 750)
        
        self.session = None
        self.watcher = None
        
        # 성공 횟수 카운팅 변수
        self.total_like_success = 0
        self.total_add_success = 0
        self.smart_like_success = 0
        self.smart_ai_success = 0
        self.smart_normal_success = 0
        
        self.gui_logger = GuiLogger()
        self.gui_logger.log_signal.connect(self.append_log)
        sys.stdout = self.gui_logger
        
        self.init_ui()
        QTimer.singleShot(100, lambda: self.start_action("init_session"))

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QWidget { 
                background-color: #1E1E1E; 
                color: #D4D4D4; 
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; 
            }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #333333; 
                margin-top: 5px; 
                color: #AAAAAA; 
                padding-top: 10px; 
            }
            QLineEdit, QComboBox, QTextEdit { 
                background-color: #3C3C3C; 
                border: 1px solid #555555; 
                color: white; 
                padding: 4px; 
            }
            QPushButton#action_btn { 
                background-color: #2DB400; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                border-radius: 4px; 
            }
            QPushButton#stop_btn { 
                background-color: #C13535; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                border-radius: 4px; 
            }
            QPushButton.tab_btn {
                background-color: #2D2D2D; 
                color: #888888; 
                border: none; 
                text-align: left;
                padding: 6px 15px; 
                font-size: 13px; 
                font-weight: bold; 
                border-left: 3px solid transparent; 
                height: 30px;
                min-width: 220px;
            }
            QPushButton.tab_btn:checked { 
                background-color: #252526; 
                color: #2DB400; 
                border-left: 3px solid #2DB400; 
            }
            QPushButton.tab_btn:hover { 
                background-color: #333333; 
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 상단 상태바
        top_bar = QHBoxLayout()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setStyleSheet("background-color: #808080; border-radius: 5px;")
        self.status_label = QLabel("연결 확인 중...")
        self.status_label.setStyleSheet("font-size: 11px; color: #888;")
        top_bar.addWidget(self.status_dot)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # 콘텐츠 영역
        content_layout = QHBoxLayout()
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        # 수직 탭 버튼
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.btn_tab1 = QPushButton("❤️ 이웃 공감 (+0)")
        self.btn_tab2 = QPushButton("🤝 서이추 신청 (+0)")
        self.btn_tab3 = QPushButton("⭐ 스마트 관리 (❤️+0/🤖+0/💬+0)")

        for i, btn in enumerate([self.btn_tab1, self.btn_tab2, self.btn_tab3]):
            btn.setCheckable(True)
            btn.setProperty("class", "tab_btn")
            if i == 0: btn.setChecked(True)
            self.btn_group.addButton(btn)
            left_layout.addWidget(btn)
            btn.clicked.connect(self.on_tab_clicked)
            
        # 콘텐츠 스택
        self.stack = QStackedWidget()
        self.like_tab = LikeTab(self)
        self.add_tab = AddTab(self)
        self.smart_tab = SmartNeighborManagementTab(self)
        self.stack.addWidget(self.like_tab)
        self.stack.addWidget(self.add_tab)
        self.stack.addWidget(self.smart_tab)
        left_layout.addWidget(self.stack)
        content_layout.addWidget(left_panel, stretch=5)

        # 로그창
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #111; border: 1px solid #333; font-size: 11px;")
        content_layout.addWidget(self.log_text, stretch=4)
        
        main_layout.addLayout(content_layout)
        self.update_sub_combo()

    def on_tab_clicked(self):
        sender = self.sender()
        if sender == self.btn_tab1: 
            self.append_log(config.GUI_GUIDE_MESSAGES["like"])
            self.stack.setCurrentIndex(0)

        elif sender == self.btn_tab2: 
            self.append_log(config.GUI_GUIDE_MESSAGES["add"])
            self.stack.setCurrentIndex(1)

        elif sender == self.btn_tab3: 
            self.append_log(config.GUI_GUIDE_MESSAGES["smart"])
            self.stack.setCurrentIndex(2)

    def append_log(self, text):
        self.log_text.append(text)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # 로그 분석 및 탭 텍스트 실시간 업데이트
        if "❤️ 공감 완료" in text:
            self.total_like_success += 1
            self.btn_tab1.setText(f"❤️ 이웃 공감 (+{self.total_like_success})")
        elif "🎉 이웃 신청 완료!" in text:
            self.total_add_success += 1
            self.btn_tab2.setText(f"🤝 서이추 신청 (+{self.total_add_success})")
        elif "✅ [스마트관리] 공감 성공" in text:
            self.smart_like_success += 1
            self.update_smart_tab_text()
        elif "✅ [스마트관리] AI댓글 성공" in text:
            self.smart_ai_success += 1
            self.update_smart_tab_text()
        elif "✅ [스마트관리] 일반댓글 성공" in text:
            self.smart_normal_success += 1
            self.update_smart_tab_text()
            
        QApplication.processEvents()

    def update_smart_tab_text(self):
        self.btn_tab3.setText(f"⭐ 스마트 관리 (❤️+{self.smart_like_success}/🤖+{self.smart_ai_success}/💬+{self.smart_normal_success})")

    def open_txt_file(self, path):
        try:
            if sys.platform == 'win32': os.startfile(path)
            else: subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        except Exception as e: self.append_log(f"❌ 오류: {e}")

    def sync_ui_to_config(self, inputs, target_cfg):
        for k, f in inputs.items():
            if isinstance(f, tuple):
                target_cfg["delays"][k] = (float(f[0].text()), float(f[1].text()))
            else:
                val = f.text()
                if k in target_cfg["delays"]: 
                    target_cfg["delays"][k] = float(val) if '.' in val else int(val)
                else: 
                    target_cfg["conditions"][k] = int(val) if val.isdigit() else val

    def _write_txt(self, path, prefix, target_cfg):
        try:
            lines = [f"{prefix}_DELAYS = {{"]
            for k, v in target_cfg["delays"].items():
                lines.append(f"    '{k}': {v},")
            lines.append("}\n")
            lines.append(f"{prefix}_CONDITIONS = {{")
            for k, v in target_cfg["conditions"].items():
                lines.append(f"    '{k}': {v},")
            lines.append("}")
            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            self.append_log(f"✅ 저장 완료: {os.path.basename(path)}")
        except Exception as e:
            self.append_log(f"❌ 저장 실패: {e}")

    def save_like_settings(self):
        self.sync_ui_to_config(self.like_tab.inputs, config.LIKES_NEIGHBOR_CONFIG)
        self._write_txt(config.path_like_setup, "LIKE_NEIGHBORS", config.LIKES_NEIGHBOR_CONFIG)

    def save_add_settings(self):
        self.sync_ui_to_config(self.add_tab.inputs, config.ADD_NEIGHBOR_CONFIG)
        self._write_txt(config.path_add_setup, "ADD_NEIGHBORS", config.ADD_NEIGHBOR_CONFIG)

    def save_smart_settings(self, state=None):
        # 1. 일반 스마트 관리 설정(딜레이 등)은 UI에서 가져와 동기화
        self.sync_ui_to_config(self.smart_tab.inputs, config.SMART_NEIGHBOR_CONFIG)
        
        # 2. 스마트 관리 설정 파일 저장 (setup_smart_neighbor_management.txt)
        # 얘는 UI에 있는 값을 저장하는게 맞으므로 저장 수행
        self._write_txt(config.path_smart_neighbor_management_setup, "SMART_MANAGEMENT", config.SMART_NEIGHBOR_CONFIG)

        # 3. [핵심 수정] AI 토글 처리 로직
        # 텍스트 파일을 덮어쓰지 않고, 오히려 파일을 '읽어서' 검증함
        is_checked = self.smart_tab.ai_toggle.isChecked()
        
        if is_checked:
            # 사용자가 켜려고 시도함 -> 파일에 진짜 키가 있는지 확인하기 위해 '리로드'
            # (앱 실행 중 사용자가 메모장에서 키를 넣고 저장했을 수 있으므로)
            reloaded_gemini = config.load_gemini_settings(config.path_gemini_setup)
            
            api_key = reloaded_gemini.get("GEMINI_API_KEY", "").strip()
            prompt = reloaded_gemini.get("GEMINI_PROMPT", "").strip()
            
            if not api_key or not prompt:
                self.append_log("❌ [설정 오류] API Key 또는 프롬프트가 설정 파일에 없습니다.")
                self.append_log("   (설정 파일 열기 버튼을 눌러 키를 입력하고 저장해주세요)")
                
                # 강제로 체크 해제 (시그널 막고)
                self.smart_tab.ai_toggle.blockSignals(True)
                self.smart_tab.ai_toggle.setChecked(False)
                self.smart_tab.ai_toggle.blockSignals(False)
                
                # 메모리 값 OFF
                config.GEMINI_CONFIG["USE_GEMINI"] = False
                
                # 로드된 값 중 키나 프롬프트는 업데이트 해줌 (사용자가 일부만 입력했을수도 있으니)
                config.GEMINI_CONFIG.update(reloaded_gemini)
            else:
                # 정상: 파일에 키가 있음 -> 메모리 ON
                config.GEMINI_CONFIG.update(reloaded_gemini) # 최신 키/프롬프트 반영
                config.GEMINI_CONFIG["USE_GEMINI"] = True
                self.append_log("✅ Gemini AI 기능이 활성화되었습니다.")
        else:
            # 사용자가 끔 -> 그냥 메모리에서만 끔
            config.GEMINI_CONFIG["USE_GEMINI"] = False

        # 4. UI 상태 갱신 (ON/OFF 텍스트 색상 변경 등)
        self.smart_tab.refresh_ai_ui_status()

    def run_like_task(self): 
        config.sync_all_configs()
        self.start_action("like_task", {'cnt': int(self.like_tab.like_cnt.text()), 'pg': int(self.like_tab.like_pg.text())})

    def run_add_task(self): 
        config.sync_all_configs()
        self.start_action("add_task", {
            'main_id': self.add_tab.combo_main.currentData(), 
            'sub_id': self.add_tab.combo_sub.currentData(), 
            'cnt': int(self.add_tab.add_cnt.text()), 
            'pg': int(self.add_tab.add_pg.text())
        })

    def run_smart_neighbor_management_task(self):
        config.sync_all_configs()
        self.start_action("smart_neighbor_management_task", {
            'target_comment': int(self.smart_tab.target_comment.text()), 
            'start_pg': int(self.smart_tab.start_pg.text())
        })

    def stop_task(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.is_stopped = True
            self.append_log("\n🛑 중단 요청됨...")

    def update_sub_combo(self):
        self.add_tab.combo_sub.clear()
        cid = self.add_tab.combo_main.currentData()
        if cid in config.THEME_CATEGORIES:
            for sid, sname in config.THEME_CATEGORIES[cid]['sub'].items():
                self.add_tab.combo_sub.addItem(sname, sid)

    def start_action(self, action_type, params=None):
        if action_type != "init_session" and (not self.session or not self.session.driver):
            self.append_log("❌ 브라우저 미연결")
            return
        self.toggle_ui(False)
        self.worker = ActionWorker(action_type, self.session, params)
        self.worker.ranking_signal.connect(self.smart_tab.update_ranking_ui)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_action_finished)
        self.worker.start()

    def toggle_ui(self, enabled):
        for btn in [self.btn_tab1, self.btn_tab2, self.btn_tab3]: btn.setEnabled(enabled)
        self.like_tab.btn_run.setEnabled(enabled)
        self.add_tab.btn_run.setEnabled(enabled)
        self.smart_tab.btn_run.setEnabled(enabled)
        self.like_tab.btn_stop.setEnabled(not enabled)
        self.add_tab.btn_stop.setEnabled(not enabled)
        self.smart_tab.btn_stop.setEnabled(not enabled)

    def update_status_ui(self, status):
        colors = {0: "#ff4444", 1: "#FFFF00", 2: "#2db400"}
        self.status_dot.setStyleSheet(f"background-color: {colors.get(status)}; border-radius: 5px;")
        self.status_label.setText(["연결 끊김", "로그인 필요", "✅ 정상"][status])

    def on_action_finished(self, result):
        if isinstance(result, NaverSessionManager): 
            self.session = result
            if not self.watcher:
                self.watcher = SessionWatcher(self)
                self.watcher.status_signal.connect(self.update_status_ui)
                self.watcher.start()
        elif result:
            self.append_log(str(result))
        self.toggle_ui(True)

    def closeEvent(self, event):
        if self.watcher:
            self.watcher.running = False
            self.watcher.wait()
        if self.session and self.session.driver:
            self.session.driver.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())