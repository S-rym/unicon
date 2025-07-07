document.addEventListener("DOMContentLoaded", () => {
  const date = new Date();
  const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const currentDate = date.toLocaleDateString('ja-JP', options);
  const dayOfWeek = weekdays[date.getDay()];
  const el = document.getElementById('current-date');
  if (el) {
    el.textContent = `${currentDate} (${dayOfWeek})`;
  }
});
