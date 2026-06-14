from django.contrib import admin
from .models import Item, Category, Request, Transaction, Review, Profile, SearchQuery, Notification

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'item_type', 'status', 'created_at')
    list_filter = ('item_type', 'status', 'category', 'condition')
    search_fields = ('name', 'description', 'owner__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('item', 'requester', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'buyer_borrower', 'owner', 'transaction_type', 'is_completed', 'start_date')
    list_filter = ('transaction_type', 'is_completed')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'rating')
    search_fields = ('user__username', 'department')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'evaluator', 'rated_user', 'score')
    list_filter = ('score',)

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('term', 'user', 'category', 'timestamp')
    list_filter = ('category',)
    search_fields = ('term', 'user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'is_read', 'created_at')
    list_filter = ('is_read',)
