---
name: preserve-file-encoding
description: 保留文件原始编码和换行符不被修改。当 AI 需要编辑非 UTF-8 文件（如 GBK）、批量修改可能涉及多种编码的文件、或用户要求保留文件编码和换行符时使用。
---

# 保留文件编码与换行符

## 何时使用

- AI 需要编辑可能为 GBK/GB2312/GB18030 等非 UTF-8 编码的文件
- 用户要求「不要改变文件编码」或「保持原始编码」
- 批量修改文件后需要确认编码未被改变

## 前置配置（自动，首次触发时执行）

检查项目 `.vscode/settings.json` 是否包含 `"files.autoGuessEncoding": true`。
若不存在该配置，自动创建或追加：

```json
{
  "files.autoGuessEncoding": true
}
```

此设置使 Cursor 编辑器自动识别 GBK 等编码，StrReplace 修改文件时会以原始编码保存回去。

## 操作步骤

### 修改已有文件（常规）

1. **只用 StrReplace，不用 Write 覆写已有文件**。StrReplace 走编辑器缓冲区，`autoGuessEncoding` 会保证编码不变。

### 必须使用 Write 覆写时（特殊情况）

1. 先做快照：
   ```bash
   python .cursor/skills/preserve-file-encoding/scripts/encoding_guard.py snapshot <文件或目录>
   ```
2. 执行 Write 操作
3. 还原编码：
   ```bash
   python .cursor/skills/preserve-file-encoding/scripts/encoding_guard.py restore <文件或目录>
   ```

### 编辑后验证（可选）

```bash
python .cursor/skills/preserve-file-encoding/scripts/encoding_guard.py verify <文件或目录>
```

若有文件编码发生变化，会列出具体文件和变化详情。

## 脚本说明

脚本位于 `.cursor/skills/preserve-file-encoding/scripts/encoding_guard.py`，纯 Python 标准库，无外部依赖。

三个子命令：
- `snapshot` — 检测文件的编码、BOM、换行符，保存到 `.encoding-snapshot.json`
- `verify` — 对比当前状态与快照，报告变化
- `restore` — 将编码发生变化的文件还原为快照中的编码和换行符

## 注意事项

- 排除 `debug/`、`build/`、`node_modules/` 等编译产物目录
- 此 Skill 用于**保留**原始编码，不做编码转换。如需统一转为 UTF-8 BOM，请使用 `batch-utf8-bom-crlf` 技能
