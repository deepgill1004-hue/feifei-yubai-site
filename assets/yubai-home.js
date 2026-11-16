// 蘇菲餘白｜首頁綜合版動態（2026-11-16）：捲動視差＋首屏滑鼠帶動、首屏照片輪播、7 問勾選計數、暫停動態。
// 淡入（.reveal）與 YouTube 點播沿用 yubai.js。系統開「減少動態」時全部不跑；按「暫停動態」只記在這台瀏覽器。
(() => {
  const root = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const KEY = "yubai-motion";
  let paused = reduce;
  try { if (!reduce && localStorage.getItem(KEY) === "paused") paused = true; } catch (e) { /* 無痕或封鎖儲存：照預設 */ }

  // 捲動視差＋首屏滑鼠帶動（[data-depth] 外層吃 --py／--px，內層 .fl 自己飄）
  const pars = [...document.querySelectorAll("[data-depth]")].map((el) => ({
    el, depth: parseFloat(el.dataset.depth) || 0, mx: parseFloat(el.dataset.mx) || 0,
  }));
  const mouse = { x: 0 };
  let ticking = false;
  const frame = () => {
    ticking = false;
    if (paused) return;
    const vh = window.innerHeight;
    const k = window.innerWidth < 860 ? -0.35 : -1;
    pars.forEach((p) => {
      const r = p.el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      p.el.style.setProperty("--py", `${((r.top + r.height / 2 - vh / 2) * p.depth * k).toFixed(1)}px`);
      if (p.mx) p.el.style.setProperty("--px", `${(mouse.x * p.mx).toFixed(1)}px`);
    });
  };
  const req = () => { if (!ticking) { ticking = true; requestAnimationFrame(frame); } };
  if (!reduce) {
    window.addEventListener("scroll", req, { passive: true });
    window.addEventListener("resize", req, { passive: true });
    const hero = document.querySelector(".hero");
    if (hero && window.matchMedia("(pointer: fine)").matches) {
      hero.addEventListener("mousemove", (e) => {
        const r = hero.getBoundingClientRect();
        mouse.x = (e.clientX - r.left) / r.width - 0.5;
        req();
      });
      hero.addEventListener("mouseleave", () => { mouse.x = 0; req(); });
    }
  }

  // 暫停動態
  const btn = document.querySelector(".still-btn");
  const setPaused = (v, save) => {
    paused = v;
    root.classList.toggle("y-paused", v);
    if (btn) {
      btn.setAttribute("aria-pressed", String(v));
      btn.textContent = v ? "恢復動態" : "暫停動態";
    }
    if (v) pars.forEach((p) => { p.el.style.setProperty("--py", "0px"); p.el.style.setProperty("--px", "0px"); });
    else req();
    if (save) {
      try { if (v) localStorage.setItem(KEY, "paused"); else localStorage.removeItem(KEY); } catch (e) { /* 存不了就只對這次有效 */ }
    }
  };
  if (btn) {
    if (reduce) btn.hidden = true;
    else btn.addEventListener("click", () => setPaused(!paused, true));
  }

  // 首屏照片輪播（4 張）
  const slides = [...document.querySelectorAll(".photo-arch img")];
  let si = 0;
  if (!reduce && slides.length > 1) {
    setInterval(() => {
      if (paused || document.hidden) return;
      slides[si].classList.remove("on");
      si = (si + 1) % slides.length;
      slides[si].classList.add("on");
    }, 5200);
  }

  // 7 問：前 4 題可以勾，右上角顯示勾了幾題
  const qs = [...document.querySelectorAll(".qs input[type=checkbox]")];
  const cnt = document.querySelector(".qs-count");
  const upd = () => { if (cnt) cnt.textContent = `${qs.filter((q) => q.checked).length} / ${qs.length}`; };
  qs.forEach((q) => q.addEventListener("change", upd));
  upd();

  setPaused(paused, false);
})();
