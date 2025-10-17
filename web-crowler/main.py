import os
from datetime import datetime
from dotenv import load_dotenv
import notion_client
from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler
from crawlers.saramin_crawler import SaraminCrawler

load_dotenv()

# 1. Notion API 설정
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)

# 2. 크롤러 실행
all_jobs = []

crawlers_to_run = [
    WantedCrawler(),
    JobKoreaCrawler(),
    SaraminCrawler()
]

for crawler in crawlers_to_run:
    try:
        print(f"--- {type(crawler).__name__} 크롤링 시작 ---")
        # crawl 메서드에 pages_to_crawl 인자를 전달, 테스트는 2, 실제 운영시에는 5~10으로 셋팅
        crawled_jobs = crawler.crawl(keyword='백엔드', pages_to_crawl=2)
        all_jobs.extend(crawled_jobs)
        print(f"--- {type(crawler).__name__} 크롤링 완료 ---")
    except Exception as e:
        print(f"{type(crawler).__name__} 실행 중 오류 발생: {e}")
    finally:
        crawler.close_driver()

# 3. Notion에 저장
print(f"총 {len(all_jobs)}개의 채용 공고를 찾았습니다. Notion에 저장을 시작합니다...")

collection_date = datetime.now().strftime("%Y-%m-%d")
success_count = 0
duplicate_count = 0

# 쿼리 조회 기능
for i, job in enumerate(all_jobs):
    link = job['link']
    title = job['title']

    # 1. 링크를 기준으로 쿼리 조회
    try:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter = {"property": "링크", "url": {"equals": link}}
        )

        # 2. 쿼리 결과에 데이터가 있는지 확인
        if len(response['results']) > 0:
            # 이미 존재하는 데이터
            print(f" [{i+1}/{len(all_jobs)}] [중복] {title}")
            duplicate_count += 1
            continue

    except Exception as e:
        print(f" [오류 발생] Notion DB 조회 중 문제 발생: {e}")
        continue

    # 중복이 아닐 경우
    print(f" [{i+1}/{len(all_jobs)}] [신규] {title} -> Notion에 저장 시도")
    company = job['company']
    source = job['source']


    try:
        # Notion API 호출
        notion.pages.create(
            parent={"database_id":NOTION_DATABASE_ID},
            properties={
                '직무':{
                    'title':[{'text':{'content':title}}]
                },
                '회사명':{
                    'rich_text': [{'text': {'content':company}}]
                },
                '링크':{
                    'url':link
                },
                '출처':{
                    'rich_text':[{'text':{'content':source}}]
                },
                '수집일':{
                    'date':{'start': collection_date}
                }
            }
        )
        success_count += 1

    except Exception as e:
        print(f" [오류 발생] '{title}' 저장 실패!")
        print(f' 오류원인: {e}')

print("-" * 20)
print(f"총 {len(all_jobs)}개의 공고 중,")
print(f"  - {success_count}개의 새로운 공고를 Notion에 저장했습니다.")
print(f"  - {duplicate_count}개의 공고는 이미 존재하여 건너뛰었습니다.")
print("모든 작업이 완료되었습니다.")
