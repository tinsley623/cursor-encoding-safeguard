# AI 编码安全体系（1 Rule + 2 Skills）

## 问题背景

AI 控制不了编辑器底层的二进制行为。Cursor 编辑工具写回文件时会丢失 UTF-8 BOM，AI 无法阻止。许多 MSVC C++ 项目要求所有源码 UTF-8 BOM + CRLF，丢 BOM 直接导致编译报错。

加上项目历史积累的编码混乱（GBK、无 BOM UTF-8、LF/CRLF 混杂），需要一套工具体系来保障编码安全。

## 为什么需要脚本托底

**核心思路**：AI 管不了二进制层的事，全部用脚本托底。Rule 告诉 AI 何时调脚本，Skill 提供脚本本身。

```mermaid
flowchart LR
    A["AI 下达编辑指令"] --> B["Cursor 编辑器执行"]
    B --> C["二进制层丢失 BOM / 改变编码"]
    C --> D["脚本检测并修复"]
    D --> E["文件编码安全"]

    style A fill:#4a90d9,color:#fff
    style B fill:#e8a838,color:#fff
    style C fill:#d94a4a,color:#fff
    style D fill:#50b86c,color:#fff
    style E fill:#50b86c,color:#fff
```

## 三工具闭环

```mermaid
flowchart TD
    AI["Cursor AI 编辑文件"]

    AI --> P1["StrReplace — 丢 BOM"]
    AI --> P2["Write — 丢编码"]
    AI --> P3["存量编码混乱 — 需治理"]

    P1 --> T1["🛡️ Rule: preserve-encoding<br/>自动恢复 BOM"]
    P2 --> T2["🔒 Skill: preserve-file-encoding<br/>snapshot / verify / restore"]
    P3 --> T3["🔧 Skill: batch-utf8-bom-crlf<br/>批量统一 UTF-8 BOM + CRLF"]

    style AI fill:#4a90d9,color:#fff
    style P1 fill:#d94a4a,color:#fff
    style P2 fill:#d94a4a,color:#fff
    style P3 fill:#e8a838,color:#fff
    style T1 fill:#50b86c,color:#fff
    style T2 fill:#50b86c,color:#fff
    style T3 fill:#50b86c,color:#fff
```

## 各工具说明

| 工具 | 类型 | 做什么 | 何时用 |
|---|---|---|---|
| `batch-utf8-bom-crlf` | Skill | 批量统一编码为 UTF-8 BOM + CRLF | 存量治理，跑一次清干净 |
| `preserve-encoding` | Rule | 强制 AI 每次编辑后恢复 BOM | 日常防护，自动生效 |
| `preserve-file-encoding` | Skill | snapshot/verify/restore 编码守卫 | 兜底：Write 覆写、GBK 保留、批量验证 |

## 作用时机

```mermaid
timeline
    title 工具作用时机
    section 项目初始化
        batch-utf8-bom-crlf : 批量统一存量编码 : 跑一次清干净
    section 日常开发（每次编辑）
        preserve-encoding (Rule) : StrReplace 后自动恢复 BOM : alwaysApply 自动生效
    section 特殊操作
        preserve-file-encoding : snapshot → Write → restore : 保护 GBK、批量验证
```

## 为什么三个都需要？

```mermaid
flowchart LR
    subgraph 缺少任何一个都有漏洞
        A["❌ 没有 batch Skill"] --> A1["存量编码混乱<br/>无法一次性治理"]
        B["❌ 没有 Rule"] --> B1["AI 每次编辑都丢 BOM<br/>完全靠人记得跑脚本"]
        C["❌ 没有 encoding Skill"] --> C1["Write 覆写和 GBK 文件<br/>无法保护"]
    end

    style A fill:#d94a4a,color:#fff
    style B fill:#d94a4a,color:#fff
    style C fill:#d94a4a,color:#fff
    style A1 fill:#ffcccc,color:#333
    style B1 fill:#ffcccc,color:#333
    style C1 fill:#ffcccc,color:#333
```
