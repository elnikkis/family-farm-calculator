# -*- coding: utf-8 -*-

import sys
from collections import namedtuple
from functools import lru_cache
import numpy as np
import pandas as pd


Price = namedtuple('Price', ['cost', 'price', 'kind'])

class MyError(Exception):
    pass

class MaterialError(MyError):
    pass

class PriceError(MyError):
    pass


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('price_csv')
    parser.add_argument('material_csv')
    parser.add_argument('-d', dest='debug', action='store_true', default=False)
    return parser.parse_args()

def load_prices_data(filename):
    prices = {}
    with open(filename, encoding='cp932') as fp:
        # skip header
        print('price header:', next(fp).rstrip(), file=sys.stderr)
        for line in fp:
            line = line.rstrip().split(',')
            name = line[0]
            if not name:
                print('skip row: {}'.format(line), file=sys.stderr)
                continue
            cost = int(line[1]) if line[1] else np.nan
            price = int(line[2]) if line[2] else np.nan
            kind = line[4]
            prices[name] = Price(cost, price, kind)
    return prices

def load_materials_data(filename):
    materials = {}
    with open(filename, encoding='cp932') as fp:
        print('header:', next(fp).rstrip(), file=sys.stderr)
        for line in fp:
            line = [x for x in line.rstrip().split(',') if x]

            # 空行は飛ばす
            if not line:
                continue

            if len(line) < 2 or len(line) % 2 != 1:
                print('info: {} is not set materials.'.format(line[0]), file=sys.stderr)
                continue
            target = line[0]
            # 素材名1, 個数, 素材名2, 個数, ... という形式になっている
            sources = {a: float(b) for a, b in zip(line[1::2], line[2::2])}
            materials[target] = sources
    return materials


if __name__ == '__main__':
    args = parse_args()

    # データ読み込み
    prices = load_prices_data(args.price_csv)
    materials = load_materials_data(args.material_csv)
    #print(prices)
    #print(materials)

    # コスト＝材料の売値の和
    @lru_cache(maxsize=1000)
    def get_max_cost(item_name):
        p = prices[item_name]
        # 作物なら、コストは畑に植えたときの価格
        if p.kind in ['作物', '樹木', '収集機', '蜜', '海産物', '素材']:
            return p.cost

        # それ以外のアイテムは、材料の売値の和がコスト
        cost = 0
        if item_name not in materials:
            print('{} does not have any materias.'.format(item_name), file=sys.stderr)
            return np.nan
        for material, num in materials[item_name].items():
            try:
                price = prices[material].price
                # 売値が設定されていないとき
                if np.isnan(price):
                    raise MaterialError("Cannot calculate {} cost because {}'s price is not set.".format(item_name, material))
                cost += price * num
            except KeyError as e:
                # 売値テーブルにmaterialのデータがない
                raise MaterialError('Cannot calculate {} cost because {} is not in price table.'.format(item_name, material))
        return cost

    # コストと単純儲け計算
    profits = {}
    for item in prices.keys():
        d = prices[item]
        try:
            max_cost = get_max_cost(item)
        except MyError as e:
            print(e, file=sys.stderr)
            max_cost = np.nan
        # アイテム名、原価、売値、儲け、種別
        profit = d.price - max_cost
        profits[item] = (max_cost, profit)

    # 累積儲け＝材料の儲けの和
    @lru_cache(maxsize=1000)
    def get_cumulative_profit(item_name):
        if item_name not in profits:
            # 売値テーブルにないアイテムはprofitsにもない
            print("Cannot calculate {}'s cumulative profit because it is not in profits table.".format(item_name), file=sys.stderr)
            return np.nan
        cum = profits[item_name][1]

        # 材料がなければ、それがルート
        if item_name not in materials:
            return cum

        # 材料があれば、それらの儲けも足す
        for material in materials[item_name]:
            cum += get_cumulative_profit(material)
        return cum

    # 累積儲けの計算
    cum_profits = {}
    for item in profits.keys():
        cum_profit = get_cumulative_profit(item)
        cum_profits[item] = cum_profit

    # デバッグモード以外なら
    if not args.debug:
        # output
        print('アイテム名', '売値', 'コスト', '単純儲け', '累積儲け', '種別', sep='\t')
        for item in profits.keys():
            d = prices[item]
            max_cost, profit = profits[item]
            cum_profit = cum_profits[item]

            # float -> int （四捨五入）
            if not np.isnan(max_cost):
                max_cost = round(max_cost)
            if not np.isnan(profit):
                profit = round(profit)
            if not np.isnan(cum_profit):
                cum_profit = round(cum_profit)

            print(item, d.price, max_cost, profit, cum_profit, d.kind, sep='\t')

