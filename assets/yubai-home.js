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
  let syncHop = () => {};
  const setPaused = (v, save) => {
    paused = v;
    root.classList.toggle("y-paused", v);
    syncHop();
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

  // V3 漂浮島：女生在石頭之間跳（2026-11-16 凱菲問「V3 的跳躍呢」）。data-hop：a 一路跳上去、b 跳過去再跳回來、c 原地彈跳。
  // 落腳點跟著石頭一起漂（每格讀 .fl2 當下的 transform）；落地那顆往下沉一下再彈回。
  // 暫停、系統減少動態、首屏不在畫面上就停，她回到第二顆石頭上（.rider 靜態圖，沒有 JS 時也是這樣）。
  const stage = document.querySelector(".isle-stage.v3[data-hop]");
  if (stage && !reduce) {
    const hopEl = stage.querySelector(".hopper");
    const stImg = hopEl.querySelector(".h-st"), airImg = hopEl.querySelector(".h-air");
    const nums = (s) => String(s || "").split(",").map(Number);
    const ST = nums(hopEl.dataset.st), AIR = nums(hopEl.dataset.air);   // 寬, 高, 對位點 x, y（原圖 px）
    const REF = Number(hopEl.dataset.ref) || 344, SC = Number(hopEl.dataset.scale) || 1;
    const stones = [...stage.querySelectorAll(".stone")].map((a) => ({
      a, fl: a.querySelector(".fl2"), img: a.querySelector(".dip > img"), dip: a.querySelector(".dip"),
      lbl: a.querySelector(".lbl"), feet: nums(a.dataset.feet), d: 0,
    }));
    // 落腳點：0–3＝四顆石頭各一個（data-feet）；4 起＝同一顆的第二個點（data-feet2，第四顆轉身回看站的位置）
    const spots = stones.map((st, i) => ({ st, i, f: st.feet }));
    stones.forEach((st, i) => { if (st.a.dataset.feet2) spots.push({ st, i, f: nums(st.a.dataset.feet2) }); });
    const HOP = (from, to, lift, fly) => ({ k: "hop", from, to, lift, antic: 0.16, fly: fly || 0.56, land: 0.26 });
    const TURN = (from, to) => ({ k: "hop", from, to: to ?? from, lift: 0.03, antic: 0.1, fly: 0.28, land: 0.14, turn: true });
    const STAY = (s, t) => ({ k: "stay", s, t });
    const FADE = (s, dir) => ({ k: "fade", s, dir, t: 0.5 });
    const PLANS = {
      a: [FADE(0, "in"), STAY(0, 0.6), HOP(0, 1, 0.05), STAY(1, 0.5), HOP(1, 2, 0.05), STAY(2, 0.5), HOP(2, 3, 0.05, 0.6),
          STAY(3, 0.45), TURN(3, spots.length > 4 ? 4 : 3), STAY(spots.length > 4 ? 4 : 3, 1.7), FADE(spots.length > 4 ? 4 : 3, "out")],
      b: [STAY(1, 1.3), HOP(1, 2, 0.05), STAY(2, 0.7), TURN(2), STAY(2, 0.7), HOP(2, 1, 0.05), STAY(1, 0.6), TURN(1)],
      c: [STAY(1, 1.8), HOP(1, 1, 0.05, 0.34), STAY(1, 0.1), HOP(1, 1, 0.06, 0.38), STAY(1, 1.4)],
    };
    let face = 1, total = 0;
    const segs = (PLANS[stage.dataset.hop] || PLANS.a).map((p) => {
      const d = p.k === "hop" ? p.antic + p.fly + p.land : p.t;
      const s = { ...p, d, t0: total, face };
      if (p.turn) face = -face;
      total += d;
      return s;
    });
    const lands = segs.filter((s) => s.k === "hop").map((s) => ({ s: spots[s.to].i, at: s.t0 + s.antic + s.fly, amp: s.turn ? 0.005 : 0.012 }));
    let k = 1, W = 1, ceil = -1e9;
    const size = () => {
      const archi = stage.querySelector(".archi");
      W = archi.clientWidth || 1;
      k = (stones[1].fl.offsetWidth || 1) / REF * SC;
      // 天花板：選單下緣再往下 8px（換成 .archi 裡的座標，用頁面最上面時的位置算，不受捲動影響）
      const hdr = document.querySelector("header");
      ceil = hdr ? hdr.getBoundingClientRect().bottom - archi.getBoundingClientRect().top + 8 : -1e9;
      stImg.style.width = `${(ST[0] * k).toFixed(2)}px`;
      airImg.style.width = `${(AIR[0] * k).toFixed(2)}px`;
      stImg.style.transformOrigin = `${(ST[2] * k).toFixed(2)}px ${(ST[3] * k).toFixed(2)}px`;
      airImg.style.transformOrigin = `${(AIR[2] * k).toFixed(2)}px ${(AIR[3] * k).toFixed(2)}px`;
    };
    const foot = (sp) => { const st = sp.st;   // 落腳點在 .archi 裡的位置：石頭原位＋漂浮的 transform（以 .fl2 中心為原點）＋被踩的凹陷
      const w = st.fl.offsetWidth, h = st.fl.offsetHeight, ih = st.img.offsetHeight || h;
      const m = getComputedStyle(st.fl).transform;
      let [a, b, c, d, e, f] = [1, 0, 0, 1, 0, 0];
      if (m && m.startsWith("matrix(")) [a, b, c, d, e, f] = m.slice(7, -1).split(",").map(Number);
      const px = sp.f[0] * w - w / 2, py = sp.f[1] * ih - h / 2;
      return { x: st.a.offsetLeft + w / 2 + a * px + c * py + e, y: st.a.offsetTop + h / 2 + b * px + d * py + f + st.d };
    };
    const ease = (x) => 0.5 - 0.5 * Math.cos(Math.PI * x);
    const squash = (x) => 0.12 * Math.exp(-5 * x) * Math.cos(9 * x);   // 落地壓扁再回彈
    let on = -1;
    const mark = (s) => {
      if (s === on) return;
      if (on >= 0) stones[on].lbl.classList.remove("on");
      on = s;
      if (s >= 0) stones[s].lbl.classList.add("on");
    };
    const render = (t) => {
      stones.forEach((st) => { st.d = 0; });
      lands.forEach((l) => {
        let dt = t - l.at;
        if (dt < 0) dt += total;
        if (dt < 0.9) stones[l.s].d += l.amp * W * Math.exp(-4.5 * dt) * Math.sin(12 * dt);
      });
      stones.forEach((st) => { st.dip.style.transform = st.d ? `translate3d(0, ${st.d.toFixed(2)}px, 0)` : ""; });
      const s = segs.find((x) => t >= x.t0 && t < x.t0 + x.d) || segs[segs.length - 1];
      let img = stImg, spr = ST, p, sx = 1, sy = 1, rot = 0, fc = s.face, op = 1;
      if (s.k === "stay") {
        p = foot(spots[s.s]);
        mark(spots[s.s].i);
      } else if (s.k === "fade") {
        const x = ease(Math.min(1, (t - s.t0) / s.d));
        p = foot(spots[s.s]);
        op = s.dir === "in" ? x : 1 - x;
        if (s.dir === "in") p.y -= (1 - x) * 0.025 * W;
        mark(s.dir === "in" ? spots[s.s].i : -1);
      } else {
        const lt = t - s.t0;
        if (lt < s.antic) {   // 起跳前蹲一下
          const x = ease(lt / s.antic);
          p = foot(spots[s.from]);
          sy = 1 - 0.1 * x;
          sx = 1 + 0.05 * x;
          mark(spots[s.from].i);
        } else if (lt < s.antic + s.fly) {   // 在空中：水平等速、垂直拋物線（像有重量）
          const x = (lt - s.antic) / s.fly;
          const a0 = foot(spots[s.from]), a1 = foot(spots[s.to]);
          // 最高點＝比較高那顆再高 lift×寬；頭（半空圖的上緣）不准高過天花板
          const hi = Math.min(a0.y, a1.y);
          const top = Math.min(hi - 1, Math.max(hi - s.lift * W, ceil + AIR[3] * k * 1.06));   // 1.06：起跳時拉長 5% 也算進去
          const D = a1.y - a0.y, A0 = a0.y - top, B = 8 * D + 16 * A0;
          const L = (B + Math.sqrt(Math.max(0, B * B - 64 * D * D))) / 32;   // 讓拋物線頂點剛好落在 top
          p = { x: a0.x + (a1.x - a0.x) * x, y: a0.y + D * x - 4 * L * x * (1 - x) };
          img = airImg;
          spr = AIR;
          sy = 1 + 0.05 * (1 - x) * (1 - x);
          if (s.from !== s.to && !s.turn) rot = s.face * 5 * Math.sin(Math.PI * x);
          if (s.turn && x >= 0.5) fc = -s.face;   // 轉身在最高點
          mark(-1);
        } else {   // 落地壓扁再回彈
          const q = squash((lt - s.antic - s.fly) / s.land);
          p = foot(spots[s.to]);
          sy = 1 - q;
          sx = 1 + q * 0.5;
          if (s.turn) fc = -s.face;
          mark(spots[s.to].i);
        }
      }
      img.style.transform = `translate3d(${(p.x - spr[2] * k).toFixed(2)}px, ${(p.y - spr[3] * k).toFixed(2)}px, 0) `
        + `rotate(${rot.toFixed(2)}deg) scale(${(fc * sx).toFixed(3)}, ${sy.toFixed(3)})`;
      img.style.opacity = op;
      (img === stImg ? airImg : stImg).style.opacity = 0;
    };
    let raf = 0, t0 = 0, visible = true;
    const tick = (now) => { raf = requestAnimationFrame(tick); render(((now - t0) / 1000) % total); };
    const start = () => {
      if (raf || paused || !visible) return;
      size();
      stage.classList.add("hopping");
      t0 = performance.now();
      raf = requestAnimationFrame(tick);
    };
    const stop = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      stage.classList.remove("hopping");
      mark(-1);
      stones.forEach((st) => { st.d = 0; st.dip.style.transform = ""; });
    };
    syncHop = () => (paused ? stop() : start());
    window.addEventListener("resize", () => { if (raf) size(); }, { passive: true });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver((es) => { visible = es[0].isIntersecting; if (visible) start(); else stop(); }).observe(stage);
    }
    window.__yubaiHop = { segs, total, phase: () => (raf ? ((performance.now() - t0) / 1000) % total : -1) };   // 驗收用：讀時間軸
  }

  setPaused(paused, false);
})();
