import time
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler



class SaraminCrawler(BaseCrawler):
    # 사람인 사이트 크롤러
    def __init__(self):
        super().__init__("https://www.saramin.co.kr")
    
    def crawl(self, keyword: str = '백엔드', pages_to_crawl: int = 1):
        print(f"사람인에서 '{keyword}' 키워드로 {pages_to_crawl} 페이지까지 크롤링을 시작합니다.")
        all_job_data = []

        for page in range(1, pages_to_crawl+1):
            search_url = f"{self.base_url}/zf_user/search?searchword={keyword}&recruitPage={page}"
            self.driver.get(search_url)
            self._random_sleep()

            print(f" - {page} 페이지 처리 중...")
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            job_cards = soup.select('div.item_recruit')

            if not job_cards:
                print(f" - {page} 페이지에 더 이상 공고가 없어 크롤링을 중단합니다.")
                break

            for card in job_cards:
                try:
                    title_tag = card.select_one('div.area_job > h2.job_tit > a')
                    title = title_tag['title']
                    relative_link = title_tag['href']
                    link = self.base_url + relative_link

                    company_tag = card.select_one('div.area_corp > strong.corp_name > a')
                    company = company_tag.text.strip()

                    all_job_data.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "source": "Saramin"
                    })
                except Exception:
                    continue

            print(f"사람인에서 총 {len(all_job_data)}개의 유효한 공고를 추출했습니다.")
            return all_job_data