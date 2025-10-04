import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
# 요소를 찾기 위해 사용할 By 모듈
from selenium.webdriver.common.by import By
# 키보드 입력을 위해 사용할 keys 모듈
from selenium.webdriver.common.keys import Keys



# 1. WebDriver 설정
service = ChromeService(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 2. 원티드 메인 페이지로 이동
URL = 'https://www.wanted.co.kr/'
driver.get(URL)
time.sleep(2)

# 3. 검색창 활성화를 위해 돋보기 아이콘 클릭
search_button = driver.find_element(By.CSS_SELECTOR, "button[data-attribute-id='gnb']")
search_button.click()
time.sleep(1)

# 4. 검색창에 '백엔드' 입력
search_input = driver.find_element(By.CSS_SELECTOR, 'input.SearchInput_SearchInput__R6jwT')
search_input.send_keys('백엔드')
search_input.send_keys(Keys.ENTER)
time.sleep(2)

# 5. 페이지 끝까지 스크롤
last_height = driver.execute_script('return document.body.scrollHeight')
while True:
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    new_height = driver.execute_script('return document.body.scrollHeight')
    if new_height == last_height:
        break
    last_height = new_height

print('페이지 스크롤이 완료되었습니다.')
time.sleep(5)

driver.quit()

print('Selenium 실행이 완료되었습니다.')