from django.contrib import admin

from .models import Case, CaseNote


class CaseNoteInline(admin.TabularInline):
    model = CaseNote
    extra = 0
    readonly_fields = ('author', 'created_at')


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'title', 'case_type', 'status', 'client', 'lawyer', 'opened_date')
    list_filter = ('status', 'case_type', 'lawyer')
    search_fields = ('case_number', 'title', 'description')
    date_hierarchy = 'opened_date'
    autocomplete_fields = ('client', 'lawyer')
    inlines = [CaseNoteInline]


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ('case', 'author', 'created_at')
    search_fields = ('text',)
