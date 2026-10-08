# -*- coding: utf-8 -*-
"""S11 judge：逐条核对答卷引文是否逐字见于 modules/ 四部原著。

用途：
    为 references/15b-consistency-report.md 提供可复跑的引文核验。
    归一化（NFKC + 去标点空格）后做逐字串匹配，并回落到行号定位。

用法：
    python3 scripts/judge_s11_check.py                 # 从任意目录运行均可
    python3 scripts/judge_s11_check.py --src modules   # 显式指定原文目录

退出码：
    0  全部引文命中，篇名/门类无 MISS
    1  存在 MISS 或未命中的篇名/门类（逐条已打印）
    2  输入缺失或编码非法（modules/ 不完整、非 UTF-8）

依赖：Python ≥ 3.8，仅用标准库（re / os / sys / argparse / unicodedata）。
"""
import argparse
import os
import re
import sys
import unicodedata


def die(code, what, why, fix):
    """统一错误出口：什么失败 / 为什么 / 怎么修。"""
    sys.stderr.write("Error: %s\n  原因: %s\n  解决: %s\n" % (what, why, fix))
    sys.exit(code)


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ap = argparse.ArgumentParser(description="核验答卷引文是否逐字见于 modules/ 原著")
_ap.add_argument("--src", default=os.path.join(_ROOT, "modules"),
                 help="原文目录，默认 <skill 根>/modules")
MOD = _ap.parse_args().src

files = {
    "01温论": os.path.join(MOD, "01_wenshelun.md"),
    "02指南": os.path.join(MOD, "02_linzheng-zhinan-yian.md"),
    "03存真": os.path.join(MOD, "03_yeshi-yian-cunzhen.md"),
    "04医衡": os.path.join(MOD, "04_yexuan-yiheng.md"),
}
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s。，、；：！？…·\"“”‘’（）()《》〈〉\-\u2014.,;:!?\[\]【】/|]+", "", s)

DB = {}
if not os.path.isdir(MOD):
    die(2, "原文目录不存在: %s" % MOD,
        "脚本按自身位置推断 skill 根目录，modules/ 被移动或改名后推断失效",
        "在 skill 内运行，或用 --src 指定，例如 --src /path/to/ye-tianshi/modules")
missing = [os.path.basename(p) for p in files.values() if not os.path.isfile(p)]
if missing:
    die(2, "缺少原著文件: %s" % ", ".join(missing),
        "modules/ 不完整，四部原著缺任意一部都会让对应引文被判为 MISS",
        "从发布包补回缺失文件，或确认 --src 指向 %s" % MOD)
for k, p in files.items():
    try:
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
    except UnicodeDecodeError as e:
        die(2, "%s 不是合法 UTF-8（%s）" % (os.path.basename(p), e),
            "该文件可能仍是旧编码；静默替换字符会让本应命中的引文变成假 MISS",
            "先 iconv -f GB18030 -t UTF-8 转换该文件，再重跑核验")
    if not t.strip():
        die(2, "%s 为空文件" % os.path.basename(p),
            "原文未落盘或被截断", "重新获取该文件后再跑")
    lines = t.split("\n")
    DB[k] = (norm(t), [norm(x) for x in lines], lines)

