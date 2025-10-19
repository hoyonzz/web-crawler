import os
import json
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

# 2. 데티어 수집 단계(크롤링 파이프라인)
print("🚀 채용 공고 수집을 시작합니다.")
all_jobs = []

# 클래스 자체를 리스트에 담아, 필요할 때 객체를 생성하는 방식으로 변경
crawlers_to_run = [WantedCrawler, JobKoreaCrawler, SaraminCrawler]

for crawlerClass in crawlers_to_run:
    crawler = crawlerClass()
    crawler_name = type(crawler).__name__
    print(f"--- {crawler_name} 크롤링 시작 ---")
    
    try:
        # 1단계: 목록 페이지에서 신입 공고만 필터링하여 기본 정보 수집
        crawled_jobs_list = crawler.crawl(keyword='백엔드', pages_to_crawl=1, is_newbie=True)
        
        # 2단계: 각 공고의 상세 페이지에 방문하여 본문 수집 - 테스트 범위를 3개로 제한
        jobs_to_process = crawled_jobs_list[:3]
        print(f"   -> {len(crawled_jobs_list)}개 중 {len(jobs_to_process)}개만 상세 분석 진행...")
        
        for i, job in enumerate(jobs_to_process):
            job_link = job['link']
            print(f"   ({i+1}/{len(jobs_to_process)}) 상세 정보 수집 중: {job_link[:50]}...") # 링크 앞부분만 출력

            details = crawler.get_job_description(job_link)
            job['description'] = details.get('description', '')
            job['deadline'] = details.get('deadline', '상시채용')

        all_jobs.extend(jobs_to_process)
        print(f"--- {crawler_name} 크롤링 완료")
    
    except Exception as e:
        print(f" [전체 크롤러 오류] {crawler_name} 실행 중 문제 발생:{e}")

    finally:
        crawler.close_driver()

# 3. 데이터 처리 및 저장 단계 (필터링 -> 분석 -> 저장 파이프라인)
print(f"\n✅ 총 {len(all_jobs)}개의 채용 공고 수집 완료. Notion DB와 비교 및 분석을 시작합니다...")

collection_date = datetime.now().strftime("%Y-%m-%d")
success_count = 0
duplicate_count = 0
job_filter = PersonalizedJobFilter()
filtered_count = 0

# 쿼리 조회 기능
for i, job in enumerate(all_jobs):
    title = job.get('title', '제목 없음')
    link = job.get('link')
    company = job.get('company', '회사명 없음')
    source = job.get('source', '출처 없음')
    description = job.get('description', '')
    deadline = job.get('deadline', '상시채용')

    # 1. 중복확인
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

    # 2단계: 개인화 필터링
    is_relevant, score = job_filter.calculate_relevance_score(title, description)
    if not is_relevant:
        print(f"   [{i+1}/{len(all_jobs)}] [필터링됨] {title} (점수: {score})")
        continue
    print(f"  [{i+1}/{len(all_jobs)}] [신규/통과] '{title}' (점수: {score}) -> Gemini 분석 시작...")


    # 3단계: Gemini AI 분석
    analysis_result = None
    
    if description:
        analysis_result = analyze_job_posting(description)

    # 4단계: Notion에 저장
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
        summary = analysis_result.get('summary', '')
        skills = analysis_result.get('required_skills', [])
        properties_to_save['AI 요약'] = {'rich_text': [{'text': {'content': summary}}]}
        if skills:
            properties_to_save['핵심 기술'] = {'multi_select': [{'name': skill} for skill in skills[:100]]}
    
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties_to_save
        )
        success_count += 1

    except Exception as e:
        print(f" 🚨 [오류] '{title}' 저장 실패! 원인: {e}")


# 최종 결과 요약
print("-" * 30)
print(f"  - 총 {success_count}개의 새로운 공고를 Notion에 저장했습니다.")
print(f"  - {duplicate_count}개의 공고는 이미 존재하여 건너뛰었습니다.")
print(f"  - {filtered_count}개의 공고는 필터링되어 제외되었습니다.")
print("-" * 30)