#coding:utf-8
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal #, getcontext
# getcontext().prec = 3

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class StudySettings(SingletonModel):
    prolific_study_id = models.CharField(
        max_length=128,
        verbose_name="only the *last* part of the completion URL",
        default=''
    )
    # task_reward = models.DecimalField(decimal_places=2, max_digits=4)
    # task_penalty = models.DecimalField(decimal_places=2, max_digits=4)
    # gpt_call_interval = models.IntegerField(
    #     default=5, verbose_name="Time in seconds between GPT API calls")

    system_prompt = models.TextField(null=True, blank=True)
    user_prompt = models.TextField(null=True, blank=True)

    def __str__(self):
        return "Study Configuration"

    class Meta:
        verbose_name = "Study Configuration"
        verbose_name_plural = "Study Configuration"

class Condition(models.Model):
    active = models.BooleanField(default=True, null=False)
    name = models.CharField(max_length=128, null=False)

    def __str__(self):
        return self.name

    def n_participants(self):
        participants = Participant.objects.filter(
            condition=self
        ).exclude(
            user__username__startswith='TEST_USER__')
        # n_participants = participants.count()
        
        responses = QuestionnaireResponse.objects.filter(user__participant__condition=self)
        users = responses.values_list('user', flat=True)
        completed_participants = participants.filter(user__in=users)
        n_participants = completed_participants.count()
        return n_participants

    def n_test_participants(self):
        participants = Participant.objects.filter(
            condition=self
        ).filter(
            user__username__startswith='TEST_USER__')
        # n_participants = participants.count()

        responses = QuestionnaireResponse.objects.filter(user__participant__condition=self)
        users = responses.values_list('user', flat=True)
        completed_participants = participants.filter(user__in=users)
        n_participants = completed_participants.count()
        return n_participants


class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # condition_active = models.BooleanField(default=True, null=False)
    condition = models.ForeignKey(Condition, null=True, on_delete=models.CASCADE)

    @property
    def total_score(self):
        try:
            result5 = Result.objects.get(user=self.user, month=5)
            return result5.total - 1000
        except Result.DoesNotExist:
            return 0
    
    @property
    def reward(self):
        raw_reward = self.total_score / Decimal(200.0)
        if raw_reward < Decimal(0.00):
            return Decimal(0.00)
        elif raw_reward > Decimal(3.00):
            return Decimal(3.00)
        else:
            return raw_reward

    @property
    def n_messages_sent(self):
        return Message.objects.filter(user=self.user,from_participant=True).count()

    @property
    def n_fallback(self):
        return FallbackCount.objects.get(user=self.user).count

    @property
    def fallback_rate(self):
        try:
            return self.n_fallback / self.n_messages_sent
        except ZeroDivisionError:
            return 0

    class Meta:
        verbose_name = 'Participant'
        verbose_name_plural = 'Participants'

    def __str__(self):
        return self.user.username


class Profile(models.Model):
    name = models.CharField(max_length=128, null=False)
    gender = models.CharField(max_length=128, null=False)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.name


class Month(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.IntegerField(default=1, null=False)

    errors_experienced = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Month'
        verbose_name_plural = 'Months'

    def __str__(self):
        return self.user.username


class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey('Profile', null=True, on_delete=models.CASCADE)
    followed = models.BooleanField(default=False)
    risk = models.IntegerField(null=False)
    invested = models.DecimalField(max_digits=6, decimal_places=2)
    lastChange = models.DecimalField(max_digits=5, decimal_places=2)
    chatbotNextChange = models.DecimalField(max_digits=5, decimal_places=2)
    newspostNextChange = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'

    def __str__(self):
        return self.user.username + "-" + self.profile.name


class Balance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    available = models.DecimalField(max_digits=6, decimal_places=2, default=1000.00)

    @property
    def invested(self):
        if not Portfolio.objects.filter(user=self.user, followed=True):
            return 0.0
        else:
            return round(Portfolio.objects.filter(user=self.user, followed=True).aggregate(Sum('invested')).get('invested__sum'), 2)

    class Meta:
        verbose_name = 'Balance'
        verbose_name_plural = 'Balances'

    def __str__(self):
        return self.user.username


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField(null=False)
    from_participant = models.BooleanField(null=False)
    # from_notification = models.BooleanField(null=False, default=False)
    from_button = models.BooleanField(null=False, default=False)
    text = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    portfolio_name = models.CharField(max_length=128, null=True, blank=True)
    portfolio_amount = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        if self.from_participant:
            return self.user.username + ': ' + self.text
        else:
            return self.user.username + ', Bot: ' + self.text


class UserAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField(default=1, null=False)
    available = models.DecimalField(max_digits=6, decimal_places=2, null=False)
    invested = models.DecimalField(max_digits=6, decimal_places=2, null=False)
    portfolio = models.CharField(max_length=128, null=False)
    chatbot_change = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    newspost_change = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    action = models.CharField(max_length=128, null=False)
    amount = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    class Meta:
        verbose_name = 'User Action'
        verbose_name_plural = 'User Actions'

    def __str__(self):
        return self.user.username + ': ' + self.action + " (" + str(self.amount) + ") " + self.portfolio


# class DismissNotificationCount(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     count = models.IntegerField(default=0, null=False)
#
#     class Meta:
#         verbose_name = 'Dismiss Notification Count'
#         verbose_name_plural = 'Dismiss Notification Counts'
#
#     def __str__(self):
#         return self.user.username


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField(default=1, null=False)
    profit = models.DecimalField(max_digits=6, decimal_places=2, null=False)
    images_tagged = models.IntegerField(default=0, null=False)
    total = models.DecimalField(max_digits=6, decimal_places=2, null=False)

    class Meta:
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    def __str__(self):
        return self.user.username + ", Month: " + str(self.month)


class QuestionnaireResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.TextField()
    completion_time = models.FloatField()
    subtask_time = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FallbackCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.IntegerField(default=0, null=False)

    class Meta:
        verbose_name = 'Fallback Count'
        verbose_name_plural = 'Fallback Counts'

    def condition(self):
        return self.user.participant.condition.name

    def __str__(self):
        return self.user.username
    
class NewsfeedButtonClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    click_count = models.IntegerField(default=0, null=False)

class BotButtonClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    click_count = models.IntegerField(default=0, null=False)
    
#clicktype = models.CharField(max_length=128, null=False)

# ---
    
class Question(models.Model): 
    text = models.TextField()

class Choice(models.Model):
    text = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.text} ({self.question.text} | {self.correct})'

class ChoiceSelection(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, null=True)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True)
    attempt = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['participant', 'choice', 'attempt'],
                name='unique_choice_attempt'
                )
        ]



