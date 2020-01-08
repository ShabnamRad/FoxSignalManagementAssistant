import datetime
import sys

from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from chartjs.views.lines import BaseLineChartView

from advertisement.models import Signal, Member, Expert, Symbol, ResetPassword
from advertisement.utils import send_email_async
from database import symbols
from main import stock_data
from .forms import SearchForm, AddSignalForm, LoginForm, ResetPassForm, RegisterForm, AddExpertForm, SubmitPassword, \
    ApplyAlgorithmForm
from django.contrib.auth import authenticate, login, logout


def search(request):
    if request.method == 'GET':
        form = SearchForm()
        ads = Signal.objects.all().order_by('-expert__raw_score')[:200]
        return render(request, '../templates/search.html', {
            'ads': ads,
            'form': form
        })
    else:
        form = SearchForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            ads = Signal.objects.filter(
                Q(title__contains=title) | Q(symbol__name__contains=title) | Q(expert__display_name__contains=title))[
                  :100]
            return render(request, '../templates/search.html', {
                'ads': ads,
                'form': form
            })
        else:
            return render(request, '../templates/search.html', {'form': form})


def add_advertisement(request):
    if request.method == 'GET':
        form = AddSignalForm()
        return render(request, '../templates/add_signal.html', {'form': form})
    else:
        form = AddSignalForm(request.POST, request.FILES)
        form.user = request.user
        if form.is_valid():
            form.save()
            return redirect('search')
        else:
            return render(request, '../templates/add_signal.html', {'form': form})


def add_expert(request):
    if request.method == 'GET':
        form = AddExpertForm()
        return render(request, '../templates/add_expert.html', {'form': form})
    else:
        form = AddExpertForm(request.POST, request.FILES)
        form.user = request.user
        if form.is_valid():
            form.save()
            return redirect('profile')
        else:
            return render(request, '../templates/add_expert.html', {'form': form})


def symbols_list(request):
    if request.method == 'GET':
        symbols = Symbol.objects.all()
        return render(request, '../templates/symbols.html', {
            'symbols': symbols
        })


def profile(request):
    ads = Signal.objects.filter(expert__in=request.user.member.followings.all())[:100]
    return render(request, '../templates/profile.html', {
        'ads': ads
    })


def dashboard(request):
    return render(request, '../templates/dashboard.html')


def home(request):
    return render(request, '../templates/home.html')


def login_view(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, '../templates/login.html', {'form': form})
    else:
        form = LoginForm(request.POST)
        user = authenticate(request, username=form['username'].value(), password=form['password'].value())
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, '../templates/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, '../templates/register.html', {'form': form})
    else:
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
        else:
            return render(request, '../templates/register.html', {'form': form})


def reset_password(request):
    if request.method == 'GET':
        form = ResetPassForm()
        return render(request, '../templates/forget_password.html', {'form': form})
    else:
        form = ResetPassForm(request.POST, request.FILES)
        try:
            advertiser = Member.objects.filter(email=form.data['email'])[0]
            new_password = ResetPassword(advertiser=advertiser)
            new_password.save()
            subject = 'Reset Password'
            body = render_to_string('email_template', context={
                'username': advertiser.user.username,
                'reset_link': new_password.get_reset_password_link()
            })
            email = EmailMessage(subject=subject, body=body, to=[advertiser.email])
            send_email_async(email)
            return redirect('home')
        except Member.DoesNotExist:
            return render(request, '../templates/forget_password.html', {
                'form': form,
                'error': 'No user with this email address'
            })


def change_password(request):
    if request.method == 'GET':
        form = SubmitPassword()
        return render(request, '../templates/change_password.html', {'form': form})
    else:
        form = SubmitPassword(request.POST)
        token = request.GET.get('token')
        if form.is_valid():
            new_password = ResetPassword.objects.filter(token=token)[0]
            new_password.advertiser.user.set_password(form.data['password'])
            new_password.advertiser.user.save()
            return redirect('home')
        else:
            return render(request, '../templates/change_password.html', {'form': form})


