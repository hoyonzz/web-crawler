from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
        chrome_options.add_argument("--headless")
        # 깃허브 액션(리눅스) 환경 필수 메모리 최적화 옵션
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        # 해상도 강제 고정
        chrome_options.add_argument("--window-size=1920,1080")

        # User-Agent 정상화
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) chrome/130.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"--user-agent={user_agent}")
        # chrome_options.add_argument("--log-level=3")

        chrome_options.add_argument("--user-data-dir=/tmp/chrome-data")
        chrome_options.add_argument("--disable-extensions")

        # Docker에 apt-get으로 설치한 시스템 Chromium 경로 지정
        chrome_options.binary_location = "/usr/bin/chromium"
        service = Service(
            executable_path="/usr/bin/chromedriver",
            service_args=["--verbose", "--log-path=/app/output/chromedriver.log"]
        )

        driver = webdriver.Chrome(service=service, options=chrome_options)
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

    def restart_driver(self):
        """
        죽은 세션을 버리고 드라이버를 재생성
        """
        try:
            self.driver.quit()
        except Exception:
            pass

        self.driver = self._setup_driver()
        print(" [복구] 드라이버 재생성 완료")

    def close_driver(self):
        # 드라이버를 안전하게 종료
        if self.driver:
            self.driver.quit()
