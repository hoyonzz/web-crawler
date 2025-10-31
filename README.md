# 🤖 채용 공고 자동 분석 파이프라인 v1.0 (Job Posting Analysis Pipeline)

신입 백엔드 개발자 '신호용'의 성공적인 취업을 돕기 위해, 여러 채용 플랫폼의 공고를 매일 자동으로 수집하고 개인화된 기준으로 분석하여 Notion DB에 저장하는 자동화 파이프라인 프로젝트입니다.

---

## 🌟 1. 핵심 기능 (Core Features)

- **🌐 다중 사이트 동시 크롤링:** `원티드`, `잡코리아`, `사람인`의 신입 백엔드 채용 공고를 안정적으로 동시 수집합니다.
- **⚙️ 2단계 개인화 필터링:**
    1.  **1차 점수 필터링:** `YAML` 설정 기반의 가중치 모델을 통해, 수백 개의 공고 중 나와 기술적으로 관련된 공고만 1차 선별합니다.
    2.  **2차 AI 심층 분석:** Google `Gemini 2.0 Flash` API를 활용하여, 선별된 공고의 핵심 역할, 요구 기술, 개인 적합도를 심층 분석하여 구조화된 JSON으로 생성합니다.
- **💾 Notion DB 자동화:**
    - 모든 수집 및 분석 결과를 지정된 Notion 데이터베이스에 중복 없이 자동으로 기록합니다.
    - **칸반 보드(Kanban Board)** 와 연동하여 `[📥 새로 수집됨]`, `[👀 검토 중]`, `[✅ 지원 완료]` 등 채용 과정을 시각적으로 관리할 수 있습니다.
- **🚀 서버리스 완전 자동화:** `GitHub Actions`를 통해 매일 정해진 시간에 전체 프로세스를 서버에서 자동으로 실행하여, 별도의 서버 관리 없이 운영됩니다.

---

## 🛠️ 2. 기술 스택 (Tech Stack)

| Category | Technology |
| :--- | :--- |
| **Language** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) |
| **Crawling** | ![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white) ![Beautiful Soup](https://img.shields.io/badge/Beautiful_Soup-404040?style=for-the-badge&logo=readthedocs&logoColor=white) |
| **AI & API** | ![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B9?style=for-the-badge&logo=google-gemini&logoColor=white) ![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white) |
| **Automation**| ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white) |
| **Config & Test** | ![YAML](https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white) ![Pytest](https://img.shields.io/badge/Pytest-0A9B53?style=for-the-badge&logo=pytest&logoColor=white) |

---

## 🏗️ 3. 시스템 아키텍처 (System Architecture)

본 시스템은 4단계의 파이프라인 구조로 동작하며, 각 단계는 데이터를 정제하고 가치를 더하는 역할을 수행합니다.

**`[ 1. 수집 (Collect) ]` -> `[ 2. 선별 (Filter) ]` -> `[ 3. 분석 (Analyze) ]` -> `[ 4. 저장 (Store) ]`**

1.  **수집 (Collect Phase):**
    -   **Input:** `백엔드`, `신입` 키워드
    -   **Process:** `Selenium`을 이용하여 3개의 채용 사이트에 접속, 동적 페이지(무한 스크롤, 더보기 버튼)를 처리하며 각 공고의 제목, 회사명, 상세 페이지 URL 등 기본 정보를 `BeautifulSoup`으로 추출합니다.
    -   **Output:** 통합된 형태의 기본 공고 정보 리스트 (List of Dictionaries)

2.  **선별 (Filter Phase):**
    -   **Input:** 기본 공고 정보 리스트, 상세 페이지 본문
    -   **Process:**
        -   **DB 중복 검사:** Notion DB API를 호출하여 이미 저장된 공고인지 확인하고, 신규 공고만 다음 단계로 전달합니다.
        -   **1차 점수화:** `job_filter_config.yaml`에 정의된 개인화 기술 키워드와 가중치를 바탕으로 각 공고의 '기술 관련도'를 점수화합니다. 기준 점수 미달 공고는 이 단계에서 탈락시켜 불필요한 AI API 호출을 방지합니다.
    -   **Output:** '신호용'과 기술적으로 관련성이 높은 신규 공고 리스트

3.  **분석 (Analyze Phase):**
    -   **Input:** 관련성 높은 신규 공고 리스트 (제목, 본문, 추출된 기술 키워드)
    -   **Process:** `Google Gemini API`에 개인 프로필과 공고 정보를 포함한 정교한 프롬프트를 전송합니다. AI는 공고를 심층 분석하여 요구 경력, 핵심 역할, 필요/학습 기술, 개인 적합도 점수 및 이유 등을 담은 구조화된 `JSON` 데이터를 생성합니다.
    -   **Output:** AI가 생성한 개인 맞춤형 분석 결과 (JSON Object)

4.  **저장 (Store Phase):**
    -   **Input:** 수집된 모든 정보와 AI 분석 결과
    -   **Process:** `notion-client`를 사용하여 최종 데이터를 Notion DB의 각 속성에 맞게 매핑하고, 새로운 페이지를 생성하여 저장합니다.
    -   **Output:** '상태' 관리가 가능한 칸반 보드가 포함된 최종 Notion 데이터베이스

---

## 🚀 6. 향후 계획 (v2.0 Roadmap)

v1.0의 안정적인 운영을 기반으로, '개인화 채용 비서'를 더욱 지능적으로 만들기 위한 다음 고도화 작업을 계획하고 있습니다.

-   **[ ] 🎯 필터 및 AI 모델 정교화 (Model Refinement):**
    -   **'정답 데이터' 기반 튜닝:** 직접 선별한 17개의 '정답 공고' 데이터셋을 기준으로, `job_filter_config.yaml`의 키워드와 가중치를 최적화하여 필터링 정확도 향상.
    -   **'소프트 기준' 평가 추가:** AI 프롬프트를 고도화하여 기술 외적인 요소(기업 비전, 근무 환경, 지리적 위치, 고용 형태 등)까지 종합적으로 분석하고 평가하는 기능 추가.
-   **[ ] 🔔 알림 및 리포팅 기능 (Notification & Reporting):**
    -   **일일 브리핑:** 매일 아침, 새로 추가된 공고의 핵심 요약 정보를 이메일이나 슬랙(Slack) 등 지정된 채널로 전송하는 알림 기능 구현.
    -   **주간 리포트:** 한 주간 수집된 공고의 통계(예: 가장 많이 요구된 기술 Top 5, 나의 관심사와 일치하는 공고 비율 등)를 시각화하여 제공.
-   **[ ] 🛡️ 시스템 안정성 강화 (System Robustness):**
    -   **크롤러 모니터링:** 특정 사이트의 HTML 구조 변경으로 인해 크롤링이 연속적으로 실패할 경우, 자동으로 알림을 보내는 모니터링 시스템 구축.
    -   **Dead Letter Queue:** AI 분석에 실패하거나 Notion 저장에 실패한 공고를 별도의 로그 파일이나 DB에 기록하여, 나중에 수동으로 재처리할 수 있는 '실패 큐' 구현.

```
