# 合并 shell.html + data.html → index.html（部署文件）
import re
base = '/home/hatch/workspace/bridge-deploy/'
shell = open(base + 'shell.html', encoding='utf-8').read()
data = open(base + 'data.html', encoding='utf-8').read()
a0 = data.index('<article class="doc">')
s0 = data.index('<script>')
article = data[a0:data.index('</article>') + len('</article>')]
script = data[s0:data.index('</script>') + len('</script>')]
out = shell.replace('<!--DATA-ARTICLE-->', article).replace('<!--DATA-SCRIPT-->', script)
open(base + 'index.html', 'w', encoding='utf-8').write(out)
print('built index.html 字节:', len(out.encode()))
