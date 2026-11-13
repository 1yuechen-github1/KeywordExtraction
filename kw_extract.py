#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
 病历关键词提取与填空工具  kw_extract.py
================================================================================
用途：输入一份纯文本病历，自动提取关键词并按【三阶类别】归类，可直接用于填空。

运行（只依赖 Python 3.7+，无需任何第三方库）：
    python kw_extract.py 病历.txt
    python kw_extract.py 病历.txt --out 结果.json
    python kw_extract.py 病历.txt --tsv          # 表格形式（便于粘到 Excel）
    python kw_extract.py 病历.txt --fill 模板.txt --fill-out 已填.txt
    type 病历.txt | python kw_extract.py -        # 从管道读

三阶类别词表：同目录下的 kw_taxonomy.json（214 词 / 28 类）。
  若该文件不存在，则使用脚本内置词表（功能相同）。
  可用 --taxonomy 指定其它词表文件。

输出：
  1) 每个关键词的（三阶类别）清单
  2) 按三阶类别分组的清单
  3) --fill 模式下，把模板里的 {{类别}} 或 {类别} 占位符替换为提取到的值
================================================================================
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

# ─────────────────────────────────────────────────────────────────────────────
# 0. 内置词表（词 → 三阶类别）；若外部 kw_taxonomy.json 存在则覆盖
# ─────────────────────────────────────────────────────────────────────────────
TAXONOMY = {
    # 牙位
    **{f"{a}{b}": "专科检查-牙位-FDI编码"
       for a in "1234" for b in "12345678"},
    # 时间
    "2周": "现病史-时间-时间窗口", "3周": "现病史-时间-时间窗口",
    "4周": "现病史-时间-时间窗口", "1周": "现病史-时间-时间窗口",
    "1月": "现病史-时间-时间窗口", "2月": "现病史-时间-时间窗口",
    "3月": "现病史-时间-时间窗口", "4月": "现病史-时间-时间窗口",
    "5月": "现病史-时间-时间窗口", "6月": "现病史-时间-时间窗口",
    "7月": "现病史-时间-时间窗口", "数月": "现病史-时间-时间窗口",
    "数天": "现病史-时间-时间窗口", "数日": "现病史-时间-时间窗口",
    # 品牌 / 型号
    "Astra": "治疗-种植体-品牌", "Straumann": "治疗-种植体-品牌",
    "Nobel": "治疗-种植体-品牌", "NobelCC": "治疗-种植体-品牌",
    "Roeman": "治疗-种植体-品牌", "ITI": "治疗-种植体-品牌",
    "EV": "治疗-种植体-型号", "TX": "治疗-种植体-型号", "BLT": "治疗-种植体-型号",
    "BL": "治疗-种植体-型号", "SP": "治疗-种植体-型号", "WN": "治疗-种植体-型号",
    "RN": "治疗-种植体-型号", "NC": "治疗-种植体-型号", "CC": "治疗-种植体-型号",
    "S": "治疗-种植体-型号", "PMC": "治疗-种植体-型号", "Replace": "治疗-种植体-型号",
    # 植骨 / 膜
    "Bio-Oss": "治疗-植骨-骨粉品牌", "Bio-Oss骨粉": "治疗-植骨-骨粉品牌",
    "Bio-Gide": "治疗-植骨-骨粉品牌", "Bio-Gide胶原膜": "治疗-植骨-膜材料",
    "兰度": "治疗-植骨-骨粉品牌", "联结": "治疗-植骨-骨粉品牌",
    "海奥": "治疗-植骨-膜材料", "傲塑": "治疗-植骨-骨粉品牌",
    "胶原膜": "治疗-植骨-膜材料", "可吸收生物膜": "治疗-植骨-膜材料",
    "生物膜": "治疗-植骨-膜材料", "骨膜": "治疗-植骨-膜材料",
    "自体骨": "治疗-植骨-骨粉品牌", "自体骨颗粒": "治疗-植骨-骨粉品牌",
    "自体骨屑": "治疗-植骨-骨粉品牌", "骨替代材料": "治疗-植骨-骨粉品牌",
    "胶原蛋白海绵": "治疗-植骨-膜材料",
    # 配件
    "愈合基台": "治疗-修复配件", "覆盖螺丝": "治疗-修复配件",
    "封闭螺丝": "治疗-修复配件", "转移杆": "治疗-修复配件",
    "扫描杆": "治疗-修复配件", "基台保护帽": "治疗-修复配件",
    # 诊断
    "上颌牙列缺损": "诊断-颌位", "下颌牙列缺损": "诊断-颌位",
    "牙列缺损": "诊断-颌位", "牙体缺损": "诊断-颌位",
    # 状态 / 阴性征象
    "无红肿": "专科检查-牙龈/黏膜情况", "有红肿": "专科检查-牙龈/黏膜情况",
    "稍红肿": "专科检查-牙龈/黏膜情况", "轻度红肿": "专科检查-牙龈/黏膜情况",
    "明显红肿": "专科检查-牙龈/黏膜情况", "正常": "专科检查-牙龈/黏膜情况",
    "无异常": "专科检查-牙龈/黏膜情况", "无松动": "专科检查-种植体-松动度",
    "有松动": "专科检查-种植体-松动度", "在位": "专科检查-种植体-松动度",
    "部位良好": "专科检查-种植体-松动度", "松（-）": "专科检查-种植体-松动度",
    "无龋损": "专科检查-余留牙情况", "无伸长": "专科检查-余留牙情况",
    "无倾斜": "专科检查-余留牙情况", "轻度伸长": "专科检查-余留牙情况",
    "明显伸长": "专科检查-余留牙情况", "明显倾斜": "专科检查-余留牙情况",
    "中度萎缩": "专科检查-余留牙情况", "无阴影": "专科检查-影像学情况",
    "透明影": "专科检查-影像学情况", "欠佳": "专科检查-口腔卫生-卫生等级",
    "好": "专科检查-口腔卫生-卫生等级", "一般": "专科检查-口腔卫生-卫生等级",
    "尚可": "专科检查-角化龈-宽度等级", "不足": "专科检查-角化龈-宽度等级",
    "充足": "专科检查-角化龈-宽度等级", "稍有不足": "专科检查-角化龈-宽度等级",
    "薄": "专科检查-龈生物型-厚薄", "厚": "专科检查-龈生物型-厚薄",
    "埋入": "术后参数-种植体-愈合方式", "穿龈": "术后参数-种植体-愈合方式",
    "骨结合": "专科检查-种植体-骨结合",
    # 软组织
    "牙龈厚度": "专科检查-软组织-牙龈厚度", "穿龈深度": "专科检查-软组织-穿龈深度",
    "附着龈": "专科检查-软组织-附着龈宽度", "角化龈宽度": "专科检查-角化龈-宽度等级",
    "颊侧角化龈宽度": "专科检查-角化龈-宽度等级",
    "颊侧软组织轮廓": "专科检查-软组织-轮廓", "BOP阳性": "专科检查-软组织-出血指数",
    # 修复空间
    "咬合空间": "专科检查-修复空间-咬合空间", "修复空间": "专科检查-修复空间-咬合空间",
    # 解剖
    "唇侧": "治疗-解剖-植骨位点-方向", "颊侧": "治疗-解剖-植骨位点-方向",
    "舌侧": "治疗-解剖-植骨位点-方向", "腭侧": "治疗-解剖-植骨位点-方向",
    "牙槽嵴顶": "治疗-解剖-植骨位点-骨面", "骨缺损": "治疗-解剖-植骨位点-骨面",
    "骨开窗": "治疗-解剖-植骨位点-骨面", "上颌窦": "治疗-解剖-植骨位点-骨面",
    "植骨位置": "治疗-解剖-植骨位点-骨面", "牙龈乳头": "治疗-解剖-植骨位点-骨面",
    # 术式 / 器械
    "上颌窦内提升": "治疗-手术-术式", "内提": "治疗-手术-术式",
    "拔牙": "治疗-手术-术式", "拔除": "治疗-手术-术式",
    "转瓣": "治疗-手术-术式", "牙龈减张": "治疗-手术-术式",
    "成形牙龈乳头": "治疗-手术-术式", "平整牙槽骨尖": "治疗-手术-术式",
    "定位": "治疗-手术-术式", "术前洁牙": "治疗-手术-术式",
    "超声根面整平术": "治疗-手术-术式", "重新口扫取模": "治疗-手术-术式",
    "拆线": "治疗-手术-术式", "植骨": "治疗-手术-术式",
    "数字化导板": "治疗-手术-器械", "Summer's 骨凿": "治疗-手术-器械",
    # 戴牙适配
    "无法就位": "治疗-修复-戴牙适配", "不密合": "治疗-修复-戴牙适配",
    "就位欠佳": "治疗-修复-戴牙适配", "固位良好": "治疗-修复-戴牙适配",
    # 病史
    "高血压病史": "既往史-系统性疾病-阳性", "心脏病": "既往史-系统性疾病-阳性",
    "糖尿病等系统性疾病": "既往史-系统性疾病-阳性",
    "否认传染性疾病": "既往史-系统性疾病-否认",
    "否认家族遗传病": "既往史-系统性疾病-否认",
    "否认药物过敏史": "既往史-系统性疾病-否认",
    "否认高血压": "既往史-系统性疾病-否认",
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. 预处理
# ─────────────────────────────────────────────────────────────────────────────
ENT = {"&times;": "×", "&nbsp;": " ", "&middot;": "·", "&amp;": "&", "&lt;": "<",
       "&gt;": ">", "&quot;": '"', "&apos;": "'", "&deg;": "°"}
XMLJUNK = re.compile(r"</?w:[^>]*>|</?xml[^>]*>|</?[\w]+:[^>]*>")
PLACEHOLDER = {"未提及", "未描述", "未查", "无", "不详", "（色号）", "（", "）", "-", "—", "/"}
NOISE = {"mm", "直径", "长度", "高", "上", "前", "或", "史", "牙位", "一", "两", "三", "四"}
ADV = re.compile(r"(【\s*医\s*嘱\s*】|医\s*嘱\s*[：:]|用法\s*[：:])")
SECS = ["既往史", "现病史", "辅助检查", "专科检查", "治疗方案", "种植体植入情况",
        "种植系统选择", "治疗计划", "X片显示", "主诉", "检查", "诊断", "处理", "治疗", "医嘱",
        "术前诊断", "手术名称"]


def preprocess(text):
    """清实体/标签/下划线占位，切掉医嘱段"""
    s = str(text or "")
    for k, v in ENT.items():
        s = s.replace(k, v)
    s = XMLJUNK.sub("", s)
    s = re.sub(r"</?[a-zA-Z][^>]{0,60}>", "", s)
    # `_内容_` → 内容；单个 _ / __ 保留
    s = re.sub(r"_(?=[^_\s])[^_\n]{1,30}?(?<=[^_\s])_", lambda m: m.group(0)[1:-1], s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    m = ADV.search(s)
    if m:
        s = s[:m.start()]
    return s


def split_sections(s):
    """按段名切段：{段名: 内容}"""
    out = OrderedDict()
    pat = re.compile(r"(【\s*(?:%s)\s*】|(?:%s)\s*[：:])" % ("|".join(SECS), "|".join(SECS)))
    pos, cur = 0, "全文"
    for m in pat.finditer(s):
        seg = s[pos:m.start()].strip()
        if seg:
            out[cur] = (out.get(cur, "") + " " + seg).strip()
        cur = re.sub(r"[【】\s：:]", "", m.group(0))
        pos = m.end()
    tail = s[pos:].strip()
    if tail:
        out[cur] = (out.get(cur, "") + " " + tail).strip()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 2. 抽取规则
# ─────────────────────────────────────────────────────────────────────────────
PAT_TORQUE = re.compile(r"[<>]?\s*[0-9]+(?:\.[0-9]+)?\s*N\s*(?:[·.．]\s*)?c?m?\b")
PAT_TIME = re.compile(r"(?:[0-9]+|[一二三四五六七八九十两_]+)\s*(?:周|个月|月|天|日|年)")
PAT_DIM = re.compile(r"[0-9]+(?:\.[0-9]+)?(?:\s*[、,，~\-–]\s*[0-9]+(?:\.[0-9]+)?)*\s*(?:mm|毫米)")
# 该尺寸是"标签本身"而非数值的情形（如正文只写"穿龈深度"没给数值）→ 不作为尺寸关键词
DIM_LABEL_ONLY = re.compile(r"^(?:牙龈厚度|穿龈深度|附着龈|角化龈宽度|颊侧角化龈宽度|咬合空间|修复空间)$")
PAT_COLOR = re.compile(r"(?<![0-9A-Za-z.])([0-9]?[A-D][0-9]|[0-9]M[0-9])(?![0-9.])")
PAT_TOOTH = re.compile(r"(?<![0-9.])([1-4][1-8])(?![0-9])")
PAT_SPEC = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*[*×xX]\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|毫米)?")
PAT_COUNT = re.compile(r"([0-9]+|[一二三四五六七八九十两])\s*(枚|个|支)")
PAT_GRAM = re.compile(r"[0-9]+(?:\.[0-9]+)?\s*g\b")
PAT_BRAND = re.compile(r"(Astra|Straumann|Nobel|NOBLE|Novel|NobelCC|Roeman|ITI|Bio-?Horizons|Osstem|Dentium|Bego|Ankylos)", re.I)
PAT_LINE = re.compile(r"\b(BLT|BL|EV|TX|SP|WN|RN|NC|CC|PMC|TL|TE|Replace)\b")
PAT_SNUM = re.compile(r"([0-9]+\.[0-9]+)\s*S(?![A-Za-z])")
PAT_MED = re.compile(r"(清理牙槽骨腔|清理骨腔内软组织|平整牙槽骨尖|先锋钻预备|扩孔钻逐级预备种植窝|"
                     r"导向感?检查种植体植入方式及深度|取远中自体骨|成形牙龈乳头|牙龈减张|"
                     r"可吸收缝线缝合|上颌窦内提升|提升上颌窦黏膜|骨劈开|骨挤压|转瓣|"
                     r"数字化导板引导|数字化导板|术前洁牙|超声根面整平术|重新口扫取模|拆线)")

# 术语 → 尺寸归属
DIM_OWNER = [
    (re.compile(r"牙龈厚度[^0-9]{0,8}$"), "专科检查-软组织-尺寸-厚度"),
    (re.compile(r"(角化龈宽度|颊侧角化龈宽度)[^0-9]{0,8}$"), "专科检查-角化龈-宽度等级"),
    (re.compile(r"穿龈深度[^0-9]{0,8}$"), "专科检查-软组织-尺寸-深度"),
    (re.compile(r"附着龈[^0-9]{0,8}$"), "专科检查-软组织-尺寸-长度"),
    (re.compile(r"愈合基台[^0-9]{0,8}$"), "治疗-修复配件尺寸"),
    (re.compile(r"(覆盖螺丝|封闭螺丝)[^0-9]{0,8}$"), "治疗-修复配件尺寸"),
]
# 术式 → 类别
MED_CAT = {
    "清理牙槽骨腔": "治疗-手术-术式", "清理骨腔内软组织": "治疗-手术-术式",
    "平整牙槽骨尖": "治疗-手术-术式", "先锋钻预备": "治疗-手术-术式",
    "扩孔钻逐级预备种植窝": "治疗-手术-术式",
    "导向感检查种植体植入方式及深度": "治疗-手术-术式",
    "导向感检查种植体植入方向及深度": "治疗-手术-术式",
    "取远中自体骨": "治疗-手术-术式", "成形牙龈乳头": "治疗-手术-术式",
    "牙龈减张": "治疗-手术-术式", "可吸收缝线缝合": "治疗-手术-术式",
    "上颌窦内提升": "治疗-手术-术式", "提升上颌窦黏膜": "治疗-手术-术式",
    "骨劈开": "治疗-手术-术式", "骨挤压": "治疗-手术-术式",
    "转瓣": "治疗-手术-术式", "数字化导板引导": "治疗-手术-器械",
    "数字化导板": "治疗-手术-器械", "术前洁牙": "治疗-手术-术式",
    "超声根面整平术": "治疗-手术-术式", "重新口扫取模": "治疗-手术-术式",
    "拆线": "治疗-手术-术式",
}


def classify(tok, body="", tax=None):
    """给 token 定三阶类别"""
    tax = tax if tax is not None else TAXONOMY
    t = str(tok or "").strip()
    if not t:
        return "待归类"
    b = str(body or "")
    # 1 词表直查
    if t in tax:
        return tax[t]
    tt = re.sub(r"\s+", "", t)
    for k, v in tax.items():
        if re.sub(r"\s+", "", k) == tt:
            return v
    # 2 牙位
    if re.fullmatch(r"[1-4][1-8]", t):
        return "专科检查-牙位-FDI编码"
    if re.fullmatch(r"[1-4][1-8](?:\s*[-~]\s*[1-4]?[1-8])?", t):
        return "专科检查-牙位-FDI编码"
    # 3 扭力
    if PAT_TORQUE.fullmatch(t):
        return "术后参数-种植体-扭力"
    # 4 时间
    if PAT_TIME.fullmatch(t):
        return "现病史-时间-时间窗口"
    # 5 色号
    if PAT_COLOR.fullmatch(t):
        return "比色号"
    # 6 克数
    if PAT_GRAM.fullmatch(t):
        return "治疗-植骨-克数"
    # 7 尺寸 → 按前置术语归属
    if PAT_DIM.fullmatch(t) or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?S", t):
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?S", t):
            return "治疗-种植体-型号"
        for m in re.finditer(re.escape(t), b):
            pre = b[max(0, m.start() - 20):m.start()]
            for pat, cat in DIM_OWNER:
                if pat.search(pre):
                    return cat
        # `A×B` 里 A=直径、B=长度
        for m in re.finditer(r"([0-9.]+)\s*[*×xX]\s*([0-9.]+)", b):
            num = re.match(r"[0-9.]+", t).group(0)
            if num == m.group(1):
                return "治疗-种植体-尺寸-直径"
            if num == m.group(2):
                return "治疗-种植体-尺寸-长度"
        return "治疗-种植体/愈合基台-尺寸-mm"
    # 8 枚数
    if PAT_COUNT.fullmatch(t):
        return "治疗-种植体-枚数"
    # 9 术式
    if t in MED_CAT:
        return MED_CAT[t]
    # 10 品牌 / 型号
    if PAT_BRAND.fullmatch(t) or PAT_BRAND.match(t):
        return "治疗-种植体-品牌"
    if t in ("EV", "TX", "BLT", "BL", "SP", "WN", "RN", "NC", "CC", "S", "PMC",
             "TL", "TE", "Replace", "CCPMC"):
        return "治疗-种植体-型号"
    # 11 膜 / 骨粉
    if any(k in t for k in ("膜", "胶原", "海绵")):
        return "治疗-植骨-膜材料"
    if any(k in t for k in ("骨粉", "Bio-Oss", "Bio-?Gide", "骨替代", "自体骨", "联结", "兰度", "海奥", "傲塑")):
        return "治疗-植骨-骨粉品牌"
    # 12 解剖
    if t in ("唇侧", "颊侧", "舌侧", "腭侧"):
        return "治疗-解剖-植骨位点-方向"
    if t in ("牙槽嵴顶", "骨缺损", "骨开窗", "上颌窦", "牙槽嵴", "植骨位置", "牙龈乳头"):
        return "治疗-解剖-植骨位点-骨面"
    # 13 配件
    if t in ("愈合基台", "覆盖螺丝", "封闭螺丝", "转移杆", "扫描杆", "基台保护帽", "临时冠"):
        return "治疗-修复配件"
    # 14 诊断
    if "牙列缺损" in t or "牙体缺损" in t:
        return "诊断-颌位"
    # 15 状态 / 阴性
    if any(k in t for k in ("红肿", "充血", "水肿")):
        return "专科检查-牙龈/黏膜情况"
    if any(k in t for k in ("松动", "在位", "部位良好", "松（-")):
        return "专科检查-种植体-松动度"
    if any(k in t for k in ("龋", "伸长", "倾斜", "萎缩", "结石")):
        return "专科检查-余留牙情况"
    if "阴影" in t or "透明影" in t:
        return "专科检查-影像学情况"
    if t in ("好", "一般", "欠佳", "尚可") or "卫生" in t:
        return "专科检查-口腔卫生-卫生等级"
    if t in ("埋入", "穿龈", "埋入穿龈"):
        return "术后参数-种植体-愈合方式"
    if t in ("薄", "厚"):
        return "专科检查-龈生物型-厚薄"
    if t in ("正常", "无异常", "未提及"):
        return "专科检查-牙龈/黏膜情况" if t != "未提及" else "待归类"
    # 16 术式（动词型）
    if any(k in t for k in ("清理", "预备", "平整", "定位", "植入", "缝合", "翻瓣", "劈开",
                            "挤压", "减张", "转瓣", "拔除", "拔牙", "拆线", "取模", "扫")):
        return "治疗-手术-术式"
    # 17 病史
    if any(k in t for k in ("史", "否认", "高血压", "糖尿病", "心脏病")):
        return "既往史-系统性疾病-阳性" if "否认" not in t else "既往史-系统性疾病-否认"
    return "待归类"


# ─────────────────────────────────────────────────────────────────────────────
# 3. 抽取
# ─────────────────────────────────────────────────────────────────────────────
def extract(text, tax=None):
    """返回 (有序 token 列表, token→类别)"""
    tax = tax if tax is not None else TAXONOMY
    body = preprocess(text)
    secs = split_sections(body)
    found, order = OrderedDict(), []

    def add(tok, cat=None):
        tok = str(tok or "").strip()
        if not tok or tok in PLACEHOLDER or tok in NOISE:
            return
        if len(tok) == 1 and not re.fullmatch(r"[0-9]", tok):
            return                      # 单字（除数字）丢弃
        if tok not in found:
            found[tok] = cat or classify(tok, body, tax)
            order.append(tok)

    # 优先长的术式
    for m in PAT_MED.finditer(body):
        add(m.group(1))
    # 扭力
    for m in PAT_TORQUE.finditer(body):
        add(re.sub(r"\s+", "", m.group(0)))
    # 时间
    for m in PAT_TIME.finditer(body):
        add(re.sub(r"\s+", "", m.group(0)))
    # 色号
    for m in PAT_COLOR.finditer(body):
        add(m.group(0))
    # 克数
    for m in PAT_GRAM.finditer(body):
        add(re.sub(r"\s+", "", m.group(0)))
    # 规格 A×B（拆成 直径 / 长度）
    spec_nums = set()
    for m in PAT_SPEC.finditer(body):
        add(m.group(1), "治疗-种植体-尺寸-直径")
        add(m.group(2), "治疗-种植体-尺寸-长度")
        spec_nums.add(m.group(1)); spec_nums.add(m.group(2))
    # `4.2S`
    for m in PAT_SNUM.finditer(body):
        add(m.group(1) + "S", "治疗-种植体-型号")
    # 尺寸（带单位）—— 属于 `A×B` 规格的不再单独抽（避免 10 / 10mm 重复）
    for m in PAT_DIM.finditer(body):
        tok = re.sub(r"\s+", "", m.group(0))
        num = re.match(r"[0-9.]+", tok).group(0)
        if num in spec_nums:
            if re.search(r"[×xX*]\s*" + re.escape(tok), body):      # ×10mm → 已是长度
                continue
            if re.search(re.escape(tok) + r"\s*[×xX*]", body):      # 4.5mm× → 已是直径
                continue
        add(tok)
    # 主诉 / 现病史 短句（如"复诊，无不适，戴牙"）作为整条关键词
    secmap = split_sections(body)
    for sec in ("主诉",):
        if sec in secmap:
            seg = re.split(r"[。；;]", secmap[sec])[0].strip()
            if 3 <= len(seg) <= 30:
                add(seg, "主诉")
    # 枚数
    for m in PAT_COUNT.finditer(body):
        add(m.group(1) + m.group(2), "治疗-种植体-枚数")
    # 牙位
    for m in PAT_TOOTH.finditer(body):
        tail = body[m.end():m.end() + 3]
        pre = body[max(0, m.start() - 3):m.start()]
        if re.match(r"\s*(?:mm|毫米|周|月|天|N|%|g|枚|个|支|年)", tail):
            continue
        if re.match(r"\s*N\s*(?:[·.．]|cm\b|c\b|m\b)", tail):   # 35N·cm 里的 35
            continue
        if re.match(r"[0-9]", pre) or re.match(r"[·.．]\s*$", pre):
            continue
        add(m.group(1), "专科检查-牙位-FDI编码")
    # 品牌 / 型号
    for m in PAT_BRAND.finditer(body):
        nm = m.group(1)
        canon = {"astra": "Astra", "straumann": "Straumann", "nobel": "Nobel",
                 "noble": "NOBLE", "novel": "Novel", "nobelcc": "NobelCC",
                 "roeman": "Roeman", "iti": "ITI"}.get(nm.lower(), nm)
        add(canon, "治疗-种植体-品牌")
    for m in PAT_LINE.finditer(body):
        add(m.group(1), "治疗-种植体-型号")
    # 词表里的词（直查）——纯数字类需做上下文校验，避免 `35N·cm` 被当成牙位 35
    for k, v in tax.items():
        if not k or len(k) < 2:
            continue
        if k not in body:
            continue
        if re.fullmatch(r"[1-4][1-8]", k):
            ok = False
            for m in re.finditer(r"(?<![0-9.])" + re.escape(k) + r"(?![0-9])", body):
                tail = body[m.end():m.end() + 3]
                pre = body[max(0, m.start() - 3):m.start()]
                if re.match(r"\s*(?:mm|毫米|周|月|天|N|%|g|枚|个|支|年)", tail):
                    continue
                if re.match(r"\s*N\s*(?:[·.．]|cm\b|c\b|m\b)", tail):
                    continue
                if re.match(r"[0-9]", pre) or re.match(r"[·.．]\s*$", pre):
                    continue
                ok = True
                break
            if ok:
                add(k, v)
            continue
        add(k, v)
    # 尺寸类术语：若正文里**该术语旁边确实有数值**，则不把标签本身当关键词
    for term in ("牙龈厚度", "穿龈深度", "附着龈", "角化龈宽度", "颊侧角化龈宽度", "咬合空间"):
        if term in body and re.search(re.escape(term) + r"[^0-9\n]{0,6}[0-9]", body):
            if term in found:
                found.pop(term, None)
                if term in order:
                    order.remove(term)
    # 主诉短句（兜底：直接从原文取）
    m0 = re.search(r"主\s*诉\s*[：:]?\s*([^\n。；;]{3,30})", body)
    if m0:
        add(m0.group(1).strip(), "主诉")
    # 带单位的数值变体：`NobelReplace`、`35N cm`、`11.5`（裸尺寸）等
    for m in re.finditer(r"(NobelReplace|Nobel\s*Replace|Replace)", body, re.I):
        add("NobelReplace", "治疗-种植体-型号")
    for m in re.finditer(r"[0-9]+(?:\.[0-9]+)?\s*N\s*cm", body):
        add(re.sub(r"\s+", "", m.group(0)).replace("Ncm", "N cm"), "术后参数-种植体-扭力")
    # 裸小数（如 11.5 / 4.2），且不在 `A×B` 中、不跟单位 → 尺寸（数值）
    for m in re.finditer(r"(?<![0-9.])([0-9]+\.[0-9]+)(?![0-9])", body):
        v = m.group(1)
        tail = body[m.end():m.end() + 3]
        pre = body[max(0, m.start() - 4):m.start()]
        if re.match(r"\s*(?:mm|毫米|N|%|g|周|月|天|年|枚)", tail):
            continue
        if re.search(r"[×xX*]\s*$", pre) or re.match(r"\s*[×xX*]", tail):
            continue
        if re.search(r"N\s*$", pre):
            continue
        add(v, "治疗-种植体/愈合基台-尺寸（数值）")
    # 裸整数尺寸（如 275 / 3 / 5），限上下文含"直径/长度/尺寸"时
    for m in re.finditer(r"(?:直径|长度|尺寸)[^0-9]{0,8}([0-9]{1,3})(?![0-9.])", body):
        add(m.group(1), "治疗-种植体/愈合基台-尺寸（数值）")
    # 中文数字 + 单位（两毫米 / 三周 / 数月）
    for m in re.finditer(r"([一二三四五六七八九十两]+)\s*(毫米|mm|周|个月|月|天|日|年)", body):
        add(m.group(1) + m.group(2), "现病史-时间-时间窗口" if m.group(2) not in ("毫米", "mm")
            else "治疗-种植体/愈合基台-尺寸-mm")
    # `__月`/`_月` 等占位 → 视作"数月"
    for m in re.finditer(r"_{1,3}\s*(个月|月|周|天|日|年)", body):
        add("数" + m.group(1), "现病史-时间-时间窗口")
    # `0.25g` 之后紧跟品牌名（0.25gCraos）→ 补品牌
    for m in re.finditer(r"[0-9.]+\s*g\s*([A-Z][A-Za-z]{2,})", body):
        add(m.group(1), "治疗-植骨-骨粉品牌")
    # 术式：根冠方骨缺损 / 骨块及受区间隙 / 提升上颌窦黏膜
    for k in ("根冠方骨缺损", "骨块及受区间隙", "提升上颌窦黏膜", "上颌窦黏膜"):
        if k in body:
            add(k, "治疗-解剖-植骨位点-骨面" if "缺损" in k or "间隙" in k else "治疗-手术-术式")
    # 中文牙位
    for k in ("左上五", "左上5", "右下七", "左下七", "右上七", "左上六", "右上六", "右下六", "左下六"):
        if k in body:
            add(k, "专科检查-牙位-FDI编码")
    return order, found


def group_by_cat(tokens, mapping):
    g = OrderedDict()
    for t in tokens:
        g.setdefault(mapping[t], []).append(t)
    return g


# ─────────────────────────────────────────────────────────────────────────────
# 4. 填空
# ─────────────────────────────────────────────────────────────────────────────
def fill(template, tokens, mapping, sep=", "):
    """把模板里的 {类别} / {{类别}} 占位符替换为提取到的值"""
    g = group_by_cat(tokens, mapping)
    out = str(template)
    # 支持完整类别名、末级类名、以及"待归类"
    keys = []
    for cat in g:
        keys.append(cat)
        keys.append(cat.split("-")[-1])
    keys = sorted(set(keys), key=len, reverse=True)
    for k in keys:
        val = ""
        if k in g:
            val = sep.join(g[k])
        else:
            leaf = [c for c in g if c.split("-")[-1] == k]
            if leaf:
                val = sep.join(sum((g[c] for c in leaf), []))
        out = out.replace("{{%s}}" % k, val).replace("{%s}" % k, val)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI
# ─────────────────────────────────────────────────────────────────────────────
def read_text(path):
    if path == "-":
        return sys.stdin.read()
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "gbk", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def load_tax(path):
    if path and os.path.exists(path):
        try:
            d = json.load(open(path, encoding="utf-8"))
            if isinstance(d, dict) and d:
                return d
        except Exception as e:
            print("词表读取失败，改用内置词表：%s" % e, file=sys.stderr)
    # 同目录默认文件
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kw_taxonomy.json")
    if os.path.exists(here):
        try:
            d = json.load(open(here, encoding="utf-8"))
            if isinstance(d, dict) and d:
                return d
        except Exception:
            pass
    return TAXONOMY


def kw_extract(text):
    """
    接收病历文本，返回关键词提取结果。
    """
    tax = load_tax(None)
    tokens, mapping = extract(text, tax)
    grouped = group_by_cat(tokens, mapping)

    return {
        "关键词数": len(tokens),
        "类别数": len(grouped),
        "关键词": [
            {
                "词": token,
                "类别": mapping[token]
            }
            for token in tokens
        ],
        "按类别": dict(grouped)
    }


def main():
    ap = argparse.ArgumentParser(description="病历关键词提取与填空")
    ap.add_argument("input", help="病历纯文本文件（- 表示从标准输入读）")
    ap.add_argument("--taxonomy", help="三阶类别词表 JSON（默认 kw_taxonomy.json 或内置）")
    ap.add_argument("--out", help="结果 JSON 输出路径")
    ap.add_argument("--tsv", action="store_true", help="输出 TSV（便于粘到 Excel）")
    ap.add_argument("--flat", action="store_true", help="只输出「关键词（类别）」一行")
    ap.add_argument("--fill", help="填空模板文件（用 {类别} 或 {{类别}} 作占位符）")
    ap.add_argument("--fill-out", help="填空结果输出路径（默认打印）")
    a = ap.parse_args()

    tax = load_tax(a.taxonomy)
    text = read_text(a.input)
    tokens, mapping = extract(text, tax)
    g = group_by_cat(tokens, mapping)

    if a.flat:
        print(", ".join("%s（%s）" % (t, mapping[t]) for t in tokens))
    elif a.tsv:
        print("关键词\t三阶类别")
        for t in tokens:
            print("%s\t%s" % (t, mapping[t]))
    else:
        print("=" * 78)
        print("关键词 %d 个 ； 三阶类别 %d 类" % (len(tokens), len(g)))
        print("=" * 78)
        for cat, ts in g.items():
            print("\n【%s】（%d）" % (cat, len(ts)))
            print("   " + ", ".join(ts))
        print()
        print("-" * 78)
        print("完整清单：")
        print("   " + ", ".join("%s（%s）" % (t, mapping[t]) for t in tokens))

    result = {
        "关键词数": len(tokens),
        "类别数": len(g),
        "关键词": [{"词": t, "类别": mapping[t]} for t in tokens],
        "按类别": {c: ts for c, ts in g.items()},
    }
    if a.fill:
        tpl = read_text(a.fill)
        filled = fill(tpl, tokens, mapping)
        if a.fill_out:
            open(a.fill_out, "w", encoding="utf-8").write(filled)
            print("\n[填空结果已写入] %s" % a.fill_out)
        else:
            print("\n" + "=" * 78 + "\n填空结果：\n" + "=" * 78)
            print(filled)
        result["填空结果"] = filled
    if a.out:
        json.dump(result, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n[结果已写入] %s" % a.out)



if __name__ == "__main__":
    main()





