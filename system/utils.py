# system/utils.py
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
import config

def smart_sleep(range_tuple, reason):
    """지정된 범위 내에서 랜덤하게 대기하며 사유를 출력 (reason 필수)"""
    min_sec, max_sec = range_tuple
    wait_time = random.uniform(min_sec, max_sec)
    # 모든 대기 상황을 출력하도록 설정
    print(f"   (⏳ {reason}: {wait_time:.2f}초 대기...)")
    time.sleep(wait_time)

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