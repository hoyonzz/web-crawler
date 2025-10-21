import os
import google.generativeai as genai
from dotenv import load_dotenv



print("--- 로컬 API 직접 호출 테스트 시작 ---")

# 1. .env파일 로드
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ [오류] .env 파일에서 api찾을 수 없음")
    exit()

# 2. API 클라이언트 설정
try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ API 키 설정 완료")
except Exception as e:
    print(f"❌ [오류] API 키 설정 중 문제 발생 : {e}")
    exit()

# 3. 모델 초기화
model_name = 'gemini-2.0-flash'
try:
    model = genai.GenerativeModel(model_name)
    print(f"✅ '{model_name}' 모델 초기화 성공.")
except Exception as e:
    print(f"❌ [오류] '{model_name}' 모델 초기화 실패 : {e}")
    exit()

# 4. API 호출
test_prompt = "이 문장을 세 단어로 요약해줘: 나는 오늘 아침에 맛있는 사과를 먹었다."
print(f"\n-> 모델에 다음 프롬프트를 전송합니다:\n '{test_prompt}'")

try:
    response = model.generate_content(test_prompt)

    try:
        text = response.text
    except AttributeError:
        text = response.candidates[0].content.parts[0].text
    
    print("\n🎉 [성공] API 호출에 성공했습니다!")
    print("--- 모델 응답 ---")
    print(text)
    print("--------------------")

except Exception as e:
    print(f"\n🚨 [실패] API 호출 중 오류가 발생했습니다.")
    print(f"   - 오류 타입: {type(e).__name__}")
    print(f"   - 오류 메시지: {e}")

print("\n--- 로컬 API 직접 호출 테스트 종료 ---")