from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import time
import random

from typing import Dict



class BaseCrawler(ABC):
    # 모든 크롤러가 상속받아야 하는 추상 기본 클래스

    def __init__(self, base_url, delay_range=(2, 5)):
        self.base_url = base_url
        self.delay_range = delay_range
        self.driver = self._setup_driver()

    def _random_sleep(self):
        # 설정된 딜레이 범위 내에서 랜덤한 시간만큼 대기
        delay = random.uniform(self.delay_range[0], self.delay_range[1])

        time.sleep(delay)

    def _setup_driver(self):
        # Selenium WebDriver를 설정하고 반환
        chrome_options = Options()
        # 최신 헤드리스 모드
        chrome_options.add_argument("--headless=new")
        # 깃허브 액션(리눅스) 환경 필수 메모리 최적화 옵션
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # 해상도 강제 고정
        chrome_options.add_argument("--window-size=1920,1080")
        # 자동화 제어 메시지 숨기기 및 웹드라이버 명찰 제거
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)
        # User-Agent 정상화
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) chrome/130.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")

        # Selenium 4.6 이상부터는 webdriver_manager없이 내장 매니저가 자동동작하지만 안정성을 위해 기존 명시적 호출 유지
        # service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(options=chrome_options)

        # JavaScript 단에서 webdriver 속성을 지워버리는 쐐기 스크립트 실행
        # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        #     "source": """
        #         Object.defineProperty(navigator, 'webdriver', {
        #             get: () => undefined
        #         })
        #     """
        # })
        chrome_options.add_argument("--log-level=3")
        return driver
    
    @abstractmethod
    def crawl(self, keyword: str, pages_to_crawl: int = 1, is_newbie: bool = False):
        # 크롤링 프로세스를 시작하는 메인 메서드(자식 클래스에서 반드시 구현)
        # 반환 값은 dict를 담은 list 형태
        pass

    @abstractmethod
    def get_job_description(self, url:str) -> Dict[str, str]:
        # 반환 타입을 본문과 마감일을 모두 담을 수 있는 Dict로 변경
        # 주어진 URL의 상세 페이지에 방문하여, 채용 공고의 본문 텍스트 반환
        # 자식 클래스는 이 메서드를 반드시 구현
        pass

    def close_driver(self):
        # 드라이버를 안전하게 종료
        if self.driver:
            self.driver.quit()
