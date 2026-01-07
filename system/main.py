# system/main.py
import sys
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
    """숫자 입력을 강제하는 헬퍼 함수"""
    while True:
        val = input(prompt_text).strip()
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("❌ 숫자를 정확히 입력해주세요. (1 이상의 정수)")

def main():
    print("🤖 네이버 블로그 자동화 봇 (v1.0)")
    
    session = NaverSessionManager()
    if not session.ensure_login():
        print("프로그램을 종료합니다.")
        return

    liker_bot = BlogLikesNeighbor(session.driver)
    adder_bot = BlogAddNeighbor(session.driver)

    while True:
        print("\n" + "="*40)
        print(" 1. 이웃 새글 공감하기")
        print(" 2. 주제별 블로그 찾아 서로이웃 신청하기")
        print(" q. 종료")
        print("="*40)
        
        choice = input("선택 > ").strip().lower()

        if choice == '1':
            # [수정] 무조건 입력받기
            count = get_user_input_number("몇 개의 글에 공감할까요?: ")
            liker_bot.run(count)

        elif choice == '2':
            # 1. 대분류 출력 및 입력
            print_main_categories()
            while True:
                main_cat = input("대분류 번호를 입력하세요: ").strip()
                if main_cat.isdigit() and int(main_cat) in config.THEME_CATEGORIES:
                    main_cat_id = int(main_cat)
                    break
                print("❌ 올바른 대분류 번호가 아닙니다.")
            
            # 2. 상세분류 출력 및 입력
            if print_sub_categories(main_cat_id):
                target_sub_dict = config.THEME_CATEGORIES[main_cat_id]['sub']
                while True:
                    sub_cat = input("상세 주제의 번호(대괄호 안 숫자)를 입력하세요: ").strip()
                    if sub_cat.isdigit() and int(sub_cat) in target_sub_dict:
                        dir_no = int(sub_cat)
                        break
                    print("❌ 올바른 상세 번호가 아닙니다.")
                
                sub_name = target_sub_dict[dir_no]
                print(f"👉 선택된 주제: 대분류[{main_cat_id}] - {sub_name}({dir_no})")
                
                # [수정] 무조건 입력받기
                target_count = get_user_input_number("몇 명에게 신청할까요?: ")
                
                adder_bot.run(main_cat_id, dir_no, target_count)
            else:
                print("❌ 카테고리 정보를 불러오지 못했습니다.")

        elif choice == 'q':
            print("👋 프로그램을 종료합니다.")
            break
        
    session.driver.quit()

if __name__ == "__main__":
    main()