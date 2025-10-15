import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler



class WantedCrawler(BaseCrawler):
    # 원티드 사이트 크롤러

    def __init__(self):
        # 부모 클래스 __init__을 호출하여 base_url 전달
        super().__init__("https://www.wanted.co.kr/")

    def crawl(self, keyword: str = "백엔드"):
        # BaseCrawler의 의무 조항을 실제로 구현, 원티드 채용 정보 크롤링하여 list of dict 형태로 반환
        print("원티드 크롤링을 시작합니다>_<")
        self.driver.get(self.base_url)
        time.sleep(2)

        search_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-attribute-id='gnb']")
        search_button.click()
        time.sleep(1)

        search_input = self.driver.find_element(By.CSS_SELECTOR, 'input.SearchInput_SearchInput__R6jwT')
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.Enter)
        time.sleep(2)

        last_height = self.driver.execute_script('return document.body.scrollHeight')
        while True:
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(2)
            new_height = self.driver.execute_script('return document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

        # 데이터 추출 및 가공
        job_data = []
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        job_cards = soup.select("div[role='listitem'] a")

        for card in job_cards:
            title = card.select_one("strong[class*='JobCard_title']").text
            company_name = card.select_one("span[class*='CompanyName']").text
            link = "https://www.wanted.co.kr" + card['href']
            job_data.append({"title": title, "company": company_name, "link":link, "source": "Wanted"})

        print(f"원티드에서 총 {len(job_data)}개의 공고를 찾았습니다.")
        return job_data