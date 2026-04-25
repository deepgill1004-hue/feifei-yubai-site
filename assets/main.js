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

    formNote.textContent = "已收到，謝謝你。也可以先加入 LINE 領取醫美必問清單。";
    signupForm.reset();
  });
}
