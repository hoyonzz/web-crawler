import os
from dotenv import load_dotenv
import notion_client
from crawlers.wanted_crawler import WantedCrawler

load_dotenv()

# 1. Notion API 설정
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)

# 2. 크롤러 실행
all_jobs = []
wanted_crawler = WantedCrawler()
try:
    wanted_jobs = wanted_crawler.crawl(keyword='백엔드')
    all_jobs.extend(wanted_jobs)
finally:
    wanted_crawler.close_driver()

# 3. Notion에 저장
print(f"총 {len(all_jobs)}개의 채용 공고를 찾았습니다. Notion에 저장을 시작합니다...")
for job in all_jobs:
    title = job['title']
    company = job['company']
    link = job['link']
    # collect_date

print('모든 작업이 완료되었습니다.')
