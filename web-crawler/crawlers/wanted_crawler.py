import time
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys



class WantedCrawler(BaseCrawler):
    # 원티드 사이트 크롤러

    def __init__(self):
        # 부모 클래스 __init__을 호출하여 base_url 전달
        super().__init__("https://www.wanted.co.kr/")

    def crawl(self, keyword: str = "백엔드", pages_to_crawl: int = 1, sort_by: str = 'latest'):
        # BaseCrawler의 의무 조항을 실제로 구현, 원티드 채용 정보 크롤링하여 list of dict 형태로 반환
        order_param = 'latest' if sort_by == 'latest' else 'score'

        print(f"원티드에서 '{keyword}' 키워드로 '{sort_by}' 순으로 크롤링을 시작합니다...")

        # 포지션 탭의 URL로 바로 접근하여 불필요한 클릭 과정 생략
        target_url = f"{self.base_url}/search?query={keyword}&tab=position&order={order_param}"
        self.driver.get(target_url)
        self._random_sleep()

        # 무한 스크롤로 데이터 수집
        print(" - 무한 스크롤을 시작합니다.")
        last_height = self.driver.execute_script('return document.documentElement.scrollHeight')

        # 키보드 입력을 받을 대상을 지정
        body = self.driver.find_element(By.TAG_NAME, 'body')

        patience = 5
        patience_counter = 0

        while True:
            body.send_keys(Keys.END)


            # self.driver.execute_script('window.scrollTo(0, document.documentElement.scrollHeight);')
            self._random_sleep()
            new_height = self.driver.execute_script('return document.documentElement.scrollHeight')

            if new_height == last_height:
                patience_counter += 1
                print(f" - 페이지 높이 변화 없음.(인내심: {patience_counter}/{patience})")
                if patience_counter >= patience:
                    print(" - 스크롤이 페이지 끝에 도달했거나, 더 이상 로딩되지 않아 중단합니다.")
                    break
            else:
                # 높이가 변했다면, 인내심 카운터 초기화
                patience_counter = 0

            last_height = new_height

        # 데이터 추출 및 가공
        job_data = []
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        job_cards = soup.select("div[role='listitem'] a")

        for card in job_cards:
            try:
                title = card.select_one("strong[class*='JobCard_title']").text
                company_name = card.select_one("span[class*='CompanyName']").text
                link = "https://www.wanted.co.kr" + card['href']
                job_data.append({"title": title, "company": company_name, "link":link, "source": "Wanted"})
            except Exception:
                continue
        print(f"원티드에서 총 {len(job_data)}개의 공고를 찾았습니다.")
        return job_data
    
    def get_job_description(self, url: str) -> str:
        # 원티드의 상세 페이지의 본문 내용 수집:상세페이지에 방문, '더보기'버튼 클릭, 전체 본문 내용 수집

        try:
            self.driver.get(url)
            self._random_sleep()

            # 1. 페이지 펼치는 버튼 클릭 로직
            try:
                more_button_xpath = "//button[span[text()='상세 정보 더 보기']]"
                more_button = self.driver.find_element(By.XPATH, more_button_xpath)

                self.driver.execute_script("arguments[0].click();", more_button)
                print("   -> '상세 정보 더 보기' 버튼을 클릭했습니다.")
                self._random_sleep()
            except Exception:
                print("   -> '상세 정보 더 보기' 버튼이 없거나 클릭할 수 없습니다. 그대로 진행합니다.")
                pass


            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # 2. 전체 본문을 감싸는 article 태그 찾기
            content_article = soup.select_one('article[class*="JobDescription_JobDescription"]')

            if content_article:
                return content_article.text.strip()
            else:
                print("   -> [경고] 기본 선택자로 본문을 찾지 못했습니다. 2차 선택자를 시도합니다.")

                # h2 태그 중 '포지션 상세'라는 텍스트를 가진 요소의 부모를 찾는다
                h2 = soup.find('h2', string='포지션 상세')
                if h2:
                    return h2.parent.text.strip()
                return ""
        except Exception as e:
            print(f" [상세 정보 수집 오류] {url} 처리 중 문제 발생: {e}")
            return ""
 