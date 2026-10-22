#!/usr/bin/env python3
"""Build the offline engineering manual with Pandoc and Python's stdlib.

Only derived files under site/ are replaced. Markdown, reports and run evidence
remain untouched. Run from any directory; Pandoc must be available on PATH.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
from urllib.parse import quote, unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGES = [
    ("README.md", "index.html", "项目概览", "从构型分布到结构系综", "目标、当前边界与阅读入口"),
    ("docs/tutorial.md", "tutorial.html", "使用教程", "从配置到结果", "启动、运行、检查与反馈"),
    ("docs/research_program.md", "research.html", "研究方案", "从工程示例到独立研究", "研究假设、对照实验与停止标准"),
    ("docs/generative_theory.md", "theory.html", "数学推导", "从概率分布到生成与验证", "流、扩散、概率路径及非晶响应"),
    ("docs/real_generation_results.md", "generation.html", "生成示例", "单珠水冰：真实预训练采样", "独立示例、生成构型与复跑步骤"),
    ("docs/literature_survey.md", "literature.html", "文献调研", "已有方法与证据边界", "水、非晶与聚合物的分布学习"),
    ("docs/technical_roadmap.md", "roadmap.html", "技术路线", "从可运行到可验证", "模型选择、科学验收与两条反馈回环"),
    ("docs/potentials_and_environment.md", "environment.html", "势与环境", "参考势与运行前置条件", "复用权重、环境和适用范围"),
    ("docs/smoke_results.md", "evidence.html", "执行证据", "CPU 冒烟执行记录", "实际命令、作业、日志与验证边界"),
    ("docs/documentation_patterns.md", "documentation.html", "文档案例", "可借鉴的科学与工程文档", "GitHub实例、项目技能与采用方式"),
]
SOURCE_TO_PAGE = {(ROOT / p[0]).resolve(): p[1] for p in PAGES}


def escaped(value):
    return html.escape(str(value), quote=True)


def local_url(path):
    return quote(os.path.relpath(path, SITE).replace(os.sep, "/"), safe="/")


def rewrite_url(url, source):
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
        return url
    target = (source.parent / unquote(parts.path)).resolve()
    if target == ROOT / "reports":
        return "#pdf-downloads"
    destination = SOURCE_TO_PAGE.get(target, local_url(target))
    return urlunsplit(("", "", destination, parts.query, parts.fragment))


def walk_links(value, source):
    if isinstance(value, dict):
        if value.get("t") in ("Link", "Image"):
            value["c"][-1][0] = rewrite_url(value["c"][-1][0], source)
        for child in value.values():
            walk_links(child, source)
    elif isinstance(value, list):
        for child in value:
            walk_links(child, source)


def convert(pandoc, source):
    result = subprocess.run([pandoc, "--from=markdown", "--to=json", str(source)],
                            check=True, stdout=subprocess.PIPE, encoding="utf-8")
    document = json.loads(result.stdout)
    if document["blocks"] and document["blocks"][0].get("t") == "Header":
        if document["blocks"][0]["c"][0] == 1:
            document["blocks"].pop(0)
    walk_links(document, source)
    result = subprocess.run([pandoc, "--from=json", "--to=html5", "--mathml", "--no-highlight", "--wrap=none"],
                            input=json.dumps(document, ensure_ascii=False), check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    if "Could not convert TeX math" in result.stderr:
        raise RuntimeError("MathML conversion failed in " + str(source) + ":\n" + result.stderr)
    # MathML tables retain an intrinsic width. An HTML region supplies a genuine
    # scroll container so long derivations remain readable on a narrow screen.
    # Pandoc 2.12's texmath emits unitless sizes for \big/\Big delimiters;
    # Firefox requires an explicit length/percentage. A legacy unitless value
    # is a multiplier of the reference glyph size, hence convert to percent.
    output = re.sub(r'\b(minsize|maxsize)="([0-9]+(?:\.[0-9]+)?)"',
                    lambda m: '{}="{:g}%"'.format(m[1], float(m[2]) * 100), result.stdout)
    output = re.sub(r'<img src="([^"]*figures/research_v2/[^"]+\.svg)"([^>]*)>',
                    r'<a class="diagram-link" href="\1" target="_blank" rel="noopener" aria-label="打开矢量流程图，可放大查看"><img src="\1"\2></a>',
                    output)
    return re.sub(r'<p>(<math display="block".*?</math>)</p>',
                  r'<div class="math-scroll" role="region" tabindex="0" aria-label="公式，可横向滚动">\1</div>',
                  output, flags=re.S)


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicate_ids = []
        self.links = []
        self.headings = []
        self._heading = None
        self.math_count = 0
        self.external_assets = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                self.duplicate_ids.append(attrs["id"])
            self.ids.add(attrs["id"])
        if tag in ("h2", "h3") and attrs.get("id"):
            self._heading = [tag, attrs["id"], []]
        if tag == "math":
            self.math_count += 1
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])
        if tag in ("script", "link", "img", "iframe", "source"):
            resource = attrs.get("src") or (attrs.get("href") if tag == "link" else "")
            if resource and (urlsplit(resource).scheme in ("http", "https") or resource.startswith("//")):
                self.external_assets.append(resource)

    def handle_data(self, data):
        if self._heading:
            self._heading[2].append(data)

    def handle_endtag(self, tag):
        if self._heading and tag == self._heading[0]:
            self.headings.append((self._heading[0], self._heading[1], "".join(self._heading[2]).strip()))
            self._heading = None


def inspect(content):
    parser = Inspector()
    parser.feed(content)
    return parser


def pdf_panel():
    snapshots = []
    reports = ROOT / "reports"
    if reports.exists():
        for survey in reports.rglob("literature_survey.pdf"):
            roadmap = survey.parent / "technical_roadmap.pdf"
            if roadmap.is_file() and survey.stat().st_size and roadmap.stat().st_size:
                group=[survey,roadmap]
                example=survey.parent/'bgmat_cpu_generation.pdf'
                if example.is_file(): group.append(example)
                research=survey.parent/'research_program.pdf'
                if research.is_file(): group.append(research)
                patterns=survey.parent/'documentation_patterns.pdf'
                if patterns.is_file(): group.append(patterns)
                snapshots.append(group)
    paths = max(snapshots, key=lambda group: max(path.stat().st_mtime_ns for path in group)) if snapshots else []
    if paths:
        items = "".join('<li><a href="{}">{}</a><span>{} KB</span></li>'.format(
            escaped(local_url(path)), escaped(str(path.relative_to(ROOT / "reports"))),
            max(1, round(path.stat().st_size / 1024))) for path in paths)
        contents = '<ul class="download-list">' + items + "</ul>"
    else:
        contents = '<p>尚无 PDF 快照。生成报告后重新构建站点，下载链接会自动加入。</p>'
    return '<section class="downloads" id="pdf-downloads" aria-labelledby="pdf-title"><h2 id="pdf-title">PDF 快照</h2>' + contents + "</section>"


PIPELINE = """<section class="pipeline" aria-labelledby="pipeline-title">
  <h2 id="pipeline-title">研究路径</h2>
  <ol>
    <li><strong>定义条件</strong><span>组成、温度、密度与制备历史</span></li>
    <li><strong>学习分布</strong><span>构型样本与物理约束</span></li>
    <li><strong>采样系综</strong><span>生成器、种子与版本记录</span></li>
    <li><strong>独立验证</strong><span>分布、物理量与反馈更新</span></li>
  </ol>
  <p>仓库分别维护研究项目与公共工具。已有CPU调度检查和bgmat真实生成示例；新模型训练及完整科学验收由各课题独立推进。</p>
