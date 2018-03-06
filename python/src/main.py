import pandas as pd
from datetime import datetime, timedelta
import re
import sys


def main():
    # print(input())
    # f = open("data.txt")
    lines = sys.stdin.readlines()
    #work_data_input = f.readlines()
    work_data_input = list(lines)
    month_str = work_data_input.pop(0)
    # print(month_str)
    month = datetime.strptime(month_str.strip(), "%Y/%m")
    past_month_work_unit_data = []
    work_unit_data = []
    # 入力をデータ化
    for work_unit in work_data_input:
        try:
            work_data = parse_unit(work_unit)
        except:
            exit(code=1)
        if month.month != parse_unit(work_unit)[0].month:
            past_month_work_unit_data.append(work_data)
        else:
            work_unit_data.append(work_data)
    try:
        # 所定休日労働時間
        defined_holiday_time = get_defined_holiday_work(work_unit_data)
        # 法定休日労働時間
        law_holiday_time = get_law_holiday_work(work_unit_data)
        # 深夜残業区間抽出
        midnight_time = get_midnight_work(work_unit_data)
        # 法定外残業時間数抽出
        outlaw_time = get_outlaw_overtime_work(work_unit_data, past_month_work_unit_data)
        # 法定内残業時間抽出
        inlaw_time = get_law_overtime_work(work_unit_data, outlaw_time)
    except:
        exit(1)

    #標準出力
    val_list = [str(int(val/60)) for val in (map(round_30, [inlaw_time, outlaw_time, midnight_time, defined_holiday_time, law_holiday_time]))]
    print("\n".join(val_list))


def round_30(flot):
    surplus = flot % 60
    # 30未満切り捨て
    if surplus < 30:
        return flot - surplus
    # 30以上切り上げ
    else:
        return flot - surplus + 60



def get_defined_holiday_work(work_data):
    """
    :param work_data: 
    :return: 所定休日労働時間 
    """
    work_time = 0
    for work_datum in work_data:
        for work_unit in work_datum[1]:
            if work_unit[0].weekday() < 5:
                # 前日から食い込んできている場合
                if work_unit[1].weekday() == 5:
                    days_last = work_datum[0] + timedelta(days=1)
                    work_time += (work_unit[1] - days_last).seconds / 60
                # 前日から食い込んできていない場合
                else:
                    pass
            # 当日の場合 26:00 ~ 28:00とかでもカバー
            elif work_unit[0].weekday() == 5:
                if work_unit[1].weekday() == 5:
                    work_time += (work_unit[1] - work_unit[0]).seconds / 60
                else:
                    days_last = work_datum[0] + timedelta(days=1)
                    work_time += (days_last - work_unit[0]).seconds / 60
    return work_time


def get_law_holiday_work(work_data):
    """
    :param work_data: 
    :return: 所定休日労働時間
    """
    work_time = 0
    for work_datum in work_data:
        for work_unit in work_datum[1]:
            if work_unit[0].weekday() < 6:
                # 前日から食い込んできている場合
                if work_unit[1].weekday() == 6:
                    days_last = work_datum[0] + timedelta(days=1)
                    work_time += (work_unit[1] - days_last).seconds / 60
                # 前日から食い込んできていない場合
                else:
                    pass
                # 当日の場合 26:00 ~ 28:00とかでもカバー
            elif work_unit[0].weekday() == 6:
                if work_unit[1].weekday() == 6:
                    work_time += (work_unit[1] - work_unit[0]).seconds / 60
                else:
                    days_last = work_datum[0]+ timedelta(days=1)
                    work_time += (days_last - work_unit[0]).seconds / 60
    return work_time


def get_midnight_work(work_data):
    work_time = 0
    for work_datum in work_data:
        twenty_o_clock = datetime.strptime("{} {}".format(work_datum[0].strftime("%Y/%m/%d"), "22:00"), "%Y/%m/%d %H:%M")
        for work_unit in work_datum[1]:
            if work_unit[0] >= twenty_o_clock:
                work_time += (work_unit[1] - work_unit[0]).seconds / 60
            else:
                if work_unit[1] >= twenty_o_clock:
                    work_time += (work_unit[1] - twenty_o_clock).seconds / 60
                else:
                    pass
    return work_time


