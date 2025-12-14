from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    UserAccount, AppGroup, GroupMembership, Decision, DecisionSharedGroup,
    CatalogItem, DecisionItem, DecisionVote, DecisionSelection,
    Taxonomy, Term, DecisionItemTerm, CatalogItemTerm,
    Question, AnswerOption, UserAnswer
)


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """Admin for custom user model"""
    list_display = ['username', 'email', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email']
    ordering = ['-created_at']


@admin.register(AppGroup)
class AppGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'role', 'is_confirmed', 'invited_at']
    list_filter = ['role', 'is_confirmed', 'invited_at']
    search_fields = ['user__username', 'group__name']
    raw_id_fields = ['user', 'group']


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'status', 'item_type', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description']
    raw_id_fields = ['group']


@admin.register(DecisionSharedGroup)
class DecisionSharedGroupAdmin(admin.ModelAdmin):
    list_display = ['decision', 'group', 'shared_at']
    list_filter = ['shared_at']
    raw_id_fields = ['decision', 'group']


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'created_at']
    search_fields = ['label']


@admin.register(DecisionItem)
class DecisionItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'decision', 'catalog_item', 'created_at']
    list_filter = ['created_at']
    search_fields = ['label', 'external_ref']
    raw_id_fields = ['decision', 'catalog_item']


@admin.register(DecisionVote)
class DecisionVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'is_like', 'rating', 'voted_at']
    list_filter = ['is_like', 'voted_at']
    raw_id_fields = ['user', 'item']


@admin.register(DecisionSelection)
class DecisionSelectionAdmin(admin.ModelAdmin):
    list_display = ['decision', 'item', 'selected_at']
    list_filter = ['selected_at']
    raw_id_fields = ['decision', 'item']


@admin.register(Taxonomy)
class TaxonomyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['value', 'taxonomy']
    list_filter = ['taxonomy']
    search_fields = ['value']
    raw_id_fields = ['taxonomy']


@admin.register(DecisionItemTerm)
class DecisionItemTermAdmin(admin.ModelAdmin):
    list_display = ['item', 'term']
    raw_id_fields = ['item', 'term']


@admin.register(CatalogItemTerm)
class CatalogItemTermAdmin(admin.ModelAdmin):
    list_display = ['catalog_item', 'term']
    raw_id_fields = ['catalog_item', 'term']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'scope', 'item_type', 'created_at']
    list_filter = ['scope', 'created_at']
    search_fields = ['text']


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'order_num']
    list_filter = ['question']
    raw_id_fields = ['question']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'decision', 'answered_at']
    list_filter = ['answered_at']
    raw_id_fields = ['user', 'question', 'decision', 'answer_option']
