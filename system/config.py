# system/config.py
import os
import sys

# 현재 파일의 위치를 기준으로 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
settings_path = os.path.join(root_dir, 'settings.txt')

user_settings = {}
try:
    with open(settings_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, user_settings)
except Exception:
    pass

# 값 매핑
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

NEIGHBOR_CONFIG = {
    "messages": user_settings.get("NEIGHBOR_MESSAGES", [])
}

# [신규] 댓글 메시지 리스트
COMMENT_MESSAGES = user_settings.get("COMMENT_MESSAGES", [])

DELAY_RANGE = user_settings.get("CUSTOM_DELAYS", {})
# [수정] 실패 기준 분리 (기본값 5)
DEFAULT_LIKE_FAILURE_COUNT = user_settings.get("DEFAULT_LIKE_FAILURE_COUNT", 5)
DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT = user_settings.get("DEFAULT_ADD_NEIGHBOR_FAILURE_COUNT", 5)

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
    "popup_close_btn": "a.button_close, button.btn_close"            # 닫기 버튼
}