def get_law_overtime_work(work_data, outlaw_work_time):
    """
    :param work_data: 
    :return: 法定内残業時間 
    """
    law_work_time = 0
    law_ovetime_work_time = 0
    get_outlaw_overtime_work_time = 0
    for work_datum in work_data:
        intime_end = datetime.strptime("{} {}".format(work_datum[0].strftime("%Y-%m-%d"), "16:00"), "%Y-%m-%d %H:%M")
        for work_unit in work_datum[1]:
            law_overtime_work_time_a_day = 0
            law_work_time_a_day = 0

            # 全部土日の場合
            if work_unit[0].weekday() > 4:
                law_overtime_work_time_a_day = 0
            # 終わりだけ土日に突っ込んでいる場合
            elif work_unit[1].weekday() > 4:
                # まるまるはみ出ている場合
                if work_unit[0] > intime_end:
                    law_overtime_work_time_a_day += ((work_datum[0] + timedelta(days=1)) - work_unit[0]).seconds / 60
                # 終わりだけはみ出ている場合
                elif work_unit[1] > intime_end:
                    law_overtime_work_time_a_day += ((work_datum[0] + timedelta(days=1)) - intime_end).seconds / 60
                    law_work_time_a_day += (intime_end - work_unit[0]).seconds / 60
            # 土日に突っ込んでない場合
            else:
                # まるまるはみ出ている場合
                if work_unit[0] > intime_end:
                    law_overtime_work_time_a_day += (work_unit[1] - work_unit[0]).seconds / 60
                # 終わりだけはみ出している場合
                elif work_unit[1] > intime_end:
                    law_overtime_work_time_a_day += (work_unit[1] - intime_end).seconds / 60
                    law_work_time_a_day += (intime_end - work_unit[0]).seconds / 60
                # 何もはみ出ていない場合
                else:
                    law_work_time_a_day += (work_unit[1] - work_unit[0]).seconds / 60
            law_ovetime_work_time += law_overtime_work_time_a_day
            law_work_time += law_work_time_a_day
    output = law_ovetime_work_time - outlaw_work_time
    return output if output > 0 else 0


def get_outlaw_overtime_work(work_data, past_month_work_data):
    outlaw_work_time = 0
    week_work_time = 0
    # 予め先月の実労働時間を追加
    for past_month_work_datum in past_month_work_data:
        for past_month_work_unit in past_month_work_datum[1]:
            week_work_time += (past_month_work_unit[1] - past_month_work_unit[0]).seconds / 60
    last_weekday = 0
    for work_datum in work_data:
        work_time_a_day = 0
        date = work_datum[0]
        if last_weekday <= date.weekday():
            last_weekday = date.weekday()
            if date.weekday() < 6:
                # 一日あたりの労働時間の算出
                for work_unit in work_datum[1]:
                    # 法定外残業は土日曜日に適用されないので, またいだ部分をカット
                    if work_unit[0].weekday() > 4:
                        pass
                    # 法定外残業は所定休日に適用されないので, またいだ部分をカット
                    elif work_unit[1].weekday() > 4:
                        work_time_a_day += ((date + timedelta(days=1)) - work_unit[0]).seconds / 60
                    else:
                        work_time_a_day += (work_unit[1] - work_unit[0]).seconds / 60

                # 法定外残業の算出
                # 1日8時間以上の時 一週間の労働時間に追加し, 法定外残業に残りを追加
                if work_time_a_day > 480:
                    outlaw_work_time += work_time_a_day - 480
                    week_work_time += work_time_a_day
                # 1日8時間未満の時 一週間の労働時間に追加
                else:
                    week_work_time += work_time_a_day
        else:
            last_weekday = date.weekday()
            #print("あああ", outlaw_work_time)
            if week_work_time > 40 * 60:
                outlaw_work_time += week_work_time - 40 * 60
            week_work_time = 0
    return outlaw_work_time









def parse_unit(work_data_units):
    """
    データ形式： [[datetime1, datetime2]]
    :param work_data_units: "yyyy/mm/dd( HH:MM-HH:MM)*"
    :return: [[datetime start_datetime, datetime end_datetime]]
    """
    work_data_unit_list = work_data_units.strip().split(" ")
    date_str = work_data_unit_list.pop(0)
    date = datetime.strptime(date_str, "%Y/%m/%d")
    work_data_unit_list_parsed = []

    for work_data_unit in work_data_unit_list:
        # 開始終了ペアをデータ化 %HH:%MM-%HH:%MM 単位
        start, end = work_data_unit.split("-")
        start_data = list(map(int, start.split(":")))
        end_data = list(map(int, end.split(":")))
        work_unit = [0, 0]
        # 翌日まで回っている場合の計算
        # start_dataが翌日になっている場合
        if start_data[0] >= 24:
            start_data = map(str, [start_data[0] % 24, start_data[1]])
            next_date = date + timedelta(days=1)
            start_data_str = "{} {}".format(next_date.strftime("%Y/%m/%d"), ":".join(start_data))
            work_unit[0] = datetime.strptime(start_data_str, "%Y/%m/%d %H:%M")
        else:
            start_data_str = "{} {}".format(date_str, start)
            work_unit[0] = datetime.strptime(start_data_str, "%Y/%m/%d %H:%M")

        # end_dataが翌日になっている場合
        if end_data[0] >= 24:
            end_data = map(str, [end_data[0] % 24, end_data[1]])
            next_date = date + timedelta(days=1)
            end_data_str = "{} {}".format(next_date.strftime("%Y/%m/%d"), ":".join(end_data))
            work_unit[1] = datetime.strptime(end_data_str, "%Y/%m/%d %H:%M")
        else:
            end_data_str = "{} {}".format(date_str, end)
            work_unit[1] = datetime.strptime(end_data_str, "%Y/%m/%d %H:%M")
        work_data_unit_list_parsed.append(work_unit)
    return date, work_data_unit_list_parsed


if __name__=="__main__":
    main()
