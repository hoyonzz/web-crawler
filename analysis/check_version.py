import google.generativeai as genai
import sys, os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

for m in genai.list_models():
        
    if "generateContent" in m.supported_generation_methods:
        print(m.name)

print("--- 환경 진단 시작 ---")
try:
    print(f"Python 실행 경로: {sys.executable}")

    # 파이썬이 실제로 불러와서 사용하고 있는 라이브러리의 버전
    print(f"google-generativeai 라이브러리 버전: {genai.__version__}")

    version_parts = [int(part) for part in genai.__version__.split('.')]
    if version_parts[1] < 5:
        print("\n[경고] 라이브러리 버전이 너무 낮습니다. v1beta API를 사용할 가능성이 높습니다.")
        print("터미널에서 'pip install --upgrade google-generativeai'를 다시 실행해주세요.")
    else:
        print('\n[성공] 라이브러리 버전이 최신입니다. API 호출에 문제가 없어야 합니다.')

except ImportError:
    print('[오류] google-generativeai 라이브러리가 설치되지 않았습니다.')
except Exception as e:
    print(f"[알수 없는 오류] {e}")

print("---환경 진단 종료 ---")