// 現在時刻から時限数を判定する関数
function getCurrentClasstime() {
  const now = new Date();
  const hhmmss = now.getHours() * 10000 + now.getMinutes() * 100 + now.getSeconds();

  const timeSlots = [
  { slot: '1', start: '9:20', end: '11:00' },
  { slot: '2', start: '11:00', end: '12:50' },
  { slot: '3', start: '12:50', end: '15:20' },
  { slot: '4', start: '15:20', end: '17:10' },
  { slot: '5', start: '17:10', end: '23:00' }
];

  for (const t of timeSlots) {
    if (hhmmss >= t.start && hhmmss <= t.end) {
      return t.slot;
    }
  }
  return null; // 時限外
}

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const errorMessageDisplay = document.getElementById('errorMessage');

  loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const studentId = document.getElementById('studentId').value;
  const passwordRaw = document.getElementById('password').value;
  const password = passwordRaw
  const classtime = 1//getCurrentClasstime(); //試験的に1限で固定できる

  /*if (!classtime) {
    errorMessageDisplay.textContent = '現在の時刻は授業時間外です。ログインできません。';
    return;
  }*/ //ログイン時間外無しにする。

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ studentId, password,  })  // password変数を使う classtimeを無しにしてみた
    });

      const data = await response.json();

      if (data.success) {
        errorMessageDisplay.textContent = '';
        alert('ログイン成功！');
        // 必要なら画面遷移など
        window.location.href = '/index';
      } else {
        errorMessageDisplay.textContent = data.message || 'ログインに失敗しました。';
      }
    } catch (error) {
      errorMessageDisplay.textContent = '通信エラーが発生しました。';
      console.error(error);
    }
  });
});
