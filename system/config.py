import os
import sys

# 1. 실행 환경에 따른 루트 경로 결정
if getattr(sys, 'frozen', False):
    # PyInstaller 배포 환경
    base_path = os.path.dirname(sys.executable)
    if "Contents/MacOS" in base_path:
        base_path = os.path.abspath(os.path.join(base_path, "../../.."))
else:
    # 소스 코드 직접 실행 시 (system/ 폴더 기준 상위 루트)
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 사용자 데이터 폴더 구조 정의
user_data_dir = os.path.join(base_path, 'user_data')
settings_dir = os.path.join(user_data_dir, 'settings')
profile_dir = os.path.join(user_data_dir, 'naver_profile')

# 폴더 자동 생성
os.makedirs(settings_dir, exist_ok=True)
os.makedirs(profile_dir, exist_ok=True)

# 3. 파일 경로 정의
path_db = os.path.join(user_data_dir, 'neighbor_history.db')
path_like_setup = os.path.join(settings_dir, 'setup_like.txt')
path_add_setup = os.path.join(settings_dir, 'setup_add_neighbor.txt')
path_comment_setup = os.path.join(settings_dir, 'setup_comments.txt')
path_neighbor_msg = os.path.join(settings_dir, 'setup_add_neighbor_messages.txt')
path_comment_msg = os.path.join(settings_dir, 'setup_add_neighbor_comments.txt')
path_gemini_setup = os.path.join(settings_dir, 'setup_gemini.txt')
path_smart_neighbor_management_setup = os.path.join(settings_dir, "setup_smart_neighbor_management.txt")

def load_settings(file_path):
    settings = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                exec(f.read(), {}, settings)
        except Exception as e:
            print(f"⚠️ 로드 실패: {e}")
    return settings

def load_gemini_settings(file_path):
    default_settings = {
        "GEMINI_API_KEY": "",
        "GEMINI_PROMPT": "자연스럽게 댓글을 다세요. 분석 말투 금지.",
        "USE_GEMINI": False
    }
    if not os.path.exists(file_path):
        try:
            content = f"GEMINI_API_KEY = ''\nGEMINI_PROMPT = \"\"\"{default_settings['GEMINI_PROMPT']}\"\"\"\nUSE_GEMINI = False\n"
            with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        except: return default_settings
    
    loaded = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: exec(f.read(), {}, loaded)
    except: return default_settings
    default_settings.update(loaded)
    return default_settings

# 설정 변수 초기화
LIKES_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}}
ADD_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}, "messages": [], "comments": []}
NEIGHBOR_COMMENT_CONFIG = {"delays": {}, "conditions": {}, "messages": []}
GEMINI_CONFIG = {}
SMART_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}, "weights": {}}

# [핵심] gui_main에서 호출할 설정 동기화 함수
def sync_all_configs():
    global LIKES_NEIGHBOR_CONFIG, ADD_NEIGHBOR_CONFIG, NEIGHBOR_COMMENT_CONFIG, GEMINI_CONFIG
    
    like_raw = load_settings(path_like_setup)
    add_raw = load_settings(path_add_setup)
    comment_raw = load_settings(path_comment_setup)
    neighbor_msg_data = load_settings(path_neighbor_msg)
    comment_msg_data = load_settings(path_comment_msg)
    GEMINI_CONFIG = load_gemini_settings(path_gemini_setup)
    smart_neighbor_management_raw = load_settings(path_smart_neighbor_management_setup)

    LIKES_NEIGHBOR_CONFIG["delays"] = like_raw.get("LIKE_NEIGHBORS_DELAYS", {})
    LIKES_NEIGHBOR_CONFIG["conditions"] = like_raw.get("LIKE_NEIGHBORS_CONDITIONS", {})
    
    ADD_NEIGHBOR_CONFIG["delays"] = add_raw.get("ADD_NEIGHBORS_DELAYS", {})
    ADD_NEIGHBOR_CONFIG["conditions"] = add_raw.get("ADD_NEIGHBORS_CONDITIONS", {})
    ADD_NEIGHBOR_CONFIG["messages"] = neighbor_msg_data.get("NEIGHBOR_MESSAGES", [])
    ADD_NEIGHBOR_CONFIG["comments"] = comment_msg_data.get("COMMENT_MESSAGES", [])
    
    NEIGHBOR_COMMENT_CONFIG["delays"] = comment_raw.get("COMMENT_DELAYS", {})
    NEIGHBOR_COMMENT_CONFIG["conditions"] = comment_raw.get("COMMENT_CONDITIONS", {})
    NEIGHBOR_COMMENT_CONFIG["messages"] = comment_msg_data.get("COMMENT_MESSAGES", [])
    
    SMART_NEIGHBOR_CONFIG["delays"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_DELAYS", {
        '페이지로딩': (2.0, 3.5),
        '스크롤간격': (0.2, 0.3)
    })
    SMART_NEIGHBOR_CONFIG["conditions"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_CONDITIONS", {
        '스크롤보폭': 500,
        '댓글목표': 30,    
        '시작페이지': 1,
        '댓글주기': 7,
    })
    
    SMART_NEIGHBOR_CONFIG["weights"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_WEIGHTS", {
        '댓글점수': 10,
        '답글접수': 3,
        '공감점수': 1
    })

