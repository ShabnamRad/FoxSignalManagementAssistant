import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE

from advertisement.constant import SEX_CHOICES
from advertisement.utils import generate_random_token


def get_image_path(instance, filename):
    return os.path.join(str(Signal.objects.all().count()) + filename)


class Signal(models.Model):
    title = models.CharField(max_length=80)
    is_succeeded = models.BooleanField(default=None, blank=True, null=True)
    profit = models.FloatField(default=None, blank=True, null=True)
    start_date = models.DateField(default=None, blank=True, null=True)
    close_date = models.DateField(default=None, blank=True, null=True)
    expected_return = models.FloatField(default=None, blank=True, null=True)
    expected_risk = models.FloatField(default=None, blank=True, null=True)

    symbol = models.ForeignKey('Symbol', on_delete=models.CASCADE)
    expert = models.ForeignKey('Expert', on_delete=models.CASCADE, null=True, default="", blank=True)

    def __str__(self):
        return self.title + ' ' + self.symbol.name

    @property
    def user_id(self):
        return self.expert.display_name


class Member(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=12, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True)
    age = models.IntegerField(null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    followings = models.ManyToManyField(to='Expert', related_name='followers')
    # expert = models.ForeignKey(to='Expert', null=True, blank=True, on_delete=CASCADE)

    def __str__(self):
        return self.first_name  # + ' ' + self.last_name


class Expert(models.Model):
    display_name = models.CharField(max_length=30)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    website = models.URLField(max_length=200, null=True)

    def __str__(self):
        return self.display_name


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


