"use strict";
document.documentElement.classList.add("js");
if (window.matchMedia("(max-width: 1250px)").matches) {
  document.querySelectorAll(".toc details").forEach(details => { details.open = false; });
}

const menuButton = document.getElementById("menu-toggle");
const sidebar = document.getElementById("sidebar");
function closeMenu() {
  sidebar.classList.remove("is-open");
  menuButton.setAttribute("aria-expanded", "false");
}
menuButton.addEventListener("click", () => {
  const open = sidebar.classList.toggle("is-open");
  menuButton.setAttribute("aria-expanded", String(open));
});
sidebar.addEventListener("click", event => {
  if (event.target.closest("a") && window.matchMedia("(max-width: 800px)").matches) closeMenu();
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
    closeMenu();
    menuButton.focus();
  }
});

const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const searchStatus = document.getElementById("search-status");
searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim().toLocaleLowerCase();
  searchResults.replaceChildren();
  searchResults.hidden = !query;
  if (!query) { searchStatus.textContent = ""; return; }
  const all = (window.GENX_SEARCH || []).filter(item => (item.title + " " + item.page).toLocaleLowerCase().includes(query));
  const matches = all.slice(0, 12);
  searchStatus.textContent = "找到 " + all.length + " 个章节";
  matches.forEach(item => {
    const link = document.createElement("a");
    link.href = item.url;
    const title = document.createElement("span");
    title.textContent = item.title;
    const page = document.createElement("small");
    page.textContent = item.page;
    link.append(title, page);
    searchResults.append(link);
  });
  if (!matches.length) {
    const empty = document.createElement("p");
    empty.textContent = "没有匹配章节。试试“水”“运行”或“反馈”。";
    searchResults.append(empty);
  } else if (all.length > matches.length) {
    const more = document.createElement("p");
    more.textContent = "显示前 12 项；输入更具体的关键词可缩小范围。";
    searchResults.append(more);
  }
});
searchInput.addEventListener("keydown", event => {
  if (event.key === "ArrowDown") {
    const first = searchResults.querySelector("a");
    if (first) { event.preventDefault(); first.focus(); }
  }
  if (event.key === "Escape") {
    searchInput.value = "";
    searchInput.dispatchEvent(new Event("input"));
  }
});

document.querySelectorAll(".prose table").forEach((table, index) => {
  const wrapper = document.createElement("div");
  wrapper.className = "table-scroll";
  wrapper.tabIndex = 0;
  wrapper.setAttribute("role", "region");
  wrapper.setAttribute("aria-label", "表格 " + (index + 1) + "，可横向滚动");
  table.before(wrapper);
  wrapper.append(table);
});

async function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try { await navigator.clipboard.writeText(text); return true; } catch (_) { /* file:// may need fallback */ }
  }
  const field = document.createElement("textarea");
  field.value = text;
  field.setAttribute("readonly", "");
  field.style.position = "fixed";
  field.style.opacity = "0";
  document.body.append(field);
  field.select();
  let copied = false;
  try { copied = document.execCommand("copy"); } finally { field.remove(); }
  return copied;
}
document.querySelectorAll(".prose pre").forEach(pre => {
  const text = pre.textContent;
  const wrapper = document.createElement("div");
  wrapper.className = "code-block";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-button";
  button.textContent = "复制";
  button.setAttribute("aria-label", "复制此代码块");
  pre.before(wrapper);
  wrapper.append(pre, button);
  button.addEventListener("click", async () => {
    let success = false;
    try { success = await copyText(text); } catch (_) { /* report manual fallback below */ }
    button.focus();
    button.textContent = success ? "已复制" : "请手动复制";
    document.getElementById("copy-status").textContent = success ? "代码已复制到剪贴板" : "浏览器未允许复制，请选中代码手动复制";
    window.setTimeout(() => { button.textContent = "复制"; }, 2200);
  });
});
