import os
import random
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max, Min

from advertisement.constant import SEX_CHOICES
from advertisement.utils import generate_random_token
from bourse_refs.models import Stock, StockHistory


def get_image_path(instance, filename):
    return os.path.join(str(Signal.objects.all().count()) + filename)


class Signal(models.Model):
    title = models.CharField(max_length=80)
    is_succeeded = models.BooleanField(default=None, blank=True, null=True)
    profit = models.FloatField(default=None, blank=True, null=True, help_text='Percentage')
    start_date = models.DateField(default=None, blank=True, null=True)
    close_date = models.DateField(default=None, blank=True, null=True)
    expected_return = models.FloatField(default=None, blank=True, null=True, help_text='Percentage')
    expected_risk = models.FloatField(default=None, blank=True, null=True, help_text='Percentage')

    symbol = models.ForeignKey('Symbol', on_delete=models.CASCADE)
    expert = models.ForeignKey('Expert', on_delete=models.CASCADE, null=True, default="", blank=True)

    should_buy = models.BooleanField(default=False)

    ACTIONS = ["buy", "not"]

    class Meta:
        ordering = ['-start_date', '-close_date']

    def __str__(self):
        return self.title + ' ' + self.symbol.name

    @property
    def user_id(self):
        return self.expert.display_name

    @staticmethod
    def get_price(sym, date):
        return StockHistory.objects.filter(date__lt=date, stock__name=sym.name).last().last_price

    @staticmethod
    def get_policy2(s, sample, stage, day, Q):  # s must be a string describing state
        action_ind = 0
        if sample[stage].start_date <= day:
            return 'not'
        sum2 = 0
        for i in range(len(Signal.ACTIONS)):
            sum2 += Q[s, Signal.ACTIONS[i]]
        x = random.randint(0, int(sum2))
        for i in range(len(Signal.ACTIONS)):
            if x <= Q[s, Signal.ACTIONS[i]]:
                return Signal.ACTIONS[action_ind]
            x -= Q[s, Signal.ACTIONS[i]]

    @staticmethod
    def get_policy(s, sample, stage, day, Q):  # s must be a string describing state
        action_ind = 0
        if sample[stage].start_date <= day:
            return 'not'
        for i in range(len(Signal.ACTIONS)):
            if Q[s, Signal.ACTIONS[i]] > Q[s, Signal.ACTIONS[action_ind]]:
                action_ind = i
        return Signal.ACTIONS[action_ind]

    @staticmethod
    def learn(s, action, s_prim, rew, Q, alpha):
        opt_cont_value = 1
        for i, act in Q.keys():
            if i[0].startswith(s_prim[0]):
                if opt_cont_value < Q[i, act]:
                    opt_cont_value = Q[i, act]
        Q[s, action] = (1 - alpha) * Q[s, action] + alpha * (rew * opt_cont_value)

    def step(self, s, action, stage, day, last_stage, sample, look_back_window, Q):
        end = len(s[0])
        new_stage = last_stage
        if action == "buy":
            if sample[stage].start_date > day:
                rew = 1 + sample[stage].profit / 100
                profit = sample[last_stage].profit / 100
            else:
                start_price = self.get_price(sample[last_stage].symbol, sample[last_stage].start_date)
                end_price = self.get_price(sample[last_stage].symbol, sample[stage].start_date)
                if end_price / start_price >= sample[last_stage].profit / 100:
                    rew = 3
                elif sample[stage].start_date <= sample[last_stage].start_date + timedelta(days=10):
                    rew = 0
                else:
                    rew = 1 + sample[stage].profit / 100 - sample[last_stage].profit / 100
                profit = end_price / start_price
            s_prim = s[0][end - look_back_window + 1:] + ('T' if sample[stage].is_succeeded else 'F'), (
                int(sample[stage + 1].expected_return / 10) * 10 if stage < len(sample) - 1 else 0), round(
                s[2] * profit * 0.985, 1)
            day = sample[stage].close_date
            new_stage = stage
        else:
            s_prim = s[0][end - look_back_window + 1:] + ('T' if sample[stage].is_succeeded else 'F'), (
                int(sample[stage + 1].expected_return / 10) * 10 if stage < len(sample) - 1 else 0), s[2]
            rew = 1
        if not (s_prim, "buy") in Q.keys():
            Q.update({(s_prim, "buy"): 1})
        if not (s_prim, "not") in Q.keys():
            Q.update({(s_prim, "not"): 1})
        return s_prim, rew, day, new_stage

    def expert_aggregate(self):
        look_back_window = 6
        act_percentage = 0.3
        epsilon = 1

        sample = list(Signal.objects.filter(expert=self.expert, is_succeeded__isnull=False).order_by('start_date', 'close_date')) + [self]
        start_state = "T" * look_back_window, int(sample[0].expected_return/10)*10, 1
        Q = {(start_state, "buy"): 1, (start_state, "not"): 1}

        score = 1 * 0.985
        day = date(year=1970, month=1, day=1)
        last_stage = -1
        for w in range(15):
            for stage in range(int((1 - act_percentage) * len(sample))):
                if not Stock.objects.filter(name=sample[stage].symbol.name).exists():
                    continue
                # if sample[stage].close_date > 1563922723:
                #     continue

                r = random.uniform(0, 1)
                if r > epsilon:
                    a = self.get_policy2(start_state, sample, stage, day, Q)
                else:
                    a = random.choice(Signal.ACTIONS)

                if a == "buy" and last_stage > -1:
                    start_price = self.get_price(sample[last_stage].symbol, sample[last_stage].start_date)
                    if sample[stage].start_date >= sample[last_stage].close_date:
                        # print("YES")
                        end_price = self.get_price(sample[last_stage].symbol, sample[last_stage].close_date)
                    else:
                        # print("SELL")
                        end_price = self.get_price(sample[last_stage].symbol, sample[stage].start_date)
                    score *= (end_price / start_price) * 0.985
                    last_stage = stage

                end_state, reward, day, last_stage = self.step(start_state, a, stage, day, last_stage, sample, look_back_window, Q)
                self.learn(start_state, a, end_state, reward, Q, alpha=0.01)

                start_state = end_state
                stage += 1

            if w != 14:
                score = 1
                day = date(year=1970, month=1, day=1)
                last_stage = -1

            if epsilon > 0.06:
                epsilon -= 0.06
            elif epsilon > 0:
                epsilon = 0

        answer = "not"
        for stage in range(int((1 - act_percentage) * len(sample)), len(sample)):
            # if sample[stage].close_date > 1563922723:
            #     continue
            if not Stock.objects.filter(name=sample[stage].symbol.name).exists():
                continue
            a = self.get_policy(start_state, sample, stage, day, Q)
            if a == 'buy':
                if stage == len(sample) - 1:
                    answer = 'buy'
                if last_stage != -1:
                    start_price = self.get_price(sample[last_stage].symbol, sample[last_stage].start_date)
                    if sample[stage].start_date >= sample[last_stage].close_date:
                        # print("YES")
                        end_price = self.get_price(sample[last_stage].symbol, sample[last_stage].close_date)
                    else:
                        # print("SELL")
                        end_price = self.get_price(sample[last_stage].symbol, sample[stage].start_date)
                    if stage < len(sample) - 1:
                        score *= (end_price / start_price) * 0.985
                last_stage = stage
            end_state, _, day, last_stage = self.step(start_state, a, stage, day, last_stage, sample, look_back_window, Q)
            start_state = end_state

        if answer == 'buy':
            self.should_buy = True
        if last_stage != -1 and last_stage != len(sample) - 1:
            score *= (1 + sample[last_stage].profit / 100) * 0.985
        Signal.score = score

    def save(self, **kwargs):
        if self.is_succeeded is None:
            self.expert_aggregate()
        super().save(**kwargs)


class Member(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=12, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True)
    age = models.IntegerField(null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    followings = models.ManyToManyField(to='Expert', related_name='followers')

    def __str__(self):
        return self.first_name  # + ' ' + self.last_name


class Expert(models.Model):
    display_name = models.CharField(max_length=30)
    website = models.URLField(max_length=200, null=True)
    raw_score = models.FloatField(default=1)

    def __str__(self):
        return self.display_name

    @property
    def score(self):
        ads = Signal.objects.filter(expert=self).select_related('symbol')
        failure = len(ads.filter(is_succeeded=False))
        self.raw_score = 1 - (failure / (len(ads) + 1))
        self.save()
        max_score = Expert.objects.all().aggregate(Max('raw_score'))['raw_score__max']
        min_score = Expert.objects.all().aggregate(Min('raw_score'))['raw_score__min']
        if max_score == min_score:
            return 100
        normalized_score = (self.raw_score - min_score) / (max_score - min_score)
        return int(normalized_score*100)


class Symbol(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ResetPassword(models.Model):
    advertiser = models.ForeignKey(Member, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, default=generate_random_token)

    def get_reset_password_link(self):
        return "{}/change_password?token={}".format(settings.SITE_DOMAIN, self.token)


