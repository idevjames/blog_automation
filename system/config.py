import os
import sys

# 실행 환경에 따른 루트 경로 결정
if getattr(sys, 'frozen', False):
    # PyInstaller 배포 환경 (.app 또는 .exe 실행 시)
    base_path = os.path.dirname(sys.executable)
    if "Contents/MacOS" in base_path:
        # macOS .app 패키지 기준 dist/ 폴더 위치로 이동
        base_path = os.path.abspath(os.path.join(base_path, "../../.."))
else:
    # 소스 코드 직접 실행 시 (system/ 폴더 기준)
    base_path = os.path.dirname(os.path.abspath(__file__))

# 모든 설정 파일은 base_path 내부의 settings 폴더에 있음
settings_dir = os.path.join(base_path, 'settings')

# 개발 환경 대응 (소스 루트에 settings가 있는 경우)
if not os.path.exists(settings_dir):
    parent_settings = os.path.join(os.path.dirname(base_path), 'settings')
    if os.path.exists(parent_settings):
        settings_dir = parent_settings

path_like_setup = os.path.join(settings_dir, 'setup_like.txt')
path_add_setup = os.path.join(settings_dir, 'setup_add_neighbor.txt')
path_comment_setup = os.path.join(settings_dir, 'setup_comments.txt')
path_neighbor_msg = os.path.join(settings_dir, 'setup_add_neighbor_messages.txt')
path_comment_msg = os.path.join(settings_dir, 'setup_add_neighbor_comments.txt')

def load_settings(file_path):
    settings = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                exec(f.read(), {}, settings)
        except Exception as e:
            print(f"⚠️ 로드 실패: {e}")
    return settings

like_raw = load_settings(path_like_setup)
add_raw = load_settings(path_add_setup)
comment_raw = load_settings(path_comment_setup)
neighbor_msg_data = load_settings(path_neighbor_msg)
comment_msg_data = load_settings(path_comment_msg)

LIKES_NEIGHBOR_CONFIG = {
    "delays": like_raw.get("LIKE_NEIGHBORS_DELAYS", {}),
    "conditions": like_raw.get("LIKE_NEIGHBORS_CONDITIONS", {})
}
ADD_NEIGHBOR_CONFIG = {
    "delays": add_raw.get("ADD_NEIGHBORS_DELAYS", {}),
    "conditions": add_raw.get("ADD_NEIGHBORS_CONDITIONS", {}),
    "messages": neighbor_msg_data.get("NEIGHBOR_MESSAGES", []),
    "comments": comment_msg_data.get("COMMENT_MESSAGES", [])
}

NEIGHBOR_COMMENT_CONFIG = {
    "delays": comment_raw.get("COMMENT_DELAYS", {}),
    "conditions": comment_raw.get("COMMENT_CONDITIONS", {}),
    "messages": comment_msg_data.get("COMMENT_MESSAGES", [])
}

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

THEME_CATEGORIES = {
    1: {"name": "엔터테인먼트/예술", "sub": {5: "문학/책", 6: "영화", 8: "미술/디자인", 7: "공연/전시", 11: "음악", 9: "드라마", 12: "스타/연예인", 13: "만화/애니", 10: "방송"}},
    2: {"name": "생활/노하우/쇼핑", "sub": {14: "일상/생각", 15: "육아/결혼", 16: "반려동물", 17: "좋은글/이미지", 18: "패션/미용", 19: "인테리어/DIY", 20: "요리/레시피", 21: "상품리뷰", 36: "원예/재배"}},
    3: {"name": "취미/여가/여행", "sub": {22: "게임", 23: "스포츠", 24: "사진", 25: "자동차", 26: "취미", 27: "국내여행", 28: "세계여행", 29: "맛집"}},
    4: {"name": "지식/동향", "sub": {30: "IT/컴퓨터", 31: "사회/정치", 32: "건강/의학", 33: "비지니스/경제", 35: "어학/외국어", 34: "교육/학문"}}
}

