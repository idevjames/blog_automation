import time
import random
from typing import Union, Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

# =========================================================
# ⚙️ [내부 설정] Smart Util Configuration
# =========================================================
SMART_CONFIG = {
    "TYPING_SPEED": (0.05, 0.15),
    "CLICK_OFFSET_RATIO": 3,
    "SCROLL_CHUNK_SIZE": (300, 600),
    "SCROLL_STEP_DELAY": (0.05, 0.15),
    "SLEEP_CHUNK": 0.1
}

# =========================================================
# 🛠️ [공개 함수]
# =========================================================

def smart_sleep(range_tuple: Tuple[float, float], reason: str = ""):
    """랜덤 대기"""
    min_sec, max_sec = range_tuple
    wait_time = random.uniform(min_sec, max_sec)
    
    if reason:
        print(f"   (⏳ {reason}: {wait_time:.2f}초...)")

    start_time = time.time()
    chunk = SMART_CONFIG["SLEEP_CHUNK"]
    while time.time() - start_time < wait_time:
        remaining = wait_time - (time.time() - start_time)
        sleep_sec = min(remaining, chunk)
        if sleep_sec > 0:
            time.sleep(sleep_sec)

def smart_click(driver: WebDriver, element: WebElement, visible_debug: bool = False) -> bool:
    print(f"   (👉 스마트 클릭 시도...)")
    try:
        if not element.is_displayed():
            human_scroll(driver, element)
            time.sleep(0.5)

        if element.size['width'] == 0 or element.size['height'] == 0:
            print(f"   (⚠️ 물리 클릭 실패: 요소 크기 0)")
            return False

        # --- [DEBUG] 명시적으로 True일 때만 스타일 변경 ---
        if visible_debug:
            driver.execute_script("arguments[0].setAttribute('data-old-border', arguments[0].style.border);", element)
            driver.execute_script("arguments[0].style.border='3px solid red'", element)

        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(0.5)
        
        if visible_debug:
            time.sleep(2) # 눈으로 확인할 시간 확보
        
        actions.click().perform()
        
        return True
        
    except Exception as e:
        print(f"   (⚠️ 물리 클릭 실패: {e})")
        return False
    
    finally:
        if visible_debug:
            try: driver.execute_script("arguments[0].style.border=arguments[0].getAttribute('data-old-border');", element)
            except: pass

def human_typing(element: WebElement, text: str):
    """[Type] 타이핑"""
    try:
        element.click()
    except: pass

    min_s, max_s = SMART_CONFIG["TYPING_SPEED"]
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_s, max_s))

def human_scroll(driver: WebDriver, target: Union[WebElement, float, int]) -> bool:
    """[Scroll] 통합 스크롤"""
    if isinstance(target, WebElement):
        try:
            # 요소가 있는 곳으로 마우스 이동 (브라우저 자동 스크롤)
            ActionChains(driver).move_to_element(target).perform()
            return True
        except:
            return False
    elif isinstance(target, float):
        try:
            total_h = driver.execute_script("return document.body.scrollHeight")
            target_y = total_h * target
            return _scroll_by_pixels(driver, int(target_y))
        except: return False
    elif isinstance(target, int):
        return _scroll_by_pixels(driver, target)
    return False

def find_element_smart(driver: WebDriver, selector: str) -> Union[WebElement, None]:
    """
    [Find] 진짜 눈에 보이고 크기가 있는 '진짜 버튼'만 찾아냅니다.
    숨겨진 요소(display:none, size:0)는 철저히 무시합니다.
    """
    
    def _is_valid(el):
        """진짜 상호작용 가능한 요소인지 검증"""
        try:
            return el.is_displayed() and el.size['width'] > 0 and el.size['height'] > 0
        except:
            return False

    # 1. [Top Frame] 먼저 탐색 (보통 플로팅 바나 사이드바는 여기에 있음)
    try:
        driver.switch_to.default_content()
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for el in elements:
            if _is_valid(el):
                return el
    except: pass
    
    # 2. [mainFrame] 탐색 (본문 안에 있는 경우)
    try:
        driver.switch_to.default_content()
        driver.switch_to.frame("mainFrame")
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for el in elements:
            if _is_valid(el):
                return el
    except: pass

    return None

# =========================================================
# 🔒 [내부 함수]
# =========================================================

def _scroll_by_pixels(driver: WebDriver, pixels: int) -> bool:
    if pixels == 0: return True
    actions = ActionChains(driver)
    chunk_min, chunk_max = SMART_CONFIG["SCROLL_CHUNK_SIZE"]
    remaining = abs(pixels)
    direction = 1 if pixels > 0 else -1
    
    while remaining > 0:
        step = random.randint(chunk_min, chunk_max)
        if step > remaining: step = remaining
        actions.scroll_by_amount(0, step * direction).perform()
        remaining -= step
        time.sleep(0.05)
    return True