/* 蘇菲餘白：LINE 按鈕點擊計數（2026-11-24）
   只有 data/analytics.json 填了 line_click_endpoint，apply-theme 才會在頁面載入這支（data-endpoint＝接收端網址）。
   不用 cookie、不記任何個人資料：只送「哪一頁、哪個位置的 LINE 按鈕被點」。連結本身不改，讀者點了照樣直接開 LINE。
   位置：end＝文末（加入 LINE 按鈕與「延伸整理」區）、answer＝開頭結論框、video＝影片卡、sidebar＝側欄、
         fab＝右下角浮動鈕、header＝頁首、footer＝頁尾、page＝其他頁（首頁、諮詢頁…） */
(function () {
  var me = document.currentScript;
  var ep = me && me.getAttribute("data-endpoint");
  if (!ep || location.hostname !== "sophieyubai.com") return;
  var POS = [
    [".y-cta-line", "end"], [".letter-cta", "end"], [".y-answer", "answer"], [".y-yt-card", "video"],
    [".letter-sidebar", "sidebar"], [".y-line-fab", "fab"], [".nav-cta", "header"], [".site-header", "header"],
    [".site-footer", "footer"]
  ];
  function send(a) {
    var pos = "page";
    for (var i = 0; i < POS.length; i++) {
      if (a.closest(POS[i][0])) { pos = POS[i][1]; break; }
    }
    var body = JSON.stringify({ site: "sophieyubai.com", ev: "line", page: location.pathname, pos: pos });
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(ep, new Blob([body], { type: "text/plain;charset=UTF-8" }))) return;
    } catch (e) { /* 改用 fetch */ }
    try {
      fetch(ep, { method: "POST", body: body, keepalive: true, mode: "no-cors", headers: { "Content-Type": "text/plain;charset=UTF-8" } });
    } catch (e) { /* 送不出去就算了，不影響讀者 */ }
  }
  function onClick(ev) {
    if (ev.type === "auxclick" && ev.button !== 1) return;
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href*="line.me/R/ti/p/"]') : null;
    if (a) send(a);
  }
  document.addEventListener("click", onClick, { capture: true, passive: true });
  document.addEventListener("auxclick", onClick, { capture: true, passive: true });
})();
