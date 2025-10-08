// app/static/js/auth.js
(function () {
  const byId = (id) => document.getElementById(id);

  // Показ/скрытие секрета
  const toggle = byId("toggle-secret");
  const secret = byId("client_secret");
  if (toggle && secret) {
    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      const isHidden = secret.type === "password";
      secret.type = isHidden ? "text" : "password";
      toggle.textContent = isHidden ? "Скрыть" : "Показать";
    });
  }

  // Копирование Redirect URI
  const copyBtn = byId("copy-redirect");
  const redirect = byId("redirect_uri");
  if (copyBtn && redirect) {
    copyBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await navigator.clipboard.writeText(redirect.value);
        const txt = copyBtn.textContent;
        copyBtn.textContent = "Скопировано!";
        setTimeout(() => (copyBtn.textContent = txt), 1200);
      } catch {
        // fallback
        redirect.select();
        document.execCommand("copy");
      }
    });
  }
})();
