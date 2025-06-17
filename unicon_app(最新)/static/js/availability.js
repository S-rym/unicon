window.onload = function () {
  displayDate();

  fetch('/api/reservations')
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        const reservations = data.reservations;
        displayClassrooms(reservations);
        displayReservations(reservations);
      } else {
        console.error('予約情報取得失敗:', data.message);
        displayClassrooms([]);
        displayReservations([]);
      }
    })
    .catch(err => {
      console.error('予約情報の取得に失敗しました:', err);
      displayClassrooms([]);
      displayReservations([]);
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

// 時限判定と空き教室表示用（ここは仮で時限だけ表示）
function displayClassrooms(reservations) {
  // 固定時間 9:30に設定
  const currentHour = 9;
  const currentMinute = 30;
  const periodTitle = document.getElementById("period-title");

  let periodText = "";
  if ((currentHour === 9 && currentMinute >= 20) || (currentHour === 10) || (currentHour === 11 && currentMinute === 0)) {
    periodText = "一限の空き教室";
  } else if ((currentHour === 11 && currentMinute >= 10) || (currentHour === 12)) {
    periodText = "二限の空き教室";
  } else if ((currentHour === 13 && currentMinute >= 40) || (currentHour === 14) || (currentHour === 15 && currentMinute <= 20)) {
    periodText = "三限の空き教室";
  } else if ((currentHour === 15 && currentMinute >= 30) || (currentHour === 16) || (currentHour === 17 && currentMinute === 0)) {
    periodText = "四限の空き教室";
  } else if ((currentHour === 17 && currentMinute >= 10) || (currentHour === 18) || (currentHour === 19 && currentMinute === 0)) {
    periodText = "五限の空き教室";
  } else {
    periodTitle.innerText = "現在、空いている教室はありません";
    return;
  }

  periodTitle.innerText = periodText;
}

// 予約情報をリスト表示
function displayReservations(reservations) {
  const reservationList = document.getElementById('classroom-list'); // IDはHTMLに合わせて保持
  reservationList.innerHTML = "";  // 初期化

  if (!reservations || reservations.length === 0) {
    reservationList.innerHTML = "<li>予約情報がありません</li>";
    return;
  }

  // 予約データの形式に応じて修正してください（例: {classroom: "101", time: "9:20~11:00"}）
  reservations.forEach(res => {
  if (!res.classroom) return;  // classroomがないデータはスキップ

  const li = document.createElement('li');
  li.textContent = res.classroom;

  // タップできるようにする
  li.addEventListener('click', () => {
    alert(`${res.classroom} がタップされました`);
  });

  reservationList.appendChild(li);
});

}

