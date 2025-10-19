import os
import json
import google.generativeai as genai

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)



# API 키 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# for m in genai.list_models():
#     if "generateContent" in m.supported_generation_methods:
#         print(m.name)

# 사용할 Gemini 모델 설정
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_job_posting(job_description: str):
    # 채용공고 내용을 Gemini API를 이용해 분석하고, 핵심 기술 스택과 요약 내용 추출
    if not job_description or not GEMINI_API_KEY:
        return None
    
    # AI에게 보낼 프롬프트(명령어)
    prompt = f"""
    다음 채용 공고 내용을 분석하여 아래 형식에 맞춰 JSON으로 응답해줘.
    
    - "summary": 초보자도 이해하기 쉽게 이 포지션의 핵심 역할을 3문장으로 요약해줘.
    
    - "required_skills": 이 포지션에 '필수적인' 기술 스택이나 자격 요건을 Python리스트 형태로 나열해줘.
    
    - "preferred_skills": '우대 사항'에 해당하는 기술 스택이나 자격 요건을 Python 리스트 형태로 나열해줘.
    
    ---
    {job_description}
    ---
    """

    try:
        response = model.generate_content(prompt)
        # Gemini 응답 텍스트 파싱
        cleaned_text = response.text.strip().replace("'''json","").replace("'''","")
        return json.loads(cleaned_text)
    
    except (json.JSONDecodeError, Exception) as e:
        print(f" [Gemini 오류] 응답 파싱 중 문제 발생: {e}")
        print(f" 원본 응답: {response.text}")
        return None

