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

document.addEventListener('DOMContentLoaded', () => {
  const params = getQueryParams();
  const errorMessage = params.error;
  const errorMessageDisplay = document.getElementById('errorMessage');

  if (errorMessage) {
    errorMessageDisplay.textContent = errorMessage;
  }

  const loginForm = document.getElementById('loginForm');
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const studentId = document.getElementById('studentId').value;
    const password = document.getElementById('password').value;

    if (!studentId || !password) {
      errorMessageDisplay.textContent = "学籍番号とパスワードを入力してください。";
      return;
    }

    // 🔁 ここで /progress に遷移し、クエリでIDとパスワードを渡す
    const encodedId = encodeURIComponent(studentId);
    const encodedPw = encodeURIComponent(password);
    window.location.href = `/progress?studentId=${encodedId}&password=${encodedPw}`;
  });

  document.getElementById('createAccountBtn').addEventListener('click', () => {
    window.location.href = "/account";
  });
});
