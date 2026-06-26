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
        description="공고의 자격요건을 분석하여 요구 경력을 모두 포함. 예: '신입 또는 5년 이상'일 경우 ['신입', '3년이상'] 반환"
    )
    skill_match: Literal["상", "중", "하"] = Field(
        description="지원자의 핵심 기술과 공고의 요구사항 매칭도. 다수 일치='상', 일부 일치='중', 거의 없음='하'"
    )
    resume_version: Literal["A", "B"] = Field(
        description="지원서 버전 추천. 비동기/인프라/DB/백엔드/Django/API/배포 강세='A', LLM/LangChain/에이전트/프롬프트 강세 ='B', 구분이 모호하면 기본값 'B'"
    )
    application_priority: Literal["즉시지원", "도전", "보존"] = Field(
        description="지원자의 총 경력과 핵심 기술 일치도를 종합하여 판정. 적합도가 매우 높으면 '즉시지원', 배울 점이 많거나 일부 부족하면 '도전', 매칭도가 낮으면 '보존'"
    )
    fit_score: int = Field(
        description="지원자의 프로필을 기준으로 이 공고와의 기술적/성장 목표 적합도를 0부터 10까지의 정수로 평가"
    )
    reason: str = Field(
        description="위의 판정(경력, 매칭도, 이력서 버전, 지원 우선순위)을 내린 핵심적인 논리적 근거를 한국어 1~2문장으로 요약"
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

# LangCahin의 예외 래핑까지 방어하는 만능 필터 함수
def should_retry_api_error(e: Exception) -> bool:
    """
    429(할당량 초과) 및 5xx(서버 장애) 상황만 필터링하여 재시도 여부 결정
    """
    # 원본 APIError가 내용그대로 올라온 경우
    if isinstance(e, APIError):
        code = getattr(e, "code", None)
    
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
        max_retries=0
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

    ### Instructions
    Analyze the [Full Job Posting Text] and the [Pre-extracted Relevant Skills] provided below. 
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