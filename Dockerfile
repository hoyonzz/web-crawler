# Dockerfile

# 1. Base Image: 가벼운 파이썬 3.12 슬림 버전 사용
FROM python:3.12-slim

# 2. 작업 디렉토리 지정
WORKDIR /app

# 3. 크롬 및 시스템 패키지 설치 블록
RUN apt-get update && apt-get install -y chromium chromium-driver && rm -rf /var/lib/apt/lists/*

# 4. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 전체 코드 복사
COPY . .

# 6. 기본 실행 명령어
CMD ["echo", "Ready for the next step!"]