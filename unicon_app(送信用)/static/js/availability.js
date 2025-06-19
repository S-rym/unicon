window.onload = function () {
  displayDate();

  fetch('/api/reservations')
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        const reservations = data.reservations;
        displayClassrooms(reservations);
        setInterval(() => displayClassrooms(reservations), 60 * 1000); // 1分ごとに更新して再実行(追加)
      } else {
        console.error('予約情報取得失敗:', data.message);
        displayClassrooms([]);
      }
    })
    .catch(err => {
      console.error('予約情報の取得に失敗しました:', err);
      displayClassrooms([]);
    });
};

function displayDate() {
  const date = new Date();
  const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const currentDate = date.toLocaleDateString('ja-JP', options);
  const dayOfWeek = weekdays[date.getDay()];
  document.getElementById('current-date').textContent = `${currentDate} (${dayOfWeek})`;
}

// 時限判定と空き教室表示
function displayClassrooms(reservations) {
  const now = new Date();
  const currentHour = now.getHours(); 
  const currentMinute = now.getMinutes();
  const periodTitle = document.getElementById("period-title");

  let period = "";

  // 時限の判定ロジック（例：一限 9:20〜11:00など）
  if ((currentHour === 9 && currentMinute >= 20) || (currentHour === 10) || (currentHour === 11 && currentMinute === 0)) {
    period = "1時限";
  } else if ((currentHour === 11 && currentMinute >= 10) || (currentHour === 12)) {
    period = "2時限";
  } else if ((currentHour === 13 && currentMinute >= 40) || (currentHour === 14) || (currentHour === 15 && currentMinute <= 20)) {
    period = "3時限";
  } else if ((currentHour === 15 && currentMinute >= 30) || (currentHour === 16) || (currentHour === 17 && currentMinute === 0)) {
    period = "4時限";
  } else if ((currentHour === 17 && currentMinute >= 10) || (currentHour === 18) || (currentHour === 19 && currentMinute === 0)) {
    period = "5時限";
  } else {
    periodTitle.innerText = "現在、空いている教室はありません";
    displayReservations([]);  // 空リストを渡してリストをクリア
    return;
  }

  periodTitle.innerText = `${period}の空き教室`;

  // 対象の時限（period）に一致する予約のみフィルター
  const filtered = reservations.filter(res => res.classtime === period);
  displayReservations(filtered);
}

// 予約情報をリスト表示
function displayReservations(reservations) {
  const reservationList = document.getElementById('classroom-list');
  reservationList.innerHTML = ""; // 初期化

  if (!reservations || reservations.length === 0) {
    reservationList.innerHTML = "<li>予約情報がありません</li>";
    return;
  }

  reservations.forEach(res => {
    if (!res.classroom) return;

    const li = document.createElement('li');
    li.textContent = `${res.classroom}（${res.classtime}）`;

    li.addEventListener('click', () => {
      alert(`${res.classroom} がタップされました`);
    });

    reservationList.appendChild(li);
  });
}
