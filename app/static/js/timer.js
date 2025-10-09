// Подключение к WebSocket для таймера
const timerWS = new WebSocket(`ws://${location.host}/ws`);
// Подключение к WebSocket для конфигурации (цвет и т.п.)
const colorWS = new WebSocket(`ws://${location.host}/timer_cfg`);

const timerEl = document.getElementById("timer");
let lastTime = null; // запоминаем предыдущее значение секунд

// Получаем обновления времени от сервера
timerWS.onmessage = (event) => {
  if (timerEl) {
    const newTime = event.data;

    // Сравниваем новое и старое значение (HH:MM:SS → в секунды)
    const toSeconds = (str) => {
      const [h, m, s] = str.split(":").map(Number);
      return h * 3600 + m * 60 + s;
    };

    if (lastTime !== null) {
      const prevSec = toSeconds(lastTime);
      const newSec = toSeconds(newTime);

      if (newSec > prevSec) {
        // Было пополнение → запускаем анимацию
        timerEl.classList.remove("timer-pulse");
        void timerEl.offsetWidth; // хак для перезапуска CSS-анимации
        timerEl.classList.add("timer-pulse");
      }
    }

    timerEl.textContent = newTime;
    lastTime = newTime;
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
