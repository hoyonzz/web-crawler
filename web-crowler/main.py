import os
from datetime import datetime
from dotenv import load_dotenv
import notion_client
from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler

load_dotenv()

# 1. Notion API 설정
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)

# 2. 크롤러 실행
all_jobs = []

crawlers_to_run = [
    WantedCrawler(),
    JobKoreaCrawler()
]

for crawler in crawlers_to_run:
    try:
        print(f"--- {type(crawler).__name__} 크롤링 시작 ---")
        crawled_jobs = crawler.crawl(keyword='백엔드')
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
for i, job in enumerate(all_jobs):
    title = job['title']
    company = job['company']
    link = job['link']
    source = job['source']

    # 보낼 데이터 구조 미리 출력(디버깅용)
    print(f" [{i+1}/{len(all_jobs)}] Notion에 저장 시도: {title} @ {company}")

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
print(f"총{len(all_jobs)}개의 공고 중, {success_count}개를 Notion에 성공적으로 저장했습니다.")
print('모든 작업이 완료되었습니다.')
