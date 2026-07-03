import time
import re
import os
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from typing import Dict

class WantedCrawler(BaseCrawler):
    # 원티드 사이트 크롤러

    def __init__(self):
        # 부모 클래스 __init__을 호출하여 base_url 전달
        super().__init__("https://www.wanted.co.kr/")

    def crawl(self, keyword: str = "", pages_to_crawl: int = 1, is_newbie: bool = False):
        print(f"🚀 원티드 다중 필터(직군 5개, 지역, 경력) URL 직접 주입 크롤링 시작...")

        # 1. 파라미터 조합
        # is_newbie가 True면 신입~1년(years=0&years=1), False면 전체(years=-1)
        year_param = "years=0&years=1" if is_newbie else "years=-1"

        # 카테고리(직군 5개선택), 지역:서울 전체, 경기 전체
        target_url = (
            f"{self.base_url}wdlist/518"
            f"?country=kr&job_sort=job.latest_order"
            f"&{year_param}"
            f"&locations=seoul.all&locations=gyeonggi.all"
            f"&selected=899&selected=10110&selected=655&selected=10231&selected=873"
        )

        self.driver.get(target_url)
        
        print(" -> 원티드 API 데이터 로딩을 기다리는 중입니다...")

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/wd/']"))
            )
        except Exception:
            print(" 🚨 [로딩 타임아웃] 15초가 지나도 공고가 뜨지 않았습니다.")
            # 눈이 없는 헤드리스 브라우저가 도대체 뭘 보고 있는지 확인하기 위해 파일로 저장
            os.makedirs("output", exist_ok=True)
            with open("output/error_dump.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(" 🚨 현재 브라우저 화면을 'output/error_dump.html' 파일로 저장했습니다. 루트 폴더를 확인해 주세요!")
            return [] # 빈 리스트 반환하고 즉시 종료
        
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
        job_cards = soup.select("a[href*='/wd/']")

        seen_links = set()

        for card in job_cards:
            try:
                # 1. 링크 조립 및 유효성 검증
                raw_link = card.get('href', '')
                if not raw_link:
                    continue

                link = "https://www.wanted.co.kr" + raw_link if not raw_link.startswith('http') else raw_link

                # 순수 채용 공고가 아닌 배너 링크는 건너뛰기
                if not re.search(r'/wd/\d+', link):
                    continue

                # 중복 수집 방지
                if link in seen_links:
                    continue

                # 2. 제목 추출
                title_span = card.select_one("span[class*='body__position']")
                if not title_span:
                    continue
                title = title_span.text.strip()
                
                # 3. 회사명 추출
                company_span = card.select_one("span[class*='__company__']")
                if company_span:
                    company_name = company_span.text.strip()
                else:
                    company_name = "회사명 확인 필요"

                # 4. 최종 데이터 적재
                job_data.append({
                    'title': title,
                    'company': company_name,
                    'link':link,
                    'source':'Wanted',
                })
                seen_links.add(link)

            except Exception as e:
                continue

        print(f"\n✅ 원티드 최종 수집 완료: 총 {len(job_data)}개 (중복 제거 후)")
        return job_data
    
    def get_job_description(self, url: str) -> Dict[str, str]:
        # 원티드의 상세 페이지의 본문 내용 수집:상세페이지에 방문, '더보기'버튼 클릭, 전체 본문 내용 수집
        description = ""
        deadline = "확인 필요"

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


            # 헤더 요약 정보 선제 추출
            header_info = ""
            h1_tag = soup.select_one('h1')
            if h1_tag:
                target_container = h1_tag.find_parent('header')
                if not target_container:
                    target_container = h1_tag.parent

                if target_container:
                    header_info = target_container.get_text(separator=" | ", strip=True)
                header_tag = h1_tag.find_parent('div')

            # 2. 전체 본문을 감싸는 article 태그 찾기
            content_article = soup.select_one('article[class*="JobDescription_JobDescription"]')

            if content_article:
                description = content_article.text.strip()
            else:
                print("   -> [경고] 기본 선택자로 본문을 찾지 못했습니다. 2차 선택자를 시도합니다.")

                # h2 태그 중 '포지션 상세'라는 텍스트를 가진 요소의 부모를 찾는다
                h2 = soup.find('h2', string='포지션 상세')
                if h2 and h2.parent:
                    description = h2.parent.text.strip()

            if header_info:
                description = f"[상단 요약 정보]\n{header_info}\n\n[상세 본문]\n{description}"
            else:
                print(" -> [경고] 상단 요약 정보를 추출하지 못했습니다. 본문 데이터만 유지합니다.")

            # 3. 마감일 추출
            deadline_h2 = soup.find('h2', string=lambda t: t and '마감일' in t)
            if deadline_h2 and deadline_h2.parent:
                deadline_span = deadline_h2.parent.find('span')
                if deadline_span:
                    deadline = deadline_span.text.strip()
                
        except Exception as e:
            print(f" 🚨 [상세 정보 수집 오류] {url} 처리 중 문제 발생: {e}")
        
        return {'description': description, 'deadline':deadline}
 
if __name__ == "__main__":
    crawler = WantedCrawler()
    try:
        jobs = crawler.crawl(keyword='백엔드', pages_to_crawl=1, is_newbie=True)
        print(f"\n>>> 최종 수집: {len(jobs)}건")
        for j in jobs[:5]:
            print(j)
        if jobs:
            detail = crawler.get_job_description(jobs[0]['link'])
            print(f"본문 길이: {len(detail['description'])} / 마감일: {detail['deadline']}")
            print(f"본문 앞 150자: {detail['description'][:150]}")
    finally:
        crawler.close_driver()