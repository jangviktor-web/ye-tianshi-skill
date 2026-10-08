# -*- coding: utf-8 -*-
"""统计 S11 两轮答卷（甲＝s11_answers.md／乙＝s11_answers_v2.md）的口头禅与结构频率。

用途：
    为 references/15b-consistency-report.md 里「『何以故耶』20 → 2 次」
    「『议治法：』骨架 18 → 0」这类结论提供可复跑的计数口径。

用法：
    python3 outputs/s11_phrase_count.py        # 从任意目录运行均可

退出码：
    0  正常；2 答卷文件缺失或为空

依赖：Python ≥ 3.8，仅用标准库（re / io / os / sys / collections）。
"""
import collections
import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    """读同目录答卷；失败时给出「什么／为什么／怎么修」。"""
    p = os.path.join(_HERE, name)
    if not os.path.isfile(p):
        sys.stderr.write("Error: 找不到答卷文件 %s\n"
                         "  原因: 本脚本与答卷同目录存放，文件被移动或缺失\n"
                         "  解决: 从发布包补回 %s，或确认在 ye-tianshi/outputs/ 内运行\n"
                         % (p, name))
        sys.exit(2)
    t = io.open(p, encoding="utf-8").read()
    if not t.strip():
        sys.stderr.write("Error: %s 为空文件\n"
                         "  原因: 答卷未落盘或被截断\n"
                         "  解决: 重新获取该答卷文件后重跑\n" % name)
        sys.exit(2)
    return t


A = _read("s11_answers.md")
B = _read("s11_answers_v2.md")

# strip the ⚠️ disclaimer lines for counting (same in both, but avoid noise)
def clean(t):
    return "\n".join(l for l in t.split("\n") if "⚠️" not in l)

A, B = clean(A), clean(B)

groups = {
 "设问式": ["何以故耶", "此何故", "何以堪此", "是……乎", "抑……乎", "其故何也", "其故何", "宁非", "得非", "岂", "焉能", "奈何", "乎？", "耶？"],
 "承接/标记词": ["盖", "夫", "至于", "若夫", "凡", "窃谓", "愚谓", "考", "按", "尝"],
 "立法词": ["议治法：", "议治法", "议用", "议以", "议泻", "议", "拟进", "拟用", "拟", "当与", "法当", "治当", "务在", "宗", "佐以", "兼以", "参以", "冀"],
 "收束池": ["一定理也", "乃定例也", "此内治之大法也", "则信乎千古定论也", "不可不知", "可不慎哉", "可不慎乎", "不可不慎之也", "但保其不至羸困则善矣", "观者详之", "非敢参末议也", "斯为难调", "其鉴之", "斯为善治者矣"],
 "骨架冒号": ["议治法：", "辨证：", "治法："],
}
for g, ps in groups.items():
    print("== " + g + " ==")
    for p in ps:
        a, b = A.count(p), B.count(p)
        if a or b:
            flag = ""
            if a >= 4 or b >= 4:
                flag = "  <<<"
            print("  %-16s 甲=%-3d 乙=%-3d%s" % (p, a, b, flag))
    print()

# 冒号列举式（议治法：X、Y、Z）
def colon_list(t):
    return len(re.findall(r"议治法：", t))
print("甲『议治法：』冒号列举 =", colon_list(A), "；乙 =", colon_list(B))
print("甲『议字号』总(议字) =", A.count("议"), "；乙 =", B.count("议"))

# 每题结构统计
def blocks(t):
    return re.split(r"^## 题目 ", t, flags=re.M)[1:]
ba, bb = blocks(A), blocks(B)
print("\n甲题数=%d 乙题数=%d" % (len(ba), len(bb)))

names = ["问诊互动(以舌/脉/食/便反问或请以见示)", "案片夹引(带姓名＋数字案)", "警示语(最忌/大忌/慎不可)",
         "收束句", "文末免责框"]
def feat(t):
    return dict(
        问诊反问=bool(re.search(r"须详察|详审|请以.*见示|见示|再议|详辨", t)),
        案片=bool(re.search(r"[（(][一二三四五六七八九十〇]{2,3}[）)]", t)),
        警示=bool(re.search(r"最忌|大忌|慎不可|最要|最须|切忌", t)),
        免责=t.count("⚠️"),
    )
import statistics

def dims(ba, bb):
    for nm, arr in (("甲", ba), ("乙", bb)):
        cnt = collections.Counter()
        for x in arr:
            f = feat(x)
            for k, v in f.items():
                if isinstance(v, bool):
                    cnt[k] += 1
                else:
                    cnt[k] += v
        print(nm, dict(cnt))

dims(ba, bb)
