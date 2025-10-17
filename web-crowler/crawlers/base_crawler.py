from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options



class BaseCrawler(ABC):
    # 모든 크롤러가 상속받아야 하는 추상 기본 클래스

    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = self._setup_driver()

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
    def crawl(self, keyword: str, pages_to_crawl: int = 1):
        # 크롤링 프로세스를 시작하는 메인 메서드(자식 클래스에서 반드시 구현)
        # 반환 값은 dict를 담은 list 형태
        pass

    def close_driver(self):
        # 드라이버를 안전하게 종료
        if self.driver:
            self.driver.quit()