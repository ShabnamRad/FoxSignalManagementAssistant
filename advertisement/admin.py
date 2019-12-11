from django.contrib import admin

from .models import Member, Signal, Symbol, Expert

admin.site.register(Member)
admin.site.register(Signal)
admin.site.register(Symbol)
admin.site.register(Expert)

