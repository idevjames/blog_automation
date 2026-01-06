import time
import random
from selenium.webdriver.common.action_chains import ActionChains
import config

def smart_sleep(range_tuple, reason=None):
    min_sec, max_sec = range_tuple
    wait_time = random.uniform(min_sec, max_sec)
    if reason:
        print(f"   (⏳ {reason}: {wait_time:.2f}초 대기...)")
    time.sleep(wait_time)

def smart_click(driver, element):
    """요소의 크기를 계산하여 중앙 기준 랜덤 좌표로 물리적 클릭 수행"""
    try:
        actions = ActionChains(driver)
        size = element.size
        w = size['width']
        h = size['height']

        # config의 비율을 사용하여 랜덤 오프셋 생성
        ratio = config.DELAY_RANGE["click_offset_ratio"]
        random_x = random.randint(int(-w/ratio), int(w/ratio))
        random_y = random.randint(int(-h/ratio), int(h/ratio))

        actions.move_to_element_with_offset(element, random_x, random_y).click().perform()
        print(f"   (🎯 물리 클릭 반영: x_offset={random_x}, y_offset={random_y})")
        return True
    except Exception as e:
        print(f"   (⚠️ 물리 클릭 실패, JS로 대체 시도: {e})")
        driver.execute_script("arguments[0].click();", element)
        return False