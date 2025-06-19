document.addEventListener('DOMContentLoaded', () => {
  // data-name属性を持つgタグをすべて取得
  const buildings = document.querySelectorAll('g[data-name]');
  
  buildings.forEach(building => {
    building.addEventListener('click', () => {
      const name = building.getAttribute('data-name');
      alert(name + 'がクリックされました');
      // ここにクリック時の処理を追加（例：ページ遷移など）
      // window.location.href = /building/${name};
    });
    building.style.cursor = 'pointer'; // ポインターに変えると分かりやすい
  });
}); 