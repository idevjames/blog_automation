import config
from bot_class.session_manager import NaverSessionManager
from bot_class.blog_bot import NaverBlogBot
from bot_class.blog_neighbor import BlogNeighbor

def main():
    session_manager = NaverSessionManager()
    
    try:
        if session_manager.ensure_login():
            blog_bot = NaverBlogBot(session_manager.driver)
            neighbor_bot = BlogNeighbor(session_manager.driver)
            
            while True:
                print("\n" + "="*40)
                print(" 1. 이웃 새글 공감하기")
                print(" 2. 주제별 블로그 서로이웃 신청하기")
                print(" q. 프로그램 종료")
                print("="*40)
                choice = input("선택하세요: ").lower().strip()

                if choice == '1':
                    # [공감하기] 항상 블로그 메인으로 이동 후 시작
                    val = input(f"몇 개 공감할까요? (엔터 시 {config.DEFAULT_LIKE_COUNT}개): ")
                    target = int(val) if val.isdigit() else config.DEFAULT_LIKE_COUNT
                    
                    if blog_bot.go_to_blog_main():
                        blog_bot.click_neighbor_likes(target)

                elif choice == '2':
                    # [서로이웃] 목표 인원 수만큼 성공할 때까지 페이지 자동 넘김
                    val = input("몇 명에게 '성공적으로' 신청할까요? (예: 5): ")
                    target_people = int(val) if val.isdigit() else 5
                    
                    print(f"\n🚀 총 {target_people}명 신청 성공을 목표로 시작합니다!")
                    
                    current_success = 0
                    page = 1
                    
                    while current_success < target_people:
                        # 1. 해당 페이지로 이동
                        neighbor_bot.go_to_theme_list(page)
                        
                        # 2. 이웃 신청 수행 (인자 2개 전달)
                        added, is_done = neighbor_bot.process_neighbors(current_success, target_people)
                        
                        current_success += added
                        
                        # 목표 달성 체크
                        if is_done or current_success >= target_people:
                            print(f"\n🎉 목표 달성! 총 {current_success}명에게 신청을 완료했습니다.")
                            break
                        
                        # 목표 미달성 시 다음 페이지로
                        print(f"\n📢 {page}페이지 탐색 끝. (현재 성공: {current_success}/{target_people})")
                        print(f"➡️ 다음 페이지({page + 1})로 이동하여 계속 찾습니다...")
                        page += 1
                        
                elif choice == 'q':
                    print("프로그램을 종료합니다.")
                    break
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        session_manager.driver.quit()

if __name__ == "__main__":
    main()