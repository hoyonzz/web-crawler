import os
from dotenv import load_dotenv

# type
from pydantic import BaseModel, Field
from typing import Literal

# llm
from langchain_google_genai import ChatGoogleGenerativeAI
from google.genai.errors import APIError

# network
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

MY_PROFILE = """
[Basic Information]
- Name: 신호용 (SHIN HO YONG)
- Career Level: Junior (신입) / 비전공(음악학과) 출신 IT 커리어 전환자
- Certifications: 정보처리기사, SQLD, 컴퓨터활용능력 1급, JLPT N2

[Core Tech Stack (Common)]
- Language & Framework: Python, Django, Django REST Framework, FastAPI
- Database: PostgreSQL, MySQL, SQLite
- Infra & CI/CD: Docker Compose, GitHub Actions, AWS Lightsail, Nginx, Gunicorn
- Collaboration: Git, GitHub

[Track A: Backend & Data Pipeline Focus]
- 핵심 역량: Asyncio/WebSocket 기반 실시간 비동기 처리, RDBMS 마이그레이션(ACID 보장), 데이터 무결성 방어
- 파이프라인: Selenium 크롤링, 서버리스(GitHub Actions) ETL 자동화, 이종 시스템 스키마 매핑
- 아키텍처: Monolithic → MSA 데이터 레이크 전환 설계

[Track B: AI Service & LLM Pipeline Focus]
- 핵심 역량: LLM(Gemini/OpenAI) 기반 파이프라인 자동화, Agentic Workflow 설계
- AI 스택: LangChain, LangGraph, RAG(ChromaDB·Embeddings)
- 프롬프트 엔지니어링: System Prompt 제어, Few-shot 기반 JSON 포맷 강제, Hallucination 방어 및 후처리 롤백
- 최적화: 룰 기반 1차 필터 + LLM 2차 분석 결합으로 API 호출 비용 최적화
"""

# Pydantic 스키마
class JobAnalysis(BaseModel):
    career_level: list[Literal["신입", "1~2년", "3년이상", "경력무관"]] = Field(
    description=(
        "공고의 [상단 요약 정보]와 [상세 본문(자격요건)]을 교차 검증하여 실제 요구 경력을 모두 추출합니다. "
        "【절대 준수 규칙 — 번호 순서대로 적용】 "
        "1. 진실의 우선순위: 상단 요약이나 플랫폼 태그에 '신입'·'경력무관'이 있어도, 상세 본문(자격요건·지원자격)에 "
        "'경력 3년 이상' 등 명확한 연차 조건이 있으면 무조건 본문을 1순위로 신뢰합니다. "
        "2. '무관'의 함정: '경력무관'은 신입도 지원 가능한 경우에만 선택합니다. '경력(연수무관)', '경력직(연차무관)', "
        "'경력자(연차 상관없음)'처럼 경력자임을 전제하고 연차만 따지지 않는 표현은 신입 지원 불가이므로 "
        "['1~2년', '3년이상']으로 판정합니다. '경력무관'과 '경력이되 연수무관'은 정반대 의미임에 주의하세요. "
        "3. 복수 조건: '신입 또는 경력 3년 이상'처럼 여러 범위가 허용되면 ['신입', '3년이상'] 모두 선택합니다. "
        "4. 범위 매핑: 연차 범위는 겹치는 구간을 모두 포함합니다. '1~4년'→['1~2년','3년이상'], "
        "'0~3년'→['신입','1~2년','3년이상'], '2년 이상'→['1~2년','3년이상'], '3년 이하'→['신입','1~2년']. "
        "5. 경력직 추정: 명시적 연차는 없지만 '경력직', '경력자 채용', '실무 경험자'처럼 경력을 전제하는 표현이 있으면 "
        "['1~2년', '3년이상']으로 판정합니다. "
        "6. 최종 폴백: 연차도 경력 관련 언급도 전혀 없을 때만 ['경력무관']으로 판정합니다."
        )
    )
    skill_match: Literal["상", "중", "하"] = Field(
        description="공고의 필수 요건 중 지원자 보유 기술의 비율로 판정. 필수 기술의 70% 이상 보유='상', 40~70%='중', 40% 미만='하'. 우대사항은 판정에서 제외"
    )
    resume_version: Literal["A", "B"] = Field(
        description="지원서 버전 추천. 비동기/인프라/DB/백엔드/Django/API/배포 강세='A', LLM/LangChain/에이전트/프롬프트 강세='B', 구분이 모호하거나 양쪽 모두 해당하면='B'"
    )
    application_priority: Literal["즉시지원", "도전", "보존"] = Field(
        description="판정 규칙(반드시 순서대로 적용): ① career_level에 '신입', '1~2년', '경력무관' 중 하나도 없으면(즉 '3년이상'만 있으면) 지원 자격 미달이므로 다른 조건과 무관하게 무조건 '보존'. ② 지원 가능(①통과)하고 skill_match가 '상'이면 '즉시지원'. ③ 지원 가능하지만 skill_match가 '중' 이하거나 new_to_learn이 3개 이상이면 '도전'"
    )
    fit_score: int = Field(
        description="지원자 프로필 기준 적합도 0~10 정수. 기준: 9~10=필수요건 전부 충족+성장방향 일치, 7~8=필수 대부분 충족, 5~6=핵심 일부 충족, 3~4=경력 미달이나 기술 방향은 유사, 0~2=직무 자체가 다름. 경력 미달(3년이상만 요구) 공고는 기술이 맞아도 최대 5점"
    )
    reason: str = Field(
        description="application_priority 판정의 결정적 근거를 첫 문장에, 나머지 판정(매칭도·버전) 근거를 이어서. 한국어 1~2문장"
    )
    required_must_have: list[str] = Field(
        description="공고의 필수 자격 요건 중 지원자가 이미 보유하고 있는 핵심 기술 목록"
    )
    new_to_learn: list[str] = Field(
        description="공고의 필수 자격 요건에 명시되었으나, 지원자의 프로필에 없어 새로 학습해야 하는 기술 목록"
    )
    preferred_summary: str = Field(
        description="공고의 우대 사항 섹션을 1~2문장으로 간결하게 요약"
    )
    target_position: str = Field(
        description="이 공고에서 지원자가 지원해야할 직무 포지션명. 공고에 복수 직무가 있는 경우(예: 계열사별·부문별 채용) 지원자 프로필(Python/백엔드/AI)에 가장 적합한 하나를 선택해 그 직무명을 그대로 기재. 단일 직무 공고면 해당 직무명. 예: 'S/W엔지니어(금융계열사)'"
    )