class LineChartJsonView(BaseLineChartView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.other_signals = None

    def get_labels(self):
        arr = stock_data[symbols[Signal.objects.get(id=self.kwargs['ad']).symbol.name]]
        return [x[0] for x in arr]

    def get_providers(self):
        providers = ['Other Signals'] * len(self.other_signals)
        providers.insert(0, 'Signal')
        providers.insert(0, 'Selling Dates')
        providers.insert(0, 'Buying Dates')
        providers.append('Price')
        return providers

    def get_data(self):
        sig = Signal.objects.get(id=self.kwargs['ad'])
        other_signals = Signal.objects.filter(expert=sig.expert, symbol=sig.symbol).exclude(
            id=self.kwargs['ad']).order_by('start_date').values_list('start_date', 'close_date')
        self.other_signals = other_signals
        price_arr = stock_data[symbols[sig.symbol.name]]
        signal_arr = [None for x in price_arr]
        other_signals_arr = [[None for x in price_arr] for i in range(len(other_signals))]
        buy_arr = [None for x in price_arr]
        sell_arr = [None for x in price_arr]

        for i, x in enumerate(price_arr):
            if sig.start_date <= x[0].date() <= sig.close_date:
                signal_arr[i] = x[1]
                if x[0].date() == sig.start_date or i == 0 or price_arr[i - 1][0].date() < sig.start_date:
                    buy_arr[i] = x[1]
                if x[0].date() == sig.close_date or i == len(price_arr) - 1 or price_arr[i + 1][
                    0].date() > sig.close_date:
                    sell_arr[i] = x[1]
            for j, (start, close) in enumerate(other_signals):
                if start <= x[0].date() <= close:
                    other_signals_arr[j][i] = x[1]
                    if x[0].date() == start or i == 0 or price_arr[i - 1][0].date() < start:
                        buy_arr[i] = x[1]
                    if x[0].date() == close or i == len(price_arr) - 1 or price_arr[i + 1][0].date() > close:
                        sell_arr[i] = x[1]
        res = [x for x in other_signals_arr]
        res.insert(0, signal_arr)
        res.insert(0, sell_arr)
        res.insert(0, buy_arr)
        res.append([x[1] for x in price_arr])
        return res


class SymbolChartJsonView(BaseLineChartView):
    def get_labels(self):
        arr = stock_data[symbols[self.kwargs['symbol']]]
        return [x[0] for x in arr]

    def get_providers(self):
        return ['Price']

    def get_data(self):
        arr = stock_data[symbols[self.kwargs['symbol']]]
        return [[x[1] for x in arr]]


def advertisement_detail(request, advertisement_id):
    try:
        advertisement = Signal.objects.get(pk=advertisement_id)
        return render(request, '../templates/ad_detail.html', {
            'advertisement': advertisement
        })
    except Signal.DoesNotExist:
        raise Http404("Question does not exist")


def symbol_detail(request, symbol_name):
    try:
        symbol_obj = Symbol.objects.get(name=symbol_name)
        ads = Signal.objects.filter(symbol=symbol_obj).order_by('-start_date')
        return render(request, '../templates/symbol_detail.html', {
            'symbol': symbol_obj,
            'ads': ads
        })
    except Symbol.DoesNotExist:
        raise Http404("Question does not exist")


def expert_page(request, expert_id):
    expert = Expert.objects.get(id=expert_id)
    ads = Signal.objects.filter(expert=expert).select_related('symbol')
    failure = len(ads.filter(is_succeeded=False))
    success = len(ads.filter(is_succeeded=True))
    score = expert.score

    symbols = set(ads.values_list('symbol__name', flat=True))
    ads_chart = [Signal.objects.filter(expert=expert, symbol__name=sname).latest('id') for sname in symbols]

    securities = set(ads.values_list('symbol__id', 'symbol__name'))
    return render(request, '../templates/expert_page.html', {
        'expert': expert,
        'ads_chart': ads_chart,
        'ads': ads,
        'securities': securities,
        'score': score,
        'failure': failure,
        'success': success
    })


def falo(request, expert_id):
    request.user.member.followings.add(expert_id)
    return HttpResponse("OK")


def onfalo(request, expert_id):
    request.user.member.followings.remove(expert_id)
    return HttpResponse("OK")


def expert_aggregate(request):
    experts = Expert.objects.all()
    if request.method == 'GET':
        ads = Signal.objects.all().order_by('-expert__raw_score')[:200]
        form = ApplyAlgorithmForm
        return render(request, '../templates/expert_aggregation.html', {
            'ads': ads,
            'form': form,
            'experts': experts,
            'weights': {},
            'final_wealth': 0,
            'show_results': False,
        })
    else:
        experts = list(map(int, request.POST['experts'].split(',')))
        all_ads = False
        if 0 in experts:
            experts = Expert.objects.all()
            ads = Signal.objects.all()
            all_ads = True
        else:
            experts = Expert.objects.filter(id__in=experts)
            ads = Signal.objects.filter(expert_id__in=experts)

        output = {}
        weights = {}
        num_of_signals = {}
        wealth = 1
        taken_signals = []
        not_taken_signals = []
        to_invest = 0.78

        for ad in ads:
            if ad.is_succeeded is None:
                continue
            user_id = ad.expert.id
            expert = ad.expert
            start_date = ad.start_date
            signal_id = ad.id
            weights[expert] = 1
            num_of_signals[user_id] = 0
            if start_date not in output:
                output[start_date] = {}
            output[start_date].update(
                {signal_id: {'user_id': ad.expert.id, 'share_id': ad.symbol.name, 'profit': ad.profit / 100,
                             'close_date': ad.close_date, 'is_successful': ad.is_succeeded, 'expert': expert,
                             'expected_return': ad.expected_return,
                             'start_date': ad.start_date,
                             'expected_risk': ad.expected_risk}})

        def sell_all_possible_shares(signal_date, taken_signals, weights, num_of_signals, not_taken_signals):
            # taking back profit from sold shares
            total_profit = 0
            closed_signals_ids = []
            for taken_signal in taken_signals:
                sig = taken_signal[0]
                if sig['close_date'] <= signal_date:
                    last_profit = taken_signal[1] * (1 + sig['profit'])
                    # print("selling " + sig['share_id'] + " share, end date: " +
                    #       str(sig['close_date']) + ", getting : " + str(last_profit))
                    total_profit += last_profit
                    closed_signals_ids.append(taken_signal)
                    uid = sig['user_id']
                    if not sig['is_successful']:
                        # print(sig['share_id'] + "in " + str(sig['start_date']) + " was a failure")
                        weights[sig['expert']] *= 1 - 1 / (num_of_signals[uid] + 1)

            for closed_signal in closed_signals_ids:
                taken_signals.remove(closed_signal)

            closed_signals_ids = []
            for sig in not_taken_signals:
                if sig['close_date'] <= signal_date:
                    closed_signals_ids.append(sig)
                    uid = sig['user_id']
                    if not sig['is_successful']:
                        # print(signal['share_id'] + "in " + str(signal['start_date']) + " was a failure")
                        weights[sig['expert']] *= 1 - 1 / (num_of_signals[uid] + 1)

            for closed_signal in closed_signals_ids:
                not_taken_signals.remove(closed_signal)

            return total_profit

        for signal_date in sorted(output.keys()):
            # a day with signals in history.
            all_signals_for_share = {}
            investing_percentage = {}
            return_plus_risk = {}
            for signal_id in output[signal_date].keys():
                signal = output[signal_date][signal_id]
                # a signal in the signal_date.
                share_id = signal['share_id']
                user_id = signal['user_id']
                num_of_signals[user_id] += 1
                user_weight = weights[signal['expert']]
                investing_percentage[signal_id] = user_weight
                return_plus_risk[signal_id] = (signal['expected_return'] + signal['expected_risk']) / ((
                            signal['close_date'] - signal['start_date']).days + 1)
                if share_id not in all_signals_for_share:
                    all_signals_for_share[share_id] = []
                all_signals_for_share[share_id].append(signal)

            # normalizing weights and return_plus_risks
            sum_of_weights = sum(investing_percentage.values())
            sum_of_rps = sum(return_plus_risk.values())
            if sum_of_rps != 0:
                return_plus_risk.update((x, y / sum_of_rps) for (x, y) in return_plus_risk.items())
            investing_percentage.update(
                (x, (2 * y / sum_of_weights + return_plus_risk.get(x)) / 3) for (x, y) in
                investing_percentage.items())

            new_profit = sell_all_possible_shares(signal_date, taken_signals, weights, num_of_signals,
                                                  not_taken_signals)
            wealth += new_profit
            # print(wealth)

            step = 0.22
            if new_profit > 1 and to_invest <= 1 - step:
                to_invest += step

            # investing
            new_wealth = wealth
            for (sig_id, p) in investing_percentage.items():
                signal = output[signal_date][sig_id]
                if new_wealth > 0.0001:
                    invested_money = wealth * to_invest * p
                    # print("buying " + signal['share_id'] + " share, start: " + str(
                    #     signal_date) + ", spending : " + str(
                    #     invested_money))
                    taken_signals.append((signal, invested_money))
                    new_wealth -= invested_money
                else:
                    not_taken_signals.append(signal)
            wealth = new_wealth

        # print("Selling remaining shares in:")
        signal_date = datetime.date(year=2030, month=1, day=1)
        new_profit = sell_all_possible_shares(signal_date, taken_signals, weights, num_of_signals, not_taken_signals)
        wealth += new_profit
        if all_ads:
            ads = ads.order_by('-expert__raw_score')[:200]
        # normalization
        sum_of_weights = sum(weights.values())
        for e, weight in weights.items():
            weights[e] = weight/sum_of_weights

        return render(request, '../templates/expert_aggregation.html', {
            'ads': ads,
            'experts': experts,
            'weights': weights,
            'final_wealth': (wealth - 1) * 100,
            'show_results': True,
        })
