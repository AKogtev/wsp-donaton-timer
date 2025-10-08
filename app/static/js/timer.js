const proto = location.protocol === "https:" ? "wss://" : "ws://";

// время
const ws = new WebSocket(proto + location.host + "/ws");
ws.onmessage = (e) => {
  document.getElementById("timer").innerText = e.data;
};

// конфиг (цвет)
const wsCfg = new WebSocket(proto + location.host + "/timer_cfg");
wsCfg.onmessage = (e) => {
  const color = (e.data === "white") ? "#fff" : "#000";
  document.getElementById("timer").style.color = color;
};
