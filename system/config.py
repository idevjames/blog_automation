# system/config.py
import os
import sys

# 현재 파일의 위치를 기준으로 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# 설정 파일 경로
neighbor_message_path = os.path.join(root_dir, '서이추메세지관리.txt')
comment_message_path = os.path.join(root_dir, '서이추댓글관리.txt')
delay_config_path = os.path.join(root_dir, '랜덤딜레이관리.txt')
condition_config_path = os.path.join(root_dir, '작업조건관리.txt')

# 각 설정 파일에서 값 로드
neighbor_settings = {}
comment_settings = {}
delay_settings = {}
condition_settings = {}

# 서로이웃 신청 메시지 로드
try:
    with open(neighbor_message_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, neighbor_settings)
except Exception:
    pass

# 댓글 메시지 로드
try:
    with open(comment_message_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, comment_settings)
except Exception:
    pass

# 랜덤 딜레이 설정 로드
try:
    with open(delay_config_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, delay_settings)
except Exception:
    pass

# 작업 조건 및 실패 기준 설정 로드
try:
    with open(condition_config_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, condition_settings)
except Exception:
    pass

# 값 매핑
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

NEIGHBOR_CONFIG = {
    "messages": neighbor_settings.get("NEIGHBOR_MESSAGES", [])
}

# [신규] 댓글 메시지 리스트
COMMENT_MESSAGES = comment_settings.get("COMMENT_MESSAGES", [])

# 딜레이 설정 로드
raw_delays = delay_settings.get("CUSTOM_DELAYS", {})

# 사용자 친화적인 이름을 기존 코드와 호환되도록 매핑
# 주의: page_load는 두 기능에서 모두 사용되므로, 각각의 설정을 우선 사용하고 없으면 기본값 사용
DELAY_RANGE = {
    # 게시글 공감 관련 (blog_likes_neighbor.py에서 사용)
    "page_load": raw_delays.get("게시글공감_페이지로딩", raw_delays.get("서로이웃신청_페이지로딩", (1.0, 2.5))),
    "before_click": raw_delays.get("게시글공감_클릭전대기", (0.1, 0.3)),
    "between_actions": raw_delays.get("게시글공감_작업간대기", raw_delays.get("서로이웃신청_작업간대기", (0.2, 0.5))),
    "verify_interval": raw_delays.get("게시글공감_확인대기", (0.3, 0.5)),
    "page_nav": raw_delays.get("게시글공감_페이지이동", (1.0, 2.5)),
    
    # 서로이웃 신청 관련 (blog_add_neighbor.py에서 사용)
    "window_switch": raw_delays.get("서로이웃신청_팝업대기", (1.0, 2.0)),
    "popup_step_wait": raw_delays.get("서로이웃신청_팝업초기대기", (0.2, 0.5)),
    "popup_interaction": raw_delays.get("서로이웃신청_팝업작업대기", (0.2, 0.5)),
    "popup_form_load": raw_delays.get("서로이웃신청_메시지입력창대기", (1.5, 2.0)),
    "popup_typing": raw_delays.get("서로이웃신청_메시지입력후대기", (0.2, 0.5)),
    "popup_submit": raw_delays.get("서로이웃신청_전송후대기", (1.0, 2.0)),

    # 서로이웃 완료 후 공감/댓글 기능 (blog_add_neighbor.py에서 사용)
    "window_switch": raw_delays.get("서로이웃신청_공감댓글_스크롤대기", (0.5, 1.0)),
    "popup_step_wait": raw_delays.get("서로이웃신청_공감댓글_댓글창대기", (1.5, 2.0)),
    "popup_interaction": raw_delays.get("서로이웃신청_공감댓글_스크롤최대", 0.8),

    # 공통 설정
    "retry_wait": raw_delays.get("공통_재시도대기", (0.5, 1.0)),
    "click_offset_ratio": raw_delays.get("공통_클릭랜덤화", 3),
}

# 작업 조건 설정 로드
raw_conditions = condition_settings.get("WORK_CONDITIONS", {})

# [수정] 실패 기준 분리 (기본값 5)
DEFAULT_LIKE_FAILURE_COUNT = raw_conditions.get("게시글공감_최대실패횟수", 5)
DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT = raw_conditions.get("서로이웃신청_최대실패횟수", 5)

# [신규] 서로이웃 신청 조건 설정 로드
NEIGHBOR_CONDITION = {
    "max_likes": raw_conditions.get("서로이웃신청_최대공감수", 100),
    "max_comments": raw_conditions.get("서로이웃신청_최대댓글수", 10)
}

