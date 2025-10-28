import os
import json
from datetime import datetime
from dotenv import load_dotenv
import notion_client
import time


from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler
from crawlers.saramin_crawler import SaraminCrawler
from data_processor.personalized_job_filter import PersonalizedJobFilter
from analysis.gemini_analyzer import analyze_job_posting_with_ai

load_dotenv()

# 테스트 시 분석할 최대 갯수
TEST_MODE_LIMIT = 5

# 설정 초기화
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)



# 스크립스 시작 시 모든 크롤러 인스턴스 미리 생성
print("🚀 크롤러 인스턴스를 초기화합니다...")
crawler_classes = [WantedCrawler, JobKoreaCrawler, SaraminCrawler]
crawler_instances = {cls.__name__: cls() for cls in crawler_classes}
print("✅ 모든 크롤러가 준비되었습니다.")

# 전체 프로세스를 try...finally로 감싸 안정성 높이기
# 파이프라인 시작 
try:
    print("🚀 [1단계] 모든 사이트에서 기본 공고 목록 수집을 시작합니다.")
    all_jobs_basic_info = []
    # 미리 생성된 인스턴스를 사용하여 목록 수집
    for name, crawler in crawler_instances.items():
        print(f"\n--- {name} 실행 ---")
        try:
            pages = 5 if name != 'WantedCrawler' else 1
            jobs = crawler.crawl(keyword='백엔드', pages_to_crawl=pages, is_newbie=True)
            all_jobs_basic_info.extend(jobs)
            print(f"   -> {len(jobs)}개의 공고 목록 수집 완료.")
        except Exception as e:
            print(f" 🚨 [오류] {name} 목록 수집 실패: {e} ")

    print(f"\n✅ [1단계 완료] 총 {len(all_jobs_basic_info)}개의 공고 목록 수집 완료.")

    # 중복 제거 단계
    print(f"\n🚀 [2단계] Notion DB와 비교하여 신규 공고 필터링 시작...")
    new_jobs_basic_info = []
    for job in all_jobs_basic_info:
        link = job.get('link')
        if not link: continue
        try:
            response = notion.databases.query(
                database_id=NOTION_DATABASE_ID,
                filter={"property": "링크", "url": {"equals": link}}
            )
            if len(response['results']) == 0:
                new_jobs_basic_info.append(job)
        except Exception as e:
            print(f"🚨 [오류] DB 중복 확인 실패: {job.get('title')}, {e}")
    print(f"\n✅ [2단계 완료] {len(new_jobs_basic_info)}개의 새로운 공고 발견.")

    # 상세 정보 수집 단계
    jobs_to_process = new_jobs_basic_info[:TEST_MODE_LIMIT] if TEST_MODE_LIMIT is not None else new_jobs_basic_info
    print(f"\n🚀 [3단계] {len(jobs_to_process)}개 신규 공고의 상세 정보 수집 시작...")
    full_new_jobs, failed_count = [], 0  

    for job in jobs_to_process:
        source_crawler_name = job.get('source', '') + "Crawler"
        crawler = crawler_instances.get(source_crawler_name)
        if not crawler: 
            failed_count += 1
            continue
        
        try:
            details = crawler.get_job_description(job['link'])
            job.update(details)
            full_new_jobs.append(job)
        except Exception as e:
            print(f"🚨 [오류] 상세 정보 수집 실패: {job.get('title')}, {e}")
            failed_count += 1

    print(f"\n✅[3단계 완료] {len(full_new_jobs)}개의 공고에 대한 상세 정보 수집을 완료했습니다.")


    # 분석 및 Notion 저장
    print("\n🚀[4단계] 개인화 필터링, AI 분석 및 Notion 저장 시작...")
    job_filter = PersonalizedJobFilter()
    success_count = 0
    filtered_count = 0

    for i, job in enumerate(full_new_jobs):
        title = job.get('title', '제목 없음')
        description = job.get('description', '')

        # 상세 정보 수집 실패 케이스를 미리 배제
        if not description or len(description.strip()) < 50:
            print(f"\n---({i+1} / {len(full_new_jobs)}) 건너뛰기: {title} (상세 정보 없음) ---")
            failed_count += 1
            continue

        print(f"\n--- ({i+1} / {len(full_new_jobs)}) 분석 중: {title}---")

        # 개인화 필터링
        is_relevant, score = job_filter.calculate_relevance_score(title, description)
        if not is_relevant:
            print(f" -> [필터링됨] 관련도가 낮아 건너뜁니다. (점수: {score})")
            filtered_count += 1
            time.sleep(0.5)
            continue

        print(f" -> [통과] 관련도 높음 (점수: {score}). AI 분석을 시작합니다...")

        # Gemini AI 분석
        matched_skills = job_filter.extract_matched_skills(description)
        ai_analysis_json = analyze_job_posting_with_ai(title, description, matched_skills)

        if not ai_analysis_json:
            print(" -> 🚨[오류] AI 분석에 실패했습니다. 다음 공고로 넘어갑니다.")
            # 분석 실패 시에도 API 과부하를 피하기 위해 대기하기
            print(" -> API 속도 제어를 위해 5초 대기합니다...")
            time.sleep(5)
            continue

        # Notion에 저장
        ai_analysis_text = json.dumps(ai_analysis_json, ensure_ascii=False, indent = 2)
        properties_to_save = {
            '직무':{'title':[{'text':{'content':title}}]},
            '회사명':{'rich_text': [{'text':{'content':job.get('company', '회사명 없음')}}]},
            '링크':{'url':job.get('link')},
            '출처':{'rich_text':[{'text':{'content':job.get('source', '출처 없음')}}]},
            '수집일':{'date':{'start':datetime.now().strftime("%Y-%m-%d")}},
            '마감일':{'rich_text':[{'text':{'content':job.get('deadline', '확인 필요')}}]},
            'AI 분석 결과': {'rich_text':[{'text':{'content':ai_analysis_text}}]},
            '관련도 점수': {'number': score}
        }

        try:
            notion.pages.create(parent={"database_id":NOTION_DATABASE_ID}, properties=properties_to_save)
            success_count += 1
            print(f"    -> ✅ '{title}' Notion 저장 성공!")
        except Exception as e:
            print(f"   🚨 [오류] '{title}' 저장 실패! 원인: {e}")

        # 속도 제어 로직 추가 Gemini API의 분당 요청 한도 15RPM을 준수하기 위해 대기
        # 마지막 항목에서는 대기할 필요가 없으므로 조건추가
        if i < len(full_new_jobs) - 1:
            print(" -> API 속도 제어를 위해 5초 대기합니다...")
            time.sleep(5)

finally:
    # 모든 작업이 끝난 후, 마지막에 드라이버 일괄 종료
    print("\n🚀 모든 작업 완료. 크롤러 드라이버를 종료합니다...")
    for crawler in crawler_instances.values():
        crawler.close_drvier()
    print("✅ 모든 드라이버가 안전하게 종료되었습니다.")


# 최종 결과 요약
print("-" * 30)
print("✅ 모든 파이프라인이 완료되었습니다.")
print(f"  - 총 {success_count}개의 새로운 공고를 Notion에 저장했습니다.")
print(f"  - {failed_count}개의 공고는 상세 정보 수집 중 오류가 발생했습니다.")
print(f"  - {filtered_count}개의 공고는 필터링되어 제외되었습니다.")
print("-" * 30)