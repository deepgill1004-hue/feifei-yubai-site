const signupForm = document.querySelector("#signupForm");
const formNote = document.querySelector("#formNote");

if (signupForm && formNote) {
  signupForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(signupForm);
    const email = String(data.get("email") || "").trim();

    if (!email) {
      formNote.textContent = "請先留下 Email。";
      return;
    }

    formNote.textContent =
      "已收到。正式上線時，這裡會接到 beehiiv 或 Brevo 的訂閱名單。";
    signupForm.reset();
  });
}
