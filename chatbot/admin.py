from django.contrib import admin
from import_export import resources
from import_export.admin import ExportActionModelAdmin

from .models import (
    Profile,
    Portfolio,
    Balance,
    Message,
    UserAction,
    Participant,
    Condition,
    # DismissNotificationCount,
    Result,
    QuestionnaireResponse,
    CredibilityCounter,
    FallbackCount,
    NewsfeedButtonClick,
    BotButtonClick,
    )


class BalanceResource(resources.ModelResource):
    class Meta:
        model = Balance
        fields = ['user', 'available', 'invested',
                    'user_username', 'user__participant__condition_active']


class BalanceAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'available', 'invested']
    resource_class = BalanceResource


class MessageResource(resources.ModelResource):
    class Meta:
        model = Message
        fields = ['user', 'month', 'from_participant',
                    'from_button', 'created_at', 'text', 'user_username', 'user__participant__condition_active']


class MessageAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    #list_display = ['__str__', 'user__participant__condition_active']
    list_display = ['__str__', 'user']
    resource_class = MessageResource


class ResultResource(resources.ModelResource):
    class Meta:
        model = Result
        fields = ['month', 'profit', 'images_tagged', 'total',
                    'user_username', 'user__participant__condition_active']


class ResultAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['__str__', 'user']
    resource_class = ResultResource


class QuestionnaireResponseResource(resources.ModelResource):
    class Meta:
        model = QuestionnaireResponse
        fields = ['user', 'answer', 'completion_time', 'subtask_time',
                    'created_at', 'updated_at',
                    'user_username', 'user__participant__condition_active']


class QuestionnaireResponseAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['__str__', 'user']
    resource_class = QuestionnaireResponseResource


class FallbackCountResource(resources.ModelResource):
    class Meta:
        model = FallbackCount
        fields = ['user', 'count']


class FallbackCountAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'user']
    resource_class = FallbackCountResource


class UserActionResource(resources.ModelResource):
    class Meta:
        model = UserAction
        fields = ['user', 'month', 'available', 'invested',
                    'portfolio', 'chatbot_change', 'newspost_change',
                    'action', 'amount',
                    'user_username', 'user__participant__condition_active']


class UserActionAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['__str__', 'user']
    resource_class = UserActionResource


class BotButtonClickResource(resources.ModelResource):
     class Meta:
         model = BotButtonClick
         fields = ['user', 'click_count']

class BotButtonClickAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'user']
    resource_class = BotButtonClickResource

class NewsfeedButtonClickResource(resources.ModelResource):
     class Meta:
         model = NewsfeedButtonClick
         fields = ['user', 'click_count']

class NewsfeedButtonClickAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'user']
    resource_class = NewsfeedButtonClickResource

class CredibilityCounterResource(resources.ModelResource):
     class Meta:
         model = CredibilityCounter
         fields = ['user', 'portfolio_cred']

class CredibilityCounterAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'user']
    resource_class = CredibilityCounterResource





# class DismissNotificationCountResource(resources.ModelResource):
#     class Meta:
#         model = DismissNotificationCount
#         fields = ['user', 'count',
#                     'user_username', 'user__participant__condition_active']

# class DismissNotificationCountAdmin(ExportActionModelAdmin):
#     list_display = ['__str__', 'count']
#     resource_class = DismissNotificationCountResource

admin.site.register(Balance, BalanceAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(UserAction, UserActionAdmin)
admin.site.register(QuestionnaireResponse, QuestionnaireResponseAdmin)
admin.site.register(FallbackCount, FallbackCountAdmin)
# admin.site.register(DismissNotificationCount, DismissNotificationCountAdmin)
admin.site.register(Profile)
admin.site.register(Portfolio)
admin.site.register(Participant)
admin.site.register(Condition)
admin.site.register(NewsfeedButtonClick, NewsfeedButtonClickAdmin)
admin.site.register(BotButtonClick, BotButtonClickAdmin)
admin.site.register(CredibilityCounter, CredibilityCounterAdmin)
