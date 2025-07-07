document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const errorMessageDisplay = document.getElementById('errorMessage');

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const studentId = document.getElementById('studentId').value;
    const password = document.getElementById('password').value;

    // 🌿 game.html にリダイレクトして、クエリにIDとパスワードを含めて渡す
    window.location.href = `/game?studentId=${encodeURIComponent(studentId)}&password=${encodeURIComponent(password)}`;
  });
});
