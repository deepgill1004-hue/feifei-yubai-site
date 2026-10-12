// 蘇菲餘白｜全站動態：頁首變色、首頁輪播、捲動淡入、視差、短片點播、文章閱讀進度。
// 系統開「減少動態」時只保留功能、不跑動畫。
(() => {
  const root = document.documentElement;
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("y-js");
  root.classList.toggle("still", still);

  // 頁首：離開首屏後變實底
  const header = document.querySelector(".site-header");
  if (header) {
    const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // 首頁 Hero 輪播
  const slides = [...document.querySelectorAll(".hero-media .slide")];
  if (!still && slides.length > 1) {
    let i = 0;
    setInterval(() => {
      slides[i].classList.remove("on");
      i = (i + 1) % slides.length;
      slides[i].classList.add("on");
    }, 6500);
  }

  // 內頁也加淡入（首頁的 .reveal 已寫在 HTML）
  document.querySelectorAll(".letter-item, .topic-card, .faq-list article, .service-list article, .letter-cta, .page-portrait")
    .forEach((el, i) => { el.classList.add("reveal"); el.style.setProperty("--d", `${(i % 3) * 80}ms`); });

  const items = document.querySelectorAll(".reveal");
  if (still || !("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach((el) => io.observe(el));
  }

  // 視差
  const para = [...document.querySelectorAll("[data-parallax]")];
  // 文章閱讀進度
  const body = document.querySelector(".letter-body");
  let bar = null;
  if (body) {
    bar = document.createElement("div");
    bar.className = "y-progress";
    document.body.appendChild(bar);
  }
  if ((!still && para.length) || bar) {
    let ticking = false;
    const update = () => {
      const vh = window.innerHeight;
      if (!still) {
        para.forEach((el) => {
          const r = el.parentElement.getBoundingClientRect();
          if (r.bottom < 0 || r.top > vh) return;
          const shift = ((r.top + r.height / 2) - vh / 2) * -0.08;
          el.style.transform = `translate3d(0, ${shift.toFixed(1)}px, 0) scale(1.12)`;
        });
      }
      if (bar) {
        const r = body.getBoundingClientRect();
        const total = r.height - vh * 0.6;
        const p = Math.min(1, Math.max(0, (-r.top + vh * 0.3) / (total > 0 ? total : 1)));
        bar.style.transform = `scaleX(${p.toFixed(3)})`;
      }
      ticking = false;
    };
    update();
    window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener("resize", update, { passive: true });
  }

  // 短片：點了才載入播放，同時只播一支
  document.querySelectorAll(".video").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.querySelector("video")) return;
      document.querySelectorAll(".video video").forEach((v) => v.pause());
      const v = document.createElement("video");
      v.src = btn.dataset.src;
      v.controls = true;
      v.playsInline = true;
      v.autoplay = true;
      btn.classList.add("playing");
      btn.appendChild(v);
      v.addEventListener("play", () => {
        document.querySelectorAll(".video video").forEach((o) => { if (o !== v) o.pause(); });
      });
    });
  });

  // 文章列表：搜尋＋主題篩選＋大圖/小圖（記住讀者上次選的版面）
  const toolbar = document.querySelector(".y-toolbar");
  const list = document.querySelector(".letter-list.y-cards");
  if (toolbar && list) {
    const cards = [...list.querySelectorAll(".y-card")];
    const hay = cards.map((c) => c.textContent.toLowerCase());
    const input = toolbar.querySelector("input");
    const chips = [...toolbar.querySelectorAll(".y-chips button")];
    const views = [...toolbar.querySelectorAll(".y-view button")];
    const count = toolbar.querySelector(".y-count");
    let chip = "";
    const apply = () => {
      const q = input.value.trim().toLowerCase();
      const keys = chip ? chip.toLowerCase().split("|") : [];
      let shown = 0;
      cards.forEach((c, i) => {
        const ok = (!q || hay[i].includes(q)) && (!keys.length || keys.some((k) => hay[i].includes(k)));
        c.hidden = !ok;
        if (ok) { shown += 1; c.classList.add("in"); }
      });
      count.textContent = q || chip ? `找到 ${shown} 篇` : `共 ${cards.length} 篇`;
    };
    input.addEventListener("input", apply);
    chips.forEach((b) => b.addEventListener("click", () => {
      chips.forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      chip = b.dataset.k;
      apply();
    }));
    const setView = (v) => {
      list.classList.toggle("is-list", v === "list");
      views.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === v)));
    };
    let saved = null;
    try { saved = localStorage.getItem("yubai-view"); } catch (e) { /* 無痕模式 */ }
    setView(saved || (window.matchMedia("(max-width: 900px)").matches ? "list" : "grid"));
    views.forEach((b) => b.addEventListener("click", () => {
      setView(b.dataset.view);
      try { localStorage.setItem("yubai-view", b.dataset.view); } catch (e) { /* 無痕模式 */ }
    }));
    apply();
  }

  // 文章頁底部「繼續看」：上一篇／下一篇＋最新文章左右滑
  const me = document.currentScript || document.querySelector('script[src*="assets/yubai.js"]');
  if (me && /\/letters\/(?!index\.html$)[^/]+\.html$/.test(location.pathname)) {
    const root = new URL("../", me.src);
    const here = decodeURIComponent(location.pathname.split("/").pop());
    const esc = (s) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
    fetch(new URL("letters/articles.json", root)).then((r) => r.ok ? r.json() : []).then((all) => {
      const i = all.findIndex((a) => a.f === here);
      if (!all.length) return;
      const url = (a) => new URL(`letters/${a.f}`, root).href;
      const newer = i > 0 ? all[i - 1] : null;
      const older = i >= 0 && i < all.length - 1 ? all[i + 1] : null;
      const pick = all.filter((a, k) => k !== i && a !== newer && a !== older).slice(0, 8);
      const card = (a) => `<a href="${url(a)}"><figure>${a.i ? `<img src="${new URL(a.i, root).href}" alt="" loading="lazy" decoding="async" />` : ""}</figure><small>No.${a.n}</small><b>${esc(a.t)}</b></a>`;
      const pn = (a, cls, label) => a ? `<a class="${cls}" href="${url(a)}"><small>${label}</small><b>${esc(a.t)}</b></a>` : "<span></span>";
      const sec = document.createElement("section");
      sec.className = "y-more";
      sec.setAttribute("aria-label", "繼續看");
      sec.innerHTML = `<div class="y-more-inner"><div class="y-more-head"><h2>繼續看</h2><a href="${new URL("letters/index.html", root).href}">看全部 ${all.length} 篇 →</a></div>`
        + (newer || older ? `<div class="y-pn">${pn(older, "prev", "← 上一篇")}${pn(newer, "next", "下一篇 →")}</div>` : "")
        + `<div class="y-rail">${pick.map(card).join("")}</div></div>`;
      const main = document.querySelector("main");
      (main || document.body).appendChild(sec);
    }).catch(() => { /* 抓不到清單就不顯示，不影響閱讀 */ });
  }
})();