# LangCahin의 예외 래핑까지 방어하는 만능 필터 함수
def should_retry_api_error(e: Exception) -> bool:
    """
    429(할당량 초과) 및 5xx(서버 장애) 상황만 필터링하여 재시도 여부 결정
    """
   
    # LangChain이 감싸서 반환하거나, 테스트 코드의 문자열 예외인 경우
    err_msg = str(e)
    if any(c in err_msg for c in ["429", "500", "502", "503", "504"]):
        return True
    
    return False

# Tenacity 데코레이터: 최대 3번 시도, 재시도 간격은 4초->8초->10초로 증가
@retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=4, max=10),
        retry=retry_if_exception(should_retry_api_error),
        reraise=True
)
def _call_api_with_retry(prompt: str) -> JobAnalysis:
    """
    내부적으로 LangChain API를 호출하고 재시도를 담당하는 헬퍼 함수
    """
    print(" -> API 호출 시도 중...")
    # 랭체인의 재시도를 끄고, Tenacity로 조절
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_retries=0,
        timeout=60,
    )
    structured_llm = llm.with_structured_output(JobAnalysis)
    return structured_llm.invoke(prompt)
    

# 핵심 분석 함수
def analyze_job_posting_with_ai(job_title: str, job_description: str, matched_skills: list) -> JobAnalysis | None:
    if not job_description:
        print(" ->[경고] 공고 설명이 비어있습니다.")
        return None
    
    prompt_template = """
    ### Persona
    You are a senior tech recruiter specializing in analyzing IT job postings. Your task is to analyze the provided job posting for a junior backend developer candidate based on the profile provided.

    ### Candidate Profile
    {my_profile}

    ### Judgment Guidelines
    - The candidate's target positions are ONLY for 신입(entry-level) to 2 years of experience.
    - Postings requiring 3+ years of experience are NOT eligible for application.

    ### Instructions
    Analyze the [Full Job Posting Text] and the [Pre-extracted Relevant Skills] provided below. 
    The [Pre-extracted Relevant Skills] are keywords detected by a rule-based filter. Use them as hints, but base your final judgment on the full posting text.
    All string values MUST be written in Korean.
    If a specific piece of information is not found, use the Korean string "정보 없음".

    --- START OF DATA ---

    ### [Full Job Posting Text]
    **Title:** {job_title}
    **Description:** {job_description}

    ### [Pre-extracted Relevant Skills]
    {matched_skills}

    --- END OF DATA ---
    """


    prompt = prompt_template.format(
        my_profile = MY_PROFILE,
        job_title=job_title,
        job_description=job_description,
        matched_skills=matched_skills
    )

    try:
        result = _call_api_with_retry(prompt)
        print(" -> ✅ LangChain 구조화 출력 성공!")
        return result

    except Exception as e:
        print(f" [llm 오류] 처리중 문제 발생: {type(e).__name__}, {e}")
        return None