import datetime
import random
import csv
from builtins import round

import matplotlib.pyplot as plt

from bourse_refs.models import StockHistory, Stock


def get_price(sym, date):
    return StockHistory.objects.filter(date__lt=date, stock__name=sym).last().last_price


with open('predictions.csv', encoding="utf8") as file:
    data = list(csv.reader(file))


data = data[2:]
output = {}
for row in data:
    user_id = row[-2] + '||||||' + row[5]
    is_succeeded = row[7][0] == 'T'
    profit = float(row[6])
    start_date = datetime.datetime.fromtimestamp(int(row[9][6:-2])/1000)
    close_date = datetime.datetime.fromtimestamp(int(row[17][6:-2])/1000)
    expected_return = float(row[-4][1:])
    expected_risk = float(row[-3][1:])
    symbol = row[5]

    if user_id not in output:
        output[user_id] = []
    output[user_id].append({'profit': profit / 100, 'start_date': start_date, 'close_date': close_date,
                            'prediction': is_succeeded, 'expected_return': expected_return,
                            'expected_risk': expected_risk, 'symbol': symbol})

for key in output.keys():
    output[key].reverse()

actions = ["buy", "not"]
epsilon = 1
act_percentage = 0.3
alpha = 0.01


def get_policy2(s):  # s must be a string describing state
    action_ind = 0
    if sample[stage]['start_date'] <= day:
        return 'not'
    sum2 = 0
    for i in range(len(actions)):
        sum2 += Q[s, actions[i]]
    x = random.randint(0, int(sum2))
    for i in range(len(actions)):
        if x <= Q[s, actions[i]]:
            return actions[action_ind]
        x -= Q[s, actions[i]]


def get_policy(s):  # s must be a string describing state
    action_ind = 0
    if sample[stage]['start_date'] <= day:
        return 'not'
    for i in range(len(actions)):
        if Q[s, actions[i]] > Q[s, actions[action_ind]]:
            action_ind = i
    return actions[action_ind]


def learn(s, action, s_prim, rew):
    opt_cont_value = 1
    for i, act in Q.keys():
        if i[0].startswith(s_prim[0]):
            if opt_cont_value < Q[i, act]:
                opt_cont_value = Q[i, act]
    Q[s, action] = (1 - alpha) * Q[s, action] + alpha * (rew * opt_cont_value)


def step(s, action, stage, day, last_stage):
    end = len(s[0])
    new_stage = last_stage
    if action == "buy":
        if sample[stage]['start_date'] > day:
            rew = 1 + sample[stage]['profit']# * (min(1, 1 - min(1, abs(sample[stage]['profit'] - sample[stage]['expected_return']/100))))
            profit = sample[last_stage]['profit']
        else:
            start_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['start_date'])
            end_price = get_price(sample[last_stage]['symbol'], sample[stage]['start_date'])
            if end_price/start_price >= sample[last_stage]['profit']:
                rew = 3
            elif sample[stage]['start_date'] <= sample[last_stage]['start_date'] + 10 * 86400:
                rew = 0
            else:
                rew = 1 + sample[stage]['profit'] - sample[last_stage]['profit'] # min(0, 1 + sample[stage]['profit'] * 5) # * (min(1, 1 - min(1, abs(sample[stage]['profit'] - sample[stage]['expected_return']/100))))
            profit = end_price/start_price
        s_prim = s[0][end - look_back_window + 1:] + sample[stage]['prediction'], (
            int(sample[stage + 1]['expected_return'] / 10) * 10 if stage < len(sample) - 1 else 0), round(s[2] * profit, 1)
        day = sample[stage]['close_date']
        new_stage = stage
    else:
        s_prim = s[0][end - look_back_window + 1:] + sample[stage]['prediction'], (int(sample[stage + 1]['expected_return']/10)*10 if stage < len(sample) - 1 else 0), s[2]
        rew = 1
    if not (s_prim, "buy") in Q.keys():
        Q.update({(s_prim, "buy"): 1})
    if not (s_prim, "not") in Q.keys():
        Q.update({(s_prim, "not"): 1})
    return s_prim, rew, day, new_stage


arr = []
ERROR = set()
for look_back_window in range(6, 7):
    sum_score, count_score, count_success = 0, 0, 0

    epsilon = 1
    for key, sample in output.items():
        start_state = "T" * look_back_window, int(sample[0]['expected_return']/10)*10, 1
        Q = {(start_state, "buy"): 1, (start_state, "not"): 1}

        score = 1
        day = -1
        last_stage = -1
        for w in range(15):
            for stage in range(int((1 - act_percentage) * len(sample))):
                if not Stock.objects.filter(sample[stage]['symbol']).exists():
                    continue
                if sample[stage]['close_date'] > 1563922723:
                    continue

                r = random.uniform(0, 1)
                if r > epsilon:
                    a = get_policy2(start_state)
                else:
                    a = random.choice(actions)

                if a == "buy" and last_stage > -1:
                    start_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['start_date'])
                    if sample[stage]['start_date'] >= sample[last_stage]['close_date']:
                        # print("YES")
                        end_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['close_date'])
                    else:
                        # print("SELL")
                        end_price = get_price(sample[last_stage]['symbol'], sample[stage]['start_date'])
                    score *= end_price / start_price
                    last_stage = stage


                end_state, reward, day, last_stage = step(start_state, a, stage, day, last_stage)
                learn(start_state, a, end_state, reward)

                start_state = end_state
                stage += 1

            if w != 14:
                score = 1
                day = -1
                last_stage = -1

            if epsilon > 0.06:
                epsilon -= 0.06
            elif epsilon > 0:
                epsilon = 0

        # score = 1
        # print(score)
        # last_stage = -1
        for stage in range(int((1 - act_percentage) * len(sample)), len(sample)):
            if sample[stage]['close_date'] > 1563922723:
                continue
            if not Stock.objects.filter(sample[stage]['symbol']).exists():
                continue

            a = get_policy(start_state)
            if a == 'buy':
                if last_stage != -1:
                    start_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['start_date'])
                    if sample[stage]['start_date'] >= sample[last_stage]['close_date']:
                        # print("YES")
                        end_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['close_date'])
                    else:
                        # print("SELL")
                        end_price = get_price(sample[last_stage]['symbol'], sample[stage]['start_date'])
                    score *= end_price / start_price
                last_stage = stage
            end_state, _, day, last_stage = step(start_state, a, stage, day, last_stage)
            start_state = end_state

        if last_stage != -1:
            score *= 1 + sample[last_stage]['profit']
            # start_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['start_date'])
            # end_price = get_price(sample[last_stage]['symbol'], sample[last_stage]['close_date'])
            # score *= start_price / end_price

        # sum_score += score
        # count_success += score > 1
        # count_score += 1
        # if score > 4:
        #     print(key, score)

    # arr.append(sum_score/count_score)
    # print(sum_score / count_score, ',')

# plt.plot(arr)
plt.hist(arr)
plt.show()
