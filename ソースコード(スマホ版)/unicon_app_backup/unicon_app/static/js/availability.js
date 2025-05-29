window.onload = function () {
  displayDate();
  displayClassrooms();
};

function displayDate() {
  const date = new Date();
  const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const currentDate = date.toLocaleDateString('ja-JP', options);
  const dayOfWeek = weekdays[date.getDay()];
  document.getElementById('current-date').textContent = `${currentDate} (${dayOfWeek})`;
}

function displayClassrooms() {
  const currentHour = new Date().getHours();
  const classroomList = document.getElementById("classroom-list");
  const periodTitle = document.getElementById("period-title");

  // 実際の空き教室情報（"第一食堂" や "9号館ラウンジ"は除外）
  const classroomData = {
    "first": ["12号館1202室", "9号館6階教室", "12号館304室"],
    "second": ["12号館202室", "9号館305室", "12号館503室"],
    "third": ["12号館503室", "9号館201室", "12号館301室"]
  };

  let period = "";
  if (currentHour >= 9 && currentHour < 11) {
    period = "first";
    periodTitle.innerText = "一限の空き教室";
  } else if (currentHour >= 11 && currentHour < 13) {
    period = "second";
    periodTitle.innerText = "二限の空き教室";
  } else if (currentHour >= 13 && currentHour < 15) {
    period = "third";
    periodTitle.innerText = "三限の空き教室";
  } else if (currentHour >= 15 && currentHour < 17) {
    period = "third";
    periodTitle.innerText = "四限の空き教室";
  } else if (currentHour >= 17 && currentHour < 19) {
    period = "third";
    periodTitle.innerText = "五限の空き教室";
  } else {
    periodTitle.innerText = "現在、空いている教室はありません";
    classroomList.innerHTML = "";
    return;
  }

  // 現在の時間帯に対応する空き教室リスト
  const availableClassrooms = classroomData[period];
  classroomList.innerHTML = "";
  availableClassrooms.forEach(room => {
    const li = document.createElement("li");
    li.textContent = room;
    classroomList.appendChild(li);
  });
}
