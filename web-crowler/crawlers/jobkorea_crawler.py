import time
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler



class JobKoreaCrawler(BaseCrawler):
    # 잡코리아 사이트 크롤러

    def __init__(self):
        super().__init__("https://www.jobkorea.co.kr")

    def crawl(self, keyword: str = '백엔드'):
        # 잡코리아에서 주어진 키워드로 채용 정보를 크롤링
        search_url = f"{self.base_url}/Search/?stext={keyword}"
        self.driver.get(search_url)
        time.sleep(3) # 페이지 로딩 대기

        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        job_data = []
        job_cards = soup.select('div[data-sentry-component="CardJob"]')

        print(f"잡코리아에서 {len(job_cards)}개의 공고 카드를 찾았습니다. 데이터 추출을 시작합니다.")

        for card in job_cards:
            try:
                # 1. 제목(size18을 포함하는 span태그)
                title_span = card.select_one('span[class*="Typography_variant_size18"]')
                title = title_span.text.strip()

                # 2. 제목을 감싸고 있는 부모 a 태그 추출
                link_tag = title_span.find_parent('a')
                # .find_parent('a')는 해당 요소의 부모 중 가장 가까운 a 태그를 찾는다
                relative_link = link_tag['href']
                link = self.base_url + relative_link

                # 3. 회사명(size16)을 포함하는 span태그
                company_span = card.select_one('span[class*="Typography_variant_size16"]')
                company = company_span.text.strip()

                job_data.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "source": "JobKorea",
                })
            except Exception as e:
                print(f" [오류] 특정 공고 카드 처리 중 문제 발생: {e} - > 건너 뜁니다.")
                continue
        print(f"잡코리아에서 총 {len(job_data)}개의 유효한 공고를 추출했습니다.")
        return job_data