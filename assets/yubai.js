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

  // YouTube 短影片：頁面上只有縮圖，點了才換成 youtube-nocookie 播放器（不拖慢首屏）；沒有 JS 時就是連到 YouTube 的連結
  document.querySelectorAll("a.y-yt[data-yt]").forEach((a) => {
    const id = a.dataset.yt;
    if (!/^[\w-]{11}$/.test(id)) return;
    a.addEventListener("click", (e) => {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      const box = document.createElement("div");
      box.className = "y-yt";
      const f = document.createElement("iframe");
      f.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&playsinline=1&rel=0`;
      f.title = a.getAttribute("aria-label") || "YouTube 影片";
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      f.allowFullscreen = true;
      box.appendChild(f);
      a.replaceWith(box);
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
        + ((newer || older) && !document.querySelector(".y-pn-static") ? `<div class="y-pn">${pn(older, "prev", "← 上一篇")}${pn(newer, "next", "下一篇 →")}</div>` : "")
        + `<div class="y-rail">${pick.map(card).join("")}</div></div>`;
      const main = document.querySelector("main");
      (main || document.body).appendChild(sec);
    }).catch(() => { /* 抓不到清單就不顯示，不影響閱讀 */ });

    // 文章頁底部「這篇相關的好物」：只在文章內容跟商品標籤對得上時才出現（資料＝picks.json，由 affiliate_sync.py 產）
    fetch(new URL("picks.json", root)).then((r) => r.ok ? r.json() : null).then((pk) => {
      if (!pk || !pk.products || !pk.products.length) return;
      const body = document.querySelector(".letter-body") || document.querySelector("main");
      const text = ((document.querySelector("h1") || {}).textContent || "") + " " + (body ? body.textContent.slice(0, 4000) : "");
      const scored = pk.products.map((p) => ({ p, s: p.tags.filter((t) => text.includes(t)).length })).filter((x) => x.s >= 2)
        .sort((a, b) => b.s - a.s).slice(0, 3);
      if (!scored.length) return;
      const page = encodeURIComponent(here.slice(0, 80));
      const card = ({ p }) => `<a class="y-pk" href="${p.go}?c=art&p=${page}" rel="sponsored noopener" target="_blank"><small>${esc(p.category)}・${esc(p.price)}</small><b>${esc(p.name)}</b><span>${esc(p.why)}</span><em>到蝦皮看 →</em></a>`;
      const sec = document.createElement("section");
      sec.className = "y-picks";
      sec.setAttribute("aria-label", "這篇相關的好物");
      sec.innerHTML = `<div class="y-more-inner"><div class="y-more-head"><h2>這篇相關的好物</h2><a href="${new URL("picks.html", root).href}">蘇菲私藏清單 →</a></div>`
        + `<div class="y-pk-grid">${scored.map(card).join("")}</div><p class="y-pk-note">${esc(pk.disclosure)}</p></div>`;
      const main = document.querySelector("main") || document.body;
      main.insertBefore(sec, main.querySelector(".y-more"));
    }).catch(() => { /* 抓不到清單就不顯示 */ });
  }
})();
