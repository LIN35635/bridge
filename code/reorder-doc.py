#!/usr/bin/env python3
# 文档按日期倒序重排：日志型块（睡眠日记录、健身训练小节、7.3、7.4 表格行）从新到旧
import re, sys

SRC = sys.argv[1]
html = open(SRC, encoding='utf-8').read()
orig_len = len(html)

def split_h5_blocks(text, start_marker, end_marker):
    """切出 start_marker 到 end_marker 之间的区域，按 <h5 边界切块，返回 (前缀, [块...], 后缀全串起止)"""
    i = text.index(start_marker)
    j = text.index(end_marker)
    region = text[i:j]
    parts = re.split(r'(?=<h5 )', region)
    head, blocks = parts[0], [p for p in parts[1:] if p.strip()]
    return i, j, head, blocks

def replace_region(text, i, j, new_region):
    return text[:i] + new_region + text[j:]

# ---------- 第六部分 睡眠：条目倒序 ----------
i, j, head, blocks = split_h5_blocks(html, '<h5 class="doc-sub" id="doc-p6-1">', '<h5 class="doc-sub" id="doc-p6-6">')
assert len(blocks) == 7, f'睡眠条目数异常: {len(blocks)}'
blocks.reverse()
# “一、每日睡眠记录｜”前缀：从 10-14 块移到 10-20 块
for k, b in enumerate(blocks):
    if '2026年10月14日' in b:
        blocks[k] = b.replace('一、每日睡眠记录｜2026年10月14日', '2026年10月14日')
    if '2026年10月20日' in b:
        blocks[k] = b.replace('2026年10月20日', '一、每日睡眠记录（按日期从新到旧）｜2026年10月20日')
html = replace_region(html, i, j, head + ''.join(blocks))
print('睡眠：7 条已倒序（10-20 在前）')

# ---------- 第五部分 健身：训练小节倒序 ----------
i, j, head, blocks = split_h5_blocks(html, '<h5 class="doc-sub" id="doc-p5-4">', '<h5 class="doc-sub" id="doc-p5-6">')
assert len(blocks) == 3, f'健身小节数异常: {len(blocks)}'
blocks.reverse()
for k, b in enumerate(blocks):
    if '10月13日' in b:
        blocks[k] = b.replace('二、已完成的力量训练｜2026年10月13日', '2026年10月13日')
    if '10月19日' in b:
        blocks[k] = b.replace('2026年10月19日', '二、已完成的力量训练（按日期从新到旧）｜2026年10月19日')
html = replace_region(html, i, j, head + ''.join(blocks))
print('健身：3 个训练小节已倒序（10-19 在前）')

# ---------- 表格行倒序（7.3 / 7.4） ----------
def reverse_table_rows(text, anchor_id):
    k = text.index(f'id="{anchor_id}"')
    t0 = text.index('<tbody>', k)
    t1 = text.index('</tbody>', t0)
    body = text[t0 + len('<tbody>'):t1]
    parts = re.split(r'(<tr(?:\s[^>]*)?>.*?</tr>)', body, flags=re.S)
    rows = [p for p in parts if p.lstrip().startswith('<tr')]
    seps = [p for p in parts if not p.lstrip().startswith('<tr')]
    residue = ''.join(seps)
    assert len(rows) >= 3, f'{anchor_id} 行数异常: {len(rows)}'
    assert residue.strip() == '', f'{anchor_id} 仍有行外残留，停止重排: {residue.strip()[:80]}'
    pre, post, mids = seps[0], seps[-1], seps[1:-1]
    units = []
    for idx, r in enumerate(rows):
        units.append(r + (mids[idx] if idx < len(mids) else ''))
    units.reverse()
    new_body = pre + ''.join(units) + post
    return text[:t0 + len('<tbody>')] + new_body + text[t1:], len(rows)

html, n73 = reverse_table_rows(html, 'doc-m7-4')
print(f'7.3：{n73} 行已倒序')
html, n74 = reverse_table_rows(html, 'doc-m7-5')
print(f'7.4：{n74} 行已倒序')

# ---------- 导航链接顺序同步（第五、六部分） ----------
def reverse_nav_links(text, part_id, ids):
    k = text.index(f'id="{part_id}"')
    n0 = text.index('<nav', k)
    n1 = text.index('</nav>', n0)
    nav = text[n0:n1]
    found = {}
    for link_id in ids:
        m = re.search(r'<a href="#' + link_id + r'">[^<]*</a>', nav)
        assert m, f'导航链接缺失: {link_id}'
        found[link_id] = m.group(0)
    rev = list(ids)[::-1]
    # 用占位符逐个替换，避免互相覆盖
    for idx, link_id in enumerate(ids):
        nav = nav.replace(found[link_id], f'\x00{idx}\x00')
    for idx, link_id in enumerate(ids):
        nav = nav.replace(f'\x00{idx}\x00', found[rev[idx]])
    return text[:n0] + nav + text[n1:]

html = reverse_nav_links(html, 'part-6', ['doc-p6-1', 'doc-p6-2', 'doc-p6-3', 'doc-p6-4', 'doc-p6-5', 'doc-p6-5b', 'doc-p6-5c'])
html = reverse_nav_links(html, 'part-5', ['doc-p5-4', 'doc-p5-5', 'doc-p5-11'])
print('导航：第五、六部分日期链接已倒序')

# 睡眠 p6-0 记录范围补到 10-20
html = html.replace('记录日期：2026年10月14日—10月18日', '记录日期：2026年10月14日—10月20日')

open(SRC, 'w', encoding='utf-8').write(html)
print(f'完成。总长度 {orig_len} → {len(html)}（差 {len(html)-orig_len}，应仅为小注文字）')
