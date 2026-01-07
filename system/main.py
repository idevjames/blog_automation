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
    """
    숫자 입력을 받되, 'b' 또는 'B' 입력 시 'BACK'을 반환
    """
    while True:
        val = input(prompt_text).strip()
        
        # 뒤로가기 체크
        if val.lower() == 'b':
            return 'BACK'
            
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("❌ 숫자를 정확히 입력해주세요. (1 이상의 정수, 뒤로가기는 b)")

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
        
        choice = input("선택 (뒤로가기는 b) > ").strip().lower()

        # [메뉴 1] 이웃 새글 공감
        if choice == '1':
            count = get_user_input_number("몇 개의 글에 공감할까요? (뒤로가기: b): ")
            if count == 'BACK':
                continue # 메인 메뉴로 복귀
                
            liker_bot.run(count)

        # [메뉴 2] 서로이웃 신청
        elif choice == '2':
            # <Loop 1> 대분류 선택 반복 구간
            while True:
                print_main_categories()
                main_cat = input("대분류 번호를 입력하세요 (뒤로가기: b): ").strip()
                
                if main_cat.lower() == 'b':
                    break # <Loop 1> 탈출 -> 메인 메뉴로
                
                if main_cat.isdigit() and int(main_cat) in config.THEME_CATEGORIES:
                    main_cat_id = int(main_cat)
                    
                    # <Loop 2> 상세 주제 선택 반복 구간
                    should_break_loop1 = False # 작업 완료 시 대분류 루프까지 깰 플래그
                    
                    while True:
                        if not print_sub_categories(main_cat_id):
                            print("❌ 카테고리 로드 실패")
                            break
                        
                        target_sub_dict = config.THEME_CATEGORIES[main_cat_id]['sub']
                        sub_cat = input("상세 주제의 번호(대괄호 안 숫자)를 입력하세요 (뒤로가기: b): ").strip()

                        if sub_cat.lower() == 'b':
                            break # <Loop 2> 탈출 -> 대분류 선택으로 돌아감
                        
                        if sub_cat.isdigit() and int(sub_cat) in target_sub_dict:
                            dir_no = int(sub_cat)
                            sub_name = target_sub_dict[dir_no]
                            print(f"👉 선택된 주제: 대분류[{main_cat_id}] - {sub_name}({dir_no})")
                            
                            # [마지막 단계] 개수 입력
                            target_count = get_user_input_number("몇 명에게 신청할까요? (뒤로가기: b): ")
                            if target_count == 'BACK':
                                continue # <Loop 2>의 시작(상세 주제 선택)으로 돌아감
                            
                            # 실제 봇 실행
                            adder_bot.run(main_cat_id, dir_no, target_count)
                            
                            # 실행이 끝났으면 메인 메뉴로 나가기 위해 플래그 설정
                            should_break_loop1 = True 
                            break # <Loop 2> 탈출
                        else:
                            print("❌ 올바른 상세 번호가 아닙니다.")
                    
                    # 작업 완료 후 메인 메뉴로 가기 위한 체크
                    if should_break_loop1:
                        break # <Loop 1> 탈출 -> 메인 메뉴로
                        
                else:
                    print("❌ 올바른 대분류 번호가 아닙니다.")

        elif choice == 'q':
            print("👋 프로그램을 종료합니다.")
            break
            
        elif choice == 'b':
             # 메인에서 b를 누르면 그냥 루프 다시 돔 (아무 일도 안 일어남)
             pass
        
    session.driver.quit()

if __name__ == "__main__":
    main()