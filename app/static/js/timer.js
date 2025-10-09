// Подключение к WebSocket для таймера
const timerWS = new WebSocket(`ws://${location.host}/ws`);
// Подключение к WebSocket для конфигурации (цвет и т.п.)
const colorWS = new WebSocket(`ws://${location.host}/timer_cfg`);

const timerEl = document.getElementById("timer");

// Получаем обновления времени от сервера
timerWS.onmessage = (event) => {
  if (timerEl) {
    timerEl.textContent = event.data;
  }
};

// Получаем обновления цвета от сервера
colorWS.onmessage = (event) => {
  if (timerEl) {
    const color = event.data;
    timerEl.style.color = color;
  }
};

// Обработка ошибок соединения (для отладки)
timerWS.onerror = (err) => {
  console.error("Ошибка WebSocket таймера:", err);
};
colorWS.onerror = (err) => {
  console.error("Ошибка WebSocket конфигурации:", err);
};

// Автовосстановление соединения (по желанию)
function reconnect(wsFactory, assignTo, delay = 2000) {
  setTimeout(() => {
    const ws = wsFactory();
    assignTo(ws);
  }, delay);
}

timerWS.onclose = () => {
  console.warn("Соединение таймера закрыто, переподключаем...");
  reconnect(
    () => new WebSocket(`ws://${location.host}/ws`),
    (ws) => (timerWS = ws)
  );
};

colorWS.onclose = () => {
  console.warn("Соединение настроек закрыто, переподключаем...");
  reconnect(
    () => new WebSocket(`ws://${location.host}/timer_cfg`),
    (ws) => (colorWS = ws)
  );
};
