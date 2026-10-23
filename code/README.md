# 自动化代码（林志锋的个人系统，与网站同仓保存）

这里是为本人搭建的全部自动化程序本体。数据在仓库根目录 index.html（源数据 data.html 见本人邮箱备份），规矩在《个人交互数据桥》文档的《总规矩》里，恢复步骤见网站「接手与重建」模块第三节（从零开始重建教程）。

## 文件说明
- sentinel.py / start_sentinel.sh：BTC 突破哨兵（关键位提醒 + 工作日微信行情播报）
- bot_daemon.py：微信 iLink 机器人守护进程
- okx_read.py：OKX 只读接口（读余额、持仓、成交、委托）
- okx_watch.py：OKX 持仓盯守（按交易系统核查）
- live_gated.py：实盘闸门（风控检查 + 订单预览，设计上不发真实订单）
- okx_SYSTEM.md：交易系统定稿（主动交易加杠杆只做 BTC）
- shell.html / build.py：网站程序本体与构建脚本（shell.html 与 data.html 合并成 index.html）
- pagetest_test.js / pagetest_export-pdf.js：网站真渲染测试、PDF 导出
- reorder-doc.py：文档记录倒序重排工具
- hook_*.sh：三个唤醒脚本（微信收件、持仓盯守、止损盯价）
- cron_*.md：全部定时任务定义（保活、登记、备份、资产报告等 12 个）
- skill_*.md：给 AI 照着干活的操作手册（交易核查、止损审计、网站更新验证）
- connector_okx.md / connector_github.md：OKX 与 GitHub 的接入说明

## 密钥不在这里，永远不要上传
OKX 密钥、微信机器人凭据都只装在运行机器的本地文件里（.okx_readonly.json、creds.json、context.json），不进仓库。换机器或换 AI 时，由本人用自己的账号重新生成、重新扫码绑定。代码里读的都是这些本地文件，代码本身不含任何密钥。
