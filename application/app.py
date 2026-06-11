"""
============================================================
Application Tier (Flask 백엔드 서버)
역할:
  1) nginx가 전달한 클라이언트 요청 처리
  2) 비즈니스 로직 = 1~45 중 6개 번호 자동 추첨
  3) MySQL(Data Tier)에 결과 저장 / 기록 조회 후 결과 반환
============================================================
"""

import os
import time
import random

import pymysql
from flask import Flask, jsonify

app = Flask(__name__)

# ----------------------------------------------------------
# DB 접속 정보: docker-compose 의 environment 로 주입된 값을 읽음
# (코드에 비밀번호를 하드코딩하지 않기 위함)
# ----------------------------------------------------------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "user": os.environ.get("DB_USER", "lottouser"),
    "password": os.environ.get("DB_PASSWORD", "lottopass"),
    "database": os.environ.get("DB_NAME", "lotto"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection(retries: int = 10, delay: int = 3):
    """
    MySQL 컨테이너는 부팅에 시간이 걸려서, 앱이 먼저 떠 있으면
    연결이 실패할 수 있다. 그래서 몇 번 재시도한다.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return pymysql.connect(**DB_CONFIG)
        except pymysql.err.OperationalError as e:
            last_error = e
            print(f"[DB] 연결 실패 ({attempt}/{retries}) -> {delay}초 후 재시도")
            time.sleep(delay)
    raise last_error


def draw_numbers():
    """
    비즈니스 로직: 1~45 중에서 중복 없이 6개를 뽑아 오름차순 정렬.
    이 함수 하나만 따로 테스트할 수 있도록 분리해 둠.
    """
    return sorted(random.sample(range(1, 46), 6))


# ----------------------------------------------------------
# API 1) 번호 생성: 6개 추첨 -> DB 저장 -> 결과 반환
# ----------------------------------------------------------
@app.route("/api/generate", methods=["POST"])
def generate():
    numbers = draw_numbers()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO lotto_results (n1, n2, n3, n4, n5, n6) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                numbers,
            )
            conn.commit()
            new_round = cur.lastrowid  # 방금 저장된 회차 번호
    finally:
        conn.close()

    return jsonify({"round": new_round, "numbers": numbers})


# ----------------------------------------------------------
# API 2) 기록 조회: 최근 추첨 결과 목록 반환 (회차 / 번호 6개)
# ----------------------------------------------------------
@app.route("/api/history", methods=["GET"])
def history():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT round, n1, n2, n3, n4, n5, n6, created_at "
                "FROM lotto_results ORDER BY round DESC LIMIT 20"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "round": row["round"],
                "numbers": [row["n1"], row["n2"], row["n3"],
                            row["n4"], row["n5"], row["n6"]],
                "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return jsonify(results)


# ----------------------------------------------------------
# 헬스 체크 (nginx/디버깅용)
# ----------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # 0.0.0.0 으로 떠야 컨테이너 밖(다른 컨테이너)에서 접근 가능
    app.run(host="0.0.0.0", port=5000)
