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

// PEM→ArrayBuffer変換
function pemToArrayBuffer(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PUBLIC KEY-----|\s/g, '');
  const binary = atob(b64);
  const buffer = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) buffer[i] = binary.charCodeAt(i);
  return buffer.buffer;
}

// 公開鍵インポート
async function importPublicKey(pem) {
  const keyData = pemToArrayBuffer(pem);
  return await window.crypto.subtle.importKey(
    'spki',
    keyData,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt']
  );
}

// 暗号化
async function encryptRSAOAEP(publicKey, text) {
  const enc = new TextEncoder();
  const data = enc.encode(text);
  const encrypted = await window.crypto.subtle.encrypt(
    { name: 'RSA-OAEP' },
    publicKey,
    data
  );
  return btoa(String.fromCharCode(...new Uint8Array(encrypted)));
}

document.addEventListener('DOMContentLoaded', () => {
  const params = getQueryParams();
  const errorMessage = params.error;
  const errorMessageDisplay = document.getElementById('errorMessage');

  if (errorMessage) {
    errorMessageDisplay.textContent = errorMessage;
  }

  const loginForm = document.getElementById('loginForm');
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const studentId = document.getElementById('studentId').value;
    const password = document.getElementById('password').value;

    if (!studentId || !password) {
      errorMessageDisplay.textContent = "学籍番号とパスワードを入力してください。";
      return;
    }

    // 暗号化
    try {
      //★★★★★★★★★★★★★★★★★★★★★★★★★★★
      //ここで公開鍵のpathを指定しているのでstaticフォルダにpublic_key.pemを配置してほしい
      const res = await fetch('/static/public_key.pem');
      //★★★★★★★★★★★★★★★★★★★★★★★★★★★
      const pem = await res.text();
      const pubKey = await importPublicKey(pem);
      const encryptedPw = await encryptRSAOAEP(pubKey, password);

      const encodedId = encodeURIComponent(studentId);
      const encodedPw = encodeURIComponent(encryptedPw);
      window.location.href = `/progress?studentId=${encodedId}&password=${encodedPw}`;
    } catch (err) {
      errorMessageDisplay.textContent = "暗号化に失敗しました。";
    }
  });

  document.getElementById('createAccountBtn').addEventListener('click', () => {
    window.location.href = "/account";
  });
});
