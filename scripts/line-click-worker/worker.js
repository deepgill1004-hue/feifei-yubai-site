// 蘇菲餘白：LINE 按鈕點擊計數的接收端（Cloudflare Worker＋D1，2026-11-24）
// 網站（assets/yubai-click.js）在讀者點 LINE 按鈕時送：{"site":"sophieyubai.com","ev":"line","page":"/letters/…","pos":"end"}
//   POST /        記一次點擊（只收 Origin 是 https://sophieyubai.com 的）；回 204
//   GET  /stats   週報排程讀：?days=60（預設 60、最多 400），要帶 Authorization: Bearer <STATS_TOKEN>
//                 回 {"site","since","rows":[{"day":"2026-11-24","page":"/letters/…","pos":"end","n":3}, …]}
// 不存 IP、不存 cookie、不存瀏覽器資訊；日期用台灣時間。部署步驟見 data/README.md。
const SITE = "https://sophieyubai.com";
const POS = new Set(["end", "answer", "video", "sidebar", "fab", "header", "footer", "page"]);
const PAGE_RE = /^\/[A-Za-z0-9._\/-]{0,200}$/;

function twDay(ms) {
  return new Date(ms + 8 * 3600e3).toISOString().slice(0, 10);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "POST" && (url.pathname === "/" || url.pathname === "/line")) {
      if (req.headers.get("Origin") !== SITE) return new Response(null, { status: 403 });
      let d;
      try {
        d = JSON.parse((await req.text()).slice(0, 1000));
      } catch {
        return new Response(null, { status: 400 });
      }
      if (!d || d.ev !== "line") return new Response(null, { status: 204 });
      const pos = POS.has(d.pos) ? d.pos : "page";
      const page = PAGE_RE.test(d.page || "") ? d.page : "/";
      await env.DB.prepare(
        "INSERT INTO clicks (day, page, pos, n) VALUES (?1, ?2, ?3, 1) ON CONFLICT(day, page, pos) DO UPDATE SET n = n + 1"
      ).bind(twDay(Date.now()), page, pos).run();
      return new Response(null, { status: 204 });
    }
    if (req.method === "GET" && url.pathname === "/stats") {
      if (!env.STATS_TOKEN || req.headers.get("Authorization") !== `Bearer ${env.STATS_TOKEN}`) {
        return new Response("forbidden", { status: 403 });
      }
      const days = Math.min(400, Math.max(1, Number(url.searchParams.get("days")) || 60));
      const since = twDay(Date.now() - (days - 1) * 864e5);
      const { results } = await env.DB.prepare(
        "SELECT day, page, pos, n FROM clicks WHERE day >= ?1 ORDER BY day, page, pos"
      ).bind(since).all();
      return Response.json({ site: "sophieyubai.com", since, rows: results });
    }
    return new Response(null, { status: 404 });
  },
};
