import time
from typing import Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_crawler import BaseCrawler



class JumpitCrawler(BaseCrawler):
    # 점핏 사이트 크롤러
    def __init__(self):
        super().__init__("https://jumpit.saramin.co.kr")
    
    def crawl(self, keyword: str = '', pages_to_crawl: int = 1, is_newbie: bool = False):
        print(f"🚀 [점핏] 서버/백엔드 타겟팅 목록 크롤링 시작...")

        # 1. URL세팅(무한 스크롤)
        url = (
            f"{self.base_url}/positions"
            f"?jobCategory=1&jobCategory=7&jobCategory=15"
            f"&career=1"
            f"&locationTag=101000&locationTag=102000"
            f"&sort=popular"
            f"&page=1"
        )

        self.driver.get(url)
        self._random_sleep()
        
        # 무한 스크롤 로직
        print(" - 무한 스크롤을 시작합니다.")
        body = self.driver.find_element(By.TAG_NAME, 'body')
        last_height = self.driver.execute_script('return document.documentElement.scrollHeight')

        patience = 5
        patience_counter = 0

        while True:
            body.send_keys(Keys.END)
            self._random_sleep()
            new_height = self.driver.execute_script('return document.documentElement.scrollHeight')

            if new_height == last_height:
                patience_counter += 1
                print(f" - 페이지 높이 변화 없음.(인내심:{patience_counter}/{patience})")
                if patience_counter >= patience:
                    print(" - 스크롤이 페이지 끝에 도달했거나, 더 이상 로딩되지 않아 중단합니다.")
                    break
            else:
                # 높이가 변했다면 인내심 초기화
                patience_counter = 0
                last_height = new_height

        # 3. 데이터 추출
        all_job_data = []
        seen_links = set()
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        job_cards = soup.select('a[href*="/position/"]')

        for card in job_cards:
            try:
                # 링크 추출 및 중복 제거
                raw_link = card.get('href', '')
                if not raw_link:
                    continue
                link = f"{self.base_url}{raw_link}" if raw_link.startswith('/') else raw_link

                if link in seen_links:
                    continue

                # 제목 추출
                title_elem = card.select_one('.position_card_info_title')
                if not title_elem:
                    continue
                title = title_elem.text.strip()

                # 회사명 추출
                company = "회사명 확인 필요"
                prev_div = title_elem.find_previous_sibling('div')
                if prev_div:
                    company = prev_div.text.strip()

                # 기술 스택 및 지역/경력 추출
                ul_tags = card.find_all('ul')
                tech_stack = ""
                location = ""

                if len(ul_tags) >= 1:
                    tech_items = []
                    for li in ul_tags[0].find_all('li'):
                        clean_tech = li.text.replace('·', '').strip()
                        tech_items.append(clean_tech)

                    tech_stack = ", ".join(tech_items)

                if len(ul_tags) >= 2:
                    meta_items = ul_tags[1].find_all('li')
                    if len(meta_items) >= 1:
                        location = meta_items[0].text.strip()

                # 5. 데이터 적재
                all_job_data.append({
                    "title": title,
                    "company": company,
                    "link":link,
                    "tech_stack": tech_stack,
                    "location": location,
                    "source": "Jumpit",
                })
                seen_links.add(link)

            except Exception as e:
                print(f" [오류] 점핏 카드 파싱 중 에러: {e}")
                continue

        print(f"\n✅ 점핏 최종 수집 완료: 총 {len(all_job_data)}개")
        return all_job_data
        
    def get_job_description(self, url: str) -> Dict[str, str]:
        self.driver.get(url)
        self._random_sleep()

        description = ""
        deadline = "확인 필요"

        try:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # 1. 마감일
            deadline_dt = soup.find('dt', string=lambda text: text and '마감일' in text)
            if deadline_dt:
                deadline_dd = deadline_dt.find_next_sibling('dd')
                if deadline_dd:
                    deadline = deadline_dd.text.strip()

            # 본문 추출
            position_info = soup.find('div', class_='position_info')
            if position_info:
                description = position_info.get_text(separator="\n", strip=True)
            else:
                for noise in soup(['header', 'footer', 'nav', 'aside']):
                    noise.decompose()
                main_content = soup.find('main')
                if main_content:
                    description = main_content.get_text(separator="\n", strip=True)

        except Exception as e:
            print(f" [점핏 상세 오류] {url} 처리 중: {e}")

        return {
            'description': description,
            'deadline':deadline
        }