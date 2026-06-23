import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By


print("🚀 도커 컨테이너 내부 크롬 구동 테스트 시작")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

try:
    print("1. 브라우저 드라이버 초기화 중...")
    driver = webdriver.Chrome(options=options)

    print("2. 테스트 페이지 접속 중...")
    driver.get("https://www.wanted.co.kr/")

    invalid_titles = ["ERROR", "Access Denied", "Just a moment", "Attention Required"]

    for invalid_word in invalid_titles:
        if invalid_word in invalid_titles:
            raise Exception(f"봇 장어 시스템 차단 감지됨 (페이지 제목: {driver.title})")

    print(f"🎉 성공! 접속한 페이지 제목: '{driver.title}'")
    driver.quit()
    print("📢 테스트가 정상적으로 완료되어 드라이버를 종료했습니다.")

except Exception as e:
    print("\n❌ 에러가 발생했습니다.")
    os.makedirs('output', exist_ok=True)

    # 1. 스크린샷 촬영
    driver.save_screenshot('output/error_screenshot.png')

    # 2. HTML 소스코드 저장
    with open('output/error_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

    print(f"에러 메시지: {e}")
    sys.exit(1)