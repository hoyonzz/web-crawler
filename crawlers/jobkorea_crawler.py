import time
import re
import os
from typing import Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler



class JobKoreaCrawler(BaseCrawler):
    # 잡코리아 사이트 크롤러


    def __init__(self):
        super().__init__("https://www.jobkorea.co.kr")



    # 클래스 상수: 두 목록 엔드포인트(이름, 경로, 페이징 파라미터)
    LIST_ENDPOINTS = [
        ("일반공고", "TemplateFreeGnoList", "FreePageNo"),
        ("메인공고", "TemplateMainGnoList", "MainPageNo"),
    ]

    def _build_list_url(self, endpoint_path: str, page_param: str, page: int, is_newbie: bool) -> str:
        # 직무: 백엔드, 웹, 시스템, DBA, 데이터, SW
        bpart_no = "1000229%2C1000231%2C1000233%2C1000235%2C1000236%2C1000239"

        # 지역: 서울(I000), 경기(B000)
        scd = "I000%2CB000"

        # 경력: 신입(1/3) + 경력무관(4)
        career_type = "1%2F3%2C4" if is_newbie else ""


        # 전체 파라미터(themeNo=165 필수)
        params = {
            "rlistTab": "0",
            "rOrderTab": "1",
            "rSearchText": "",
            "bpart_no": bpart_no,
            "spart_no": "",
            "scd": scd,                      # 지역 (항상 서울·경기)
            "edu_no": "",
            "pref": "",
            "jtype": "",
            "careerTypeCode": career_type,   # 경력 (is_newbie에 연동)
            "ctype": "",
            "jobFilter": "0",
            "listDisplayCode": "2",
            "MainPageNo": "1",
            "FreePageNo": "1",
            "psTab": "20",
            "themeNo": "165",
            "tabNo": "0",
            "giDisplayCntLimitStat": "0",
            "GIOpenTypeCode": "0",
            "pay": "",
            "pay_type_code": "",
            "IsPartCodeSearch": "true",
        }


        params[page_param] = str(page)
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/Theme/{endpoint_path}/it_developer?{query}"
        
        
    def _parse_job_card(self, card) -> Dict[str, str] | None:
        # 1.링크:dev-recruit-link1순위, GI_Read 링크 2순위
        link_tag = card.select_one('a.dev-recruit-link')
        if not link_tag:
            link_tag = card.select_one('a[href*="/Recruit/GI_Read/"]')

        if not link_tag:
            return None
        
        raw_link = link_tag.get('href', '')
        link = f"{self.base_url}{raw_link}" if raw_link.startswith('/') else raw_link

        title = link_tag.get_text(strip=True) or link_tag.get('title', '').strip()
        if not title:
            return None
        
        company = "회사명 확인 필요"
        company_tag = card.select_one('a[href*="Co_Read"]')
        if not company_tag:
            company_tag = card.select_one('[class*="coname"], [class*="corp"], [class*="name"]')
        if company_tag:
            company_text = company_tag.get_text(strip=True)
            if company_text:
                company = company_text
        # 직무 분야 (필터 적용 여부 검증용)
