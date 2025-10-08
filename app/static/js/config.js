/**
 * Логика страницы настроек: подключение к WebSocket /control,
 * отправка команд и отображение статуса.
 */

document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const coefInput = document.getElementById("coef");
  const colorSelect = document.getElementById("color");
  const tokenInput = document.getElementById("token");
  const setBtn = document.getElementById("setBtn");

  // WebSocket для управления
  const ws = new WebSocket(`ws://${window.location.host}/control`);

  ws.onopen = () => {
    statusEl.textContent = "Соединение установлено";
  };

  ws.onmessage = (e) => {
    // Выводим сообщения от сервера в статус
    statusEl.textContent = e.data;
  };

  ws.onclose = () => {
    statusEl.textContent = "Соединение закрыто";
  };

  // Кнопка "Установить коэффициент"
  setBtn.addEventListener("click", () => {
    const coef = coefInput.value.trim();
    if (coef) {
      ws.send(`coef ${coef}`);
    }
  });

  // Изменение цвета
  colorSelect.addEventListener("change", () => {
    const col = colorSelect.value;
    ws.send(`color ${col}`);
  });

  // Отправка access_token
  tokenInput.addEventListener("blur", () => {
    const token = tokenInput.value.trim();
    if (token) {
      ws.send(`token ${token}`);
    }
  });
});
