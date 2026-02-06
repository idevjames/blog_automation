import sys
from PyQt6.QtWidgets import QApplication

# 1. 인프라 & 데이터
from data.database.database_connection import DatabaseConnection
from service.settings_repository import SettingsRepository

# 2. 서비스
from service.login_session_service import LoginSessionService
from service.add_neighbor_service import AddNeighborService
from service.logger import Logger

# 3. 봇 & GUI
# from system.bot_class.telegram_bot import TelegramBot
from present.main.gui_main_window import GUIMainWindow

def main():
    app = QApplication(sys.argv)

    # ------------------------------------------------
    # [1] 싱글턴 객체 초기화 (순서 중요)
    # ------------------------------------------------
    DatabaseConnection()  # DB 연결
    SettingsRepository()  # 저장소 준비
    LoginSessionService() # 로그인 서비스 준비
    AddNeighborService()  # 서이추 서비스 준비

    # ------------------------------------------------
    # [2] GUI 실행
    # ------------------------------------------------
    window = GUIMainWindow() # 인자 없음!
    window.show()

    # # ------------------------------------------------
    # # [3] 텔레그램 봇 (옵션)
    # # ------------------------------------------------
    # repo = SettingsRepository.instance()
    # token = repo.get_telegram_config()['value']
    
    # if token:
    #     # 봇에게만 Service 인스턴스 명시적으로 넘김 (구조상 편의)
    #     bot = TelegramBot(token, "ADMIN_ID", AddNeighborService.instance())
    #     Logger.instance().set_tg_callback(bot.send_log_message)
    #     bot.start()

    exit_code = app.exec()
    
    # 종료
    LoginSessionService.instance().close()
    DatabaseConnection.instance().close()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()