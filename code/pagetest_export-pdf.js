// 《个人交互数据桥》PDF 导出器
// 用法: node export-pdf.js [YYYY-MM-DD]  （缺省用今天）
// 从 space-2.html 提取文档容器 → 生成带打印样式的独立 HTML → 调无头 Chrome 打成 PDF
const fs = require('fs');
const { JSDOM } = require('jsdom');
const { execFileSync } = require('child_process');

const SRC = '/home/hatch/workspace/bridge-deploy/data.html';
const OUTDIR = '/home/hatch/workspace/your_files';
const WORKDIR = '/home/hatch/workspace/bridge-deploy/pagetest';
const date = process.argv[2] || new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Shanghai' });

const html = fs.readFileSync(SRC, 'utf8');
const dom = new JSDOM(html);
const d = dom.window.document;
let container = d.querySelector('article.doc');
if (!container || !container.querySelector('#doc-m7-4')) { console.error('找不到文档容器'); process.exit(1); }
const chars = container.textContent.replace(/\s+/g, '').length;

const css = `
@page { size: A4; margin: 18mm 16mm 16mm 16mm; @bottom-center { content: "个人交互数据桥 · 第 " counter(page) " 页"; font-size: 8pt; color: #999; } }
* { box-sizing: border-box; }
body { font-family: "Noto Sans CJK SC", "Source Han Sans SC", sans-serif; font-size: 10.5pt; line-height: 1.7; color: #1c1c1e; margin: 0; }
.cover { border-bottom: 2.5px solid #0a5cff; padding-bottom: 14px; margin-bottom: 22px; }
.cover h1 { font-size: 24pt; margin: 0 0 6px 0; letter-spacing: 1px; }
.cover .meta { color: #555; font-size: 10pt; }
h3.doc-part { font-size: 16pt; color: #0a5cff; border-bottom: 1.5px solid #d7e3ff; padding-bottom: 5px; margin: 26px 0 12px 0; page-break-before: always; }
h3.doc-part:first-of-type { page-break-before: avoid; }
h4 { font-size: 12.5pt; margin: 18px 0 8px 0; color: #111; }
h5.doc-sub { font-size: 11pt; margin: 14px 0 6px 0; color: #333; }
.doc-body { white-space: pre-wrap; margin: 6px 0 12px 0; }
.doc-table-wrap { overflow: visible; margin: 8px 0 16px 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.3pt; line-height: 1.55; }
th, td { border: 0.6pt solid #c9ccd4; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #eef3ff; font-weight: 600; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
a { color: #0a5cff; text-decoration: none; }
.doc-nav, nav { font-size: 9.5pt; color: #555; line-height: 1.9; }
ul, ol { margin: 6px 0 10px 0; }
`;

const out = `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>个人交互数据桥（${date}）</title><style>${css}</style></head>
<body>
<div class="cover"><h1>个人交互数据桥</h1>
<div class="meta">个人数据档案（离线存档版）<br>导出日期：${date}　|　正文字数：约 ${chars.toLocaleString()} 字　|　内容与网站「我的文档」一致，文档为唯一事实源</div></div>
${container.innerHTML}
</body></html>`;

const htmlPath = `${WORKDIR}/personal-bridge-${date}.html`;
const pdfPath = `${OUTDIR}/personal-bridge-${date}.pdf`;
fs.writeFileSync(htmlPath, out, 'utf8');
execFileSync('/home/hatch/assets/artifacts/headless-shell/chrome-headless-shell', ['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage', '--no-pdf-header-footer', `--print-to-pdf=${pdfPath}`, `file://${htmlPath}`], { stdio: 'pipe' });
const sz = fs.statSync(pdfPath).size;
fs.copyFileSync(pdfPath, `${OUTDIR}/personal-bridge-latest.pdf`);
console.log(`PDF 已生成: ${pdfPath} (${(sz / 1024).toFixed(0)} KB, 正文 ${chars} 字)，常驻版 personal-bridge-latest.pdf 已同步刷新`);
