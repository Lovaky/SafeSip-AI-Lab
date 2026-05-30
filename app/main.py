from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.routes.literature import router

app = FastAPI(title="SafeSip AI Lab")

app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SafeSip AI Lab - Literature Search</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --text: #1d2433;
      --muted: #667085;
      --line: #d8dee9;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --soft: #eef6f4;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }

    .wrap {
      width: min(1080px, calc(100% - 32px));
      margin: 0 auto;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 0;
    }

    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
    }

    .docs-link {
      color: var(--accent);
      text-decoration: none;
      font-size: 14px;
      font-weight: 700;
    }

    main {
      padding: 28px 0 48px;
    }

    .search-area {
      display: grid;
      gap: 14px;
      margin-bottom: 22px;
    }

    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
    }

    input {
      width: 100%;
      height: 46px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 14px;
      color: var(--text);
      background: var(--panel);
      font-size: 16px;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
    }

    button {
      height: 46px;
      border: 0;
      border-radius: 6px;
      padding: 0 18px;
      background: var(--accent);
      color: #ffffff;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
    }

    button:hover {
      background: var(--accent-dark);
    }

    .status {
      min-height: 22px;
      color: var(--muted);
      font-size: 14px;
    }

    .share {
      display: none;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 12px;
      background: var(--soft);
      color: var(--muted);
      font-size: 14px;
    }

    .share code {
      overflow-wrap: anywhere;
      color: var(--text);
      font-family: Consolas, monospace;
    }

    .copy {
      flex: 0 0 auto;
      height: 34px;
      padding: 0 12px;
      font-size: 13px;
    }

    .results {
      display: grid;
      gap: 14px;
    }

    .paper {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: var(--panel);
    }

    .paper h2 {
      margin: 0 0 10px;
      font-size: 18px;
      line-height: 1.35;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .abstract {
      margin: 0 0 14px;
      color: #344054;
      font-size: 15px;
      line-height: 1.65;
      white-space: pre-line;
    }

    .paper a {
      color: var(--accent);
      font-weight: 700;
      text-decoration: none;
    }

    .empty {
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 24px;
      background: var(--panel);
      color: var(--muted);
      text-align: center;
    }

    @media (max-width: 640px) {
      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      form {
        grid-template-columns: 1fr;
      }

      button {
        width: 100%;
      }

      .share {
        align-items: stretch;
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <h1>SafeSip AI Lab 文献检索</h1>
      <a class="docs-link" href="/docs">API Docs</a>
    </div>
  </header>

  <main class="wrap">
    <section class="search-area">
      <form id="searchForm">
        <input id="queryInput" name="q" type="search" placeholder="输入关键词，例如 coffee, alcohol, diabetes" autocomplete="off">
        <button type="submit">搜索</button>
      </form>
      <div id="status" class="status"></div>
      <div id="shareBox" class="share">
        <code id="shareUrl"></code>
        <button id="copyButton" class="copy" type="button">复制链接</button>
      </div>
    </section>

    <section id="results" class="results">
      <div class="empty">输入关键词后开始查询 PubMed 文献。</div>
    </section>
  </main>

  <script>
    const form = document.getElementById("searchForm");
    const input = document.getElementById("queryInput");
    const statusEl = document.getElementById("status");
    const resultsEl = document.getElementById("results");
    const shareBox = document.getElementById("shareBox");
    const shareUrl = document.getElementById("shareUrl");
    const copyButton = document.getElementById("copyButton");

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderResults(items) {
      if (!items.length) {
        resultsEl.innerHTML = '<div class="empty">没有找到相关文献。</div>';
        return;
      }

      resultsEl.innerHTML = items.map((paper) => {
        const title = escapeHtml(paper.title || "Untitled");
        const abstract = escapeHtml(paper.abstract || "No abstract available.");
        const pubdate = escapeHtml(paper.pubdate || "Unknown date");
        const pmid = escapeHtml(paper.pmid || "");
        const url = escapeHtml(paper.url || "#");

        return `
          <article class="paper">
            <h2>${title}</h2>
            <div class="meta">
              <span>PMID: ${pmid}</span>
              <span>Published: ${pubdate}</span>
            </div>
            <p class="abstract">${abstract}</p>
            <a href="${url}" target="_blank" rel="noopener">查看 PubMed 原文</a>
          </article>
        `;
      }).join("");
    }

    async function runSearch(query, updateUrl = true) {
      const trimmed = query.trim();
      if (!trimmed) {
        statusEl.textContent = "";
        shareBox.style.display = "none";
        resultsEl.innerHTML = '<div class="empty">输入关键词后开始查询 PubMed 文献。</div>';
        return;
      }

      if (updateUrl) {
        const nextUrl = new URL(window.location.href);
        nextUrl.searchParams.set("q", trimmed);
        window.history.pushState({}, "", nextUrl);
      }

      shareUrl.textContent = window.location.href;
      shareBox.style.display = "flex";
      statusEl.textContent = "正在搜索 PubMed...";
      resultsEl.innerHTML = "";

      try {
        const response = await fetch(`/api/search-paper?query=${encodeURIComponent(trimmed)}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const items = data.results || [];
        statusEl.textContent = `找到 ${items.length} 条结果`;
        renderResults(items);
      } catch (error) {
        statusEl.textContent = "搜索失败，请稍后重试。";
        resultsEl.innerHTML = '<div class="empty">请求 PubMed API 时出现错误。</div>';
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runSearch(input.value);
    });

    copyButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(window.location.href);
      copyButton.textContent = "已复制";
      setTimeout(() => copyButton.textContent = "复制链接", 1200);
    });

    const initialQuery = new URLSearchParams(window.location.search).get("q");
    if (initialQuery) {
      input.value = initialQuery;
      runSearch(initialQuery, false);
    }
  </script>
</body>
</html>
"""
