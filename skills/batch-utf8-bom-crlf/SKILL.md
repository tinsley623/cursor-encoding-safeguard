---
name: batch-utf8-bom-crlf
description: 批量将指定目录下的文本文件转换为 UTF-8+BOM 编码与 CRLF 换行。在用户需要统一文件编码、修正换行符或批量转换源码为 UTF-8 BOM/CRLF 时使用。
---

# 批量 UTF-8 BOM + CRLF 转换

## 何时使用

- 用户要求「批量修改文件夹下的文件编码为 UTF-8+BOM，换行符 CRLF」
- 需要统一项目内 .cpp/.h 等源码的编码与换行（如满足 C++ 规范：BOM + CRLF）
- 需要将某目录下所有文本文件规范化编码与换行

## 操作步骤

1. **确认目标目录**：向用户确认要转换的文件夹路径（默认可为当前项目某子目录，如 `plugin_bundle` 或用户指定）。
2. **确认文件范围**：确认是否只处理特定扩展名（如 `.cpp`、`.h`、`.c`、`.hpp`），或全部文本文件。未指定时使用脚本默认：常见源码扩展名。
3. **执行转换脚本**：在项目根或指定工作目录运行：
   ```bash
   python .cursor/skills/batch-utf8-bom-crlf/scripts/convert_to_utf8_bom_crlf.py <目标目录> [扩展名列表]
   ```
   示例：
   ```bash
   python .cursor/skills/batch-utf8-bom-crlf/scripts/convert_to_utf8_bom_crlf.py plugin_bundle
   python .cursor/skills/batch-utf8-bom-crlf/scripts/convert_to_utf8_bom_crlf.py src .cpp .h .hpp .c
   ```
   可加 `--dry-run` 先列出将被转换的文件而不写入。
4. **检查结果**：脚本会输出已转换文件列表；若有解码失败会单独列出。建议用 git diff 确认变更后再提交。

## 脚本行为说明

- **编码**：尝试用 UTF-8、GBK、GB2312、Latin-1 等常见编码读取；写出统一为 **UTF-8 with BOM**。
- **换行**：统一为 **CRLF**（\r\n）。
- **二进制**：跳过无法按文本解码的文件，不覆盖。
- **备份**：不自动备份；重要目录建议先提交或备份后再运行。

## 可选：仅转换当前打开/指定文件

若用户仅需对少数文件转换，可手动操作：
- 在编辑器中打开文件 → 选择「UTF-8 with BOM」保存 → 确保换行设置为 CRLF。
- 或对单个文件运行：`python .../convert_to_utf8_bom_crlf.py -f path/to/single.cpp`

## 注意事项

- 排除 `debug/`、`debug_*/`、`build/`、`node_modules/` 等编译/依赖目录，避免误改生成文件。
- 若项目有部分文件必须保持无 BOM（如某些脚本），在运行前与用户确认或先用扩展名/路径排除。
