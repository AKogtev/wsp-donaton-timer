/**
 * Логика панели управления таймером.
 * Управление временем, запуск/остановка, цвет, коэффициент и токен OAuth.
 */

document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const timeInput = document.getElementById("time");
  const coefInput = document.getElementById("coef");
  const tokenInput = document.getElementById("token");

  const btnSet = document.getElementById("btn-set");
  const btnStart = document.getElementById("btn-start");
  const btnStop = document.getElementById("btn-stop");
  const btnReset = document.getElementById("btn-reset");
  const btnSaveCoef = document.getElementById("btn-save-coef");
  const btnSaveToken = document.getElementById("btn-save-token");
  const btnColorBlack = document.getElementById("btn-color-black");
  const btnColorWhite = document.getElementById("btn-color-white");

  const logEl = document.getElementById("log");

  const ws = new WebSocket(`ws://${window.location.host}/control`);

  ws.onopen = () => {
    addLog("Соединение установлено", "info");
    if (statusEl) statusEl.textContent = "Соединение установлено";
  };

  ws.onmessage = (e) => {
    const msg = e.data;
    if (statusEl) statusEl.textContent = msg;

    let type = "info";
    if (msg.toLowerCase().includes("ошибка") || msg.toLowerCase().includes("неизвестная")) {
      type = "error";
    } else if (
      msg.toLowerCase().includes("установлено") ||
      msg.toLowerCase().includes("изменено") ||
      msg.toLowerCase().includes("запущен") ||
      msg.toLowerCase().includes("сохранён")
    ) {
      type = "success";
    }
    addLog(msg, type);
  };

  ws.onclose = () => {
    addLog("Соединение закрыто", "error");
    if (statusEl) statusEl.textContent = "Соединение закрыто";
  };

  // Добавление строки в лог с цветом
  function addLog(message, type = "info") {
    if (!logEl) return;
    const line = document.createElement("div");
    line.textContent = message;
    if (type === "success") line.style.color = "#6be675"; // зелёный
    else if (type === "error") line.style.color = "#ff667a"; // красный
    else line.style.color = "#97a3b8"; // серый/инфо
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  }

  // Установка времени (с подтверждением)
  btnSet.addEventListener("click", () => {
    const val = timeInput.value.trim();
    if (val && confirm(`Установить время ${val}?`)) {
      ws.send(`set ${val}`);
    }
  });

  // Старт — сразу
  btnStart.addEventListener("click", () => ws.send("start"));

  // Stop — сразу
  btnStop.addEventListener("click", () => ws.send("stop"));

  // Reset (с подтверждением)
  btnReset.addEventListener("click", () => {
    if (confirm("Сбросить таймер?")) {
      ws.send("reset");
    }
  });

  // Сохранение коэффициента
  btnSaveCoef.addEventListener("click", () => {
    const val = coefInput.value.trim();
    if (val) {
      ws.send(`coef ${val}`);
    }
  });

  // Изменение цвета
  btnColorBlack.addEventListener("click", () => ws.send("color black"));
  btnColorWhite.addEventListener("click", () => ws.send("color white"));

  // Сохранение токена
  btnSaveToken.addEventListener("click", () => {
    const token = tokenInput.value.trim();
    if (token) {
      ws.send(`token ${token}`);
    }
  });
});