# 직무 분야: Main은 .rPart, Free는 p.dsc(직무 키워드 나열)
        part = ""
        part_tag = card.select_one('.rPart')
        if part_tag:
            part = part_tag.get_text(strip=True)
        else:
            dsc_tag = card.select_one('p.dsc')
            if dsc_tag:
                part = dsc_tag.get_text(strip=True)[:50]  # 키워드 앞부분만
        return {"title": title, "company": company, "link": link, "part": part, "source": "JobKorea"}

    def crawl(self, keyword: str = '', pages_to_crawl: int = 1, is_newbie: bool = False):
        print(f"🚀 잡코리아 IT 개발자 테마 목록 크롤링 시작...")

        all_job_data = []
        seen_links = set()

        for list_name, endpoint_path, page_param in self.LIST_ENDPOINTS:
            for page in range(1, pages_to_crawl + 1):
                url = self._build_list_url(endpoint_path, page_param, page, is_newbie)
                self.driver.get(url)
                self._random_sleep()
                print(f" -[{list_name}] {page} 페이지 처리 중...")

                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                # 서버가 알려주는 전체 건수
                counter = soup.select_one('[data-totalcount]')
                total_count = counter.get('data-totalcount', '?') if counter else '?'

                job_cards = soup.select('.listItem .dmpItem')

                if not job_cards:
                    print(f" -[{list_name}] {page} 페이지 공고 없음 (서버 totalcount={total_count}). 다음 목록으로 이동.")
                    if total_count != '0':   # '?' 포함: 컨테이너 부재 = 구조 문제이므로 덤프
                        self._dump_debug(soup, f"debug_jobkorea_{list_name}_p{page}.html")
                    break

                parsed_this_page = 0
                added_this_page = 0
                for card in job_cards:
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            parsed_this_page += 1
                            if job['link'] not in seen_links:
                                seen_links.add(job['link'])
                                all_job_data.append(job)
                                added_this_page += 1
                    except Exception as e:
                        print(f" [오류] 카드 파싱 중 에러: {e}")
                        continue

                print(f"   → 카드 {len(job_cards)}개 / 파싱 {parsed_this_page}건 / 신규 {added_this_page}건 (totalcount={total_count})")
                    
                # 카드는 존재하는데 파싱이 전부 실패한 경우 → 셀렉터 진단
                if parsed_this_page == 0:
                    print(f"   🚨 [{list_name}] 카드 {len(job_cards)}개 발견했으나 파싱 0건. 첫 카드 구조:")
                    print(job_cards[0].prettify()[:2000])
                    self._dump_debug(soup, f"debug_jobkorea_{list_name}_p{page}.html")
                    break


        print(f"잡코리아에서 총 {len(all_job_data)}개의 유효한 공고를 추출했습니다.")
        return all_job_data

    def _dump_debug(self, soup, filename: str):
        os.makedirs("output", exist_ok=True)
        path = os.path.join("output", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"   [진단] {path} 저장 완료. 구조 확인이 필요합니다.")                    

    def get_job_description(self, url: str) -> Dict[str, str]:
        self.driver.get(url)
        self._random_sleep()

        description = ""
        deadline = "확인 필요" # 기본값

        try:
            # 1. 마감일 추출 (iframe 바깥의 껍데기에 존재)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            page_text = soup.get_text(separator=" ")

            # 마감일 2026.07.31 패턴찾기
            deadline_match = re.search(r'마감일\s*[:\n]?\s*(\d{4}[\./-]\d{2}[\./-]\d{2})', page_text)
            if deadline_match:
                deadline = deadline_match.group(1)
            elif re.search(r'상시\s*채용', page_text):
                deadline = "상시 채용"
            elif re.search(r'오늘\s*마감', page_text):
                deadline = "오늘 마감"

            # 2. iframe탐지: ID고정 대신 전체 열거 후 본문 포함 여부로 판별
            content_soup = soup
            is_iframe = False

            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

            for frame in iframes:
                try:
                    self.driver.switch_to.frame(frame)
                    time.sleep(0.5)
                    inner_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    inner_text_len = len(inner_soup.get_text(strip=True))

                    # 본문 판별
                    if inner_soup.select_one('.tbDetailWrap, .artRecruit, .detailArea') or inner_text_len > 500:
                        content_soup = inner_soup
                        is_iframe = True
                        print(f" [상세] iframe 진입 성공 (내부 텍스트 {inner_text_len}자)")
                        break

                    self.driver.switch_to.default_content()

                except Exception:
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass
                    continue

            if not is_iframe:
                print(f" [상세] 유효 iframe없음, 바깥 DOM 사용")


            # 3.본문 텍스트 추출
            for noise_tag in content_soup(['header', 'footer', 'nav', 'aside', 'script', 'style', 'noscript']):
                noise_tag.decompose()

            # 본문 컨테이너 탐색 (검증 완료: 본문 iframe 내부의 .tbDetailWrap이 1순위)
            selector_used = "body(폴백)"
            content_body = content_soup.select_one('.tbDetailWrap')
            if content_body:
                selector_used = ".tbDetailWrap"
            if not content_body:
                content_body = content_soup.select_one('.artRecruit')
                if content_body:
                    selector_used = ".artRecruit"
            if not content_body:
                content_body = content_soup.select_one('.artTplDetail')  # 구형 템플릿 대비
                if content_body:
                    selector_used = ".artTplDetail"
            if not content_body:
                content_body = content_soup.select_one('div.detail-content')
                if content_body:
                    selector_used = "div.detail-content"
            if not content_body:
                content_body = content_soup.find('body')

            print(f"      [상세] 본문 컨테이너: {selector_used}")
            if content_body:
                description = content_body.get_text(separator="\n", strip=True)

            # 4. 이미지 공고인지 판별
            images = content_soup.find_all('img')
            if len(description) < 100 and len(images) > 0:
                description = f"[통이미지 공고] 텍스트가 {len(description)}자로 너무 적고, {len(images)}개의 이미지가 포함되어 있습니다."

        except Exception as e:
            print(f"   [잡코리아 상세 오류] {url} 처리 중: {e}")
        finally:
            try:
                if 'is_iframe' in locals() and is_iframe:
                    self.driver.switch_to.default_content()
            except Exception:
                pass


        return {'description':description, 'deadline':deadline}
