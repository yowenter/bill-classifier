# -*- encoding: utf-8 -*-

import sys
import csv
import re
from collections import Counter
import jieba
from collections import Counter
'''

把支付宝或者微信账单， 提取商品，然后分类

'''

word_category_mapping = {
    "转账": "转账",
    "星巴克": "饮料",
    "餐饮": "餐饮",
    "基金": "理财",
    "咖啡": "饮料",
    "馒头": "餐饮",
    "超市": "日用",
    "便利": "便利店",
    "酒店": "酒店",
    "烧烤": "美食",
    "房租": "房租",
    "医院": "医疗",
    "糕点": "美食",
    "收款": "转账",
    "理财": "理财",
    "小吃": "小吃",
    "乘车": "交通",
    "菜": "餐饮",
    "滴滴": "交通",
    "绝味": "美食",
    "餐厅": "餐饮",
    "冒菜": "餐饮",
    "麻辣": "餐饮",
    "CoCo": "饮料",
    "克莉丝汀 ": "美食",
    "UNIQLO": "服饰",
    "食堂": "餐饮",
    "水果": "食品",
    "交通": "交通",
    "台球": "娱乐",
    "红包": "优惠券",
    "地铁": "交通",
    "转出到": "转账",
    "宜家": "家居",
    "米粉": "餐饮",
    "还款": "贷款",
    "饭": "餐饮",
    "真功夫": "餐饮",
    "肉": "餐饮",
    "鸭": "餐饮",
    "火车": "交通",
    "汤": "餐饮",
    "米粉": "餐饮",
    "鞋": "服饰",
    "面": "餐饮"
}


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(
            "billing file missed, parse ignored. \nUsage: `python bill_divide.py <file>` \n"
        )
        sys.exit(-1)
    csv_file = sys.argv[1]
    new_file = ".".join(csv_file.split(".")[:-1]) + "_parsed.csv"
    possible_encoding = ["utf-8", "gbk"]
    use_encoding = None
    for encoding in possible_encoding:
        with open(csv_file, mode="r", encoding=encoding) as f:
            try:
                r = csv.reader(f)
                _ = [l for l in r]
                use_encoding = encoding
                break
            except Exception as e:
                # print(type(e))
                if "UnicodeDecodeError" in str(type(e)):
                    print("try encoding %s not ok, err %s. " % (encoding, e))
                else:
                    raise e

    if use_encoding is None:
        sys.stderr.write("Unknown file encoding")
        sys.exit(-1)
    print("Use encoding `%s`" % use_encoding)
    print("start parse file `%s` -> %s" % (csv_file, new_file))
    with open(csv_file, mode="r", encoding=use_encoding) as cf:
        csv_reader = csv.reader(cf)
        records = [f for f in csv_reader]
        print("loading rows: %s" % str(len(records)))


#     print(records)
# 解析出账户明细的列数。

    c = Counter([len(r) for r in records])
    if len(c.most_common()) > 0:
        # 列宽
        width = c.most_common()[0][0]
    else:
        sys.stderr.write("the billing detail can't find")
        exit(-1)
    main_records = list(filter(lambda x: len(x) == width, records))
    #     print(main_records)
    if len(main_records) <= 1:
        sys.stderr.write("找不到对应的订单记录")
        sys.exit(-1)
    header = main_records[0]
    goods_idx, mall_idx = None, None
    for i, name in enumerate(header):
        if "商品" in name.strip():
            goods_idx = i
            print("Goods idx use column %s" % i)

        if "交易对方" in name.strip():
            mall_idx = i
            print("Mall idx use %s" % i)

    if goods_idx is None or mall_idx is None:
        sys.stderr.write("找不到商品名称")
        sys.exit(-1)

    goods_docs = []
    for record in main_records[1:]:
        goods_docs.append("{0} {1}".format(record[mall_idx],
                                           record[goods_idx]))

    cleaned_docs = [["商品", "分类"]]
    goods_set = set()
    for doc in goods_docs:
        # 去除数字
        d = re.sub("\d|-|\.|/|:|\*|_|\(|\)|", "", doc)
        category = "Others"
        for k, v in word_category_mapping.items():
            if k in d:
                category = v
                break
        cleaned_docs.append([d, category])
        goods_set.add(d)
    with open(new_file, mode="w", encoding=use_encoding) as f:
        w = csv.writer(f)
        for r in cleaned_docs:
            w.writerow(r)

    distinct_file = ".".join(csv_file.split(".")[:-1]) + "_parsed_distinct.csv"
    with open(distinct_file, mode="w", encoding=use_encoding) as f:
        w = csv.writer(f)
        w.writerow(["商品", "分类"])
        for r in list(goods_set):
            w.writerow([r, ""])

    total_words = []
    for doc in goods_set:
        total_words.extend(jieba.cut(doc))

    word_count = Counter(total_words)
    top_words_file = ".".join(csv_file.split(".")[:-1]) + "_topwords.csv"
    with open(top_words_file, "w") as f:
        w = csv.writer(f)
        w.writerow(["商品词", "词频"])
        for wc in sorted(word_count.items(), key=lambda x: x[1], reverse=True):
            w.writerow(list(wc))

    distinct_2file = ".".join(
        csv_file.split(".")[:-1]) + "_parsed_distinct_2.csv"
    with open(distinct_2file, mode="w", encoding=use_encoding) as f:
        w = csv.writer(f)
        w.writerow(["商品", "分类"])
        for r in list(goods_set):
            category = ""
            for k, v in word_category_mapping.items():
                if k in r:
                    category = v
                    break
            w.writerow([r, category])

if __name__ == "__main__":
    main()