quotes = [
 ("T1a","01温论","盖伤寒之邪，留恋在表，然后化热入里；温邪则热变最速，未传心包，邪尚在肺。"),
 ("T1b","01温论","或透风于热外，或渗湿于热下"),
 ("T1c","03存真","今病发热，原不是太阳客邪见症，所投羌、防辛温表汗，此误即为逆矣"),
 ("T2a","04医衡","不得卧之证，若劳神忧虑，耗其阴血，惺惺不寐，病在心也"),
 ("T2b","02指南","顾（四四）须鬓已苍。面色光亮。操心烦劳。阳上升动"),
 ("T2b2","02指南","今气越外泄。阳不入阴"),
 ("T3a","04医衡","诸湿肿满，皆属于脾"),
 ("T3b","04医衡","肾者，胃之关也，关门不利，故聚水而从其类也"),
 ("T3c","01温论","通阳不在温，而在利小便"),
 ("T4a","02指南","顾 经来筋掣腹痛。常有心痛干呕。此肝气厥逆。冲任皆病。务在宣通气血以调经。温燥忌用"),
 ("T4b","02指南","某（二十）先腹痛而后经至。气滞为多"),
 ("T4c","02指南","张（四三）寒热间日。经来腹痛"),
 ("T4d","02指南","肝肾下病，必留连及奇经八脉，不知此旨，宜乎无功"),
 ("T5a","02指南","久咳不已，则三焦受之，是病不独在肺矣"),
 ("T5b","02指南","某 脉弱无力。发热汗出。久咳形冷。减食过半。显然内损成劳。大忌寒凉清热治嗽。姑与建中法。冀得加谷经行。犹可调摄"),
 ("T6a","02指南","腰痛一症，不得不以肾为主病"),
 ("T6b","02指南","曹（三九）湿郁。少腹痛引腰。右脚酸"),
 ("T6c","02指南","朱 脉细色夺。肝肾虚。腰痛。是络病治法"),
 ("T7a","02指南","汪（氏）风热既久未解。化成疮痍。当以和血驱风"),
 ("T7b","01温论","吾吴湿邪害人最广"),
 ("T8a","02指南","纳食主胃，运化主脾。脾宜升则健，胃宜降则和"),
 ("T8b","02指南","盖肝为起病之源。胃为传病之所"),
 ("T9a","04医衡","悸即怔忡也。怔忡者，本无惊恐，动而不宁，惊者，因外有所触而卒动"),
 ("T9b","02指南","吉（三五）心悸荡漾。头中鸣。七八年中频发不止。起居饮食如常。此肝胆内风自动。宜镇静之品。佐以辛泄之味"),
 ("T10a","04医衡","多饮而渴不止为上消"),
 ("T10a2","04医衡","消谷善饥为中消"),
 ("T10a3","04医衡","溲便频膏浊不禁为下消"),
 ("T10b","02指南","王（四五）形瘦脉搏。渴饮善食。乃三消症也"),
 ("T11a","04医衡","血病则无以养筋，筋病则掉眩强直之类"),
 ("T11b","02指南","某 内风。乃身中阳气之动变。甘酸之属宜之"),
 ("T12a","04医衡","痹者，闭也，皮肉筋骨，为风寒湿气杂感，血脉闭塞而不流通也"),
 ("T12b","02指南","俞 肩胛连及臂指。走痛而肿。一年。乃肢痹也"),
 ("T12c","04医衡","治风先治血，血行风自灭也"),
 ("T13a","02指南","肠胃皆腑。以通为用"),
 ("T13b","02指南","九窍不和，都属胃病"),
 ("T13c","02指南","张 食进脘中难下。大便气塞不爽。肠中收痛。此为肠痹（肺气不开降）"),
 ("T14a","02指南","朱（四九）烦劳太过。阳伤。痰饮日聚。阳跷脉空。寤不成寐卫阳失护。毛发自坠。乃日就其衰夺矣"),
 ("T14b","04医衡","其衰涸则为虚劳"),
 ("T15a","02指南","某 无形气伤。热邪蕴结。不饥不食"),
 ("T15b","02指南","口甘一症。内经称为脾瘅。中焦困不转运可知"),
 ("T15c","04医衡","湿痰多成倦怠嗜卧"),
 ("T16a","02指南","按襁褓小儿。体属纯阳。所患热病最多"),
 ("T16b","02指南","柴胡劫肝阴，葛根竭胃汁，致变屡矣"),
 ("T17a","04医衡","八脉之中惟任督二脉，为人身之子午，为升降之道"),
 ("T17b","02指南","周（十七）室女经水不调。先后非一。来期必先腹痛"),
 ("T17c","02指南","究脉察色。是居室易于郁怒。肝气偏横。胃先受戕。而奇经冲任跷维诸脉。皆肝胃属隶。脉不循序流行。气血日加阻痹"),
 ("T18a","02指南","孙（二四）肾气攻背项强。溺频且多。督脉不摄。腰重头疼。难以转侧"),
 ("T18b","02指南","有因肾气本虚。关门不固而脱者"),
 ("T19a","02指南","胁痛一症。多属少阳厥阴"),
 ("T19b","02指南","杂症胁痛。皆属厥阴肝经。以肝脉布于胁肋"),
 ("T19c","04医衡","胁痛旧从肝治，不知肝固内舍膺胁，何以异于心肺，内舍膺胁哉"),
 ("T19d","02指南","汪（六八）嗔怒动肝。寒热旬日。左季胁痛。难外舒转。此络脉瘀痹。防有见红之事"),
 ("T20a","04医衡","治湿不利小便，非其治也"),
 ("T20b","04医衡","夫是九者，治泄之大法"),
 ("T20c","02指南","张（妪）泄泻。脾肾虚。得食胀"),
 ("T20d","02指南","某 泻五十日。腹鸣渴饮。溲溺不利"),
]
# 篇名核查（04 医衡 二级/三级标题）
sections = ["寝食说","肿胀引经别证辨","惊悸恐辨","三消证治论","中风证治论","痹证析微论","血营气卫论","痰论","奇经八脉大旨","心胸胃脘胁腹诸痛辨","泄泻九法论"]
# 02 门类名
menlei = ["不寐","调经","咳嗽","腰腿足痛","疮疡","脾胃","木乘土","肝风","三消","痹","肠痹","便闭","痰饮","脾瘅","幼科要略","胁痛","泄泻","脱肛"]

