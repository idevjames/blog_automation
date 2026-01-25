# system/utils.py
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
import config
from PyQt6.QtWidgets import QApplication

def smart_sleep(range_tuple, reason):
    """지정된 범위 내에서 랜덤하게 대기하며 사유를 출력 (GUI 먹통/발열 방지 버전)"""
    min_sec, max_sec = range_tuple
    wait_time = random.uniform(min_sec, max_sec)
    
    exclude_reasons = [
        "메시지 작성 후 검토 대기", 
        "최종 신청 전송 완료 대기",
        "공감/댓글 영역 노출을 위한 스크롤 대기",
        "공감 클릭 전 망설임 대기",
        "공감 완료 후 댓글 작성 전 휴식",
        "댓글 입력창 가시성 대기",
        "공감 버튼 클릭 전 실제 사람처럼 대기",
        "공감 처리 결과가 서버에 반영되는지 확인 중"
    ]
    
# 사유 출력
    if reason and reason not in exclude_reasons:
        # 너무 짧은 대기는 로그 생략 가능
        if wait_time > 0.5:
            print(f"   (⏳ {reason}: {wait_time:.2f}초...)")

    # [핵심] 통으로 time.sleep을 쓰면 중단 반응이 느려지므로
    # 0.1초 단위로 쪼개서 대기 (GUI 프리징 없음 + 발열 방지)
    start_time = time.time()
    while time.time() - start_time < wait_time:
        time.sleep(0.1) 
                
def smart_click(driver, element):
    """요소의 크기를 계산하여 중앙 기준 랜덤 좌표로 물리적 클릭 수행"""
    try:
        actions = ActionChains(driver)
        size = element.size
        w = size['width']
        h = size['height']

        # [수정] config.DELAY_RANGE 대신 LIKES_NEIGHBOR_CONFIG의 클릭랜덤화 설정 참조
        # 기본적으로 LIKES 설정을 참조하되, 유연한 관리를 위해 분리된 구조를 사용합니다.
        ratio = config.LIKES_NEIGHBOR_CONFIG["delays"].get("클릭랜덤화", 2)
        
        random_x = random.randint(int(-w/ratio), int(w/ratio))
        random_y = random.randint(int(-h/ratio), int(h/ratio))

        actions.move_to_element_with_offset(element, random_x, random_y).click().perform()
        return True
    except Exception as e:
        # [수정] 에러 메시지 정리
        print(f"   (⚠️ 물리 클릭 실패 : {e})")
        return False
    
    
def human_typing(element, text):
    """사람이 타이핑하는 것처럼 한 글자씩 입력"""
    for char in text:
        element.send_keys(char)
        # 글자 사이의 간격을 랜덤하게 줘서 기계적인 느낌을 없앰
        time.sleep(random.uniform(0.05, 0.15))
        
def human_scroll(driver, distance):
    """마우스 휠을 굴리는 물리 스크롤 (자바스크립트 X)"""
    actions = ActionChains(driver)
    
    # 300~700 픽셀 사이에서 랜덤하게 휠 굴림
    amount = distance
        
    actions.scroll_by_amount(0, amount).perform()
    print(f"   (🖱️ 물리 스크롤 이동: {amount}px)")
    
    
def human_scroll_to_ratio(driver, scroll_ratio):
    """목표 비율까지 휠을 여러 번 나눠서 굴림 (가장 안전)"""
    total_height = driver.execute_script("return document.body.scrollHeight")
    target_position = total_height * scroll_ratio
    
    current_pos = driver.execute_script("return window.pageYOffset")
    remaining = target_position - current_pos
    
    while remaining > 0:
        # 한 번에 굴릴 양 (300~600 사이 랜덤)
        step = random.randint(500, 1000)
        if step > remaining:
            step = int(remaining)
            
        # 위에서 만든 물리 스크롤 호출
        human_scroll(driver, step)
        
        current_pos = driver.execute_script("return window.pageYOffset")
        remaining = target_position - current_pos
        
        # 사람처럼 잠깐씩 쉬기
        time.sleep(random.uniform(0.1, 0.3))