from django.contrib import admin
from .models import Tag

from import_export import resources
from import_export.admin import ExportActionModelAdmin

class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        fields = ['id', 'label', 'correct', 'user__id',
                    'user__username', 'user__participant__condition__name']

# class TagAdmin(admin.ModelAdmin):
#     list_display = ['id', 'label', 'user', 'correct']
class TagAdmin(ExportActionModelAdmin):
    list_display = ['id', 'label', 'user', 'correct']
    resource_class = TagResource

admin.site.register(Tag, TagAdmin)