SELECTORS = {
    # 피드 리스트 관련
    "feed_item_inner": "div.item_inner",
    "feed_author_link": "a.author",
    "feed_nickname": "em.name_author",
    "feed_reply_icon": "span.reply",
    
    # 블로그 본문 및 댓글창 관련
    "main_frame": "mainFrame",
    "my_write_nickname": "span.u_cbox_write_name",
    "comment_list_nicknames": "span.u_cbox_nick",
    "comment_open_button": ".btn_comment, a.area_comment",
    "comment_input_area": ".u_cbox_text.u_cbox_text_mention",
    "comment_submit_button": "button.u_cbox_btn_upload",
    
    # 공통 및 기타
    "feed_like_buttons": "div.u_likeit_list_module .u_likeit_list_btn, .u_likeit_button",
    "post_view_like_button": "#floating_bottom .u_likeit_button",
    "post_view_comment_button": "#floating_bottom .btn_comment",
    "pagination": ".pagination a, .section_pagination a",
    "theme_post_links": "a.desc_inner",
    "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add",
    "popup_radio_mutual_label": "label[for='each_buddy_add']",
    "popup_radio_just_neighbor": "label[for='buddy_add']",
    "popup_next_btn": "a.btn_ok, a.button_next, .btn_confirm",
    "popup_message_input": "#message, textarea.txt_area",
    "popup_submit_btn": "a.btn_ok, a.button_next",
    "popup_success_text": "p.txt_desc, .guide_message, .txt_result",
    "popup_close_btn": "a.button_close, button.btn_close",
    "post_nickname": "#nickNameArea, .nick, .blog_nickname, span.nick",
    "post_like_count": "em.u_cnt, .u_likeit_list_count",
    "post_comment_count": "#commentCount, .btn_comment em, .area_comment em",
    "theme_post_container": "div.info_post",
    "post_list_nickname": ".name_author",
    "post_list_like_count": ".like em",
    "post_list_comment_count": ".reply em",
    "floating_container": "#floating_bottom .wrap_postcomment",
    "static_container": ".wrap_postcomment",
    "like_button_face": "a.u_likeit_button._face",
    "comment_guide_text": ".u_cbox_guide",
    "comment_text_area": ".u_cbox_text",
}

# --- Gemini AI 관련 설정 추가 ---
path_gemini_setup = os.path.join(settings_dir, 'setup_gemini.txt')

def load_gemini_settings(file_path):
    """Gemini 설정을 로드하고, 파일이 없으면 기본 양식 생성"""
    default_settings = {
        "GEMINI_API_KEY": "",
        "GEMINI_PROMPT": """당신은 블로그에서 활발하게 소통하는 2030 이웃입니다. 
영혼 없는 분석가처럼 말하지 말고, 친구 블로그에 놀러 온 것처럼 자연스럽게 댓글을 다세요.

[작성 규칙]
1. 본문에서 언급된 구체적인 키워드나 내용을 하나 이상 포함할 것.
2. 너무 길지 않게 1~2문장 사이로 작성할 것.
3. 분석적인 말투(흐름이 인상적이다, 시선으로 보게 된다 등)는 '절대' 금지입니다.
4. 그림 이모티콘(이모지)는 제외하고, 채팅으로 많이 쓰는 이모티콘을 사용할 것 [예시: ㅎㅎ, ^^, :), ㅠㅠ]""",
        "USE_GEMINI": False
    }
    
    # 1. 파일이 없으면 기본 양식으로 생성 (사용자 가이드 역할)
    if not os.path.exists(file_path):
        try:
            content = (
                "# Gemini API 설정 파일\n"
                "# API 키를 입력하고 USE_GEMINI를 True로 변경하면 AI 댓글 기능이 활성화됩니다.\n"
                f"GEMINI_API_KEY = ''\n"
                f"GEMINI_PROMPT = \"\"\"{default_settings['GEMINI_PROMPT']}\"\"\"\n"
                f"USE_GEMINI = False\n"
            )
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"⚠️ 설정 파일 생성 실패: {e}")
            return default_settings

    # 2. 파일 로드
    loaded_settings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            exec(f.read(), {}, loaded_settings)
    except Exception as e:
        print(f"⚠️ Gemini 설정 로드 실패: {e}")
        return default_settings

    # 기본값과 병합 (누락된 항목 방지)
    default_settings.update(loaded_settings)
    return default_settings

# 전역 설정 변수 등록
GEMINI_CONFIG = load_gemini_settings(path_gemini_setup)

# 셀렉터에 본문 추출용 추가 (Gemini가 읽을 영역)
SELECTORS["post_content"] = ".se-main-container, #postViewArea"