# coding: utf-8
import json
from random import gauss, randrange, randint, choice as random_choice
import decimal
import os

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.timezone import datetime
from django.core import serializers
from django.db import IntegrityError
from django.db.models import Count, Q
from django.utils import timezone

#from rest_framework.response import Response
#from rest_framework.decorators import api_view

#from .serializer import ButtonSerializer

from .djutils import to_dict

from .models import Profile, Portfolio, Balance, Month, Message, Participant, \
    Condition, Result, QuestionnaireResponse, FallbackCount, NewsfeedButtonClick, BotButtonClick

    

#@api_view (['GET'])
#def getButtonClick(request):
#    buttonclick = ButtonClick.objects.all()
#    serializer = ButtonSerializer(buttonclick, many=True)
#    return Response(serializer.data)

#@api_view (['POST'])
#def postButtonClick(request):
#    serializer = ButtonSerializer(data=request.data)
#    if serializer.is_valid():
#        serializer.save()
#    return Response(serializer.data)


def welcome_page(request):
    return render(request, 'welcome.html')


def information_page(request):
    return render(request, 'information.html')


def consent_page(request):
    return render(request, 'consent.html')


def instructions_page(request):
    return render(request, 'instructions.html')


@login_required
def results_page(request):
    user = request.user
    result1 = Result.objects.get(user=user, month=1)
    result2 = Result.objects.get(user=user, month=2)
    result3 = Result.objects.get(user=user, month=3)
    result4 = Result.objects.get(user=user, month=4)
    result5 = Result.objects.get(user=user, month=5)

    context = {
        'month_1_total': result1.total,
        'month_1_profit': result1.profit,
        'month_1_images_tagged': float(result1.images_tagged*20),
        'month_2_total': result2.total,
        'month_2_profit': result2.profit,
        'month_2_images_tagged': float(result2.images_tagged*20),
        'month_3_total': result3.total,
        'month_3_profit': result3.profit,
        'month_3_images_tagged': float(result3.images_tagged*20),
        'month_4_total': result4.total,
        'month_4_profit': result4.profit,
        'month_4_images_tagged': float(result4.images_tagged*20),
        'month_5_total': result5.total,
        'month_5_profit': result5.profit,
        'month_5_images_tagged': float(result5.images_tagged*20),
        'final_score': result5.total - 1000
        }

    return render(request, 'results.html', context)


