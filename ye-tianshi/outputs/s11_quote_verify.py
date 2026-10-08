# -*- coding: utf-8 -*-
"""S11 引文核验（首轮口径）：把答卷引文只留汉字后回查四部原著。

与后继脚本的关系：
    scripts/judge_s11_check.py 用 NFKC + 去标点空格归一化，并额外核篇名与门类，
    是交付口径；本脚本只保留汉字（`[^\\u4e00-\\u9fff]` 全删），是 15b 报告
    首轮统计的原始口径。保留本文件是为了让首轮数字可复现，日常核验请用后继版。

用法：
    python3 outputs/s11_quote_verify.py        # 从任意目录运行均可

退出码：
    0  正常；2 modules/ 缺失、原著文件缺失或为空

依赖：Python ≥ 3.8，仅用标准库（re / io / os / sys）。
"""
import io
import os
import re
import sys

MOD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "modules")

files = {
    "温热论": os.path.join(MOD, "01_wenshelun.md"),
    "临证指南医案": os.path.join(MOD, "02_linzheng-zhinan-yian.md"),
    "叶氏医案存真": os.path.join(MOD, "03_yeshi-yian-cunzhen.md"),
    "叶选医衡": os.path.join(MOD, "04_yexuan-yiheng.md"),
}


def _die(what, why, fix):
    sys.stderr.write("Error: %s\n  原因: %s\n  解决: %s\n" % (what, why, fix))
    sys.exit(2)


if not os.path.isdir(MOD):
    _die("原文目录不存在: %s" % os.path.abspath(MOD),
         "脚本按自身位置取上级 modules/，目录结构被改动后推断失效",
         "确认本文件位于 ye-tianshi/outputs/ 下，且同级有 modules/ 目录")
_missing = [os.path.basename(v) for v in files.values() if not os.path.isfile(v)]
if _missing:
    _die("缺少原著文件: %s" % ", ".join(_missing),
         "modules/ 不完整，缺哪部就会让该部的引文全被判为未命中",
         "从发布包补回这些文件后重跑")
texts = {}
for k, v in files.items():
    t = io.open(v, encoding="utf-8").read()
    if not t.strip():
        _die("%s 为空文件" % os.path.basename(v), "原文未落盘或被截断",
             "重新获取该文件后重跑")
    texts[k] = t
norm = {k: re.sub(r"[^\u4e00-\u9fff]", "", v) for k, v in texts.items()}
SKIP = {"临证指南医案", "目录", "未整理"}

def nsec(txt, idx, book):
    head = txt[:idx]
    if book == "临证指南医案":
        pats = []
        for m in re.finditer(r"<篇名>([^\n<]{1,30})", head):
            pats.append((m.start(), m.group(1).strip()))
        for m in re.finditer(r"^##\s*([^\n]{1,30})", head, re.M):
            nm = m.group(1).strip()
            if nm not in SKIP:
                pats.append((m.start(), nm))
        pats.sort()
        return ("《临证指南医案·" + pats[-1][1] + "》") if pats else "《临证指南医案》未定位"
    ms = list(re.finditer(r"^###\s*([^\n#]{1,40})", head, re.M))
    return ("《%s·%s》" % (book, ms[-1].group(1).strip())) if ms else "《%s》未定位" % book

