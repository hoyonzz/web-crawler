import pytest
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processor.personalized_job_filter import PersonalizedJobFilter


@pytest.fixture
def filter_engine():
    """테스트용 필터 엔진 인스턴스"""
    return PersonalizedJobFilter()


class TestBackendJobDetection:
    """백엔드 공고 탐지 테스트"""
    
    def test_pure_backend_job(self, filter_engine):
        """순수 백엔드 공고 - 통과해야 함"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "백엔드 개발자 (Python/Django)",
            "Python Django를 활용한 REST API 개발. PostgreSQL 데이터베이스 설계."
        )
        assert is_relevant == True
        assert score >= 0.25
    
    def test_backend_with_multiple_skills(self, filter_engine):
        """다수의 백엔드 기술 스택 - 높은 점수"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "시니어 백엔드 엔지니어",
            "Django REST API 개발. PostgreSQL, Redis, Docker, Git, pytest 단위 테스트."
        )
        assert is_relevant == True
        assert score >= 0.5  # 여러 키워드 매칭 시 높은 점수
    
    def test_backend_with_oauth(self, filter_engine):
        """OAuth 경험 포함 - 포트폴리오 매칭"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "백엔드 개발자",
            "소셜 로그인 OAuth 구현. Django REST Framework 개발."
        )
        assert is_relevant == True
        assert score >= 0.3


class TestFrontendJobRejection:
    """프론트엔드 공고 거부 테스트"""
    
    def test_pure_frontend_job(self, filter_engine):
        """순수 프론트엔드 공고 - 거부되어야 함"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "프론트엔드 개발자",
            "React, Vue.js를 활용한 UI/UX 개발"
        )
        assert is_relevant == False
        assert score < 0.25
    
    def test_frontend_with_design(self, filter_engine):
        """프론트엔드 + 디자인 - 거부"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "UI/UX 디자이너",
            "Figma를 활용한 디자인. React 프론트엔드 협업."
        )
        assert is_relevant == False
    
    def test_mobile_app_developer(self, filter_engine):
        """모바일 앱 개발자 - 거부"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "iOS 앱 개발자",
            "Swift를 활용한 iOS 네이티브 앱 개발"
        )
        assert is_relevant == False


class TestFullStackJob:
    """풀스택 공고 테스트"""
    
    def test_fullstack_with_backend_focus(self, filter_engine):
        """백엔드 중심 풀스택 - 통과"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "풀스택 개발자",
            "Django 백엔드 + React 프론트엔드. 주력은 서버 개발. PostgreSQL, AWS 배포."
        )
        assert is_relevant == True
        # 백엔드 키워드가 많으므로 통과
    
    def test_fullstack_frontend_focus(self, filter_engine):
        """프론트엔드 중심 풀스택 - 상황에 따라"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "풀스택 개발자",
            "React 프론트엔드 중심. Node.js 백엔드도 가능."
        )
        # Node.js는 키워드에 없으므로 점수 낮을 수 있음
        assert score < 0.3


class TestExceptionHandling:
    """예외 처리 테스트"""
    
    def test_none_job_title(self, filter_engine):
        """None 제목 처리"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            None,
            "Python Django 백엔드 개발"
        )
        assert is_relevant == True
    
    def test_none_job_description(self, filter_engine):
        """None 설명 처리"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "백엔드 개발자",
            None
        )
        # 제목만으로는 점수가 낮을 수 있음
        assert score >= 0.0
    
    def test_empty_strings(self, filter_engine):
        """빈 문자열 처리"""
        is_relevant, score = filter_engine.calculate_relevance_score("", "")
        assert is_relevant == False
        assert score == 0.0
    
    def test_very_short_text(self, filter_engine):
        """매우 짧은 텍스트"""
        is_relevant, score = filter_engine.calculate_relevance_score(
            "개발자",
            "백엔드"
        )
        # 10자 미만 텍스트는 거부
        assert is_relevant == False


class TestSkillExtraction:
    """기술 스택 추출 테스트"""
    
    def test_extract_multiple_skills(self, filter_engine):
        """여러 기술 추출"""
        skills = filter_engine.extract_matched_skills(
            "Django REST API 개발. PostgreSQL, Redis, Docker, Git 사용."
        )
        assert 'django' in skills
        assert 'postgresql' in skills
        assert 'redis' in skills
        assert 'docker' in skills
        assert 'git' in skills
    
    def test_extract_from_empty_text(self, filter_engine):
        """빈 텍스트에서 추출"""
        skills = filter_engine.extract_matched_skills("")
        assert skills == []
    
    def test_extract_with_none(self, filter_engine):
        """None 텍스트 처리"""
        skills = filter_engine.extract_matched_skills(None)
        assert skills == []


class TestKeywordStats:
    """통계 기능 테스트"""
    
    def test_get_keyword_stats(self, filter_engine):
        """통계 정보 반환"""
        stats = filter_engine.get_keyword_stats()
        
        assert 'core_skills' in stats
        assert 'general_backend' in stats
        assert 'growth_potential' in stats
        assert 'devops_infra' in stats
        assert 'exclude_count' in stats
        assert 'max_score' in stats
        
        # 각 그룹의 키워드 개수 확인
        assert stats['core_skills']['count'] > 0
        assert stats['max_score'] > 0
