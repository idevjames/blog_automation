# system/main.py
import sys
import os
import config
from bot_class.session_manager import NaverSessionManager
from bot_class.blog_likes_neighbor import BlogLikesNeighbor
from bot_class.blog_add_neighbor import BlogAddNeighbor

def print_main_categories():
    print("\n[ 1단계: 대분류 선택 ]")
    for cat_id, cat_data in config.THEME_CATEGORIES.items():
        print(f" {cat_id}. {cat_data['name']}")
    print("="*30)

def print_sub_categories(cat_id):
    cat_data = config.THEME_CATEGORIES.get(cat_id)
    if not cat_data:
        return False
    
    print(f"\n[ 2단계: '{cat_data['name']}' 상세 주제 선택 ]")
    for sub_id, sub_name in cat_data['sub'].items():
        print(f" [{sub_id}] {sub_name}")
    print("="*30)
    return True

def get_user_input_number(prompt_text):
    while True:
        val = input(prompt_text).strip()
        if val.lower() == 'b':
            return 'BACK'
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("❌ 숫자를 정확히 입력해주세요. (1 이상의 정수, 뒤로가기는 b)")

def main():
    print("🤖 네이버 블로그 자동화 봇 (v1.5 - 환경 분리 완료)")
    
    session = NaverSessionManager()
    if not session.ensure_login():
        print("프로그램을 종료합니다.")
        return

    liker_bot = BlogLikesNeighbor(session.driver)
    adder_bot = BlogAddNeighbor(session.driver)

    while True:
        try:
            print("\n" + "="*40)
            print(" 1. 이웃 새글 공감하기")
            print(" 2. 주제별 블로그 찾아 서로이웃 신청하기")
            print(" q. 종료")
            print("="*40)
            
            choice = input("선택 (뒤로가기는 b) > ").strip().lower()

            if choice == '1':
                count = get_user_input_number("몇 개의 글에 공감할까요? (뒤로가기: b): ")
                if count == 'BACK': continue
                start_page = get_user_input_number("몇 페이지부터 탐색할까요? (처음이면 1): ")
                if start_page == 'BACK': continue
                liker_bot.run(count, start_page)

            elif choice == '2':
                while True:
                    print_main_categories()
                    main_cat = input("대분류 번호를 입력하세요 (뒤로가기: b): ").strip()
                    if main_cat.lower() == 'b': break
                    
                    if main_cat.isdigit() and int(main_cat) in config.THEME_CATEGORIES:
                        main_cat_id = int(main_cat)
                        should_break_loop1 = False 
                        
                        while True:
                            if not print_sub_categories(main_cat_id): break
                            target_sub_dict = config.THEME_CATEGORIES[main_cat_id]['sub']
                            sub_cat = input("상세 주제의 번호(대괄호 안 숫자)를 입력하세요 (뒤로가기: b): ").strip()
                            if sub_cat.lower() == 'b': break
                            
                            if sub_cat.isdigit() and int(sub_cat) in target_sub_dict:
                                dir_no = int(sub_cat)
                                target_count = get_user_input_number("몇 명에게 신청할까요? (뒤로가기: b): ")
                                if target_count == 'BACK': continue
                                start_page = get_user_input_number("몇 페이지부터 탐색할까요? (처음이면 1): ")
                                if start_page == 'BACK': continue
                                
                                adder_bot.run(main_cat_id, dir_no, target_count, start_page)
                                should_break_loop1 = True 
                                break 
                        if should_break_loop1: break
            elif choice == 'q':
                break
        except KeyboardInterrupt:
            print("\n🏠 메인 메뉴로 돌아갑니다.")
            continue
            
    session.driver.quit()

if __name__ == "__main__":
    main()