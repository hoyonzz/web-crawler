import os
from datetime import datetime
from dotenv import load_dotenv
import notion_client
import time


from crawlers.wanted_crawler import WantedCrawler
from crawlers.jobkorea_crawler import JobKoreaCrawler
from crawlers.jumpit_crawler import JumpitCrawler
from data_processor.personalized_job_filter import PersonalizedJobFilter
from analysis.gemini_analyzer import analyze_job_posting_with_ai
from data_processor.career_parser import parse_career_from_header

load_dotenv()

# 테스트 시 분석할 최대 갯수
TEST_MODE_LIMIT = 5

# 설정 초기화
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = notion_client.Client(auth=NOTION_API_KEY)



# 스크립스 시작 시 모든 크롤러 인스턴스 미리 생성
print("🚀 크롤러 인스턴스를 초기화합니다...")
crawler_classes = [WantedCrawler, JobKoreaCrawler, JumpitCrawler]
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
        link = link.split('?')[0]
        job['link'] = link

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
    if TEST_MODE_LIMIT is not None:
        PER_SOURCE_LIMIT = 4
        per_source_count = {}
        jobs_to_process = []
        for job in new_jobs_basic_info:
            s = job.get('source', 'unknown')
            if per_source_count.get(s, 0) < PER_SOURCE_LIMIT:
                jobs_to_process.append(job)
                per_source_count[s] = per_source_count.get(s, 0) + 1
    else:
        jobs_to_process = new_jobs_basic_info
    print(f"\n🚀 [3단계] {len(jobs_to_process)}개 신규 공고의 상세 정보 수집 시작...")
    full_new_jobs, failed_count = [], 0  

    error_stats = {
        "크롤러없음": 0,
        "상세수집실패": 0,
        "상세정보빈값": 0,
        "AI분석에러": 0,
        "노션저장실패": 0,
    }

    for job in jobs_to_process:
        source_crawler_name = job.get('source', '') + "Crawler"
        crawler = crawler_instances.get(source_crawler_name)
        if not crawler: 
            failed_count += 1
            error_stats["크롤러없음"] += 1
            continue
        
        try:
            details = crawler.get_job_description(job['link'])
            job.update(details)
            full_new_jobs.append(job)
        except Exception as e:
            print(f"🚨 [오류] 상세 정보 수집 실패: {job.get('title')}, {e}")
            failed_count += 1
            error_stats["상세수집실패"] += 1

    print(f"\n✅[3단계 완료] {len(full_new_jobs)}개의 공고에 대한 상세 정보 수집을 완료했습니다.")


    # 분석 및 Notion 저장
    print("\n🚀[4단계] 개인화 필터링, AI 분석 및 Notion 저장 시작...")
    job_filter = PersonalizedJobFilter()
    success_count = 0
    filtered_count = 0
    
    filtered_stats = {
        "제외키워드": 0,
        "점수미달": 0
    }

    for i, job in enumerate(full_new_jobs):
        title = job.get('title', '제목 없음')
        description = job.get('description', '')

        # 상세 정보 수집 실패 케이스를 미리 배제
        if not description or len(description.strip()) < 50:
            print(f"\n---({i+1} / {len(full_new_jobs)}) 건너뛰기: {title} (상세 정보 없음) ---")
            failed_count += 1
            error_stats["상세정보빈값"] += 1
            continue

        print(f"\n--- ({i+1} / {len(full_new_jobs)}) 분석 중: {title}---")

        # 개인화 필터링
        is_relevant, score = job_filter.calculate_relevance_score(title, description)
        if not is_relevant:
            filtered_count += 1
            reason_guess = '제외룰' if score == 0 else '점수미달'
            filtered_stats["제외키워드" if score == 0 else "점수미달"] += 1
            print(f" -> [필터링됨] {reason_guess} (점수: {score})")
            continue

        print(f" -> [통과] 관련도 높음 (점수: {score}). AI 분석을 시작합니다...")

        # Gemini AI 분석
        matched_skills = job_filter.extract_matched_skills(description)
        
        analysis = analyze_job_posting_with_ai(title, description, matched_skills)

        if not analysis:
            print(" -> 🚨[오류] AI 분석에 실패했습니다. 다음 공고로 넘어갑니다.")
            # 분석 실패 시에도 API 과부하를 피하기 위해 대기하기
            print(" -> API 한도 방어(5 RPM)를 위해 15초 대기합니다...")
            failed_count += 1
            error_stats["AI분석에러"] += 1
            time.sleep(15)
            continue
        
        rule_career = parse_career_from_header(description)
        if rule_career:
            if set(rule_career) != set(analysis.career_level):
                print(f" -> [경력 보정] LLM: {analysis.career_level} -> 룰: {rule_career}")
            analysis.career_level = rule_career

        # Notion에 저장
        properties_to_save = {
            '직무':{'title':[{'text':{'content':title}}]},
            '직무포지션':{'rich_text': [{'text': {'content': analysis.target_position}}]},
            '회사명':{'rich_text': [{'text':{'content':job.get('company', '회사명 없음')}}]},
            '링크':{'url':job.get('link')},
            '출처':{'select': {'name': job.get('source', '출처 없음')}},
            '수집일':{'date':{'start':datetime.now().strftime("%Y-%m-%d")}},
            '마감일':{'rich_text':[{'text':{'content':job.get('deadline', '확인 필요')}}]},
            '관련도 점수': {'number': score},
            '지원우선순위': {'select': {'name': analysis.application_priority}},
            '매칭도': {'select': {'name': analysis.skill_match}},
            '이력서버전': {'select': {'name': analysis.resume_version}},
            '적합도': {'number': analysis.fit_score},
            '경력요건': {'multi_select': [{'name': c} for c in analysis.career_level]},
            '판정근거': {'rich_text': [{'text': {'content': analysis.reason}}]},
            '보유기술': {'rich_text': [{'text': {'content': ', '.join(analysis.required_must_have) or '정보 없음'}}]},
            '학습필요': {'rich_text': [{'text': {'content': ', '.join(analysis.new_to_learn) or '정보 없음'}}]},
        }

        try:
            notion.pages.create(parent={"database_id":NOTION_DATABASE_ID}, properties=properties_to_save)
            success_count += 1
            print(f"    -> ✅ '{title}' Notion 저장 성공!")
        except Exception as e:
            print(f"   🚨 [오류] '{title}' 저장 실패! 원인: {e}")
            failed_count += 1
            error_stats["노션저장실패"] += 1

        # 속도 제어 로직 추가 Gemini API의 분당 요청 한도 15RPM을 준수하기 위해 대기
        # 마지막 항목에서는 대기할 필요가 없으므로 조건추가
        if i < len(full_new_jobs) - 1:
            print(" -> API 속도 제어를 위해 15초 대기합니다...")
            time.sleep(15)

