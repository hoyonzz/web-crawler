import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
# 요소를 찾기 위해 사용할 By 모듈
from selenium.webdriver.common.by import By
# 키보드 입력을 위해 사용할 keys 모듈
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


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

# 6. HTML 파싱하여 정보 추출하기
html = driver.page_source

soup = BeautifulSoup(html, 'lxml')

job_cards = soup.select("div[role='listitem'] a")

print(f"총{len(job_cards)}개의 채용 공고를 찾았습니다.")

# 미리보기_ 첫번째 공고의 제목과 회사명 추출하기
if len(job_cards) > 0:
    first_card = job_cards[0]
    
    # strong 태그이면서 class 이름이 'JobCard_title'로 시작하는 요소 찾기
    title = first_card.select_one("strong[class*='JobCard_title']").text
    # span 태그이면서 class 이름이 'CompanyName'으로 시작하는 요소 찾기
    company_name = first_card.select_one("span[class*='CompanyName']").text
    
    print(f"첫 번째 공고_제목: {title}")
    print(f"첫 번째 공고_회사명: {company_name}") 
    
    # 브라우저 닫기
    driver.quit()
    
    print("Selenium 실행이 완료되었습니다.") 
    