window.onload = function () {
  displayDate();

  // 空き教室情報取得
  fetch('/api/available_rooms')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        window._availableRooms = data.available_rooms;
        displayAvailableRoomsForCurrentPeriod();
        setInterval(() => displayAvailableRoomsForCurrentPeriod(), 60 * 1000);
      } else {
        console.error('空き教室情報取得失敗:', data.message);
        displayAvailableRooms([]);
      }
    })
    .catch(err => {
      console.error('空き教室情報の取得に失敗しました:', err);
      displayAvailableRooms([]);
    });
};

// 日付表示
function displayDate() {
  const date = new Date();
  const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const currentDate = date.toLocaleDateString('ja-JP', options);
  const dayOfWeek = weekdays[date.getDay()];
  document.getElementById('current-date').textContent = `${currentDate} (${dayOfWeek})`;
}

// 現在の時限を取得
function getCurrentPeriod() {
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  if ((currentHour === 9 && currentMinute >= 20) || (currentHour === 10) || (currentHour === 11 && currentMinute === 0)) {
    return "1時限";
  } else if ((currentHour === 11 && currentMinute >= 10) || (currentHour === 12)) {
    return "2時限";
  } else if ((currentHour === 13 && currentMinute >= 40) || (currentHour === 14) || (currentHour === 15 && currentMinute <= 20)) {
    return "3時限";
  } else if ((currentHour === 15 && currentMinute >= 30) || (currentHour === 16) || (currentHour === 17 && currentMinute === 0)) {
    return "4時限";
  } else if ((currentHour === 17 && currentMinute >= 10) || (currentHour === 18) || (currentHour === 19 && currentMinute === 0)) {
    return "5時限";
  } else {
    return null;
  }
}

// 現在の時限の空き教室を表示
function displayAvailableRoomsForCurrentPeriod() {
  const period = getCurrentPeriod();
  const periodTitle = document.getElementById("period-title");

  if (!period) {
    periodTitle.innerText = "現在、空いている教室はありません";
    displayAvailableRooms([]);
    return;
  }

  periodTitle.innerText = `${period}の空き教室`;

  const filtered = window._availableRooms?.filter(room => room.classtime === period) || [];
  displayAvailableRooms(filtered);
}

// 空き教室リストを表示
function displayAvailableRooms(rooms) {
  const list = document.getElementById('classroom-list');
  list.innerHTML = "";

  if (!rooms || rooms.length === 0) {
    list.innerHTML = "<li>空き教室情報がありません</li>";
    return;
  }

  rooms.forEach(room => {
    const li = document.createElement('li');
    li.textContent = `${room.building}号館 ${room.floor}階 ${room.classroom_number}（${room.classtime}）`;
    li.addEventListener('click', () => {
      alert(`${room.building}号館 ${room.floor}階 ${room.classroom_number} がタップされました`);
    });
    list.appendChild(li);
  });
}

// 時間割セルクリック時のメニュー表示・操作
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".timetable td").forEach((cell, index) => {
    cell.dataset.cellIndex = index;
    cell.addEventListener("click", (event) => {
      event.preventDefault();
      const menu = document.getElementById("action-menu");

      const today = new Date().getDay(); // 0: 日曜, 1: 月曜, ..., 6: 土曜
      const columnIndex = cell.cellIndex; // 1: 月, 2: 火, ..., 6: 土

      let menuHtml;

      if (today === 0) {
        // 日曜なら常に編集ボタンのみ
        menuHtml = `
          <button onclick="handleMenuSelect('edit')">編集</button>
        `;
      } else if (columnIndex === today) {
        // 曜日一致：すべてのボタン
        menuHtml = `
          <button onclick="handleMenuSelect('edit')">編集</button>
          <button onclick="handleMenuSelect('search')">検索</button>
          <button onclick="handleMenuSelect('reserve')">予約状況</button>
        `;
      } else {
        // 曜日不一致：編集のみ
        menuHtml = `
          <button onclick="handleMenuSelect('edit')">編集</button>
        `;
      }

      menu.innerHTML = menuHtml;
      menu.style.top = `${event.pageY}px`;
      menu.style.left = `${event.pageX}px`;
      menu.style.display = "block";
      window.targetCellElement = event.target;
    });
  });

  document.addEventListener("click", (e) => {
    const menu = document.getElementById("action-menu");
    if (!menu.contains(e.target) && !e.target.closest(".timetable td")) {
      menu.style.display = "none";
    }
  });
});

// メニュー選択処理
function handleMenuSelect(action) {
  const cell = window.targetCellElement;
  if (!cell) return;

  if (action === "edit") {
    cell.contentEditable = true;
    cell.focus();
    cell.addEventListener("blur", () => {
      cell.contentEditable = false;
    }, { once: true });
  } else if (action === "search") {
    const period = getPeriodFromCell(cell);
    if (period) {
      document.getElementById("period-title").innerText = `${period}の空き教室`;
      const filtered = window._availableRooms?.filter(room => room.classtime === period) || [];
      displayAvailableRooms(filtered);
    }
  } else if (action === "reserve") {
    alert("予約フォームをここに表示します（未実装）");
  }

  document.getElementById("action-menu").style.display = "none";
}

// セルから時限名を取得
function getPeriodFromCell(cell) {
  const tr = cell.closest("tr");
  if (!tr) return null;
  const th = tr.querySelector("th");
  if (!th) return null;
  return th.textContent.trim().replace("限", "時限");
}
