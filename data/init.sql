-- ============================================================
-- Data Tier 초기화 스크립트
-- MySQL 컨테이너가 처음 뜰 때 /docker-entrypoint-initdb.d 에서 자동 실행됨
-- 역할: 로또 추첨 결과를 저장할 테이블을 만든다
-- ============================================================

USE lotto;

-- 추첨 결과 저장 테이블
-- round  : 회차 (자동 증가 → 추첨할 때마다 1, 2, 3 ... 으로 늘어남)
-- n1~n6  : 추첨된 6개 번호 (1~45, 오름차순 정렬해서 저장)
-- created_at : 추첨한 시각
CREATE TABLE IF NOT EXISTS lotto_results (
    round       INT AUTO_INCREMENT PRIMARY KEY,
    n1          INT NOT NULL,
    n2          INT NOT NULL,
    n3          INT NOT NULL,
    n4          INT NOT NULL,
    n5          INT NOT NULL,
    n6          INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
