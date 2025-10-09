/**
 * Логика страницы авторизации: ввод client_id/secret и отправка формы.
 */

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggle-secret");
  const secretInput = document.getElementById("client_secret");
  const copyBtn = document.getElementById("copy-redirect");
  const redirectInput = document.getElementById("redirect_uri");

  // Переключатель показа/скрытия Client Secret
  if (toggleBtn && secretInput) {
    toggleBtn.addEventListener("click", () => {
      if (secretInput.type === "password") {
        secretInput.type = "text";
        toggleBtn.textContent = "Скрыть";
      } else {
        secretInput.type = "password";
        toggleBtn.textContent = "Показать";
      }
    });
  }

  // Кнопка "Копировать" для Redirect URI
  if (copyBtn && redirectInput) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(redirectInput.value);
        copyBtn.textContent = "Скопировано!";
        setTimeout(() => (copyBtn.textContent = "Копировать"), 1500);
      } catch (err) {
        console.error("Не удалось скопировать:", err);
      }
    });
  }
});

