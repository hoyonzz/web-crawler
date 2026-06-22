# test_filter_step1.py  (프로젝트 루트에서: python test_filter_step1.py)
from data_processor.personalized_job_filter import PersonalizedJobFilter

f = PersonalizedJobFilter()

# (이름, 제목, 본문, 기대 결과)
cases = [
    ("Java 단독",        "백엔드 개발자", "Java, Spring, MSA 기반 서비스 개발", False),
    ("Python+Java 멀티", "백엔드 개발자", "Python/Django 주력, Java 경험 우대", True),
    ("순수 Python",      "서버 개발자",  "FastAPI 비동기 서버, asyncio, PostgreSQL", True),
    ("React 풀스택",     "웹 개발자",    "Django + React 풀스택 개발", False),
    ("무관(COBOL)",      "회계 시스템",  "COBOL 기반 ERP 유지보수", False),
    ("email→ai 함정",    "마케팅 매니저","email marketing campaign, CRM 운영", False),
]

passed = 0
for name, title, desc, expected in cases:
    is_relevant, score = f.calculate_relevance_score(title, desc)
    ok = (is_relevant == expected)
    passed += ok
    print(f"{'✅' if ok else '❌'} [{name}] 기대={expected} 실제={is_relevant} 점수={score}")

print(f"\n{passed}/{len(cases)} 통과")