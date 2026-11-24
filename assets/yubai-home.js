// 蘇菲餘白｜首頁動態（2026-11-24 A 版「留白肖像」）：捲動視差＋首屏滑鼠景深、首屏逐字浮現與照片揭幕輪播、7 問勾選計數、暫停動態。
// 首屏動畫用 GSAP（assets/vendor），只動 transform、opacity、clip-path，動畫進行中不讀版面。
// 淡入（.reveal）與 YouTube 點播沿用 yubai.js。系統開「減少動態」時全部不跑；按「暫停動態」只記在這台瀏覽器。
(() => {
  const root = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;
  const KEY = "yubai-motion";
  let paused = reduce;
  try { if (!reduce && localStorage.getItem(KEY) === "paused") paused = true; } catch (e) { /* 無痕或封鎖儲存：照預設 */ }

  // 捲動視差＋首屏滑鼠景深（[data-depth] 外層吃 --py／--px）。先一次讀完所有位置再寫，避免每個元素各逼一次版面重算
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
    const rects = pars.map((p) => p.el.getBoundingClientRect());
    pars.forEach((p, i) => {
      const r = rects[i];
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
    if (hero && fine) {
      hero.addEventListener("mousemove", (e) => {
        const r = hero.getBoundingClientRect();
        mouse.x = (e.clientX - r.left) / r.width - 0.5;
        req();
      });
      hero.addEventListener("mouseleave", () => { mouse.x = 0; req(); });
    }
  }

  // 首屏 A 版：逐字浮現、資歷數字跳動、照片由下往上揭幕輪播（字卡同步換經歷）、主按鈕磁吸
  const ha = document.querySelector(".hero-a");
  let syncHero = () => {};
  if (ha) {
    const G = window.gsap;
    const imgs = [...ha.querySelectorAll(".ha-frame img")];
    const bars = [...ha.querySelectorAll(".ha-dots b")];
    const cl = ha.querySelector(".ha-cl");
    // 其餘三張等第一張載完才換上 src，不跟首屏搶頻寬
    const loadRest = () => imgs.forEach((im) => { if (im.dataset.src) { im.src = im.dataset.src; im.removeAttribute("data-src"); } });
    if (imgs[0] && !imgs[0].complete) imgs[0].addEventListener("load", () => setTimeout(loadRest, 400), { once: true });
    else setTimeout(loadRest, 400);

    if (!G || reduce) {
      root.classList.remove("ha-pre");
    } else {
      // 逐字浮現：from 會立刻把字放到起點，再拿掉 .ha-pre，畫面不會先閃一下
      if (!paused) {
        G.timeline({ defaults: { ease: "power3.out" } })
          .from(ha.querySelectorAll(".ha-c"), { yPercent: 110, opacity: 0, duration: 1, stagger: 0.08 })
          .from(ha.querySelectorAll(".ha-in"), { y: 24, opacity: 0, duration: 0.8, stagger: 0.1 }, "-=0.6")
          .from(ha.querySelector(".ha-frame"), { clipPath: "inset(10% 8% 0% 8% round 200px 200px 18px 18px)", duration: 1.3, ease: "expo.out" }, 0)
          .from(imgs[0], { scale: 1.12, duration: 2.2, ease: "power2.out" }, 0);
        ha.querySelectorAll(".ha-n").forEach((el) => {
          const o = { v: 0 }, to = Number(el.dataset.to) || 0;
          G.to(o, { v: to, duration: 1.4, ease: "power2.out", delay: 0.5, onUpdate: () => { el.textContent = Math.round(o.v); } });
        });
      }
      root.classList.remove("ha-pre");

      // 揭幕輪播：每 5 秒，下一張由下往上蓋過來並慢慢縮回原尺寸；右下進度條、左下字卡同步
      const swapCap = (k) => () => {
        const txt = imgs[k].dataset.cap || "";
        G.timeline()
          .to(cl, { yPercent: -100, opacity: 0, duration: 0.35, ease: "power2.in" })
          .call(() => { cl.textContent = txt; })
          .fromTo(cl, { yPercent: 100, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.5, ease: "power3.out" });
      };
      const cycle = G.timeline({ repeat: -1, paused: true });
      imgs.forEach((img, k) => {
        const nxt = imgs[(k + 1) % imgs.length];
        cycle.fromTo(bars[k], { scaleX: 0 }, { scaleX: 1, duration: 5, ease: "none", immediateRender: false })
          .set(nxt, { zIndex: 2 + k })
          .call(swapCap((k + 1) % imgs.length))
          .fromTo(nxt, { clipPath: "inset(100% 0 0 0)", scale: 1.1 }, { clipPath: "inset(0% 0 0 0)", scale: 1, duration: 1.4, ease: "expo.inOut", immediateRender: false })
          .set(bars[k], { scaleX: 0 });
      });
      cycle.eventCallback("onRepeat", () => {
        G.set(imgs, { zIndex: "" });
        G.set(imgs.slice(1), { clipPath: "inset(100% 0 0 0)" });
        G.set(imgs[0], { clipPath: "inset(0% 0 0 0)", scale: 1 });
      });
      let visible = true;
      syncHero = () => { if (!paused && visible && imgs.length > 1) cycle.play(); else cycle.pause(); };
      if ("IntersectionObserver" in window) {
        new IntersectionObserver((es) => { visible = es[0].isIntersecting; syncHero(); }).observe(ha);
      }

      // 主按鈕磁吸（只在滑鼠裝置）
      if (fine) {
        ha.querySelectorAll(".btn-p").forEach((b) => {
          const qx = G.quickTo(b, "x", { duration: 0.5, ease: "power3.out" }), qy = G.quickTo(b, "y", { duration: 0.5, ease: "power3.out" });
          b.addEventListener("pointermove", (e) => { const r = b.getBoundingClientRect(); qx((e.clientX - r.left - r.width / 2) * 0.28); qy((e.clientY - r.top - r.height / 2) * 0.4); });
          b.addEventListener("pointerleave", () => { qx(0); qy(0); });
        });
      }
    }
  }

  // 暫停動態
  const btn = document.querySelector(".still-btn");
  const setPaused = (v, save) => {
    paused = v;
    root.classList.toggle("y-paused", v);
    syncHero();
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

  // 7 問：前 4 題可以勾，右上角顯示勾了幾題
  const qs = [...document.querySelectorAll(".qs input[type=checkbox]")];
  const cnt = document.querySelector(".qs-count");
  const upd = () => { if (cnt) cnt.textContent = `${qs.filter((q) => q.checked).length} / ${qs.length}`; };
  qs.forEach((q) => q.addEventListener("change", upd));
  upd();

  setPaused(paused, false);
})();
