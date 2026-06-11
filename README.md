# 로또 번호 자동 생성기 (Docker 3-Tier 프로젝트)
버튼을 누르면 1~45 중 6개 번호를 자동 추첨하고, 결과를 DB에 저장하며,
지금까지의 추첨 기록을 회차별로 보여 줍니다.

---

## 1. 3-tier 구조 설명

| 계층 (Tier) | 서비스(컨테이너) | 기술 | 역할 |
|---|---|---|---|
| **Presentation** | `web` | nginx | 사용자 화면(프론트엔드) 제공, 클라이언트 요청 수신, API 요청을 백엔드로 전달 |
| **Application** | `app` | Python / Flask | 비즈니스 로직(번호 6개 추첨), DB 연결 및 결과 저장·조회, 결과 반환 |
| **Data** | `db` | MySQL | 추첨 결과 저장, 기록(회차·번호) 조회를 위한 데이터 보관 |

- **Presentation = `presentation/` 폴더** : 사용자가 보는 화면과 nginx 설정
- **Application = `application/` 폴더** : Flask 백엔드 코드
- **Data = `data/` 폴더** : DB 초기화(테이블 생성) 스크립트

---

## 2. 시스템 흐름도

```
        [ 사용자 브라우저 ]
               │
               │  http://localhost:8080
               ▼
   ┌──────────────────────────────┐
   │  web  (nginx)                 │   ← Presentation Tier
   │  · HTML/CSS/JS 화면 서빙        │
   │  · /api/ 요청은 app 으로 프록시 │
   └───────────────┬──────────────┘
                   │  /api/...   (내부 네트워크 lotto-net)
                   ▼
   ┌──────────────────────────────┐
   │  app  (Flask)                 │   ← Application Tier
   │  · 1~45 중 6개 자동 추첨        │
   │  · 결과 DB 저장 / 기록 조회     │
   └───────────────┬──────────────┘
                   │  MySQL 3306 (내부 네트워크 lotto-net)
                   ▼
   ┌──────────────────────────────┐
   │  db  (MySQL)                  │   ← Data Tier
   │  · lotto_results 테이블        │
   └──────────────────────────────┘
```

**요청 한 번의 흐름 (번호 생성 클릭 시)**

1. 사용자가 "번호 생성하기" 클릭 → 브라우저가 `POST /api/generate` 호출
2. nginx(`web`)가 받아서 `app`(Flask)으로 전달
3. Flask가 1~45 중 6개를 추첨하고 `db`(MySQL)에 저장
4. 저장된 회차 번호와 추첨 번호를 JSON으로 반환
5. 화면이 공(ball)으로 결과를 표시하고, 기록 목록을 갱신

---

## 3. 각 컨테이너의 역할

### `web` — nginx (Presentation)
- `presentation/html/`의 화면 파일(`index.html`, `style.css`, `script.js`)을 서빙
- `/api/`로 들어온 요청은 `app:5000`(Flask)으로 **리버스 프록시**
  → 브라우저는 백엔드 주소를 몰라도 되고, 같은 출처(`localhost:8080`)로만 통신

### `app` — Flask (Application)
- `POST /api/generate` : 6개 번호 추첨 → DB 저장 → 결과 반환
- `GET /api/history` : 최근 추첨 기록 20건 반환
- `GET /api/health` : 동작 확인용
- 추첨 로직: `random.sample(range(1,46), 6)` 으로 중복 없이 6개를 뽑아 오름차순 정렬
- DB 접속 정보는 코드에 박지 않고 **환경변수**로 주입받음

### `db` — MySQL (Data)
- 컨테이너 최초 실행 시 `data/init.sql`이 자동 실행되어 `lotto_results` 테이블 생성
- 데이터는 `db-data` 볼륨에 저장되어 **컨테이너를 내려도 기록이 유지**됨

**테이블 구조 (`lotto_results`)**

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `round` | INT (PK, auto increment) | 회차 (추첨할 때마다 1씩 증가) |
| `n1`~`n6` | INT | 추첨된 6개 번호 (오름차순) |
| `created_at` | TIMESTAMP | 추첨 시각 |

---

## 4. 컨테이너 간 연결 방식

- 세 컨테이너는 docker-compose가 만드는 내부 네트워크 `lotto-net`으로 연결됩니다.
- 같은 네트워크 안에서는 서비스 이름이 곧 호스트명이 됩니다.
  - nginx 설정에서 `proxy_pass http://app:5000;` → `app` = Flask 컨테이너
  - Flask 환경변수 `DB_HOST=db` → `db` = MySQL 컨테이너
- 외부(호스트)에 열려 있는 포트는 `web`의 8080 하나뿐입니다.
  `app`(5000)과 `db`(3306)는 내부에서만 통신하므로 보안상 더 안전합니다.
- 실행 순서 보장:
  - `app`은 `db`가 healthy 상태가 된 뒤에 시작 (`depends_on` + `healthcheck`)
  - 그래도 생길 수 있는 짧은 타이밍 문제를 대비해, Flask는 DB 연결을 재시도합니다.

---

## 5. 사용 포트 및 주요 설정

| 항목 | 값 |
|---|---|
| 접속 주소 | `http://localhost:8080` |
| 외부 노출 포트 | `8080` → `web`(nginx) 컨테이너의 80 |
| 내부 포트 | Flask `5000`, MySQL `3306` (외부 비공개) |
| MySQL DB 이름 | `lotto` |
| MySQL 앱 계정 | `lottouser` / `lottopass` |
| 데이터 영속화 | `db-data` 볼륨 |

---

## 6. 실행 방법

사전 준비: **Docker**와 **Docker Compose**가 설치되어 있어야 합니다.

```bash
# 1. 프로젝트 폴더로 이동
cd lotto-3tier

# 2. 전체 시스템 빌드 + 실행 (3개 컨테이너가 함께 뜸)
docker compose up --build

# 3. 브라우저에서 접속
#    http://localhost:8080
```

종료 / 정리:

```bash
# 종료 (Ctrl+C 후)
docker compose down

# 데이터(추첨 기록)까지 완전히 삭제하려면
docker compose down -v
```

---

## 7. API 명세

| 메서드 | 경로 | 설명 | 응답 예시 |
|---|---|---|---|
| POST | `/api/generate` | 번호 추첨 후 저장 | `{ "round": 3, "numbers": [5,12,23,34,38,44] }` |
| GET | `/api/history` | 최근 기록 조회 | `[ { "round":3, "numbers":[...], "created_at":"..." }, ... ]` |
| GET | `/api/health` | 상태 확인 | `{ "status": "ok" }` |

---

## 8. 디렉토리 구조

```
lotto-3tier/
├── docker-compose.yml        # 3개 컨테이너를 묶어 함께 실행
├── README.md                 # 본 문서
├── AI_PROMPT_USAGE.md        # AI 프롬프트 사용 내역
│
├── presentation/             # ── Presentation Tier (nginx)
│   ├── Dockerfile
│   ├── nginx.conf            # 화면 서빙 + /api 프록시 설정
│   └── html/
│       ├── index.html
│       ├── style.css
│       └── script.js
│
├── application/              # ── Application Tier (Flask)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py                # 추첨 로직 + API
│
└── data/                     # ── Data Tier (MySQL)
    └── init.sql              # 테이블 생성 스크립트
```