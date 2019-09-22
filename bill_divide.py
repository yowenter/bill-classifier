# -*- encoding: utf-8 -*-

import sys
import csv
from collections import Counter
'''

把支付宝或者微信账单 按照 收入/支出 分为两栏，方便对账。 

'''


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(
            "billing file missed, parse ignored. \nUsage: `python bill_divide.py <file>` \n"
        )
        sys.exit(-1)
    csv_file = sys.argv[1]
    new_file = ".".join(csv_file.split(".")[:-1]) + "_divide.csv"
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
    in_or_out, amount = None, None
    for i, name in enumerate(header):
        if name.strip() == "收/支":
            in_or_out = i
            print("收/支 at cloumn %s" % i)
        if "金额" in name.strip():
            amount = i
            print("金额 at column %s" % i)
    if in_or_out is None or amount is None:
        sys.stderr.write("找不到收支或金额")
        sys.exit(-1)

    new_header = header + ["收入", "支出"]
    new_records = []
    for r in main_records[1:]:
        if "收入" in r[in_or_out]:
            new_records.append(r + [r[amount], '0 '])
        elif "支出" in r[in_or_out]:
            new_records.append(r + ['0 ', r[amount]])
        else:
            sys.stderr.write("%s\t不属于收支 %s\n" % (r[0], r[in_or_out]))
    new_csv_records = [new_header] + new_records
    #     for r in new_csv_records:
    #         print(r)

    with open(new_file, "w", encoding=use_encoding) as f:
        w = csv.writer(f)
        for r in new_csv_records:
            w.writerow(r)

if __name__ == "__main__":
    main()
