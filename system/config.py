# system/config.py
import os
import sys

# [1] 경로 인식 로직 (실행 파일 빌드 시에도 작동하도록)
if getattr(sys, 'frozen', False):
    # .exe 또는 .app으로 실행 중일 때 (실행 파일 위치 기준)
    root_dir = os.path.dirname(sys.executable)
else:
    # 일반 .py 파일로 실행 중일 때 (system 폴더의 상위 폴더 기준)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)

# [2] 분리된 설정 파일 경로 설정
path_like_setup = os.path.join(root_dir, '게시글공감설정.txt')
path_add_setup = os.path.join(root_dir, '서이추설정.txt')
path_neighbor_msg = os.path.join(root_dir, '서이추메세지관리.txt')
path_comment_msg = os.path.join(root_dir, '서이추댓글관리.txt')

def load_settings(file_path):
    """설정 파일(.txt)에서 딕셔너리 형태로 값을 로드하는 공용 함수"""
    settings = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                exec(f.read(), {}, settings)
        except Exception as e:
            print(f"⚠️ 설정 로드 실패 ({os.path.basename(file_path)}): {e}")
    return settings

# [3] 데이터 로드 실행
like_raw = load_settings(path_like_setup)
add_raw = load_settings(path_add_setup)
neighbor_msg_data = load_settings(path_neighbor_msg)
comment_msg_data = load_settings(path_comment_msg)

# --- [이웃 새글 공감 전용 설정] ---
LIKES_NEIGHBOR_CONFIG = {
    "delays": like_raw.get("LIKE_NEIGHBORS_DELAYS", {}),
    "conditions": like_raw.get("LIKE_NEIGHBORS_CONDITIONS", {})
}

# --- [서로이웃 신청 전용 설정] ---
# 메세지와 댓글 리스트를 여기에 포함시켜 관리합니다.
ADD_NEIGHBOR_CONFIG = {
    "delays": add_raw.get("ADD_NEIGHBORS_DELAYS", {}),
    "conditions": add_raw.get("ADD_NEIGHBORS_CONDITIONS", {}),
    "messages": neighbor_msg_data.get("NEIGHBOR_MESSAGES", []),
    "comments": comment_msg_data.get("COMMENT_MESSAGES", [])
}

# 공통 설정
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# [4] 네이버 블로그 주제 분류 데이터
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

# [5] 시스템 내부용 선택자
SELECTORS = {
    "feed_like_buttons": "div.u_likeit_list_module .u_likeit_list_btn, .u_likeit_button",
    "post_view_like_button": "#floating_bottom .u_likeit_button",
    "post_view_comment_button": "#floating_bottom .btn_comment",
    "comment_input_area": "textarea.u_cbox_text",
    "comment_submit_button": "button.u_cbox_btn_upload",
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