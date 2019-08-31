from django.contrib import admin
from .models import PaymentHistory

# Register your models here.
register=admin.site.register

class PaymentHistoryFilter(admin.ModelAdmin):
	""" Filters for admin"""
	# form = AdminGiftStoreForm
	list_display = ['email', 'reference',]
	list_filter = ['email', 'reference',]
	search_fields = ['email', 'reference',]

register(PaymentHistory, PaymentHistoryFilter)
