// app/static/js/config.js
(function () {
  const byId = (id) => document.getElementById(id);
  const proto = location.protocol === "https:" ? "wss://" : "ws://";
  const ws = new WebSocket(proto + location.host + "/control");

  // ЛОГИ
  ws.onmessage = (e) => {
    const el = byId("log");
    if (!el) return;
    el.textContent += e.data + "\n";
    el.scrollTop = el.scrollHeight;
  };
  ws.onclose = () => {
    const el = byId("log");
    if (el) {
      el.textContent += "[control] соединение закрыто\n";
      el.scrollTop = el.scrollHeight;
    }
  };

  const sendCmd = (cmd) => ws.readyState === 1 && ws.send(cmd);

  // --- КНОПКИ ТАЙМЕРА ---

  // Set — подтверждение + валидация HH:MM:SS
  const btnSet = byId("btn-set");
  if (btnSet) {
    btnSet.addEventListener("click", (ev) => {
      ev.preventDefault();
      const t = (byId("time")?.value || "").trim();
      if (!t) return;
      const ok = /^\d{2}:\d{2}:\d{2}$/.test(t);
      if (!ok) {
        alert("Формат времени: HH:MM:SS (например, 00:05:00)");
        return;
      }
      if (confirm(`Установить таймер на ${t}?`)) {
        sendCmd("set " + t);
      }
    });
  }

  // Start
  const btnStart = byId("btn-start");
  if (btnStart) {
    btnStart.addEventListener("click", (ev) => {
      ev.preventDefault();
      sendCmd("start");
    });
  }

  // Stop
  const btnStop = byId("btn-stop");
  if (btnStop) {
    btnStop.addEventListener("click", (ev) => {
      ev.preventDefault();
      sendCmd("stop");
    });
  }

  // Reset — подтверждение
  const btnReset = byId("btn-reset");
  if (btnReset) {
    btnReset.addEventListener("click", (ev) => {
      ev.preventDefault();
      if (confirm("Сбросить таймер на исходное значение?")) {
        sendCmd("reset");
      }
    });
  }

  // --- TOKEN / COEF ---

  // Save Token
  const btnTok = byId("btn-save-token");
  if (btnTok) {
    btnTok.addEventListener("click", (ev) => {
      ev.preventDefault();
      const v = (byId("token")?.value || "").trim();
      if (!v) return;
      sendCmd("token " + v);
    });
  }

  // Save Ratio — дробные значения (точка/запятая)
  const btnCoef = byId("btn-save-coef");
  if (btnCoef) {
    btnCoef.addEventListener("click", (ev) => {
      ev.preventDefault();
      let v = (byId("coef")?.value || "").trim();
      if (!v) return;
      v = v.replace(",", ".");
      if (isNaN(Number(v))) {
        alert("Коэффициент должен быть числом, например 4.5");
        return;
      }
      sendCmd("coef " + v);
    });
  }

  // --- Цвет таймера ---
  const btnBlack = byId("btn-color-black");
  if (btnBlack) {
    btnBlack.addEventListener("click", (ev) => {
      ev.preventDefault();
      sendCmd("color black");
    });
  }
  const btnWhite = byId("btn-color-white");
  if (btnWhite) {
    btnWhite.addEventListener("click", (ev) => {
      ev.preventDefault();
      sendCmd("color white");
    });
  }
})();
