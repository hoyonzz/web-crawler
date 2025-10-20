import os
import json
from datetime import datetime
from dotenv import load_dotenv
import notion_client


from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler
from crawlers.saramin_crawler import SaraminCrawler

from data_processor.personalized_job_filter import PersonalizedJobFilter
from analysis.gemini_analyzer import analyze_job_posting_with_ai


load_dotenv()

# 테스트 시 분석할 최대 갯수
TEST_MODE_LIMIT = 3

# 설정 초기화
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)
job_filter = PersonalizedJobFilter()

# 파이프라인 시작 
print("🚀 채용 공고 수집을 시작합니다.")
all_new_jobs = []
# 클래스 자체를 리스트에 담아, 필요할 때 객체를 생성하는 방식으로 변경
crawlers_to_run = [WantedCrawler, JobKoreaCrawler, SaraminCrawler]

for crawlerClass in crawlers_to_run:
    crawler = crawlerClass()
    crawler_name = type(crawler).__name__
    print(f"\n--- {crawler_name} 크롤링 시작 ---")
    
    try:
        jobs = crawler.crawl(keyword='백엔드', pages_to_crawl=1, is_newbie=True)
        new_count = 0
        
        # 3. 2단계: Notion DB와 비교하여 이미 수집된 공고 제외
        for i, job in enumerate(jobs):
            link = job.get('link')
            if not link: continue

            print(f" ⏳ ({i+1}/{len(jobs)}) DB 중복 확인 중: {job.get('title', '')[:30]}...")
            response = notion.databases.query(
                database_id=NOTION_DATABASE_ID,
                filter={"property": "링크", "url": {"equals": link}}
            )
            if len(response['results']) == 0:
                all_new_jobs.append(job)
                new_count += 1
        print(f"   -> {new_count}개의 새로운 공고를 발견했습니다.")
    except Exception as e:
        print(f" [오류] {crawler_name} 실행 중 문제 발생:{e}")

    finally:
        crawler.close_driver()

print(f"\n✅[1단계 완료] 총 {len(all_new_jobs)}개의 새로운 공고를 발견했습니다.")

if TEST_MODE_LIMIT is not None and len(all_new_jobs) > TEST_MODE_LIMIT:
    print(f"\n⚠️ 시운전 모드: {len(all_new_jobs)}개의 신규 공고 중 {TEST_MODE_LIMIT}개만 상세 분석을 진행합니다.")
    jobs_to_process_details = all_new_jobs[:TEST_MODE_LIMIT]
else:
    jobs_to_process_details = all_new_jobs

print(f"\n[2단계] {len(jobs_to_process_details)}개 공고의 상세 정보 수집 시작...")
full_new_jobs, failed_details_count = [], 0
crawler_instances = {cls.__name__: cls() for cls in [WantedCrawler, JobKoreaCrawler, SaraminCrawler]}

for i, job in enumerate(jobs_to_process_details):
    source_crawer_name = job.get('source', '') + "Crawler"
    crawler = crawler_instances.get(source_crawer_name)
    link = job.get('link')

    if not crawler or not link:
        failed_details_count += 1
        continue

    print(f"\n[{i+1}/{len(jobs_to_process_details)}] 상세 정보 수집: {job.get('title', '')[:30]}...")
    try:
        details = crawler.get_job_description(link)
        job['description'] = details.get('description', '')
        job['deadline'] = details.get('deadline', '확인 필요')
        full_new_jobs.append(job)
    except Exception as e:
        print(f" [오류] 상세 정보 수집 중 문제 발생: {e}")
        failed_details_count += 1

for crawler in crawler_instances.values():
    crawler.close_driver()
print(f"\n✅[2단계 완료] {len(full_new_jobs)}개의 공고에 대한 상세 정보 수집을 완료했습니다.")


# 3단계: 분석 및 Notion 저장
print("\n[3단계] 개인화 필터링, AI 분석 및 Notion 저장 시작...")
success_count = 0
filtered_count = 0

for i, job in enumerate(full_new_jobs):
    title = job.get('title', '제목 없음')
    description = job.get('description', '')

    print(f"\n--- ({i+1} / {len(full_new_jobs)}) 분석 중: {title}---")

    # 3-1. 개인화 필터링
    is_relevant, score = job_filter.calculate_relevance_score(title, description)
    if not is_relevant:
        print(f" -> [필터링됨] 관련도가 낮아 건너뜁니다. (점수: {score})")
        filtered_count += 1
        continue

    print(f" -> [통과] 관련도 높음 (점수: {score}). AI 분석을 시작합니다...")

    # 3-2. Gemini AI 분석
    matched_skills = job_filter.extract_matched_skills(description)
    ai_analysis_json = analyze_job_posting_with_ai(title, description, matched_skills)

    if not ai_analysis_json:
        print(" -> 🚨[오류] AI 분석에 실패했습니다. 다음 공고로 넘어갑니다.")
        continue

    # 3-3. Notion에 저장
    ai_analysis_text = json.dumps(ai_analysis_json, ensure_ascii=False, indent = 2)
    properties_to_save = {
        '직무':{'title':[{'text':{'content':title}}]},
        '회사명':{'rich_text': [{'text':{'content':job.get('company', '회사명 없음')}}]},
        '링크':{'url':job.get('link')},
        '출처':{'rich_text':[{'text':{'content':job.get('source', '출처 없음')}}]},
        '수집일':{'date':{'start':datetime.now().strftime("%Y-%m-%d")}},
        '마감일':{'rich_text':[{'text':{'content':job.get('deadline', '확인 필요')}}]},
        'AI 분석 결과': {'rich_text':[{'text':{'content':ai_analysis_text}}]}
    }

    try:
        notion.pages.create(parent={"database_id":NOTION_DATABASE_ID}, properties=properties_to_save)
        success_count += 1
        print(f"    -> ✅ '{title}' Notion 저장 성공!")
    except Exception as e:
        print(f"   🚨 [오류] '{title}' 저장 실패! 원인: {e}")


# 최종 결과 요약
print("-" * 30)
print("✅ 모든 파이프라인이 완료되었습니다.")
print(f"  - 총 {success_count}개의 새로운 공고를 Notion에 저장했습니다.")
print(f"  - {len(all_new_jobs) - len(full_new_jobs)}개의 공고는 상세 정보 수집 중 오류가 발생했습니다.")
print(f"  - {filtered_count}개의 공고는 필터링되어 제외되었습니다.")
print("-" * 30)