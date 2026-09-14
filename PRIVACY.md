# 隐私（说人话版）

## 仓库里该有啥

- Skill 流程、示例配置（`*.example.*`）
- 读本地持仓的脚本
- 虚构 / 脱敏演示

## 千万别推进公开仓库的

| 东西 | 为啥 |
|------|------|
| `*.local.md` / `*.local.json` | 这是你家底和成本 |
| 券商导出、持仓截图 | 一眼能认出你 |
| 带真实盈亏的会话日记 | 交易隐私 |
| 邮箱、手机、身份证、银行卡 | 个人身份信息 |

开 PR 之前扫一眼 staged 文件，别手滑。

本地自己加个 ignore 也很香：

```gitignore
**/*.local.md
**/*.local.json
**/portfolio.local.*
```

## 第三方

行情脚本会请求腾讯、新浪、东财、baostock 等**公开接口**。本仓库不内置你的券商账号。  
邮件封装（`email_wrapper.py`）只用环境变量里的 SMTP，仓库里不该出现密码。

装错了想清数据：用 `reset-local.sh` / `uninstall.sh`（见 README）。
