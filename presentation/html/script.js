/* ============================================================
   프론트엔드 동작
   - "번호 생성하기" 클릭 -> POST /api/generate
   - 페이지 로드 시 -> GET /api/history 로 기록 표시
   API 주소는 nginx 가 같은 도메인의 /api/ 로 받아 Flask 로 넘겨줌
   ============================================================ */

const generateBtn = document.getElementById("generateBtn");
const ballsEl      = document.getElementById("balls");
const roundLabel   = document.getElementById("roundLabel");
const historyList  = document.getElementById("historyList");

// 공식 로또 공 색상 규칙 (번호 구간별 색)
function ballColor(n) {
  if (n <= 10) return "#fbc400"; // 노랑
  if (n <= 20) return "#69c8f2"; // 파랑
  if (n <= 30) return "#ff7272"; // 빨강
  if (n <= 40) return "#aaaaaa"; // 회색
  return "#b0d840";              // 초록 (41~45)
}

// 메인 추첨 결과 6개 공 그리기 (튀어나오는 애니메이션 포함)
function renderBalls(numbers) {
  ballsEl.innerHTML = "";
  numbers.forEach((n, i) => {
    const ball = document.createElement("span");
    ball.className = "ball pop";
    ball.style.background = ballColor(n);
    ball.style.animationDelay = `${i * 0.08}s`; // 하나씩 순서대로
    ball.textContent = n;
    ballsEl.appendChild(ball);
  });
}

// 번호 생성 요청
async function generate() {
  generateBtn.disabled = true;
  generateBtn.textContent = "추첨 중…";
  try {
    const res = await fetch("/api/generate", { method: "POST" });
    if (!res.ok) throw new Error("서버 응답 오류");
    const data = await res.json();

    renderBalls(data.numbers);
    roundLabel.textContent = `${data.round}회차 추첨 결과`;
    await loadHistory(); // 기록 갱신
  } catch (err) {
    roundLabel.textContent = "추첨에 실패했어요. 잠시 후 다시 시도해 주세요.";
    console.error(err);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "번호 생성하기";
  }
}

// 기록 목록 그리기
function renderHistory(items) {
  if (!items.length) {
    historyList.innerHTML =
      '<li class="history-empty">아직 추첨 기록이 없어요.</li>';
    return;
  }
  historyList.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "history-item";

    const miniBalls = item.numbers
      .map(
        (n) =>
          `<span class="mini-ball" style="background:${ballColor(n)}">${n}</span>`
      )
      .join("");

    li.innerHTML = `
      <span class="history-round">${item.round}회차</span>
      <span class="history-balls">${miniBalls}</span>
      <span class="history-time">${item.created_at}</span>
    `;
    historyList.appendChild(li);
  });
}

// 기록 불러오기
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) throw new Error("기록 조회 오류");
    renderHistory(await res.json());
  } catch (err) {
    historyList.innerHTML =
      '<li class="history-empty">기록을 불러오지 못했어요.</li>';
    console.error(err);
  }
}

generateBtn.addEventListener("click", generate);
loadHistory(); // 처음 페이지 열 때 기록 표시
