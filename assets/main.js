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
      "已記錄在這次頁面互動中。正式收信前，請先用 LINE 領清單；電子報平台註冊後再接表單。";
    signupForm.reset();
  });
}
