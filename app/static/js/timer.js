document.addEventListener("DOMContentLoaded", () => {
  const timerEl = document.getElementById("timer");
  let lastValue = null;

  const ws = new WebSocket(`ws://${window.location.host}/ws`);

  ws.onmessage = (e) => {
    const newValue = e.data;
    timerEl.textContent = newValue;

    // Сравниваем с прошлым значением
    if (lastValue && newValue > lastValue) {
      // добавляем класс анимации
      timerEl.classList.add("timer-pulse");

      // убираем класс после завершения анимации
      timerEl.addEventListener(
        "animationend",
        () => timerEl.classList.remove("timer-pulse"),
        { once: true }
      );
    }

    lastValue = newValue;
  };

  ws.onclose = () => {
    timerEl.textContent = "⏱ Соединение закрыто";
  };
});
