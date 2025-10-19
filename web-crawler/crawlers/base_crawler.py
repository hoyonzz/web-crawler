from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import time
import random



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
        chrome_options.add_argument("--headless")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) chorme/123.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    @abstractmethod
    def crawl(self, keyword: str, pages_to_crawl: int = 1, sort_by: str = 'latest'):
        # 크롤링 프로세스를 시작하는 메인 메서드(자식 클래스에서 반드시 구현)
        # 반환 값은 dict를 담은 list 형태
        pass

    @abstractmethod
    def get_job_description(self, url:str) -> str:
        # 주어진 URL의 상세 페이지에 방문하여, 채용 공고의 본문 텍스트 반환
        # 자식 클래스는 이 메서드를 반드시 구현
        pass

    def close_driver(self):
        # 드라이버를 안전하게 종료
        if self.driver:
            self.driver.quit()