</section>"""


def render(page, body, headings, pdfs):
    source, filename, label, title, subtitle = page
    navigation = "".join('<a{} href="{}"><span>{}</span><small>{}</small></a>'.format(
        ' aria-current="page"' if item[1] == filename else "", item[1], escaped(item[2]), escaped(item[4]))
        for item in PAGES)
    toc = "".join('<li class="level-{}"><a href="#{}">{}</a></li>'.format(
        level, escaped(quote(anchor)), escaped(text)) for level, anchor, text in headings)
    index = PAGES.index(page)
    adjacent = []
    if index:
        adjacent.append('<a href="{}"><small>上一页</small><span>{}</span></a>'.format(PAGES[index - 1][1], PAGES[index - 1][2]))
    if index + 1 < len(PAGES):
        adjacent.append('<a href="{}"><small>下一页</small><span>{}</span></a>'.format(PAGES[index + 1][1], PAGES[index + 1][2]))
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#17324d">
  <title>{label} | Gen_X 工程手册</title>
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/search-index.js" defer></script>
  <script src="assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">跳到正文</a>
  <header class="mobile-header"><a href="index.html">Gen_X <span>工程手册</span></a><button id="menu-toggle" aria-expanded="false" aria-controls="sidebar" type="button">目录</button></header>
  <aside class="sidebar" id="sidebar" aria-label="文档导航">
    <a class="brand" href="index.html"><span class="brand-symbol" aria-hidden="true">G<span>×</span></span><span><strong>Gen_X</strong><small>构型分布与结构生成</small></span></a>
    <div class="search"><label for="search-input">查找文档章节</label><input type="search" id="search-input" placeholder="试试：水、Slurm、反馈" autocomplete="off" aria-controls="search-results"><div id="search-results" hidden></div><span id="search-status" class="visually-hidden" role="status"></span></div>
    <nav class="primary-nav" aria-label="主要页面">{navigation}</nav>
    <div class="sidebar-bottom"><p><span class="status-dot" aria-hidden="true"></span>已有真实生成示例</p><small>CPU运行；科研统计验收另列</small><a href="#pdf-downloads">查看 PDF 快照</a><a href="../README.md">仓库 Markdown 入口</a></div>
  </aside>
  <main class="page" id="main" tabindex="-1">
    <div class="page-top"><span>Gen_X / {label}</span><a href="{source_url}">查看 Markdown 源文档</a></div>
    <header class="page-heading"><h1>{title}</h1><p>{subtitle}</p></header>
    <div class="scope-note"><strong>能力与证据</strong><span>公共调度smoke与真实生成示例分开记录。bgmat已输出8个216粒子构型；这不替代完整的分布与物性验证。</span></div>
    <div class="article-grid"><article class="prose">{pipeline}{body}</article><aside class="toc" aria-label="本页章节"><details open><summary>本页章节</summary><ol>{toc}</ol></details></aside></div>
    {pdfs}
    <nav class="adjacent" aria-label="相邻页面">{adjacent}</nav>
    <footer class="page-footer"><span>Gen_X 工程手册</span><span>Markdown 为内容源 · 本地资源 · MathML 公式</span><a href="#main">回到顶部</a></footer>
  </main>
  <span id="copy-status" class="visually-hidden" role="status"></span>
</body>
</html>
""".format(description=escaped(subtitle), label=escaped(label), title=escaped(title),
           subtitle=escaped(subtitle), source_url=escaped(local_url(ROOT / source)),
           navigation=navigation, body=body, pipeline=PIPELINE if filename == "index.html" else "",
           toc=toc, pdfs=pdfs, adjacent="".join(adjacent))


