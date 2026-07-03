import re
import yaml
from pathlib import Path



class PersonalizedJobFilter:
    """
    포트폴리오 기반 개인화된 채용 공고 필터.
    YAML 설정을 동적으로 로드하고, 스마트 매칭 알고리즘을 통해 관련도 점수를 평가하는 ETL 파이프라인의 Transform 핵심엔진
    """

    def __init__(self, config_path: str = None):
        # 1. 경로 설정
        if config_path is None:
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / 'config' / 'job_filter_config.yaml'

        # 2. 설정 로드(관심사 분리: 파일 읽기 전담 메서드 호출)
        self.config = self._load_config(str(config_path))
        self.filter_rules = self.config.get('filter_rules', {})

        # 3. YAML 데이터 구조화 및 메모리 할당
        self.threshold = self.filter_rules.get('threshold', 5.0)

        self.score_groups = {}
        self.exclude_absolute = []
        self.exclude_conditional = []

        # YAML의 딕셔너리를 순회하며 목적에 맞게 변수에 분배
        for key, value in self.filter_rules.items():
            if key == 'threshold':
                continue
            elif key == 'exclude_absolute':
                self.exclude_absolute = [k.lower() for k in value]
            elif key == 'exclude_conditional':
                self.exclude_conditional = value
            elif isinstance(value, dict) and 'weight' in value and 'keywords' in value:
                self.score_groups[key] = {
                    'weight' : value['weight'],
                    'keywords' : [k.lower() for k in value['keywords']]
                }

    def _load_config(self, config_path: str) -> dict:
        """
        YAML 파일을 읽어 딕셔너리로 반환하는 내부(Private)메서드.
        Fail-Fast 원칙을 적용하여 I/O 예외를 엄격하게 통제합니다.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 데이터 정합성 필수 검증(뼈대 그룹이 없으면 실행 자체를 막음)
            if not config or 'filter_rules' not in config:
                raise ValueError("설정 파일에 핵심 그룹인 'filter_rules'가 누락 되었습니다.")
            
            return config

        except FileNotFoundError:
            print(f"\n❌ [치명적 오류] 설정 파일을 찾을 수 없습니다.")
            print(f" 💡 시스템이 찾는 경로: {config_path}")
            raise

        except yaml.YAMLError as e:
            print(f"\n❌ [치명적 오류] YAML 파일의 들여쓰기나 문법이 잘못되었습니다.")
            print(f" 💡 상세 에러: {e}")
            raise

        except Exception as e:
            print(f"\n❌ [치명적 오류] 설정 파일 로딩 중 알 수 없는 문제가 발생했습니다.")
            print(f" 💡 상세 에러: {e}")
            raise

    def _contains(self, text:str, keyword: str) -> bool:
        """
        영문/숫자는 전후방 탐색으로, 한글은 단순 포함(in)으로 매칭
        """
        kw = keyword.lower()

        # 1. 아스키코드(영문, 숫자 등)인 경우 -> 단어 경계 매칭
        if kw.isascii():
            pattern = rf'(?<![a-zA-Z]){re.escape(kw)}(?![a-zA-Z])'
            return re.search(pattern, text) is not None
        
        # 2. 한글이 섞인 경우 -> 단순 포함 검색
        return kw in text
    
    def calculate_relevance_score(self, job_title: str, job_description: str) -> tuple[bool, float]:
        """
        Guard Clause(입구 컷) 패턴을 적용하여 제외 공고를 빠르게 걸러내고,
        절대 평가(threshold)방식으로 점수를 판정합니다.
        """
        job_title = job_title or ""
        job_description = job_description or ""
        full_text = f"{job_title} {job_description}".lower().strip()
        
        if len(full_text) < 10:
            return False, 0.0
        
        # [Guard 1] 절대 제외 룰 (무조건 입구 컷)
        if any(self._contains(full_text, w) for w in self.exclude_absolute):
            return False, 0.0
        
        # [Guard 2] 조건부 제외 룰 (핵심 스택 부재 + 특정 생태계 요구)
        for rule in self.exclude_conditional:
            missing_all = not any(self._contains(full_text, w) for w in rule.get('if_missing_all', []))
            present_any = any(self._contains(full_text, w) for w in rule.get('and_present_any', []))

            if missing_all and present_any:
                return False, 0.0
            
        # [Scoring] 가중치 점수 합산 (Guard를 무사히 통과한 공고만 연산)
        raw_score = 0.0
        for group in self.score_groups.values():
            keywords = group['keywords']
            base_weight = group['weight']

            # 매칭된 키워드 개수 산출
            matched_count = sum(1 for kw in keywords if self._contains(full_text, kw))

            raw_score += (matched_count * base_weight)


        # [Final 판정] YAML에 명시된 threshold (5.0) 절대값 비교 (max_score 나누기 제거!)
        is_relevant = raw_score >= self.threshold

        # 점수 정규화
        TARGET_MAX_SCORE = 25.0
        normalized_score = min(raw_score / TARGET_MAX_SCORE, 1.0)

        return is_relevant, round(normalized_score, 3)

    def extract_matched_skills(self, job_description, job_title=None):
        """
        (Notion 태그용)공고 본문에서 실제로 매칭된 기술 키워드 리스트 추출
        """
        job_title = job_title or ""
        job_description = job_description or ""

        full_text = f"{job_title} {job_description}".lower().strip()

        if len(full_text) < 10:
            return []

        found_skills = []

        for group in self.score_groups.values():
            for kw in group['keywords']:
                if self._contains(full_text, kw):
                    found_skills.append(kw)

        return sorted(list(set(found_skills)))
    
    def get_keyword_stats(self) -> dict:
        """
        (디버깅/모니터링용) 현재 시스템에 로드된 키워드 통계 반환
        """
        stats = {}
        for name, group in self.score_groups.items():
            stats[name] = {
                'count' : len(group['keywords']),
                'weight' : group['weight']
            }

        stats['exclude_absolute_count'] = len(self.exclude_absolute)
        stats['threshold'] = self.threshold
        return stats
