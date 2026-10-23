// Bridge 网站真渲染测试：node test.js <html文件路径>
// 场景A 全新存储 / 场景B 本地存储被空数组污染；断言零脚本错误 + 各模块关键数字
const fs = require('fs');
const { JSDOM } = require('jsdom');
const path = process.argv[2];
if (!path) { console.error('用法: node test.js <html路径>'); process.exit(2); }
const html = fs.readFileSync(path, 'utf8');

function run(label, poison) {
  const errors = [];
  const dom = new JSDOM(html, {
    url: 'https://lin35635.github.io/bridge/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    beforeParse(window) {
      window.addEventListener('error', e => errors.push('window.onerror: ' + e.message));
      if (poison) {
        const keys = ['bridge_debts_v4','bridge_trades_v4','bridge_lifes_v4','bridge_reverses_v4','bridge_expenses_v4','bridge_incomes_v4','bridge_sleeps_v4','bridge_reviews_v4'];
        keys.forEach(k => window.localStorage.setItem(k, '[]'));
      }
    }
  });
  const d = dom.window.document;
  const txt = id => { const el = d.getElementById(id); return el ? el.textContent.trim() : '(无此元素)'; };
  const count = id => { const el = d.getElementById(id); return el ? el.children.length : -1; };
  console.log('==== ' + label + ' ====');
  console.log('脚本错误:', errors.length ? errors : '无');
  console.log('债务剩余 remainNum:', txt('remainNum'));
  console.log('到账 本月/累计/条数:', txt('iMonthTotal'), '/', txt('iAllTotal'), '/', txt('iAllCount'), '| 明细条数:', count('incomeEntries'));
  console.log('睡眠 已记录晚数:', txt('sCount'), '| 近7天平均:', txt('sAvg'), '| 明细条数:', count('sleepEntries'));
  console.log('交易 明细条数:', count('tradeEntries'));
  console.log('健身 明细条数:', count('lifeEntries'));
  dom.window.close();
}
run('场景A：全新浏览器（无本地存储）', false);
run('场景B：本地存储被空数组污染', true);
