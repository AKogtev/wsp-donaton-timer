/**
 * Логика страницы авторизации: ввод client_id/secret и отправка формы.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("authForm");

  // При отправке формы передаём client_id/secret на сервер
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const clientId = document.getElementById("client_id").value.trim();
    const clientSecret = document.getElementById("client_secret").value.trim();

    fetch("/start_auth", {
      method: "POST",
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
      }),
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }).then((resp) => {
      // Сервер сам вернёт редирект на DonationAlerts
      if (resp.redirected) {
        window.location.href = resp.url;
      }
    });
  });
});