Q = [
 ("甲T2","顾（四四）须鬓已苍。面色光亮。操心烦劳。阳上升动","临证指南医案"),
 ("甲/乙T2d","操心烦劳。阳上升动","临证指南医案"),
 ("甲/乙T2e","今气越外泄。阳不入阴","临证指南医案"),
 ("甲/乙T5","久咳不已，则三焦受之","临证指南医案"),
 ("甲T5b","某 脉弱无力。发热汗出。久咳形冷。减食过半。显然内损成劳。大忌寒凉清热治嗽。姑与建中法。冀得加谷经行。犹可调摄。","临证指南医案"),
 ("乙T5b","内损虚症。经年不复。色消夺。畏风怯冷","临证指南医案"),
 ("乙T5c","法当创建中宫。大忌清寒理肺。希冀止嗽。嗽不能止。必致胃败减食致剧。","临证指南医案"),
 ("甲/乙T8","纳食主胃，运化主脾。脾宜升则健，胃宜降则和。","临证指南医案"),
 ("甲/乙T8c","肝为起病之源。胃为传病之所","临证指南医案"),
 ("甲/乙T9b","吉（三五）心悸荡漾。头中鸣。七八年中频发不止。起居饮食如常。此肝胆内风自动。","临证指南医案"),
 ("甲T11b","某 内风。乃身中阳气之动变。甘酸之属宜之。","临证指南医案"),
 ("乙T11","所患眩晕者。非外来之邪。乃肝胆之风阳上冒耳。甚则有昏厥跌仆之虞。","临证指南医案"),
 ("甲/乙T10c","三消一症。虽有上中下之分。其实不越阴亏阳亢。津涸热淫而已。","临证指南医案"),
 ("甲/乙T10d","王（四五）形瘦脉搏。渴饮善食。乃三消症也","临证指南医案"),
 ("乙T12b","某 久痹酿成历节。舌黄痰多。由湿邪阻着经脉","临证指南医案"),
 ("甲T12c","俞 肩胛连及臂指。走痛而肿。一年。乃肢痹也","临证指南医案"),
 ("甲/乙T13","张 食进脘中难下。大便气塞不爽。肠中收痛。此为肠痹。","临证指南医案"),
 ("甲T13c","肠胃皆腑。以通为用。","临证指南医案"),
 ("甲T13d","九窍不和，都属胃病","临证指南医案"),
 ("乙T13b","叶（二十）阳气郁勃。腑失传导。纳食中痞。大便结燥","临证指南医案"),
 ("甲/乙T14","朱（四九）烦劳太过。阳伤。痰饮日聚。阳跷脉空","临证指南医案"),
 ("甲/乙T14b","卫阳失护。毛发自坠。乃日就其衰夺矣。","临证指南医案"),
 ("甲T15b","口甘一症。内经称为脾瘅。中焦困不转运可知。","临证指南医案"),
 ("乙T15","脾瘅症，《经》言因数食甘肥所致","临证指南医案"),
 ("乙T15b","甘性缓，肥性腻，使脾气遏郁，致有口甘、内热、中满之患。","临证指南医案"),
 ("甲/乙T16b","柴胡劫肝阴，葛根竭胃汁，致变屡矣","临证指南医案"),
 ("甲/乙T16","按襁褓小儿。体属纯阳。所患热病最多。","临证指南医案"),
 ("甲T17b","肝肾下病，必留连及奇经八脉","临证指南医案"),
 ("甲T18","孙（二四）肾气攻背项强。溺频且多。督脉不摄。腰重头疼。难以转侧。","临证指南医案"),
 ("乙T18b","先与通阳。宗许学士法。","临证指南医案"),
 ("甲/乙T18c","有因肾气本虚。关门不固而脱者。有因湿热下坠而脱者","临证指南医案"),
 ("甲/乙T20d","某 泻五十日。腹鸣渴饮。溲溺不利","临证指南医案"),
 ("甲T20c","张（妪）泄泻。脾肾虚。得食胀","临证指南医案"),
 ("乙T20b","久泻无有不伤肾者。食减不化。阳不用事","临证指南医案"),
 ("乙T20c","久痢久泻。务在能食","临证指南医案"),
 ("乙T7","汪（氏）风热既久未解。化成疮痍。当以和血驱风。","临证指南医案"),
 ("乙T7b","痰因于湿。久而变热","临证指南医案"),
 ("乙T7b2","壅于经隧。变现疮疾疥癣。已酿风湿之毒","临证指南医案"),
]

for label, q, book in Q:
    nq = re.sub(r"[^\u4e00-\u9fff]", "", q)
    outs = []
    for b in [book] + [x for x in files if x != book]:
        start = 0
        while True:
            i = norm[b].find(nq, start)
            if i < 0:
                break
            cnt = 0; sec = "?"
            for j, ch in enumerate(texts[b]):
                if re.match(r"[\u4e00-\u9fff]", ch):
                    if cnt == i:
                        sec = nsec(texts[b], j, b); break
                    cnt += 1
            outs.append(sec)
            start = i + 1
    if outs:
        print("[OK ] %-11s %s   (共%d处)" % (label, " ｜ ".join(outs[:3]), len(outs)))
    else:
        print("[XX ] %-11s 归一化后全库未检出：%s" % (label, q[:40]))
