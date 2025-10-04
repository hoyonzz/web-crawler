import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
# 요소를 찾기 위해 사용할 By 모듈
from selenium.webdriver.common.by import By
# 키보드 입력을 위해 사용할 keys 모듈
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd


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

job_list = []

job_cards = soup.select("div[role='listitem'] a")

print(f"총{len(job_cards)}개의 채용 공고를 찾았습니다.")

# 7. 각 공고 카드를 순회하며 정보를 추출
for card in job_cards:
    # strong 태그이면서 class 이름이 'JobCard_title'로 시작하는 요소 찾기
    title = card.select_one("strong[class*='JobCard_title']").text
    # span 태그이면서 class 이름이 'CompanyName'으로 시작하는 요소 찾기
    company_name = card.select_one("span[class*='CompanyName']").text
    # 공고 상세 페이지로 연결되는 링크
    link = "https://www.wanted.co.kr" + card['href']
    
    # 추출한 정보를 딕셔너리 형태로 저장
    job_info = {
        'title': title,
        'company': company_name,
        'link':link
    }
    
    job_list.append(job_info)
    
# 8. pandas DataFrame으로 변환하고 CSV 파일로 저장
# 딕셔너리 리스트를 바탕으로 DataFrame생성
df = pd.DataFrame(job_list)

# DataFrame을 CSV 파일로 저장
df.to_csv("wanted_backend_jobs.csv", index=False, encoding='utf-8-sig')

print("CSV 파일 저장이 완료되었습니다.")
    
# 브라우저 닫기
driver.quit()

print("Selenium 실행이 완료되었습니다.") 
    