# 프로그램 시작 시 최초 로드
sync_all_configs()

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
THEME_CATEGORIES = {
    1: {"name": "엔터테인먼트/예술", "sub": {5: "문학/책", 6: "영화", 8: "미술/디자인", 7: "공연/전시", 11: "음악", 9: "드라마", 12: "스타/연예인", 13: "만화/애니", 10: "방송"}},
    2: {"name": "생활/노하우/쇼핑", "sub": {14: "일상/생각", 15: "육아/결혼", 16: "반려동물", 17: "좋은글/이미지", 18: "패션/미용", 19: "인테리어/DIY", 20: "요리/레시피", 21: "상품리뷰", 36: "원예/재배"}},
    3: {"name": "취미/여가/여행", "sub": {22: "게임", 23: "스포츠", 24: "사진", 25: "자동차", 26: "취미", 27: "국내여행", 28: "세계여행", 29: "맛집"}},
    4: {"name": "지식/동향", "sub": {30: "IT/컴퓨터", 31: "사회/정치", 32: "건강/의학", 33: "비지니스/경제", 35: "어학/외국어", 34: "교육/학문"}}
}

SELECTORS = {
    "feed_item_inner": "div.item_inner", "feed_author_link": "a.author", "feed_nickname": "em.name_author", "feed_reply_icon": "span.reply",
    "main_frame": "mainFrame", "my_write_nickname": "span.u_cbox_write_name", "comment_list_nicknames": "span.u_cbox_nick",
    "comment_open_button": ".btn_comment, a.area_comment", "comment_input_area": ".u_cbox_text.u_cbox_text_mention", "comment_submit_button": "button.u_cbox_btn_upload",
    "feed_like_buttons": "div.u_likeit_list_module .u_likeit_list_btn, .u_likeit_button", "post_view_like_button": "#floating_bottom .u_likeit_button",
    "post_view_comment_button": "#floating_bottom .btn_comment", "pagination": ".pagination a, .section_pagination a",
    "theme_post_links": "a.desc_inner", "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add",
    "popup_radio_mutual_label": "label[for='each_buddy_add']", "popup_radio_just_neighbor": "label[for='buddy_add']",
    "popup_next_btn": "a.btn_ok, a.button_next, .btn_confirm", "popup_message_input": "#message, textarea.txt_area",
    "popup_submit_btn": "a.btn_ok, a.button_next", "popup_success_text": "p.txt_desc, .guide_message, .txt_result",
    "popup_close_btn": "a.button_close, button.btn_close", "post_nickname": "#nickNameArea, .nick, .blog_nickname, span.nick",
    "post_like_count": "em.u_cnt, .u_likeit_list_count", "post_comment_count": "#commentCount, .btn_comment em, .area_comment em",
    "theme_post_container": "div.info_post", "post_list_nickname": ".name_author", "post_list_like_count": ".like em", "post_list_comment_count": ".reply em",
    "floating_container": "#floating_bottom .wrap_postcomment", "static_container": ".wrap_postcomment", "like_button_face": "a.u_likeit_button._face",
    "comment_guide_text": ".u_cbox_guide", "comment_text_area": ".u_cbox_text", "post_content": ".se-main-container, #postViewArea",
    
    
    "noti_cards": "div.comp_card.comp_notice",
    "noti_input_id": "input.input_edit",
    "noti_nickname": "em.title",
    "noti_desc": "p.desc",
    "noti_comment_icon": "span.comment",
    "noti_footer": "p.more_text",
    
    # [수정] 모바일 알림 센터용 셀렉터 (사용자 제공 HTML 기준)
    "noti_cards": "li.item__INKiv",       # 카드 전체
    "noti_nickname": "strong.text_green__kHPOw", # 닉네임
    "noti_title": "p.title__KPI3G",       # 글 제목
    "noti_desc": "p.desc__E1kFv",         # 댓글 내용 (공감일 경우 없음)
    
    # 활동 유형 아이콘 구분용
    "icon_like": "i.icon_like__FHrQX",       # 공감 아이콘
    "icon_reply": "i.icon_reply__i_ssm",     # 답글 아이콘
    "icon_comment": "i.icon_comment__a6XpX", # 댓글 아이콘
    
    "scroll_top_btn": ".scroll_top_button__uyAEr, .scroll_top__YuIw9 button"
}