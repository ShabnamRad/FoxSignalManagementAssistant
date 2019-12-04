from django.contrib import admin

from .models import Signaler, Signal, Symbol, Expert

admin.site.register(Signaler)
admin.site.register(Signal)
admin.site.register(Symbol)
admin.site.register(Expert)

