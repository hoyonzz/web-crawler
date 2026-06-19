from typing import Dict, Tuple, List
import re
import os
import yaml
from functools import lru_cache
from pathlib import Path



class PersonalizedJobFilter:
    """
    신호용 님의 포트폴리오 기반 개인화된 채용 공고 필터.
    
    포트폴리오 분석 결과:
    - JumpToDjango: Django, PostgreSQL, AWS Lightsail, REST API
    - 소셜 로그인(OAuth), 단위 테스트, Git 경험
    - 성장 목표: AI/LLM, 데이터 처리, 자동화
    
    개선 사항:
    - 키워드 20개 → 40개로 확장
    - 매칭 키워드 수를 고려한 점수 증폭
    - None/빈 문자열 예외 처리 추가
    - 정규표현식 활용으로 성능 향상
    - 통계 메서드 추가
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / 'config' / 'job_filter_config.yaml'
        self.my_keywords = self._load_config(str(config_path))

        # 점수 계산용 그룹 목록을 설정 ('exclude'는 제외)
        self._score_groups = [key for key in self.my_keywords.keys() if key != 'exclude']

        self._max_score = sum(self.my_keywords[group].get('weight', 0) for group in self._score_groups)
        
    def _load_config(self, config_path:str) -> Dict:
        # YAML 설정 파일을 읽어오는 내부 메서드
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 필수 키 검증
            required_keys = ['core_skills', 'general_backend']
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"설정 파일에 '{key}' 그룹이 없습니다.")
                
            return config

        except FileNotFoundError:
            print(f"\n❌ 오류: 설정 파일을 찾을 수 없습니다.")
            print(f"   찾는 경로: {os.path.abspath(config_path)}")
            print(f"   현재 작업 디렉토리: {os.getcwd()}")
            print(f"\n해결 방법:")
            print(f"   1. config/job_filter_config.yaml 파일이 있는지 확인하세요.")
            print(f"   2. 프로젝트 루트에서 실행하고 있는지 확인하세요.")
            raise
            
        except yaml.YAMLError as e:
            print(f"\n❌ 오류: YAML 파일 형식이 잘못되었습니다.")
            print(f"   {e}")
            raise
            
        except Exception as e:
            print(f"\n❌ 오류: 설정 파일 로딩 중 문제가 발생했습니다.")
            print(f"   {e}")
            raise

    
    def calculate_relevance_score(self, job_title: str, job_description: str) -> Tuple[bool, float]:
        """
        채용 공고의 관련도를 점수화합니다.
        
        개선 사항:
        - None/빈 문자열 예외 처리 추가
        - 매칭된 키워드 수를 고려한 점수 증폭
        - 정규화 로직 개선
        
        :param job_title: 채용 공고 제목
        :param job_description: 채용 공고 설명
        :return: (백엔드 직무 여부, 관련도 점수)
        """
        # 예외 처리
        if not job_title:
            job_title = ""
        if not job_description:
            job_description = ""
        
        full_text = f"{job_title} {job_description}".lower().strip()
        
        # 빈 텍스트 체크
        if not full_text or len(full_text) < 10:
            return False, 0.0
        
        # 1. 제외 키워드 우선 체크
        has_exclude = any(word in full_text for word in self.my_keywords['exclude'])
        
        # 핵심/일반 백엔드 키워드 체크
        core_keywords = (self.my_keywords['core_skills']['keywords'] + 
                        self.my_keywords['general_backend']['keywords'])
        is_backend_related = any(word in full_text for word in core_keywords)
        
        if has_exclude and not is_backend_related:
            return False, 0.0
        
        # 2. 가중치 기반 점수 계산 (개선: 매칭 키워드 수 고려)
        score = 0.0
        
        for group_name in self._score_groups:
            group = self.my_keywords[group_name]
            keywords = group['keywords']
            base_weight = group['weight']
            
            # 그룹 내 매칭된 키워드 수 계산
            matched_count = sum(1 for keyword in keywords if keyword in full_text)
            
            if matched_count > 0:
                # 매칭 키워드가 많을수록 점수 증가 (최대 1.5배)
                # 1개: 1.0배, 2개: 1.2배, 3개: 1.4배, 4개 이상: 1.5배
                multiplier = min(1.0 + (matched_count - 1) * 0.2, 1.5)
                score += base_weight * multiplier
        
        # 3. 최종 점수 정규화 (0.0 ~ 1.0)
        final_score = score / self._max_score if self._max_score > 0 else 0.0
        
        # 임계값: 0.25 (25% 이상)
        # - core_skills 1개: 3.0/9.0 ≈ 0.33 ✓
        # - general_backend 1개: 2.5/9.0 ≈ 0.28 ✓  
        # - growth_potential 1개: 2.0/9.0 ≈ 0.22 ✗
        is_relevant = final_score >= 0.25
        
        return is_relevant, round(final_score, 3)
    
    
    @lru_cache(maxsize=1000)
    def _normalize_keyword(self, keyword: str) -> str:
        """키워드 정규화 (캐싱)"""
        return keyword.lower().strip()
    
    
    def extract_matched_skills(self, job_description: str) -> List[str]:
        """
        공고 본문에서 매칭된 기술 키워드를 추출합니다.
        
        개선 사항:
        - 정규표현식 활용으로 정확도 향상
        - 중복 제거 및 정렬
        
        :param job_description: 채용 공고 설명
        :return: 매칭된 기술 키워드 리스트
        """
        if not job_description:
            return []
        
        text_lower = job_description.lower()
        found_skills = []
        
        # 검색 대상 키워드 (exclude 제외)
        all_keywords = []
        for group_name in self._score_groups:
            all_keywords.extend(self.my_keywords[group_name]['keywords'])
        
        # 단어 경계를 고려한 매칭 (더 정확)
        for skill in all_keywords:
            # 정규표현식 패턴: 단어 경계 내에서 매칭
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        # 중복 제거 및 정렬
        return sorted(list(set(found_skills)))
    
    
    def get_keyword_stats(self) -> Dict:
        """
        키워드 통계 정보 반환 (디버깅/모니터링용)
        
        :return: 키워드 그룹별 통계
        """
        stats = {}
        for group_name in self._score_groups:
            group = self.my_keywords[group_name]
            stats[group_name] = {
                'count': len(group['keywords']),
                'weight': group['weight'],
                'keywords': group['keywords']
            }
        
        stats['exclude_count'] = len(self.my_keywords['exclude'])
        stats['max_score'] = self._max_score
        
        return stats