def validate():
    parsed = {SITE / page[1]: inspect((SITE / page[1]).read_text(encoding="utf-8")) for page in PAGES}
    errors = []
    checked = 0
    math_count = 0
    for path, document in parsed.items():
        math_count += document.math_count
        errors.extend(str(path.relative_to(SITE)) + ": duplicate ID " + value for value in document.duplicate_ids)
        errors.extend(str(path.relative_to(SITE)) + ": external asset " + value for value in document.external_assets)
        for link in document.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            checked += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.exists():
                errors.append(str(path.relative_to(SITE)) + ": missing target " + link)
            elif parts.fragment and target in parsed and unquote(parts.fragment) not in parsed[target].ids:
                errors.append(str(path.relative_to(SITE)) + ": missing fragment " + link)
    if not math_count:
        errors.append("No MathML formulas generated")
    report = {"status": "passed" if not errors else "failed", "html_pages": len(parsed),
              "checked_local_links": checked, "mathml_elements": math_count,
              "external_runtime_assets": sum(len(p.external_assets) for p in parsed.values()),
              "errors": errors,
              "scope": "Static local target/fragment, duplicate ID, MathML and external asset checks; not a browser test"}
    return report


def build():
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("Pandoc is required: place the existing pandoc executable on PATH.")
    for asset in ("style.css", "site.js"):
        if not (SITE / "assets" / asset).is_file():
            raise SystemExit("Missing local asset: site/assets/" + asset)
    search_index = []
    pdfs = pdf_panel()
    for page in PAGES:
        source = ROOT / page[0]
        body = convert(pandoc, source)
        headings = inspect(body).headings
        (SITE / page[1]).write_text(render(page, body, headings, pdfs), encoding="utf-8")
        search_index.append({"title": page[3], "page": page[2], "url": page[1]})
        for _, anchor, title in headings:
            search_index.append({"title": title, "page": page[2], "url": page[1] + "#" + quote(anchor)})
    (SITE / "assets" / "search-index.js").write_text(
        "window.GENX_SEARCH = " + json.dumps(search_index, ensure_ascii=False) + ";\n", encoding="utf-8")
    result = validate()
    result["sources_sha256"] = {page[0]: hashlib.sha256((ROOT / page[0]).read_bytes()).hexdigest() for page in PAGES}
    result["built_utc"] = datetime.now(timezone.utc).isoformat()
    result["builder_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (SITE / "build-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build()
