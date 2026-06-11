# Application Tier 컨테이너 이미지
FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 설치 (캐시 활용 → 코드만 바뀌면 재설치 안 함)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY app.py .

# Flask 가 사용하는 포트
EXPOSE 5000

CMD ["python", "app.py"]
