# scripts/ 运行前提

这里的脚本是**审计与取数工具**，不是 skill 的运行时依赖。激活 `ye-tianshi` 角色只需要 `SKILL.md` 与 `modules/`、`references/`、`cases/`；删掉 `scripts/` 不影响角色工作。

## 环境

- Python ≥ 3.8，**仅用标准库**（`re` / `os` / `sys` / `json` / `argparse` / `collections` / `unicodedata`），无需 `pip install`
- 原文必须是 UTF-8。若仍是 GB18030/Big5，先 `iconv -f GB18030 -t UTF-8 原文件 > 新文件`

## 路径约定

两个脚本都按自身位置推断 skill 根目录（`Path(__file__)/../..`），因此**从任何工作目录运行都可以**：

```bash
python3 path/to/ye-tianshi/scripts/judge_s11_check.py
python3 path/to/ye-tianshi/scripts/build_dosage_stats.py
```

原文目录不是 `modules/` 时用 `--src` 覆盖：

```bash
python3 scripts/build_dosage_stats.py --src ../modules --out /tmp/dosage.json
```

## 两个脚本

| 脚本 | 做什么 | 输入 | 输出 | 退出码 |
|---|---|---|---|---|
| `judge_s11_check.py` | 把 56 条答卷引文 + 11 篇名 + 18 门类归一化后逐字回查原著 | `modules/01–04` | stdout 逐条 OK/MISS + 总览 | 0 全命中 / 1 有 MISS / 2 输入缺失或编码非法 |
| `build_dosage_stats.py` | 抽取「数字 + 钱/两/分」结构，统计常用药剂量分布 | `modules/01–04` | `references/_dosage_raw.json`（默认） | 0 成功且回读一致 / 2 输入缺失 / 3 抽不到剂量 / 4 写入或回读失败 |

`judge_s11_check.py` 是 `references/15b-consistency-report.md` 的可复跑版本：报告说"全部命中"时，你应当能用它自己验一遍。

## 生成物不入库

`build_dosage_stats.py` 默认写 `references/_dosage_raw.json`（约 80 KB，234 味药 / 1,052 条剂量）。这是**可重跑的中间产物**，仓库里不提交；需要时执行脚本即可复现。`scripts/dosage_raw_samples.json` 是它的抽样快照，供不便运行脚本时查阅。

## 门类判据的四种形态

《临证指南医案》这份数字化文本里，门类标记并不统一，`judge_s11_check.py` 四种都认（只认 `##` 会把 `<篇名>腰腿足痛` 这类误判成缺失）：

```
## 痹                 ← Markdown 标题
<篇名>腰腿足痛         ← 篇名标记（全文 54 处）
<目录>卷十\幼科要略     ← 目录标记
……。咳嗽。……          ← 门首按语里的裸门类名
```

一律要求**整行精确匹配**，避免「痹」命中「痹证论」这类更长篇名。
