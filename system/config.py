# config.py
import os
import sys

# -----------------------------------------------------------
# [설정 파일 로드 로직]
# settings.txt가 루트(한 단계 상위) 폴더에 있으므로 이를 읽어옵니다.
# -----------------------------------------------------------

# 현재 파일(config.py)의 부모 폴더(system)의 부모 폴더(root) 경로 구하기
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
settings_path = os.path.join(root_dir, 'settings.txt')

# 설정값을 담을 딕셔너리
user_settings = {}

try:
    with open(settings_path, 'r', encoding='utf-8') as f:
        # settings.txt의 내용을 파이썬 코드로 실행하여 변수들을 user_settings에 담음
        exec(f.read(), {}, user_settings)
except FileNotFoundError:
    print(f"\n[오류] '{settings_path}' 파일을 찾을 수 없습니다.")
    print("프로그램 실행 위치에 settings.txt 파일이 있는지 확인해주세요.")
    sys.exit(1)
except Exception as e:
    print(f"\n[오류] settings.txt 파일을 읽는 중 문제가 발생했습니다: {e}")
    sys.exit(1)

# -----------------------------------------------------------
# [값 매핑]
# user_settings 딕셔너리에서 값을 꺼내 시스템 변수에 연결
# -----------------------------------------------------------

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

NEIGHBOR_CONFIG = {
    "directory_no": user_settings.get("TARGET_DIRECTORY", 12),      
    "messages": user_settings.get("NEIGHBOR_MESSAGES", [])
}

DELAY_RANGE = user_settings.get("CUSTOM_DELAYS", {})

DEFAULT_LIKE_COUNT = user_settings.get("DEFAULT_LIKE_COUNT", 10)
DEFAULT_FAILURE_COUNT = user_settings.get("DEFAULT_FAILURE_COUNT", 3)

# -----------------------------------------------------------
# [시스템 내부용 선택자] (수정 불필요)
# -----------------------------------------------------------
SELECTORS = {
    "like_buttons": ".my_reaction a.u_likeit_button._face, button.u_likeit_list_btn, .u_likeit_button",
    "pagination": ".pagination a, .section_pagination a, .item_pagination",
    "next_button": "a.button_next, .btn_next",
    "body": "body",
    "theme_post_links": "a.desc_inner",
    "blog_iframe": "mainFrame", 
    "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add", 
    "popup_radio_mutual_label": "label[for='each_buddy_add']", 
    "popup_first_next_btn": "a.button_next._buddyAddNext",
    "popup_message_input": "textarea#message",      
    "popup_submit_btn": "a.button_next._addBothBuddy"
}