import sys
import os

# 1. 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# 2. 모듈 임포트
from system import config
from system.bot_class.session_manager import NaverSessionManager
from system.bot_class.blog_likes_neighbors import BlogLikesNeighbors
from system.bot_class.blog_neighbor_adder import BlogNeighborAdder

def main():
    # 3. 세션 매니저 생성
    session_manager = NaverSessionManager()
    
    if hasattr(session_manager, 'ensure_login'):
        session_manager.ensure_login()
    else:
        session_manager.login() 

    try:
        driver = session_manager.driver
        
        # 4. 봇 인스턴스 생성
        blog_bot = BlogLikesNeighbors(driver)
        neighbor_bot = BlogNeighborAdder(driver)
        
        while True:
            print("\n" + "="*40)
            print(" 1. 이웃 새글 공감하기")
            print(" 2. 주제별 블로그 서로이웃 신청하기")
            print(" q. 프로그램 종료")
            print("="*40)
            choice = input("선택하세요: ").lower().strip()

            if choice == '1':
                val = input(f"몇 개 공감할까요? (엔터 시 {config.DEFAULT_LIKE_COUNT}개): ")
                target = int(val) if val.isdigit() else config.DEFAULT_LIKE_COUNT
                
                if blog_bot.go_to_blog_main():
                    blog_bot.click_neighbor_likes(target)

            elif choice == '2':
                val = input("몇 명에게 '성공적으로' 신청할까요? (예: 5): ")
                target_people = int(val) if val.isdigit() else 5
                
                print(f"\n🚀 총 {target_people}명 신청 성공을 목표로 시작합니다!")
                
                current_success = 0
                page = 1
                
                while current_success < target_people:
                    neighbor_bot.go_to_theme_list(page)
                    
                    added_count, is_done = neighbor_bot.process_neighbors(current_success, target_people)
                    current_success += added_count
                    
                    if current_success >= target_people:
                        print(f"\n🎉 목표 달성! 총 {current_success}명에게 신청을 완료했습니다.")
                        break
                    
                    if is_done:
                        print("더 이상 처리할 블로그가 없습니다.")
                        break
                    
                    print(f"\n📢 {page}페이지 탐색 끝. (현재 누적 성공: {current_success}/{target_people})")
                    print(f"➡️ 다음 페이지({page + 1})로 이동하여 계속 찾습니다...")
                    page += 1
                    
            elif choice == 'q':
                print("프로그램을 종료합니다.")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 강제 종료되었습니다.")
    except Exception as e:
        # 에러 메시지만 간단히 출력 (Stacktrace 숨김)
        print(f"\n❌ 실행 중 오류 발생: {str(e).splitlines()[0]}")
    finally:
        # [수정] 브라우저를 닫지 않고 유지함
        print("\n✨ 프로그램이 끝났습니다. 브라우저는 닫지 않고 유지합니다.")
        # if hasattr(session_manager.driver, 'quit'):
        #     session_manager.driver.quit()

if __name__ == "__main__":
    main()