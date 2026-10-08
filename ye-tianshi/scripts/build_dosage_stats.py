# -*- coding: utf-8 -*-
"""统计四部原著中常用药的清代剂量分布，生成 references/_dosage_raw.json。

用途：
    为 references/12（剂量思维）与 references/25（剂量卡）提供可复现的原始计数。
    脚本只做抽取与统计，不做任何医学判断；输出是文献统计，不是用药建议。

用法：
    python3 scripts/build_dosage_stats.py                 # 在 skill 根目录或任意目录均可
    python3 scripts/build_dosage_stats.py --src modules --out scripts/_dosage_raw.json

参数：
    --src PATH   原文所在目录，默认 <skill 根>/modules
    --out PATH   JSON 输出路径，默认 <skill 根>/references/_dosage_raw.json

退出码：
    0  成功，且输出文件已回读校验
    2  输入缺失（目录或某部原著文件不存在）
    3  抽取结果为空（多半是原文文件名/编码不符）
    4  输出写入或回读失败

依赖：Python ≥ 3.8，仅用标准库（re / os / json / argparse / collections）。
"""
import argparse
import collections
import json
import os
import re
import sys

# 逻辑名 → modules/ 内实际文件名。历史上本脚本跑在沙箱里，
# 读的是 source/<裸名>.md；仓库化后原文统一为 modules/0X_<裸名>.md。
FILE_MAP = {
    "wenshelun.md": "01_wenshelun.md",
    "linzheng-zhinan-yian.md": "02_linzheng-zhinan-yian.md",
    "yeshi-yian-cunzhen.md": "03_yeshi-yian-cunzhen.md",
    "yexuan-yiheng.md": "04_yexuan-yiheng.md",
}

NUM = "一二三四五六七八九十百半"
NUMS = "(?:[一二三四五六七八九十百]+|半)"
dmap = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "半": 0.5}


def die(code, what, why, fix):
    """统一错误出口：什么失败 / 为什么 / 怎么修。"""
    sys.stderr.write("Error: %s\n  原因: %s\n  解决: %s\n" % (what, why, fix))
    sys.exit(code)


def cn2num(s):
    s = s.strip()
    if not s:
        return None
    if s in dmap:
        return dmap[s]
    if "十" in s:
        p = s.split("十")
        l = dmap.get(p[0], 1) if p[0] else 1
        r = dmap.get(p[1], 0) if len(p) > 1 and p[1] else 0
        return l * 10 + r
    return None


