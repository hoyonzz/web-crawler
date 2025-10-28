import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from crawlers.wanted_crawler import WantedCrawler


# 1. 테스트할 실제 채용 공고 URL
target_url = "https://www.wanted.co.kr/wd/295128"

print(f"🚀 [{WantedCrawler.__name__}] 디버깅을 시작합니다.")
print(f"   - 대상 URL: { target_url}")

crawler = None

try:
    # 2. 크롤러 실행
    crawler = WantedCrawler()
    details = crawler.get_job_description(target_url)

    # 3. 결과 확인
    if details and details.get('description', '').strip():
        desc = details['description']
        print("\n✅ [성공] 공고 본문을 가져왔습니다.")
        print(f"   - 본문 길이: {len(desc)}자")
        print(f"   - 본문 앞 200자: {desc[:200]}...")
    else:
        print("\n🚨 [실패] 공고 본문을 가져오지 못했습니다.")
except Exception as e:
    print(f"\n🔥 [오류] 테스트 중 예외 발생: {e}")
finally:
    input("\n... 확인 후 브라우저를 닫으려면 Enter 키를 누르세요 ...")
    if crawler:
        crawler.close_driver()
    print("✅ 디버깅을 종료합니다.")