@csrf_exempt
@require_POST
def participants_view(request):
    username = request.POST['username']
    is_test_user = False
    if username == "TEST":
        username = "TEST_USER__{}".format(datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S'))
        is_test_user = True
    try:
        user = User.objects.create_user(username=username)
        month = Month(user=user, number=1)
        month.save()

        for profile in Profile.objects.all():
            risk = randrange(9)+1

            chatbot_change = gauss(0.0, risk*5)

            if chatbot_change >= 100:
                chatbot_change = 99
            elif chatbot_change <= -100:
                chatbot_change = -99

            newspost_change = gauss(0.0, risk*5)

            if newspost_change >= 100:
                newspost_change = 99
            elif newspost_change <= -100:
                newspost_change = -99

            portfolio = Portfolio(user=user, profile=profile, followed=False, risk=risk, invested=0.00, lastChange=0.00, chatbotNextChange=chatbot_change, newspostNextChange=newspost_change)

            portfolio.save()

        balance = Balance(user=user, available=1000.00)
        balance.save()

        result = Result(user=user, month=1, profit=0.00, images_tagged=0, total=1000.00)
        result.save()

        # dismiss_notification_count = DismissNotificationCount(user=user, count=0)
        # dismiss_notification_count.save()

        fallback_count = FallbackCount(user=user, count=0)
        fallback_count.save()

    except IntegrityError:
        error = {
            "username": [{"message": "This field is duplicate.", "code": "duplicate"}]
            }
        data = json.dumps(error)
        return HttpResponseBadRequest(data, content_type='application/json')

    participant = Participant()
    participant.user = user
    # participant.created_for_testing = is_test_user

    # assign condition
    # sort by number of runs/participants
    # filter out TEST participants from this count
    all_conditions = Condition.objects.filter(active=True
        ).annotate(n_participants=Count('participant',
            exclude=Q(participant__user__username__startswith='TEST_USER__'))
        ).order_by('n_participants')
    
    # take the min value
    min_participants = all_conditions[0].n_participants
    # get all TaskList objects which have the min value of completed tasks..
    min_conditions = all_conditions.filter(n_participants=min_participants)
    no_conditions = min_conditions.count()
    # ..and randomly pick one of them
    index = randint(0, no_conditions-1)
    participant.condition = min_conditions[index]
    # all_conditions = Condition.objects.filter(active=True
    #     ).annotate(n_participants=Count('participant')
    #     ).order_by('n_participants')
    # participant.condition = all_conditions[0]

    participant.save()

    login(request, user)

    #data = json.dumps(to_dict(participant, transverse=True))
    data = json.dumps(to_dict(user, transverse=False))
    return HttpResponse(data, content_type='application/json')


# @login_required
# def get_condition_active(request):
#     user = request.user

#     condition_active = Participant.objects.get(user=user).condition_active

#     response = {'condition_active': condition_active}

#     return HttpResponse(json.dumps(response), content_type="application/json")


# @csrf_exempt
# @login_required
# def update_dismiss_notification_count(request):
#     user = request.user
#
#     dismiss_notification_count = DismissNotificationCount.objects.get(user=user)
#     dismiss_notification_count.count += 1
#     dismiss_notification_count.save()
#
#     return HttpResponse("")

#SomeModel.objects.filter(foo='bar').first()
# In this case, if the Person already exists, its name is updated
#person, created = Person.objects.update_or_create(
#        identifier=identifier, defaults={"name": name}
#)

@csrf_exempt
@login_required
def getNewsfeedButtonClick(request):
    user = request.user
    newsfeedbuttonclick, _ = NewsfeedButtonClick.objects.get_or_create(user=user)
    newsfeedbuttonclick.click_count += 1
    newsfeedbuttonclick.save()

    return JsonResponse({"msg": "click count +1"})


@csrf_exempt
@login_required
def getBotButtonClick(request):
    user = request.user
    botbuttonclick, _ = BotButtonClick.objects.get_or_create(user=user)
    botbuttonclick.click_count += 1
    botbuttonclick.save()

    return JsonResponse({"msg": "click count +1"})


@login_required
def chatbot_page(request):
    user = request.user
    print(user)
    profiles = Profile.objects.all()
    image_names = []

    for profile in profiles:
        image_names.append(profile.name.replace(' ', '-') + ".jpg")

    month_total_seconds = int(4 * 60)
    total_months = 5

    # get the last month of current user
    month = Month.objects.filter(user=user).order_by('number').last()
    now = timezone.now()
    elapsed_seconds = int((now - month.created_at).total_seconds())
    seconds_left = month_total_seconds - elapsed_seconds
    if month.number >= total_months and seconds_left < 1:
        return redirect('resultspage')
 
    context = {
        'available_balance_amount': format(Balance.objects.get(user=user).available, '.2f'),
        'invested_balance_amount': format(Balance.objects.get(user=user).invested, '.2f'),
        'image_names': image_names,
        'profiles': serializers.serialize('json', Profile.objects.all()),
        'followed_portfolios': Portfolio.objects.filter(user=user, followed=True),
        'not_followed_portfolios': Portfolio.objects.filter(user=user, followed=False),
        'seconds_left': seconds_left,
        'month_total_seconds': month_total_seconds,
        'month_number': month.number
        }

    return render(request, 'chatbot.html', context)


@login_required
def imagetagging_page(request):
    user = request.user
    balance = Balance.objects.get(user=user)
    context = {
        'available_balance_amount': balance.available,
        'invested_balance_amount': balance.invested,
        }

    return render(request, 'imagetagging.html', context)


@login_required
def update_portfolios(request):
    user = request.user
    response = {}

    for portfolio in Portfolio.objects.filter(user=user):
        next_change = random_choice([portfolio.chatbotNextChange, portfolio.newspostNextChange])

        portfolio.lastChange = round(next_change, 2)

        next_change /= 100
        next_change += 1

        if portfolio.followed:
            new_invested_amount = round(portfolio.invested * decimal.Decimal(next_change), 2)
            portfolio.invested = new_invested_amount

        portfolio.save()

    balance = Balance.objects.get(user=user)

    response['available_balance_amount'] = str(balance.available)
    response['invested_balance_amount'] = str(balance.invested)

    generate_next_portfolio_changes(request)

    return HttpResponse(json.dumps(response), content_type="application/json")


@csrf_exempt
@login_required
def update_results(request):
    user = request.user
    month = int(request.POST['month'])
    profit = float(request.POST['profit'])
    total = float(request.POST['total'])

    print('GETTING RESULT OBJECT WITH MONTH = ' + str(month))
    print('profit = ' + str(profit))
    print('total = ' + str(total))

    result = Result.objects.get(user=user, month=month)
    result.profit = profit
    result.total = total
    result.save()

    return HttpResponse("")


@login_required
def update_balances(request):
    user = request.user
    response = {}

    balance = Balance.objects.get(user=user)

    response['available_balance_amount'] = str(balance.available)
    response['invested_balance_amount'] = str(balance.invested)

    if response['available_balance_amount'] == '0.0':
        response['available_balance_amount'] = '0.00'

    if response['invested_balance_amount'] == '0.0':
        response['invested_balance_amount'] = '0.00'

    print(response)

    return HttpResponse(json.dumps(response), content_type="application/json")


@csrf_exempt
@login_required
def update_month(request):
    user = request.user
    old_month = Month.objects.filter(user=user).order_by('number').last()

    response = {}

    if old_month.number < 5:
        new_month = Month(
            user=user, 
            errors_experienced=0,
            number=old_month.number+1
            )
        new_month.save()

        result = Result(user=user, month=new_month.number, profit=0.00, images_tagged=0, total=0.00)
        result.save()

        response['has_increased'] = True
    else:
        response['has_increased'] = False

    return HttpResponse(json.dumps(response), content_type="application/json")


@login_required
def get_next_changes(request):
    user = request.user
    response = {}

    for portfolio in Portfolio.objects.filter(user=user):
        response[portfolio.profile.name + '-chatbot-change'] = float(portfolio.chatbotNextChange)
        response[portfolio.profile.name + '-newspost-change'] = float(portfolio.newspostNextChange)

    return HttpResponse(json.dumps(response), content_type="application/json")


@csrf_exempt
@login_required
def store_bot_message(request):
    user = request.user
    month = request.POST['month']
    text = request.POST['text']

    message = Message(user=user, month=month, from_participant=False, from_button=False, text=text)
    message.save()

    return HttpResponse("")


@login_required
def generate_next_portfolio_changes(request):

    user = request.user
    for portfolio in Portfolio.objects.filter(user=user):

        chatbot_change = gauss(0.0, portfolio.risk*5)

        if chatbot_change >= 100:
            chatbot_change = 99
        elif chatbot_change <= -100:
            chatbot_change = -99

        newspost_change = gauss(0.0, portfolio.risk*5)

        if newspost_change >= 100:
            newspost_change = 99
        elif newspost_change <= -100:
            newspost_change = -99

        portfolio.chatbotNextChange = chatbot_change
        portfolio.newspostNextChange = newspost_change

        portfolio.save()


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@login_required
def questionnaire_view(request):
    if request.method == 'GET':
        questionnaire = '''[
    {'label': '<hr><h5>Please answer the following questions <u>based on your overall experience</u> completing the study</h5><hr>'},
    {'question': '1. From 1 to 5 (where 1 is the least and 5 is the most), I am in full control of what I do', choices: ['1', '2', '3', '4', '5']},
    {'question': '2. From 1 to 5 (where 1 is the least and 5 is the most), I am just an instrument in the hands of somebody or something else', choices: ['1', '2', '3', '4', '5']},
    {'question': '3. From 1 to 5 (where 1 is the least and 5 is the most), my actions just happen without my intention', choices: ['1', '2', '3', '4', '5']},
    {'question': '4. From 1 to 5 (where 1 is the least and 5 is the most), I am the author of my actions.', choices: ['1', '2', '3', '4', '5']},
    {"question": "5. From 1 to 5 (where 1 is the least and 5 is the most), the consequences of my actions feel like they don't logically follow my actions.", "choices": ["1", "2", "3", "4", "5"]},
    {'question': '6. From 1 to 5 (where 1 is the least and 5 is the most), my movements are automatic - my body simply makes them.', choices: ['1', '2', '3', '4', '5']},
    {'question': '7. From 1 to 5 (where 1 is the least and 5 is the most), the outcomes of my actions generally surprise me.', choices: ['1', '2', '3', '4', '5']},
    {'question': '8. From 1 to 5 (where 1 is the least and 5 is the most), things I do are subject only to my free will.', choices: ['1', '2', '3', '4', '5']},
    {'question': '9. From 1 to 5 (where 1 is the least and 5 is the most), the decision whether and when to act is within my hands.', choices: ['1', '2', '3', '4', '5']},
    {'question': '10. From 1 to 5 (where 1 is the least and 5 is the most), nothing I do is actually voluntary.', choices: ['1', '2', '3', '4', '5']},
    {'question': '11. From 1 to 5 (where 1 is the least and 5 is the most), while I am in action, I feel like I am a remote controlled robot.', choices: ['1', '2', '3', '4', '5']},
    {'question': '12. From 1 to 5 (where 1 is the least and 5 is the most), my behaviour is planned by me from the very beginning to the very end.', choices: ['1', '2', '3', '4', '5']},
    {'question': '13. From 1 to 5 (where 1 is the least and 5 is the most), I am completely responsible for everything that results from my actions.', choices: ['1', '2', '3', '4', '5']},
    {'question': '14. From 1 to 7 (where 1 is the least and 7 is the most), the chatbot is natural.', choices: ['1', '2', '3', '4', '5', '6', '7']},
    {'question': '15. From 1 to 7 (where 1 is the least and 7 is the most), the chatbot is humanlike.', choices: ['1', '2', '3', '4', '5', '6', '7']},
    {'question': '16. From 1 to 7 (where 1 is the least and 7 is the most), the chatbot is realistic.', choices: ['1', '2', '3', '4', '5', '6', '7']},
    {'question': '17. From 1 to 7 (where 1 is the least and 7 is the most), the chatbot is present.', choices: ['1', '2', '3', '4', '5', '6', '7']},
    {'question': '18. From 1 to 7 (where 1 is the least and 7 is the most), the chatbot is authentic.', choices: ['1', '2', '3', '4', '5', '6', '7']},
    {'question': '19. From 1 to 5 (where 1 is the least and 5 is the most), my friends would say I\\’m a very patient friend.', choices: ['1', '2', '3', '4', '5']},
    {'question': '20. From 1 to 5 (where 1 is the least and 5 is the most), I am able to wait-out tough times.', choices: ['1', '2', '3', '4', '5']},
    {'question': '21. From 1 to 5 (where 1 is the least and 5 is the most), although they\\’re annoying, I don\\’t get too upset when stuck in traffic jams.', choices: ['1', '2', '3', '4', '5']},
    {'question': '22. From 1 to 5 (where 1 is the least and 5 is the most), I am patient with other people.', choices: ['1', '2', '3', '4', '5']},
    {'question': '23. From 1 to 5 (where 1 is the least and 5 is the most), I find it pretty easy to be patient with a difficult life problem or illness.', choices: ['1', '2', '3', '4', '5']},
    {'question': '24. From 1 to 5 (where 1 is the least and 5 is the most), in general waiting in lines does not bother me.', choices: ['1', '2', '3', '4', '5']},
    {'question': '25. From 1 to 5 (where 1 is the least and 5 is the most), I have trouble being patient with my close friends and family.', choices: ['1', '2', '3', '4', '5']},
    {'question': '26. From 1 to 5 (where 1 is the least and 5 is the most), I am patient during life hardships.', choices: ['1', '2', '3', '4', '5']},
    {'question': '27. From 1 to 5 (where 1 is the least and 5 is the most), when someone is having difficulty learning something new, I will be able to help them without getting frustrated or annoyed.', choices: ['1', '2', '3', '4', '5']},
    {'question': '28. From 1 to 5 (where 1 is the least and 5 is the most), I get very annoyed at red lights.', choices: ['1', '2', '3', '4', '5']},
    {'question': '29. From 1 to 5 (where 1 is the least and 5 is the most), I find it easy to be patient with people.', choices: ['1', '2', '3', '4', '5']},
    {'question': '<hr>Please leave your comments about the overall experience about this study, or your suggestions for improvement.'}
        ]
        '''
        context = {
            'questionnaire': questionnaire,
        }
        template_path = 'questionnaire.html'
        return render(request, template_path, context=context)
    elif request.method == 'POST':
        # TODO: store the result(s) and render/redirect to the next page
        post_data = json.loads(request.body.decode('utf-8'))
        questionnaire_response = QuestionnaireResponse(
            user = request.user,
            answer = post_data['groups'],
            completion_time = post_data['task_completion_time'],
            subtask_time = post_data['log']
        )
        questionnaire_response.save()

        # TODO: redirect to some end page
        # https://app.prolific.ac/submissions/complete?cc=J8OWBL27
        #study_settings = StudySettings.load()
        #study_id = study_settings.prolific_study_id
        # TODO: Fix this url
        result = {
            'completion_url': 'https://app.prolific.co/submissions/complete?cc=5E140EBC'
        }# https://app.prolific.ac/submissions/complete?cc=' + study_id
        result_data = json.dumps(result)
        return HttpResponse(result_data, content_type='application/json')

        #return redirect(completion_url)
        # return HttpResponse('the end')
