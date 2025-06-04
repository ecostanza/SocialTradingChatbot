from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ExportActionModelAdmin

from .models import (
    StudySettings,
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
    FallbackCount,
    NewsfeedButtonClick,
    BotButtonClick,
    Question,
    Choice,
    ChoiceSelection
    )


class BalanceResource(resources.ModelResource):
    class Meta:
        model = Balance
        fields = ['user', 'available', 'invested',
                    'user__username', 'user__participant__condition__name']


class BalanceAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'available', 'invested']
    resource_class = BalanceResource


class MessageResource(resources.ModelResource):
    class Meta:
        model = Message
        fields = ['user', 'month', 'from_participant',
                    'from_button', 'created_at', 'text', 'user__username']

    def get_queryset(self):
        qs = self._meta.model.objects.all()
        qs = qs.select_related('user') #, 'user__participant', 'user__participant__condition')
        return qs


class MessageAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    #list_display = ['__str__', 'user__participant__condition__name']
    list_display = ['__str__', 'user']
    search_fields = ['user__username']

    resource_class = MessageResource


class ResultResource(resources.ModelResource):
    class Meta:
        model = Result
        fields = ['month', 'profit', 'images_tagged', 'total',
                    'user__username', 'user__participant__condition__name']


class ResultAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['month', 'profit', 'images_tagged', 'user', 'total']
    search_fields = ['user__username']
    resource_class = ResultResource


class QuestionnaireResponseResource(resources.ModelResource):
    class Meta:
        model = QuestionnaireResponse
        fields = ['user', 'answer', 'completion_time', 'subtask_time',
                    'created_at', 'updated_at',
                    'user__username', 'user__participant__condition__name']


class QuestionnaireResponseAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['__str__', 'user']
    resource_class = QuestionnaireResponseResource


class FallbackCountResource(resources.ModelResource):
    class Meta:
        model = FallbackCount
        fields = ['user__username', 'user__participant__condition__name', 'count']

class FallbackCountAdmin(ExportActionModelAdmin):
    list_display = ['__str__', 'condition', 'count']
    resource_class = FallbackCountResource


class UserActionResource(resources.ModelResource):
    class Meta:
        model = UserAction
        fields = ['id', 'user', 'month', 'available', 'invested',
                    'portfolio', 'chatbot_change', 'newspost_change',
                    'action', 'amount',
                    'user__username', 'user__participant__condition__name']


class UserActionAdmin(ExportActionModelAdmin):
    #list_display = ['participant', 'participant__user__username', 'task', 'task__task_list__name']
    list_display = ['__str__', 'user']
    resource_class = UserActionResource




# class DismissNotificationCountResource(resources.ModelResource):
#     class Meta:
#         model = DismissNotificationCount
#         fields = ['user', 'count',
#                     'user_username', 'user__participant__condition__name']

# class DismissNotificationCountAdmin(ExportActionModelAdmin):
#     list_display = ['__str__', 'count']
#     resource_class = DismissNotificationCountResource

class ParticipantResource(resources.ModelResource):
    reward = fields.Field(attribute='reward')
    total_score = fields.Field(attribute='total_score')
    n_messages_sent = fields.Field(attribute='n_messages_sent')
    fallback_count = fields.Field(attribute='fallback_count')
    fallback_rate = fields.Field(attribute='fallback_rate')
    class Meta:
        model = Participant
        fields = ['user__username', 'reward', 'condition__name', 'total_score', 'n_messages_sent', 'fallback_count', 'fallback_rate']
        export_order = ['user__username', 'reward', 'condition__name', 'total_score', 'n_messages_sent', 'fallback_count', 'fallback_rate']


class TestParticipantListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "is a test participant"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "test_participant"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "yes":
            return queryset.filter(
                user__username__startswith='TEST_USER__'
            )
        if self.value() == "90s":
            return queryset.exclude(
                user__username__startswith='TEST_USER__'
            )

class ParticipantAdmin(ExportActionModelAdmin):
    def rounded_fallback_rate(self, obj):
        return round(obj.fallback_rate, 2)
    def rounded_reward(self, obj):
        return round(obj.reward, 2)
    
    list_display = ['user', 'rounded_reward', 'total_score', 'condition', 'n_messages_sent', 'n_fallback', 'rounded_fallback_rate']
    resource_class = ParticipantResource

class ConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'active', 'n_participants', 'n_test_participants']
    list_editable = ['active']


class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'text']
    # list_editable = ['text']
    inlines = [ChoiceInline]
    
class ChoiceSelectionAdmin(admin.ModelAdmin):
    list_display = ['participant', 'choice','attempt','created_at']


admin.site.register(Balance, BalanceAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(UserAction, UserActionAdmin)
admin.site.register(QuestionnaireResponse, QuestionnaireResponseAdmin)
admin.site.register(FallbackCount, FallbackCountAdmin)
# admin.site.register(DismissNotificationCount, DismissNotificationCountAdmin)
admin.site.register(Profile)
admin.site.register(Portfolio)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(NewsfeedButtonClick)
admin.site.register(BotButtonClick)

admin.site.register(Question, QuestionAdmin)
admin.site.register(ChoiceSelection, ChoiceSelectionAdmin)

admin.site.register(StudySettings)