# -----------------------------------------------------------
# [네이버 블로그 주제 분류 데이터]
# -----------------------------------------------------------
THEME_CATEGORIES = {
    1: {
        "name": "엔터테인먼트/예술",
        "sub": {
            5: "문학/책", 6: "영화", 8: "미술/디자인", 7: "공연/전시", 
            11: "음악", 9: "드라마", 12: "스타/연예인", 13: "만화/애니", 10: "방송"
        }
    },
    2: {
        "name": "생활/노하우/쇼핑",
        "sub": {
            14: "일상/생각", 15: "육아/결혼", 16: "반려동물", 17: "좋은글/이미지",
            18: "패션/미용", 19: "인테리어/DIY", 20: "요리/레시피", 21: "상품리뷰", 36: "원예/재배"
        }
    },
    3: {
        "name": "취미/여가/여행",
        "sub": {
            22: "게임", 23: "스포츠", 24: "사진", 25: "자동차", 26: "취미",
            27: "국내여행", 28: "세계여행", 29: "맛집"
        }
    },
    4: {
        "name": "지식/동향",
        "sub": {
            30: "IT/컴퓨터", 31: "사회/정치", 32: "건강/의학", 33: "비지니스/경제",
            35: "어학/외국어", 34: "교육/학문"
        }
    }
}

# -----------------------------------------------------------
# [시스템 내부용 선택자]
# -----------------------------------------------------------
SELECTORS = {
    # [1] 피드(이웃 새글) 목록에서의 공감 버튼
    "feed_like_buttons": "div.u_likeit_list_module .u_likeit_list_btn, .u_likeit_button",

    # [2] 블로그 글 본문 하단 플로팅 바
    "post_view_like_button": "#floating_bottom .u_likeit_button",
    "post_view_comment_button": "#floating_bottom .btn_comment",
    "comment_input_area": "textarea.u_cbox_text",
    "comment_submit_button": "button.u_cbox_btn_upload",
    
    # 페이지네이션 및 링크
    "pagination": ".pagination a, .section_pagination a",
    "theme_post_links": "a.desc_inner",
    
    # [3] 이웃 추가 관련
    "add_neighbor_btn": ".btn_buddy, .btn_addbuddy, .btn_blog_neighbor, #neighbor, .btn_neighbor, a.btn_add",
    
    # 팝업창 내부 선택자
    "popup_radio_mutual_label": "label[for='each_buddy_add']", # 서로이웃 라디오 버튼 라벨
    "popup_radio_just_neighbor": "label[for='buddy_add']",      # 그냥 이웃 라디오 버튼 (체크용)
    
    "popup_next_btn": "a.btn_ok, a.button_next, .btn_confirm",   # 다음/확인 버튼
    "popup_message_input": "#message, textarea.txt_area",        # 메시지 입력창
    "popup_submit_btn": "a.btn_ok, a.button_next",               # 보내기/확인 버튼
    
    # [신규] 성공/실패 판독용 선택자
    "popup_success_text": "p.txt_desc, .guide_message, .txt_result", # 완료 메시지 텍스트 영역
    "popup_close_btn": "a.button_close, button.btn_close",           # 닫기 버튼

    # [신규] 게시글 분석용 선택자 (닉네임, 공감수, 댓글수)
    # 네이버 블로그 구조상 여러 케이스를 커버하도록 설정
    "post_nickname": "#nickNameArea, .nick, .blog_nickname, span.nick", 
    "post_like_count": "em.u_cnt, .u_likeit_list_count", 
    "post_comment_count": "#commentCount, .btn_comment em, .area_comment em",
    
    # [수정/추가] 리스트 화면 분석용 선택자
    "theme_post_container": "div.info_post",      # 글 목록의 개별 박스(컨테이너)
    "post_list_nickname": ".name_author",         # 작성자 닉네임
    "post_list_like_count": ".like em",           # 공감 수 숫자
    "post_list_comment_count": ".reply em",       # 댓글 수 숫자
    "theme_post_links": "a.desc_inner",           # (기존 유지) 클릭할 글 제목 링크

    # [통합 액션용]
    "floating_container": "#floating_bottom .wrap_postcomment",
    "static_container": ".wrap_postcomment",
    "like_button_face": "a.u_likeit_button._face",
    "comment_guide_text": ".u_cbox_guide",
    "comment_text_area": ".u_cbox_text",
}