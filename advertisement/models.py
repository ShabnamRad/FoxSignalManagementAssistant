import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from advertisement.constant import SEX_CHOICES
from advertisement.utils import generate_random_token


def get_image_path(instance, filename):
    return os.path.join(str(Signal.objects.all().count()) + filename)


class Signal(models.Model):
    title = models.CharField(max_length=80)
    is_succeeded = models.BooleanField(default=None, blank=True, null=True)
    profit = models.FloatField(default=None, blank=True, null=True)
    start_date = models.DateField()
    close_date = models.DateField()
    expected_return = models.FloatField()
    expected_risk = models.FloatField()

    symbol = models.ForeignKey('Symbol', on_delete=models.CASCADE)
    signaler = models.ForeignKey('Signaler', on_delete=models.CASCADE)

    def __str__(self):
        return self.title + ' ' + self.symbol.name

    @property
    def user_id(self):
        return self.signaler.first_name


class Signaler(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=12, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True)
    age = models.IntegerField(null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Symbol(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ResetPassword(models.Model):
    advertiser = models.ForeignKey(Signaler, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, default=generate_random_token)

    def get_reset_password_link(self):
        return "{}/change_password?token={}".format(settings.SITE_DOMAIN, self.token)


