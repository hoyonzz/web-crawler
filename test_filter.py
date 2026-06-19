from data_processor.personalized_job_filter import PersonalizedJobFilter

def test_filter():
    filter_engine = PersonalizedJobFilter()
    
    test_cases = [
        {
            'title': '백엔드 개발자 (Python/Django)',
            'desc': 'Django REST API 개발. PostgreSQL, AWS 배포 경험자 우대.',
            'expected': True
        },
        {
            'title': '프론트엔드 개발자',
            'desc': 'React, Vue.js UI/UX 개발',
            'expected': False
        },
        {
            'title': 'Full Stack 개발자',
            'desc': 'Django 백엔드 + React 프론트. Git, Docker',
            'expected': True
        }
    ]
    
    print("=" * 60)
    print("필터 테스트 시작")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        is_relevant, score = filter_engine.calculate_relevance_score(
            test['title'], test['desc']
        )
        matched_skills = filter_engine.extract_matched_skills(test['desc'])
        
        result = "✓ 통과" if is_relevant == test['expected'] else "✗ 실패"
        
        print(f"\n[테스트 {i}] {result}")
        print(f"  제목: {test['title']}")
        print(f"  예상: {'관련있음' if test['expected'] else '관련없음'}")
        print(f"  실제: {'관련있음' if is_relevant else '관련없음'} (점수: {score:.3f})")
        print(f"  매칭 기술: {', '.join(matched_skills)}")

if __name__ == "__main__":
    test_filter()