drugs = ["桑叶", "冬桑叶", "鲜桑叶", "鲜菊叶", "青菊叶", "黄菊花", "甘菊炭", "菊花炭", "菊花", "野菊",
         "连翘心", "连翘", "鲜银花", "金银花", "银花", "鲜生地", "细生地", "小生地", "大生地", "生地",
         "炒麦冬", "麦冬", "天冬", "北沙参", "南沙参", "川石斛", "金石斛", "鲜金斛", "金斛", "川斛", "石斛",
         "陈阿胶", "清阿胶", "阿胶", "生白芍", "炒白芍", "白芍", "人参", "党参", "西洋参",
         "元参", "玄参", "知母", "生石膏", "石膏", "淡黄芩", "黄芩", "小川连", "川连", "川黄连", "黄连",
         "黑山栀", "黑栀皮", "山栀皮", "炒山栀", "山栀", "栀子", "丹皮", "牡丹皮", "赤芍", "乌犀角", "犀角",
         "羚羊角", "牛黄", "郁金", "石菖蒲", "菖蒲", "远志肉", "远志", "钩藤", "天麻", "川贝母", "川贝", "象贝", "贝母",
         "杏仁", "桔梗", "牛蒡子", "牛蒡", "薄荷梗", "薄荷", "荆芥", "防风", "桑枝", "桑皮", "骨皮",
         "茯苓皮", "云茯神", "抱木茯神", "茯神", "云苓", "茯苓", "泽泻", "猪苓", "苡仁", "薏苡",
         "川通草", "通草", "滑石", "寒水石", "木通", "陈皮白", "广皮白", "广皮", "陈皮", "橘红", "青皮",
         "枳实", "枳壳", "厚朴", "炒半夏", "半夏曲", "半夏", "姜皮", "大腹皮", "熟地", "熟地黄", "炒山药", "山药",
         "山萸肉", "萸肉炭", "萸肉", "五味子", "五味", "炒枸杞", "枸杞子", "枸杞", "女贞实", "女贞子", "旱莲草",
         "炙龟甲", "龟版胶", "龟甲", "龟板", "生鳖甲", "鳖甲胶", "鳖甲", "生牡蛎", "牡蛎", "龙骨", "九孔石决明", "石决明", "磁石", "淡菜",
         "玉竹", "天花粉", "花粉", "栝蒌皮", "栝蒌", "瓜蒌", "金铃子", "川楝子", "炒延胡", "延胡", "小茴香", "小茴",
         "当归身", "归身", "当归", "川芎", "桃仁", "红花", "紫丹参", "丹参", "益母草", "生香附", "香附", "青蒿", "白薇",
         "生甘草", "炙甘草", "甘草", "炙草", "大枣肉", "南枣肉", "南枣", "煨姜", "淡干姜", "炮干姜", "干姜", "生姜", "炮附子", "附子",
         "肉桂心", "肉桂", "川桂枝尖", "川桂枝", "桂枝尖", "桂枝", "黄柏", "龙胆草", "萆薢", "防己", "草决明", "谷精草", "夏枯草", "望月砂",
         "绿豆皮", "黑豆皮", "豆皮", "刺蒺藜", "白蒺藜", "沙苑子", "沙蒺藜", "沙苑", "人中黄", "金汁", "人中白",
         "鲜竹叶", "竹叶心", "竹叶", "竹沥", "芦根", "茅根", "鲜荷叶边", "鲜荷叶", "荷叶边", "荷叶", "浙贝",
         "生神曲", "神曲", "南山楂", "山楂", "炒麦芽", "麦芽", "生谷芽", "谷芽", "生白扁豆", "白扁豆", "秋石", "地骨皮", "冬瓜子", "紫菀", "苏子"]


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="抽取四部原著中的剂量并统计（文献统计，非用药建议）",
                                 add_help=True)
    ap.add_argument("--src", default=os.path.join(root, "modules"),
                    help="原文目录，默认 <skill 根>/modules")
    ap.add_argument("--out", default=os.path.join(root, "references", "_dosage_raw.json"),
                    help="JSON 输出路径，默认 <skill 根>/references/_dosage_raw.json")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        die(2, "原文目录不存在: %s" % args.src,
            "本脚本按 skill 根目录推断 modules/ 的位置，目录被移动或改名后推断会失效",
            "在 skill 根目录运行，或用 --src 指定，例如 --src /path/to/ye-tianshi/modules")

    missing = [f for f in FILE_MAP.values() if not os.path.isfile(os.path.join(args.src, f))]
    if missing:
        die(2, "缺少原著文件: %s" % ", ".join(missing),
            "modules/ 内容不完整，或文件名不符合 0X_<裸名>.md 约定",
            "核对 %s 下的文件名后重试；缺失者请从发布包补回" % args.src)

    dirs = collections.defaultdict(list)
    for logical, real in FILE_MAP.items():
        path = os.path.join(args.src, real)
        try:
            with open(path, encoding="utf-8") as fh:
                txt = fh.read()
        except UnicodeDecodeError as e:
            die(2, "%s 不是合法 UTF-8（%s）" % (real, e),
                "该文件可能仍是 GB18030/Big5 等旧编码",
                "先 iconv -f GB18030 -t UTF-8 转换，再重跑本脚本")
        for d in drugs:
            lb = r"(?<![\u4e00-\u9fff])"
            for pre, post in [(re.escape(d) + r"[（(]", r"\s*[）)]"), (re.escape(d), r"")]:
                pat = lb + pre + r"(" + NUMS + r")\s*(钱|两|分)(半)?" + post
                for m in re.finditer(pat, txt):
                    v = cn2num(m.group(1))
                    if v is None:
                        continue
                    val = float(v) + (0.5 if m.group(3) else 0)
                    u = m.group(2)
                    qian = val if u == "钱" else (val * 10 if u == "两" else val / 10.0)
                    dirs[d].append([round(val, 2), u, round(qian, 3), real])

    if not dirs:
        die(3, "未抽到任何剂量",
            "原文里没匹配到「数字+钱/两/分」结构，通常是文件被替换成了摘要本而非全本",
            "确认 --src 指向 modules/02、03、04 三部医案原文，而非 SKILL.md 摘要")

    def summ(d, units):
        s = [x for x in dirs[d] if x[1] in units]
        if not s:
            return None
        q = sorted(x[2] for x in s)
        return (len(s), q[0], q[-1], sum(q) / len(q), q[len(q) // 2])

    rows = []
    for d in drugs:
        r = summ(d, {"钱", "分"})
        if r and r[0] >= 2:
            rows.append((d,) + r)
    rows.sort(key=lambda x: -x[1])
    print("=== 煎剂/散剂（钱·分）常用药统计 ===")
    print("药名|n|最轻(钱)|最重(钱)|均值(钱)|中位(钱)|折克均值")
    for d, n, mn, mx, av, md in rows:
        print("%s|%d|%.2f|%.2f|%.2f|%.2f|%.1fg" % (d, n, mn, mx, av, md, av * 3.73))
    print()
    print("=== 丸/膏方（含两）大剂量 ===")
    for d in drugs:
        s = [x for x in dirs[d] if x[1] == "两"]
        if len(s) >= 2:
            q = sorted(x[0] for x in s)
            print("%s|n=%d|%s两" % (d, len(s), "/".join(str(int(x)) if x == int(x) else str(x)
                                                        for x in sorted(set(q)))))

    outdir = os.path.dirname(os.path.abspath(args.out))
    try:
        os.makedirs(outdir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(dirs, fh, ensure_ascii=False, indent=1)
    except OSError as e:
        die(4, "写入失败: %s（%s）" % (args.out, e),
            "目标目录不可写或路径是文件",
            "用 --out 指到可写位置，例如 --out scripts/_dosage_raw.json")

    # 写后回读校验：文件存在、可解析、条目数与内存一致
    try:
        with open(args.out, encoding="utf-8") as fh:
            back = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        die(4, "输出回读失败: %s（%s）" % (args.out, e),
            "写入被中断或磁盘满",
            "删除该文件后重跑；仍失败请检查磁盘空间")
    if len(back) != len(dirs):
        die(4, "输出条目数不符（回读 %d，内存 %d）" % (len(back), len(dirs)),
            "写入过程被截断", "重跑本脚本；若复现请附 --out 路径开 issue")
    print("\n已写出 %s（%d 味药，%d 条剂量，%.1f KB）"
          % (os.path.relpath(args.out, root), len(back),
             sum(len(v) for v in back.values()),
             os.path.getsize(args.out) / 1024))


if __name__ == "__main__":
    main()
