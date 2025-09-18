# crawlers


### list

+ app_spider (app 应用市场的爬虫)
+ maimai_spider
 + cex (中心化交易所/网络状态等脚本)

## 使用说明 - CEX 脚本

- 运行示例：`python cex/okx-network-status.py`
- 发送 Lark 机器人通知：请先设置环境变量 `LARK_WEBHOOK_URL`
  - macOS/Linux: `export LARK_WEBHOOK_URL="https://open.larksuite.com/open-apis/bot/v2/hook/xxx"`
  - Windows PowerShell: `$Env:LARK_WEBHOOK_URL = "https://open.larksuite.com/open-apis/bot/v2/hook/xxx"`
- 未设置时，脚本会记录警告并跳过发送 webhook。

### Lark 消息格式

- 已切换为交互式卡片（interactive card），更适合长文本与结构化信息。
- 卡片结构：
  - `msg_type: interactive`
  - `card.header.title`: 各脚本自定义标题（如 “Binance 网络状态变更”）。
  - `card.elements[0].text`: 使用 `lark_md` + 代码块展示合并后的日志文本。
- 注意：若需要富样式/按钮，可在 `card.elements` 中按需拓展。
