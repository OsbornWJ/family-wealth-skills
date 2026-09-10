# Hermes 运行时说明

## 邮箱/Cron状态（2026-06-04：已永久禁用）

**所有自动推送和定时任务已永久删除。** 2026-06-03事故：配置过程中发送了300+封测试邮件，用户邮箱被严重轰炸。

### 当前状态
- 所有cron任务已删除
- 所有邮件脚本及密码文件已删除
- `.env` 中EMAIL配置已清理

### 禁止事项
- ❌ 绝不发送任何测试/确认/自动邮件
- ❌ 绝不自动推送任何内容到邮箱
- ✅ 所有分析在对话中直接输出



## 脚本同步

若 cron 从 `~/.hermes/profiles/stunner/scripts/` 跑副本，改 skill 内 `scripts/*.py` 后需同步：

```bash
cp ~/.hermes/profiles/stunner/skills/data-science/a-share-daily-monitor/scripts/*.py \
   ~/.hermes/profiles/stunner/scripts/
```
