import symbol

from django.core.mail import EmailMessage
from django.http import Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from chartjs.views.lines import BaseLineChartView
from django.utils.datetime_safe import strftime

from advertisement.models import Signal, Signaler, ResetPassword
from advertisement.utils import send_email_async
from database import symbols
from main import stock_data
from .forms import SearchForm, AddSignalForm, LoginForm, ResetPassForm, AddSignalerForm, SubmitPassword
from django.contrib.auth import authenticate, login, logout


def search(request):
    if request.method == 'GET':
        form = SearchForm()
        ads = Signal.objects.all()
        return render(request, '../templates/search.html', {
            'ads': ads,
            'form': form
        })
    else:
        form = SearchForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            ads = Signal.objects.filter(title__contains=title)
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
        form = AddSignalerForm()
        return render(request, '../templates/register.html', {'form': form})
    else:
        form = AddSignalerForm(request.POST)
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
            advertiser = Signaler.objects.filter(email=form.data['email'])[0]
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
        except Signaler.DoesNotExist:
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
        return [strftime(x[0], '%Y-%m') for x in arr]

    def get_providers(self):
        return ['Price', 'Signaler']

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
