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
    default_prompt = """당신은 블로그에서 활발하게 소통하는 2030 이웃입니다. 
영혼이 없거나 반말하지 않으며, 친절하고 다정한 말투로 댓글을 작성하세요.

[작성 규칙]
1. 제목에 포함된 핵심 키워드를 활용하여 '포스팅 덕분에 도움을 받았다'는 감사의 내용을 작성할 것.
2. 본문의 아주 세부적인 정보(층수, 시간, 가격 등)는 틀릴 위험이 있으니 직접 언급하지 말고, 전체적인 주제를 칭찬할 것.
3. 너무 길지 않게 1~2문장 사이로 작성할 것.
4. 분석적인 말투는 금지하며, 이웃과 대화하듯 자연스럽게 작성할 것.
5. 이모지는 제외하고, 채팅 이모티콘(ㅎㅎ, ^^, :), ㅠㅠ]"""

    default_settings = {
        "GEMINI_API_KEY": "",
        "GEMINI_PROMPT": default_prompt
    }

    # 1. 파일이 없으면 생성 (USE_GEMINI는 파일에 쓰지 않음)
    if not os.path.exists(file_path):
        try:
            # 사용자가 수정하기 편하게 포맷팅하여 저장
            content = f"GEMINI_API_KEY = ''\n\nGEMINI_PROMPT = \"\"\"{default_prompt}\"\"\"\n"
            with open(file_path, 'w', encoding='utf-8') as f: 
                f.write(content)
        except Exception as e:
            print(f"⚠️ 설정 파일 생성 실패: {e}")
            # 파일 생성 실패 시 기본값에 USE_GEMINI False 주입 후 반환
            default_settings["USE_GEMINI"] = False
            return default_settings
    
    # 2. 파일 읽기 (사용자가 수정한 값을 가져옴)
    loaded = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: 
            exec(f.read(), {}, loaded)
    except Exception as e: 
        print(f"⚠️ 설정 파일 로드 실패: {e}")
        default_settings["USE_GEMINI"] = False
        return default_settings
    
    # 로드된 값 업데이트
    default_settings.update(loaded)

    # 3. [핵심] 메모리 변수 설정: 키와 프롬프트가 둘 다 있어야 True
    api_key = default_settings.get("GEMINI_API_KEY", "").strip()
    prompt = default_settings.get("GEMINI_PROMPT", "").strip()

    if api_key and prompt:
        default_settings["USE_GEMINI"] = True
    else:
        default_settings["USE_GEMINI"] = False

    return default_settings

# 설정 변수 초기화
LIKES_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}}
ADD_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}, "messages": [], "comments": []}

GEMINI_CONFIG = {}
SMART_NEIGHBOR_CONFIG = {"delays": {}, "conditions": {}, "weights": {}}

# [핵심] gui_main에서 호출할 설정 동기화 함수
def sync_all_configs():
    global LIKES_NEIGHBOR_CONFIG, ADD_NEIGHBOR_CONFIG, GEMINI_CONFIG, SMART_NEIGHBOR_CONFIG
    
    like_raw = load_settings(path_like_setup)
    add_raw = load_settings(path_add_setup)

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
    
    SMART_NEIGHBOR_CONFIG["delays"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_DELAYS", {
        '페이지로딩': (2.0, 3.5),
        '스크롤간격': (0.2, 0.3),
        '블로그_접속_대기': (2.0, 3.0),
        '프레임_전환_대기': (0.5, 1.0),
        '중복_체크_대기': (0.1, 0.3),
        '입력창_찾기_대기': (0.5, 0.8),
        '입력창_클릭_대기': (0.2, 0.4),
        '타이핑_후_대기': (0.2, 0.3),
        '등록_완료_대기': (0.2, 0.5),
    })
    SMART_NEIGHBOR_CONFIG["conditions"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_CONDITIONS", {
        '스크롤보폭': 700,
        '데이터수집스크롤간격': (0.2, 0.3),
        '댓글목표': 30,    
        '시작페이지': 1,
        '댓글주기': 7,
    })
    
    SMART_NEIGHBOR_CONFIG["weights"] = smart_neighbor_management_raw.get("SMART_MANAGEMENT_WEIGHTS", {
        '댓글점수': 10,
        '답글접수': 3,
        '공감점수': 1
    })
    SMART_NEIGHBOR_CONFIG["messages"] = comment_msg_data.get("COMMENT_MESSAGES", [])

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

GUI_GUIDE_MESSAGES = {
    "like": """============================================================
[안내] ❤️ 이웃 공감 모드
- 블로그 홈 (내 이웃 게시글) 피드를 순회하며 이웃들의 최신글에 공감을 남깁니다
- 목표 수 / 시작페이지를 설정하여 범위를 조절하세요
- 최초 실행의 경우 실패 시 [🚀 실행 시작]을 다시 눌러주세요
============================================================""",
    "add": """============================================================
[안내] 🤝 서이추 신청 모드
- 블로그 홈 > 주제별 보기에서 피드를 순회하며 서로이웃을 추가합니다.
- 대분류 / 상세 주제 / 목표 인원 / 시작 페이지를 설정하여 범위를 조절하세요
- 서로 이웃 추가에 성공하면 공감과 댓글을 작성합니다 (신청 메세지 목록 / 댓글 목록 참고)
===========================================================""",
    "smart": """============================================================
[안내] ⭐ 스마트 관리 모드
- 알림 리스트에서 이웃 데이터 및 점수를 합산합니다. (댓글/답글/공감 수 저장)
- 이웃 데이터가 모두 확보되면 블로그 홈(내 이웃 게시글) 피드를 순회합니다
- Gemini AI Studio에 방문하여 API Key와 프롬프트를 입력하면 정해진 토큰 내에서 AI 댓글을 수행합니다
- 댓글을 달게되면 내부 DB에 저장하여 주기(일) 동안 해당 블로거에게 댓글을 남기지 않습니다
- 내부적인 정책에 따라 행동 양식이 변경됩니다
 [AI_COMMENT]
 - 내 게시글에 방문하여 댓글을 남긴 이웃 
 => AI로 댓글을 작성하여 남김
 
 [NORMAL_COMMENT]
 - 내 댓글에 답글만 남긴 이웃 
 => 저장된 댓글만 남김
 
 [LIKE_ONLY]
 - 기록에 없는 이웃 
 => 공감만 진행
==========================================================="""
}