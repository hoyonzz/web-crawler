import os
import json
import google.generativeai as genai
import traceback

from dotenv import load_dotenv
from typing import Union


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)



# API 키 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# for m in genai.list_models():
#     if "generateContent" in m.supported_generation_methods:
#         print(m.name)

# 사용할 Gemini 모델 설정
# model = genai.GenerativeModel('gemini-2.0-flash')



def analyze_job_posting_with_ai(job_title: str, job_description: str, matched_skills: list) -> Union[dict, None]:
    # 채용 공고 내용을 Gemini API를 이용해 분석하고, 구조화된 JSON을 반환
    if not job_description:
        print(" -> [경고] 공고 설명이 비어있습니다.")
        return None
    
    # AI에게 보낼 프롬프트(명령어)
    prompt_template = """
### Persona
You are a senior tech recruiter specializing in analyzing IT job postings. Your task is to analyze the provided job posting for a junior backend developer candidate named 'SHIN HO YONG' and structure the key information into a JSON format.

### Profile of 'SHIN HO YONG'
- **Core Skills:** Python, Django, PostgreSQL, AWS
- **Experienced Skills:** REST API, Git, Nginx, Gunicorn, MySQL, Unit Testing
- **Growth Interests:** AI/LLM, Data Engineering, Automation Pipelines

### Instructions
Analyze the [Full Job Posting Text] and the [Pre-extracted Relevant Skills] provided below. You MUST follow these rules:
1.  Output the result ONLY in the specified JSON format.
2.  Do not add any explanatory text before or after the JSON object.
3.  All string values within the JSON MUST be written in Korean.
4.  If a specific piece of information is not found, use the Korean string "정보 없음".

### Output Format (JSON ONLY)
```json
{{{{
  "career_level": "요구 경력을 '신입', '주니어(1-3년)', '경력(4년 이상)', '경력무관' 중 하나로 분류하여 문자열로 출력",
  "core_responsibilities": [
    "공고의 '주요 업무' 또는 '담당할 일' 섹션을 분석하여, 가장 핵심적인 역할 2~3가지를箇条書き(불렛 포인트) 형태의 문자열 배열로 요약"
  ],
  "required_skills_summary": {{{{
    "must_have": [
      "공고의 '자격 요건', '필수 사항' 섹션을 분석하여, '신호용'이 보유한 기술 중 반드시 필요한 핵심 기술들을 문자열 배열로 나열. [사전 추출된 관련 기술 목록]을 최우선으로 참고할 것."
    ],
    "new_to_learn": [
      "공고의 '자격 요건'에 명시되었지만, '신호용'의 프로필에 없는 새로운 필수 기술들을 문자열 배열로 나열."
    ]
  }}}},
  "preferred_skills_summary": "공고의 '우대 사항' 섹션을 1~2 문장으로 간결하게 요약",
  "fit_score_for_me": {{{{
    "score": "주어진 [신호용의 프로필]을 기준으로, 이 공고와의 기술적/성장 목표 적합도를 0부터 10까지의 정수(Integer)로 평가",
    "reason": "위 점수를 부여한 핵심적인 이유를 1문장으로 요약"
  }}}}
}}}}
```

--- START OF DATA ---

### [Full Job Posting Text]
**Title:** {job_title}
**Description:** {job_description}

### [Pre-extracted Relevant Skills]
{matched_skills}

--- END OF DATA ---
"""


    prompt = prompt_template.format(
        job_title=job_title,
        job_description=job_description,
        matched_skills=matched_skills
    )

    try:
        # 매번 새로운 모델 인스턴스 생성
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        print(f" -> Gemini API 호출 시작...")
        response = model.generate_content(prompt)
        try:
            # Gemini 응답 텍스트 파싱
            text = response.text
            print(f" -> API 응답 수신 성공 (길이: {len(text)}자)")
        except AttributeError as ae:
            print(" -> .text 속성을 찾을 수 없어 candidates에서 직접 추출합니다: {ae}")
            try:
              text = text = response.candidates[0].content.parts[0].text
              print(f" -> candidates에서 텍스트 추출 성공 (길이: {len(text)}자)")
            except Exception as e:
              print(f" -> [오류] 응답 텍스트 추출 실패: {e}")
              print(f" -> 전체 응답 객체: {response}")
              return None
        
        # JSON 파싱
        cleaned_text = text.strip()
        
        # 마크다운 코드 블록 제거
        if cleaned_text.startwith("```"):
            cleaned_text_text = cleaned_text.replace("``````", "").strip()
          
        print(f" -> JSON 파싱 시도 중...")
        parsed_json = json.loads(cleaned_text)
        print(f" -> ✅ JSON 파싱 성공!")

        return parsed_json
    
    except json.JSONDecodeError:
        print(f" [Gemini 오류] JSON 응답 파싱 중 문제 발생. AI 응답 형식이 잘못됨.")
        print(f" 원본 응답: {text}")
        return None
    
    except Exception as e:
        print(f" [Gemini 오류] 요청 또는 응답 처리 중 문제: {type(e).__name__}, {e}")
        return None

