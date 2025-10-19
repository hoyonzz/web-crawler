import os, json
from datetime import datetime
from dotenv import load_dotenv
import notion_client


from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler
from crawlers.saramin_crawler import SaraminCrawler

from data_processor.personalized_job_filter import PersonalizedJobFilter

from analysis.gemini_analyzer import analyze_job_posting


load_dotenv()

# 1. Notion API 설정
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)

# 2. 크롤러 실행
all_jobs = []
# 클래스 자체를 리스트에 담아, 필요할 때 객체를 생성하는 방식으로 변경

# crawlers_to_run = [WantedCrawler, JobKoreaCrawler, SaraminCrawler]
crawlers_to_run = [WantedCrawler] # 테스트를 위해 임시


for crawlerClass in crawlers_to_run:
    crawler = crawlerClass()
    crawler_name = type(crawler).__name__
    print(f"--- {crawler_name} 크롤링 시작 ---")

    try:
        # 1단계: 목록 페이지에서 기본 정보 수집
        crawled_jobs_full_list = crawler.crawl(keyword='백엔드')

        # 2단계: 각 공고의 상세 페이지에 방문하여 본문 수집 - 테스트 범위를 3개로 제한
        jobs_to_process=crawled_jobs_full_list[:3]
        print(f"   -> {len(crawled_jobs_full_list)}개 중 {len(jobs_to_process)}개만 테스트를 진행...")
        
        print(f"   -> 상세 정보 수집을 시작합니다...")
        for i, job in enumerate(jobs_to_process):
            job_link = job['link']
            print(f"   ({i+1}/{len(jobs_to_process)}) {job_link[:50]}...") # 링크 앞부분만 출력
            job['description'] = crawler.get_job_description(job_link)

        all_jobs.extend(jobs_to_process)
        print(f"--- {crawler_name} 크롤링 완료")
    
    except Exception as e:
        print(f" [전체 크롤러 오류] {crawler_name} 실행 중 문제 발생:{e}")

    finally:
        crawler.close_driver()

# 3. Notion에 저장 및 Gemini 분석
print(f"총 {len(all_jobs)}개의 채용 공고를 찾았습니다. Notion DB와 비교 및 분석을 시작합니다...")

collection_date = datetime.now().strftime("%Y-%m-%d")
success_count = 0
duplicate_count = 0

job_filter = PersonalizedJobFilter()

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
    title = job.get('title', "")
    description = job.get('description', "")

    is_relevant, score = job_filter.calculate_relevance_score(title, description)

    if not is_relevant:
        print(f" [{i+1}/{len(all_jobs)}] [필터링됨] '{title}' (점수:{score})")
        continue
    print(f"  [{i+1}/{len(all_jobs)}] [통과] '{title}' (점수: {score}) -> Gemini 분석 시작...")


    # ToDo 상세 페이지에 접속해서 공고 본문 텍스트를 가져와야함
    job_description = job.get('description', "")
    analysis_result = None

    if job_description and is_relevant:
        analysis_result = analyze_job_posting(job_description)
        if analysis_result:
            print("--- Gemini 분석 완료 ---")
        else:
            print("--- Gemini 분석 실패 ---")
    else:
        print("   - 본문 내용이 없어 Gemini 분석을 건너뜁니다.")
    
    company = job['company']
    source = job['source']

    # properties 딕셔너리를 동적으로 구성
    properties_to_save = {
        '직무': {
            'title': [{'text': {'content': title}}]
            },
        '회사명': {
            'rich_text': [{'text': {'content': company}}]
            },
        '링크': {
            'url': link
            },
        '출처':{'rich_text': [{'text': {'content': source }}]
            },
        '수집일': {
            'date': {'start': collection_date}
        },
    }

    # Gemini 분석 결과가 있을 경우, 해당 속성들을 추가
    if analysis_result:
        summary = analysis_result.get('summary', '요약 정보 없음')
        required_skills = analysis_result.get('required_skills', [])
        properties_to_save['AI 요약'] = {'rich_text': [{text': {'content': summary}}]}
        if required_skills:
            properties_to_save['핵심 기술'] = {'multi_select': [{'name': skill} for skill in required_skills[:100]]}
    
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties_to_save
        success_count += 1

    except Exception as e:
        print(f" [오류 발생] '{title}' 저장 실패!")
        print(f' 오류원인: {e}')

print("-" * 20)
print(f"총 {len(all_jobs)}개의 공고 중,")
print(f"  - {success_count}개의 새로운 공고를 Notion에 저장했습니다.")
print(f"  - {duplicate_count}개의 공고는 이미 존재하여 건너뛰었습니다.")
print("모든 작업이 완료되었습니다.")
