// game.js

// URLパラメータから値を取得
function getQueryParams() {
  const params = {};
  window.location.search
    .substring(1)
    .split("&")
    .forEach(pair => {
      const [key, value] = pair.split("=");
      if (key) params[decodeURIComponent(key)] = decodeURIComponent(value || "");
    });
  return params;
}

// ログインAPIを呼ぶ関数
async function login(studentId, password) {
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ studentId, password })
    });
    return await response.json();
  } catch (e) {
    return { success: false, message: '通信エラーが発生しました。' };
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  const params = getQueryParams();
  const studentId = params.studentId;
  const password = params.password;

  if (!studentId || !password) {
    document.body.innerHTML = '<h2 style="color: white; text-align:center;">IDまたはパスワードが不足しています</h2>';
    return;
  }

  const data = await login(studentId, password);

  if (data.success) {
    // ログイン成功したらトップページへ遷移
    window.location.href = '/index';
  } else {
    // ログイン失敗時はメッセージ表示のあと3秒後にログインページへ戻る（メッセージをURLパラメータで渡す）
    document.body.innerHTML = `<h2 style="color: white; text-align:center;">ログイン失敗: ${data.message}</h2>`;
    setTimeout(() => {
      const encodedMessage = encodeURIComponent(data.message);
      window.location.href = `/?error=${encodedMessage}`;
    }, 3000);
  }
});
