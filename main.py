import csv
import os
import numpy as np
from datetime import datetime
from random import randint

from matplotlib import pyplot as plt


def date(s):
    return datetime(year=int(s[:4]), month=int(s[4:6]), day=int(s[6:]))


def get_change(data, i):
    if i < len(data) and (date(data[i][0]) - date(data[i - 1][0])).days <= 4:
        return (data[i][4] / data[i - 1][3] - 1) * 100


stock_data = {}


def readfile(filename):
    if not filename.endswith('.csv'):
        return
    stock_data[filename[:-4]] = []
    with open('data/' + filename) as file:
        data = list(csv.reader(file))
    assert (str(data[
                    0]) == "['date', 'max_price', 'min_price', 'last_price', 'last_deal_price', 'first_price', 'yesterday_price', 'value', 'volume', 'count']")
    data = data[1:]
    for row in data:
        d = date(row[0])
        if d.year >= 2018 or (d.year == 2016 and d.month >= 5):
            stock_data[filename[:-4]].append((d, int(float(row[3]))))
    stock_data[filename[:-4]].reverse()
