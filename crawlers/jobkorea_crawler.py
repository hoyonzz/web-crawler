import time
from typing import Dict
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler



class JobKoreaCrawler(BaseCrawler):
    # 잡코리아 사이트 크롤러

    def __init__(self):
        super().__init__("https://www.jobkorea.co.kr")

    def crawl(self, keyword: str = '백엔드', pages_to_crawl: int = 1, is_newbie: bool = False):
        career_type = "1" if is_newbie else ""
        print(f"잡코리아에서 '신입' 필터: {is_newbie}, {pages_to_crawl} 페이지까지 크롤링...")

       
        # 주어진 키워드로 지정된 페이지 수만큼 채용 정보 크롤링
        all_job_data = []
        # 1부터 pages_to_crawl 숫자까지 루프
        for page in range(1, pages_to_crawl + 1):
            # URL에 페이지 번호 추가    
            search_url = f"{self.base_url}/Search/?stext={keyword}&Page_No={page}&careerType={career_type}"
            self.driver.get(search_url)
            self._random_sleep()

            print(f"   - {page} 페이지 처리 중...")
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            job_cards = soup.select('div[data-sentry-component="CardJob"]')

            # 페이지에 공고 카드가 더 이상 없으면
            if not job_cards:
                print(f"   - {page} 페이지에 더 이상 공고가 없어 크롤링을 중단합니다.")
                break

            for card in job_cards:
                try:
                    # 1. 제목(size18을 포함하는 span태그)
                    title_span = card.select_one('span[class*="Typography_variant_size18"]')
                    title = title_span.text.strip()

                    # 2. 제목을 감싸고 있는 부모 a 태그 추출
                    link_tag = title_span.find_parent('a')
                    # .find_parent('a')는 해당 요소의 부모 중 가장 가까운 a 태그를 찾는다
                    link = link_tag['href']
                    # link = self.base_url + relative_link

                    # 3. 회사명(size16)을 포함하는 span태그
                    company_span = card.select_one('span[class*="Typography_variant_size16"]')
                    company = company_span.text.strip()

                    all_job_data.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "source": "JobKorea",
                    })
                except Exception as e:
                    print(f" [오류] 특정 공고 카드 처리 중 문제 발생: {e} - > 건너 뜁니다.")
                    continue
        print(f"잡코리아에서 총 {len(all_job_data)}개의 유효한 공고를 추출했습니다.")
        return all_job_data
    
    def get_job_description(self, url: str) -> Dict[str, str]:
        self.driver.get(url)
        self._random_sleep()
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        description = ""
        deadline = "확인 필요" # 기본값

        try:
            # 본문 내용 : 'detail-content'클래스를 가진 div가 가장 안정적
            content_div = soup.select_one('div.detail-content')
            if content_div:
                description = content_div.text.strip()

            # 마감일: '오늘 마감' 또는 날짜 정보를 포함하는 span
            deadline_span = soup.find('span', class_=lambda c: c and('d-day' in c or 'day' in c))
            if deadline_span:
                deadline = deadline_span.text.strip()
        except Exception as e:
            print(f"   [잡코리아 상세 오류] {url} 처리 중: {e}")


        return {'description':description, 'deadline':deadline}