finally:
    # 모든 작업이 끝난 후, 마지막에 드라이버 일괄 종료
    print("\n🚀 모든 작업 완료. 크롤러 드라이버를 종료합니다...")
    for crawler in crawler_instances.values():
        crawler.close_driver()
    print("✅ 모든 드라이버가 안전하게 종료되었습니다.")

filter_detail_str = f"제외 룰: {filtered_stats['제외키워드']}건, 점수 미달: {filtered_stats['점수미달']}건"
error_detail_str = (f"수집 실패: {error_stats['상세수집실패']}건, 빈값: {error_stats['상세정보빈값']}건, "
                    f"AI 에러: {error_stats['AI분석에러']}건, DB 저장 에러: {error_stats['노션저장실패']}건")

summary_text = f"""## 📊 채용 공고 AI 분석 파이프라인 결과 ({datetime.now():%Y-%m-%d})

| 항목 | 건수 | 상세 내역 |
|:---|:---:|:---|
| **총 수집 공고** | {len(all_jobs_basic_info)} | 각 플랫폼별 1페이지 수집 합계 |
| **신규 (중복 제외)** | {len(new_jobs_basic_info)} | Notion DB와 링크 비교 후 남은 건수 |
| **✅ Notion 적재 성공** | **{success_count}** | **AI 분석 및 구조화 완료** |
| **📉 1차 필터 탈락** | {filtered_count} | {filter_detail_str} |
| **🚨 수집/분석 에러** | {failed_count} | {error_detail_str} |
"""

print(summary_text)

# GitHub Actions 환경인 경우 Step Summary에 결과 기록
github_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
if github_summary_file:
    try:
        with open(github_summary_file, "a", encoding="utf-8") as f:
            f.write(summary_text)
        print(" -> 깃허브 액션 요약 리포트(Job Summary) 작성 완료.")
    except Exception as e:
        print(f" -> 🚨 요약 리포트 작성 실패: {e}")