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
})();
