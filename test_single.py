# test_single.py
import json
from crawlers.wanted_crawler import WantedCrawler
from analysis.gemini_analyzer import analyze_job_posting_with_ai

def test_single_job(url: str):
    print(f"🚀 단일 공고 정밀 테스트 시작: {url}")
    
    # 1. 크롤러 1회용 인스턴스 생성
    crawler = WantedCrawler()
    
    try:
        # 2. 상세 본문 긁어오기 (패치된 헤더 정보 포함 여부 확인)
        print("\n[Step 1] 상세 텍스트 수집 중...")
        details = crawler.get_job_description(url)
        description = details.get('description', '')
        
        print("-" * 50)
        print("🔍 [크롤러가 가져온 날것의 텍스트 (LLM에게 전달될 내용)]")
        # 터미널에서 경력 정보가 제대로 포함되었는지 육안으로 확인
        print(description[:500] + "\n... (생략) ...\n") 
        print("-" * 50)
        
        if not description or len(description) < 50:
            print("🚨 텍스트 수집 실패! 구조 확인이 필요합니다.")
            return

        # 3. AI 분석 실행
        print("\n[Step 2] Gemini AI 분석 실행 중...")
        # matched_skills는 테스트용 더미 데이터 전달
        analysis = analyze_job_posting_with_ai(
            job_title="테스트 공고", 
            job_description=description, 
            matched_skills=["Python", "Django"]
        )
        
        if analysis:
            print("\n✅ [AI 분석 결과 (Pydantic 모델 JSON 출력)]")
            # 모델의 결과값을 JSON 형태로 이쁘게 출력
            print(json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False))
        else:
            print("🚨 AI 분석 실패 또는 타임아웃 발생.")
            
    finally:
        crawler.close_driver()
        print("\n✅ 드라이버 종료 완료.")

if __name__ == "__main__":
    # 회원님이 환각 오류를 발견하신 공고 URL 중 하나를 타겟으로 지정
    target_url = "https://www.wanted.co.kr/wd/362629"
    test_single_job(target_url)