import time
import os
from dotenv import load_dotenv

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
# 요소를 찾기 위해 사용할 By 모듈
from selenium.webdriver.common.by import By
# 키보드 입력을 위해 사용할 keys 모듈
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd

import notion_client

# .ev 파일에서 환경 변수 로드
load_dotenv()

# 1. Notion API 설정
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Notion 클라이언트 초기화
notion = notion_client.Client(auth=NOTION_API_KEY)

# Chrome 옵션을 설정하기 위한 Options 객체 생성
chrome_options=Options()
# 헤드리스 모드를 활성화하는 옵션 추가
chrome_options.add_argument("--headless")
# 일부 서버 환경에서 필요한 추가 옵션
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 2. Selenium 설정 및 실행
service = ChromeService(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 원티드 메인 페이지로 이동
URL = 'https://www.wanted.co.kr/'
driver.get(URL)
time.sleep(2)

# 검색창 활성화를 위해 돋보기 아이콘 클릭
try:
    search_button = driver.find_element(By.CSS_SELECTOR, "button[data-attribute-id='gnb']")
    search_button.click()
    time.sleep(1)
except NoSuchElementException as e:
    # 에러 발생 시, 현재 화면을 스크린샷으로 저장하고 HTML을 저장
    driver.save_screenshot("error_screenshot.png")
    with open("error_page.html", "w", encoding='utf-8') as f:
        f.write(driver.page_source)
    print("오류: 검색 버튼을 찾을 수 없습니다. 스크린샷과 HTML을 저장합니다.")
    raise e # 원래 오류를 다시 발생시켜서 워크플로우를 중단시킴

# 검색창에 '백엔드' 입력
search_input = driver.find_element(By.CSS_SELECTOR, 'input.SearchInput_SearchInput__R6jwT')
search_input.send_keys('백엔드')
search_input.send_keys(Keys.ENTER)
time.sleep(2)

# 페이지 끝까지 스크롤
last_height = driver.execute_script('return document.body.scrollHeight')
while True:
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    new_height = driver.execute_script('return document.body.scrollHeight')
    if new_height == last_height:
        break
    last_height = new_height

print('페이지 스크롤 완료.')

# 3. 데이터 추출 및 Notion에 저장
html = driver.page_source
soup = BeautifulSoup(html, 'lxml')
job_cards = soup.select("div[role='listitem'] a")

print(f"총{len(job_cards)}개의 채용 공고를 찾았습니다. Notion에 저장을 시작합니다...")

# 각 공고 카드를 순회하며 정보를 추출
for card in job_cards:
    # strong 태그이면서 class 이름이 'JobCard_title'로 시작하는 요소 찾기
    title = card.select_one("strong[class*='JobCard_title']").text
    # span 태그이면서 class 이름이 'CompanyName'으로 시작하는 요소 찾기
    company_name = card.select_one("span[class*='CompanyName']").text
    # 공고 상세 페이지로 연결되는 링크
    link = "https://www.wanted.co.kr" + card['href']
    
    # Notion 데이터베이스에 페이지를 생성
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "직무": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "회사명": {
                    "rich_text": [
                        {
                            "text": {
                                "content": company_name
                            }
                        }
                    ]
                },
                "링크": {
                    "url": link
                }
            }
        )
        print(f"'{title}' 공고를 Notion에 성공적으로 저장했습니다.")
    except Exception as e:
        print(f"'{title}' 공고 저장 중 오류 발생: {e}")

    # 서버에 부담 주지 않게 각 요청 사이에 대기
    time.sleep(0.5)
    # 추출한 정보를 딕셔너리 형태로 저장
    
# 브라우저 닫기
driver.quit()

print("모든 작업이 완료되었습니다.") 
    