print("=" * 70)
misses = []
for tag, src, q in quotes:
    if src not in DB:
        die(2, "引文 %s 指向未知来源键 %r" % (tag, src),
            "quotes 表里的键与 files 字典不一致，该条会被静默跳过",
            "把键改成 01温论 / 02指南 / 03存真 / 04医衡 之一")
    nq = norm(q)
    found = nq in DB[src][0]
    loc = ""
    if found:
        for i, ln in enumerate(DB[src][1], 1):
            if nq in ln:
                loc = "%s:%d" % (src, i)
                break
    # 打印时截到 45 字：够辨认引文起句，又不至于让一行折行
    print("%s %-6s [%s] %s  %s" % ("OK " if found else "MISS", tag, src, loc, q[:45]))
    if not found:
        misses.append("引文 %s（%s）" % (tag, src))
print("=" * 70)

print("## 篇名核查（《叶选医衡》modules/04）")
for s in sections:
    hit = [i for i, ln in enumerate(DB["04医衡"][2], 1) if s in ln]
    print("%s %s  -> 行%s" % ("OK " if hit else "MISS", s, hit[:3]))
    if not hit:
        misses.append("篇名 %s" % s)

print("## 门类核查（《临证指南医案》modules/02）——兼容本版本的四种标记形态")
t02 = DB["02指南"][2]


def menlei_hit(line, m):
    """门类名 m 是否作为结构标记出现在这一行。

    本数字化版本里门类有四种并存写法，只认 ## 会漏判：
      ## 痹                 ← Markdown 标题（卷一系）
      <篇名>腰腿足痛         ← 篇名标记（54 处）
      <目录>卷十\\幼科要略     ← 目录标记
      ……。咳嗽。……          ← 门首按语里的裸门类名
    一律要求整行精确匹配，避免「痹」命中「痹证论」这类更长篇名。
    """
    s = line.strip()
    return (s == "## " + m
            or s == "<篇名>" + m
            or re.match(r"^<目录>[^\\]*\\" + re.escape(m) + r"$", s) is not None
            or ("。" + m + "。") in s[:60])


for m in menlei:
    # 门类扫描窗口取行首 60 字：门首按语里门类名总在开头，
    # 扫全行会把正文中偶然提到的词误判为门类。
    hit = [i for i, ln in enumerate(t02, 1) if menlei_hit(ln, m)]
    print("%s %s  -> %s" % ("OK " if hit else "MISS", m, hit[:3]))
    if not hit:
        misses.append("门类 %s" % m)

print("-" * 70)
print("核验条目：%d（引文 %d · 篇名 %d · 门类 %d）；未命中：%d"
      % (len(quotes) + len(sections) + len(menlei), len(quotes), len(sections),
         len(menlei), len(misses)))
if misses:
    for x in misses:
        print("  MISS:", x)
    sys.exit(1)
print("全部命中。")
