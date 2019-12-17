import symbol

from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from chartjs.views.lines import BaseLineChartView
from django.utils.datetime_safe import strftime

from advertisement.models import Signal, Member, Expert, Symbol, ResetPassword
from advertisement.utils import send_email_async
from database import symbols
from main import stock_data
from .forms import SearchForm, AddSignalForm, LoginForm, ResetPassForm, RegisterForm, AddExpertForm, SubmitPassword
from django.contrib.auth import authenticate, login, logout


def search(request):
    if request.method == 'GET':
        form = SearchForm()
        ads = Signal.objects.all()[:100]
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
            return redirect('dashboard')
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
            return redirect('dashboard')
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
            return redirect('dashboard')
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
    def get_labels(self):
        arr = stock_data[symbols[self.kwargs['symbol']]]
        return [x[0] for x in arr]

    def get_providers(self):
        return ['Buying Dates', 'Selling Dates', 'This Very Signal', 'Other Signals', 'Price']

    def get_data(self):
        price_arr = stock_data[symbols[self.kwargs['symbol']]]
        signal_arr = [None for x in price_arr]
        other_signals_arr = [None for x in price_arr]
        buy_arr = [None for x in price_arr]
        sell_arr = [None for x in price_arr]
        sig = Signal.objects.get(id=self.kwargs['ad'])

        other_signals = Signal.objects.filter(expert=sig.expert, symbol=sig.symbol).exclude(id=self.kwargs['ad']).order_by('start_date').values_list('start_date', 'close_date')

        for i, x in enumerate(price_arr):
            if sig.start_date <= x[0].date() <= sig.close_date:
                signal_arr[i] = x[1]
                if x[0].date() == sig.start_date or i == 0 or price_arr[i-1][0].date() < sig.start_date:
                    buy_arr[i] = x[1]
                if x[0].date() == sig.close_date or i == len(price_arr)-1 or price_arr[i+1][0].date() > sig.close_date:
                    sell_arr[i] = x[1]
            for start, close in other_signals:
                if start <= x[0].date() <= close:
                    other_signals_arr[i] = x[1]
                    if x[0].date() == start or i == 0 or price_arr[i-1][0].date() < start:
                        buy_arr[i] = x[1]
                    if x[0].date() == close or i == len(price_arr)-1 or price_arr[i+1][0].date() > close:
                        sell_arr[i] = x[1]
                    break
        return [buy_arr, sell_arr, signal_arr, other_signals_arr, [x[1] for x in price_arr]]


class SymbolChartJsonView(BaseLineChartView):
    def get_labels(self):
        arr = stock_data[symbols[self.kwargs['symbol']]]
        return [strftime(x[0], '%Y-%m') for x in arr]

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
        return render(request, '../templates/symbol_detail.html', {
            'symbol': symbol_obj
        })
    except Symbol.DoesNotExist:
        raise Http404("Question does not exist")


def expert_page(request, expert_id):
    expert = Expert.objects.get(id=expert_id)
    ads = Signal.objects.filter(expert=expert).select_related('symbol')

    securities = set(ads.values_list('symbol__id', 'symbol__name'))
    return render(request, '../templates/expert_page.html', {
        'expert': expert,
        'ads': ads,
        'securities': securities,
    })


def falo(request, expert_id):
    request.user.member.followings.add(expert_id)
    return HttpResponse("OK")


def onfalo(request, expert_id):
    request.user.member.followings.remove(expert_id)
    return HttpResponse("OK")