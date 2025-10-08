/**
 * Логика страницы таймера: отображение оставшегося времени и обновление по WebSocket.
 */

document.addEventListener("DOMContentLoaded", () => {
  const timerEl = document.getElementById("timer");

  // WebSocket для получения текущего времени таймера
  const ws = new WebSocket(`ws://${window.location.host}/ws`);

  ws.onmessage = (e) => {
    // Просто обновляем текст на экране
    timerEl.textContent = e.data;
  };

  ws.onclose = () => {
    timerEl.textContent = "⏱ Соединение закрыто";
  };
});
