#coding:utf-8
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted

import sys, os
here = os.path.dirname(__file__)
project_dir, _ = os.path.split(here)
sys.path.insert(0, project_dir)

import os, django
# os.environ["DJANGO_SETTINGS_MODULE"] = 'investment_bot.settings'
django.setup()
from chatbot.models import Portfolio, Profile, Balance, Month, UserAction, FallbackCount, Participant
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Count
from django.core.exceptions import MultipleObjectsReturned
from random import randint
from django.db import connection
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
import random
from django.utils import timezone

# def try_except(f):
#     def applicator(dispatcher, tracker, domain, *args, **kwargs):
#       try:
#          return f(dispatcher, tracker, domain, *args,**kwargs)
#       except Exception as e:
#          print(f'Error from {f.__class__.__name__}: {e}')
#          return []

#     return applicator

import functools

def try_except(f):
    @functools.wraps(f)
    def applicator(*args, **kwargs):
      try:
         return f(*args,**kwargs)
      except Exception as e:
        #  print(f'Error from {f.__class__.__name__}: {e}')
         print(f'{e.__class__.__name__} from {args[0].__class__.__name__}: {e}')
         
         return []

    return applicator

from csv import reader
r = reader(open('./responses.csv', 'r'))
# skip header line
next(r)
second_lut = {}
passive_lut = {}
for line in r:
    first, second, passive = line
    second_lut[first] = second
    passive_lut[first] = passive
    # print(f'{first}\n{second}\n{passive}\n')

def custom_utter_message(message, tracker, dispatcher, buttons=None, message_params=None):
    user = get_user(tracker)
    condition = get_condition(user)

    # print("condition: ", condition)
    # print("'2nd' in condition: ", '2nd' in condition)
    try:
        if '1st' in condition:
            new_message = message 
                
        elif '2nd' in condition:
            new_message = second_lut[message] 

        elif 'passive' in condition:
            new_message = passive_lut[message] 
                
        else:
            raise ValueError('Invalid condition')    
        
        if message_params:
            new_message = new_message % message_params

        print(new_message)
        
        dispatcher.utter_message(new_message, buttons=buttons)
    except KeyError:
        dispatcher.utter_message('LUT error for: ' + message, buttons=buttons)
        print(f'LUT error for: {repr(message)}')
    except Exception as e:
        print(f'new_message: {new_message}')
        print(f'message_params: {message_params}')
        dispatcher.utter_message('Error: ' + str(e), buttons=buttons)
        print(e)

def get_user(tracker):
    username = tracker.current_state()["sender_id"]

    connection.close()
    user = User.objects.get(username=username)
    return user

def get_condition(user):
    participant = Participant.objects.get(user=user)
    condition = participant.condition.name
    return condition

def is_time_for_error(user):
    # get the last month of current user
    month = Month.objects.filter(user=user).order_by('number').last()
    now = timezone.now()
    elapsed_time = (now - month.created_at).total_seconds()
    print('elapsed_time:', elapsed_time)
    print('month.number:', month.number)
    print('month.errors_experienced:', month.errors_experienced)
    print('total months:', Month.objects.filter(user=user).count()) 
    
    # # no errors for odd numbered months
    # if month.number % 2 == 1:
    #     return False

    # no errors for the first month
    if month.number <= 1:
        return False
    
    # TODO: tweak this and possibly make it parametric
    ERRORS_PER_MONTH = 3
    time_threshold = 60 + month.errors_experienced * int(180.0 / (ERRORS_PER_MONTH + 1))
    if elapsed_time > time_threshold and month.errors_experienced < ERRORS_PER_MONTH:
        month.errors_experienced += 1
        month.save()
        print("--- time for error ----")
        return True
    
    return False

"""
Short responses
"""

class Okay(Action):
    def name(self) -> Text:
        return "action_okay"

    @try_except
    def run(self, dispatcher, tracker, domain):

        messages = []

        messages.append("Ok")
        messages.append("Okay")
        messages.append("Yep")
        messages.append("Sure")
        messages.append("Alright")
        messages.append("Got it")
        messages.append("Definitely")
        messages.append("Absolutely")
        messages.append("Of course")
        messages.append("Yes")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []

class NoProblem(Action):
    def name(self) -> Text:
        return "action_no_problem"

    @try_except
    def run(self, dispatcher, tracker, domain):

        custom_utter_message(
            "No problem!",
            tracker,
            dispatcher)

        return []

class Cool(Action):
    def name(self) -> Text:
        return "action_cool"

    @try_except
    def run(self, dispatcher, tracker, domain):

        custom_utter_message(
            "Cool",
            tracker,
            dispatcher)

        return []


"""
Long responses
"""

class WhatICanDo(Action):
    def name(self) -> Text:
        return "action_what_I_can_do"

    @try_except
    def run(self, dispatcher, tracker, domain):

        custom_utter_message(
            "I can follow or unfollow portfolios, add or withdraw amounts and provide advice like: \"Who should I follow?\", \"Who should I unfollow?\", \"Invest 100 on Aricka\" or \"withdraw from alois\"",
            tracker,
            dispatcher)

        return []

class RemindImageTagging(Action):
    def name(self) -> Text:
        return "action_remind_image_tagging"

    @try_except
    def run(self, dispatcher, tracker, domain):

        # action_remind_image_tagging
        custom_utter_message(
            "I want to remind you that you can switch to Image Tagging by clicking the \"Task\" button in the top right corner",
            tracker,
            dispatcher)

        return []

class Newsfeed(Action):
    def name(self) -> Text:
        return "action_newsfeed"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("I don't know much about the newsfeed")
        messages.append("I'm not familiar with the newsfeed")
        messages.append("I'm not well-versed in the newsfeed")
        messages.append("I know very little about the newsfeed")
        messages.append("I would say I don't know much about the newsfeed")
        messages.append("I need to say I don't know much about the newsfeed")
        messages.append("I would say I'm not well-versed about the newsfeed")
        messages.append("I actually know very little about the newsfeed")
        messages.append("I actually don't know much about the newsfeed")
        messages.append("I have a limited understanding of the newsfeed")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []

class ImDoingMyBest(Action):
    def name(self) -> Text:
        return "action_im_doing_my_best"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("Sorry, my predictions are meant to be as accurate as possible, but my responses might contain errors")
        messages.append("Sorry, I try to make my predictions as accurate as possible, but sometimes my responses could be erroneous")
        messages.append("Apologies, my goal is to provide accurate predictions, however my responses could be inaccurate")
        messages.append("I'm sorry, my predictions are intended to be as correct as possible, but my response may contain errors")
        messages.append("I'm sorry; although I aim for high accuracy in my predictions, errors can still appear in my responses")
        messages.append("Apologies, although I aim for high accuracy in my predictions, errors can still appear in my responses")
        messages.append("Apologies, although I aim for high accuracy in my predictions, errors can still appear in my responses")
        messages.append("Sorry, I try to make my predictions as accurate as possible, but sometimes my responses could be inaccurate")
        messages.append("Sorry, my predictions are meant to be as accurate as possible, but might contain errors")
        messages.append("Apologies, my predictions are meant to be as accurate as possible, but my responses might contain errors")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []


class FollowOnePortfolioAtATime(Action):
    def name(self) -> Text:
        return "action_please_follow_one_portfolio_at_a_time"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("Sorry, I can only follow one portfolio at a time (one message for each portfolio)")
        messages.append("I'm sorry, I can manage following only one portfolio at a time (one message for each)")
        messages.append("Apologies, but I'm only able to follow one portfolio at a time (one message for each)")
        messages.append("Sorry, my capacity allows me to follow just one portfolio at a time (one message for each portfolio)")
        messages.append("I'm sorry, but I can handle only one portfolio at a time (one message for each portfolio)")
        messages.append("Apologies, but I can handle only one portfolio at a time (one message for each portfolio)")
        messages.append("Apologies, my capacity allows me to follow just one portfolio at a time (one message for each portfolio)")
        messages.append("Unfortunately, I can only follow one portfolio at a time (one message for each portfolio)")
        messages.append("Apologies, I can only follow one portfolio at a time (one message for each portfolio)")
        messages.append("Sorry, my capacity allows me to follow just one portfolio at a time (one message for each portfolio)")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []

class UnfollowEveryone(Action):
    def name(self) -> Text:
        return "action_are_you_sure_unfollow_everyone"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("I want to confirm: shall I unfollow everyone?")
        messages.append("I'd like to confirm: should I unfollow everyone?")
        messages.append("I need to check: shall I unfollow everyone?")
        messages.append("Just double-checking: should I unfollow everyone now?")
        messages.append("I would like to verify: shall I unfollow everyone?")
        messages.append("Just double-checking: shall I stop following everyone?")
        messages.append("Just double-checking: should I unfollow everyone?")
        messages.append("I'd like to confirm: should I unfollow everyone?")
        messages.append("I want to confirm: shall I stop following everyone?")
        messages.append("I want to check: shall I unfollow everyone?")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []

class InvalidAmount(Action):
    def name(self) -> Text:
        return "action_invalid_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("I think that's not a valid amount")
        messages.append("I'm afraid that's not a valid amount")
        messages.append("I don't think that's a valid amount")
        messages.append("I reckon that's not a valid amount")
        messages.append("I don't believe that's a valid amount")
        messages.append("I'm afraid that amount doesn't look right")
        messages.append("I need to say that amount isn't valid")
        messages.append("I believe that amount isn't valid")
        messages.append("I feel that amount might not be valid")
        messages.append("I don't think that's a right amount")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
        ]

class InvalidPortfolio(Action):
    def name(self) -> Text:
        return "action_invalid_portfolio"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
        messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
        messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
        messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
        messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
        messages.append("Sorry, I can't find that one. Have you spelt the name right?")
        messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
        messages.append("My bad. I can't find that portfolio, have you spelt it right?")
        messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
        messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            ]

class AlreadyNotFollowedPortfolio(Action):
    def name(self) -> Text:
        return "action_already_not_followed_portfolio"
    
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("Sorry, I'm not following that portfolio")
        messages.append("Sorry, I think I'm not following that portfolio now")
        messages.append("Apologies, I am not following that portfolio")
        messages.append("I'm sorry to say that I do not follow that portfolio at the moment")
        messages.append("Sorry, that portfolio isn't one I'm following")
        messages.append("Sorry, I don't have that portfolio on my follow list")
        messages.append("Apologies, I don't have that portfolio on my follow list")
        messages.append("Apologies, I believe I don't have that portfolio on my follow list")
        messages.append("Sorry, I do not follow that portfolio")
        messages.append("Apologies, I don't have that portfolio on my follow list")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            ]

class AlreadyFollowedPortfolio(Action):
    def name(self) -> Text:
        return "action_already_followed_portfolio"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        messages = []

        messages.append("I'm already following that portfolio")
        messages.append("I think I'm already following that portfolio")
        messages.append("I already follow that portfolio")
        messages.append("I think that portfolio is already on my follow list")
        messages.append("I believe that portfolio is already among those I follow")
        messages.append("That portfolio is already on my follow list")
        messages.append("I believe I'm already tracking that portfolio")
        messages.append("It seems I'm already following that portfolio")
        messages.append("It seems that portfolio is already on my follow list")
        messages.append("I believe I'm already following that portfolio")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return []

class GiveGeneralAdvice(Action):
    def name(self) -> Text:
        return "action_give_general_advice"

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)

        highest_change = 1
        highest_pronoun = ''
        highest_him_her = ''
        lowest_change = -1
        lowest_pronoun = ''
        lowest_him_her = ''

        highest_changing_portfolio_name = None
        lowest_changing_portfolio_name = None

        for portfolio in Portfolio.objects.filter(user=user):

            chatbot_change = portfolio.chatbotNextChange

            if portfolio.followed and chatbot_change < lowest_change:
                lowest_change = chatbot_change
                lowest_changing_portfolio_name = portfolio.profile.name

                if portfolio.profile.gender == 'Male':
                    lowest_pronoun = 'his'
                    lowest_him_her = 'him'
                else:
                    lowest_pronoun = 'her'
                    lowest_him_her = 'her'

            elif not portfolio.followed and chatbot_change > highest_change:
                highest_change = chatbot_change
                highest_changing_portfolio_name = portfolio.profile.name

                if portfolio.profile.gender == 'Male':
                    highest_pronoun = 'his'
                    highest_him_her = 'him'
                else:
                    highest_pronoun = 'her'
                    highest_him_her = 'her'

        messages = []
        profile_name = None

        portfolio_query = None

        higher_is_greater = highest_change >= abs(lowest_change)

        buttons = []
        message_params = {}

        if highest_changing_portfolio_name is None and lowest_changing_portfolio_name is None:
            messages.append("I don't recommend following or unfollowing anyone at this moment")
            messages.append("I wouldn't advise to follow or unfollow anyone just now")
            messages.append("I don't think there is anyone else worth following or unfollowing at the moment")
            messages.append("I would not follow or unfollow anyone else at the moment")
            messages.append("I don't think there is any other portfolio that is worth following or unfollowing this month")
            messages.append("At the moment, I would not make any alterations to your follow list")
            messages.append("I can't think of anyone else I should follow or unfollow at the moment")
            messages.append("I don't think there is anyone else I should start or stop following at the moment")
            messages.append("I can't think of anyone else to follow or unfollow")
            messages.append("At this point, I don't see any pressing need to follow or unfollow anyone")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
   
            custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)

        elif lowest_changing_portfolio_name is None or higher_is_greater:
            # messages.append("I think you should start following " + highest_changing_portfolio_name + ". I believe " + highest_pronoun + " portfolio will increase by " + str(round(highest_change)) + "% next month")
            messages.append("I would follow %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")
            messages.append("I would consider to follow %(portfolio_name)s. I think %(pronoun)s portfolio will increase by %(value)s%% next month")
            messages.append("I think %(portfolio_name)s's portfolio will increase by %(value)s%% next month, so I would follow %(him_her)s")
            messages.append("I believe %(portfolio_name)s's portfolio will see an increase of %(value)s%% next month. I would start to follow %(him_her)s")
            messages.append("I predict a positive change of %(value)s%% in %(portfolio_name)s's portfolio next month. I think starting to follow %(him_her)s is a good choice")
            messages.append("I would following %(portfolio_name)s. I predict a growth of %(value)s%% in %(pronoun)s portfolio next month")
            messages.append("I'd start following %(portfolio_name)s. I think %(pronoun)s portfolio will go up by %(value)s%%")
            messages.append("I would start following %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")
            messages.append("I would consider starting to follow %(portfolio_name)s. I think it will increase by %(value)s%% next month")
            messages.append("I predict a positive change of %(value)s%% in %(portfolio_name)s's portfolio. I'd start following %(him_her)s")


            profile_name = highest_changing_portfolio_name
            portfolio_query = "not_followed"
            buttons.append({"title": "Do it", "payload": "Do it"})
            buttons.append({"title": "Never mind", "payload": "Never mind"})

            message_params = {
                'portfolio_name': highest_changing_portfolio_name, 
                'value': str(round(highest_change)),
                'pronoun': highest_pronoun,
                'him_her': highest_him_her
            }

        else:
            # messages.append("I think you should stop following " + lowest_changing_portfolio_name + ". I believe " + lowest_pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month")
            messages.append("I would stop follow %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%% next month")
            messages.append("I think %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I would stop following %(him_her)s")
            messages.append("I would unfollow %(portfolio_name)s. I predict %(pronoun)s portfolio will decrease by %(value)s%% next month")
            messages.append("I'd stop following %(portfolio_name)s. I predict a negative change of %(value)s%% in %(him_her)s portfolio next month")
            messages.append("I would stop following %(portfolio_name)s. I think %(pronoun)s portfolio will decrease by %(value)s%% next month")
            messages.append("I think it's time to stop following %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%%")
            messages.append("I predict %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I'd consider stopping following %(him_her)s")
            messages.append("My predictions indicate that %(portfolio_name)s's portfolio will decrease by %(value)s%%. I would end my following of %(him_her)s")
            messages.append("I predict the value of %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I would unfollow %(him_her)s")
            messages.append("I would unfollow %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%%")
            
            profile_name = lowest_changing_portfolio_name
            portfolio_query = "followed"
            buttons.append({"title": "Do it", "payload": "Do it"})
            buttons.append({"title": "Never mind", "payload": "Never mind"})

            message_params = {
                'portfolio_name': lowest_changing_portfolio_name, 
                'value': str(round(abs(lowest_change))),
                'pronoun': lowest_pronoun,
                'him_her': lowest_him_her
            }

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        return [SlotSet("name", profile_name), SlotSet("portfolio_query", portfolio_query)]


class GiveFollowingAdvice(Action):
    def name(self) -> Text:
        return "action_give_following_advice"

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)

        not_followed_portfolios = Portfolio.objects.filter(user=user, followed=False)

        highest_changing_portfolio_name = None

        messages = []

        buttons = []
        message_params = {}

        if not not_followed_portfolios:
            messages.append("I'm following everyone now!")
            messages.append("I'm currently following everyone!")
            messages.append("At the moment, I'm following all!")
            messages.append("I'm following everyone at the moment!")
            messages.append("As of now, I'm following everyone!")
            messages.append("I'm afraid there's no one left to follow!")
            messages.append("I believe there's no one left to follow!")
            messages.append("I'm sure there's no portfolio left to follow!")
            messages.append("I'm following everyone already!")
            messages.append("I'm already following everyone!")
        else:
            highest_change = 1
            pronoun = ''
            him_her = ''

            for portfolio in not_followed_portfolios:
                chatbot_change = portfolio.chatbotNextChange

                if chatbot_change > highest_change:
                    highest_change = chatbot_change
                    highest_changing_portfolio_name = portfolio.profile.name

                    if portfolio.profile.gender == 'Male':
                        pronoun = 'his'
                        him_her = 'him'
                    else:
                        pronoun = 'her'
                        him_her = 'her'
            
            message_params = {
                'portfolio_name': highest_changing_portfolio_name, 
                'value': str(round(highest_change)),
                'pronoun': pronoun,
                'him_her': him_her
            }

            if highest_changing_portfolio_name is not None:
                # messages.append("I think you should start following " + highest_changing_portfolio_name + ". I believe " + pronoun + " portfolio will increase by " + str(round(abs(highest_change))) + "% next month")
                messages.append("I would follow %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")
                messages.append("I would consider to follow %(portfolio_name)s. I think %(pronoun)s portfolio will increase by %(value)s%% next month")
                messages.append("I think %(portfolio_name)s's portfolio will increase by %(value)s%% next month, so I would follow %(him_her)s")
                messages.append("I believe %(portfolio_name)s's portfolio will see an increase of %(value)s%% next month. I would start to follow %(him_her)s")
                messages.append("I predict a positive change of %(value)s%% in %(portfolio_name)s's portfolio next month. I think starting to follow %(him_her)s is a good choice")
                messages.append("I would following %(portfolio_name)s. I predict a growth of %(value)s%% in %(pronoun)s portfolio next month")
                messages.append("I'd start following %(portfolio_name)s. I think %(pronoun)s portfolio will go up by %(value)s%%")
                messages.append("I would start following %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")
                messages.append("I would consider starting to follow %(portfolio_name)s. I think it will increase by %(value)s%% next month")
                messages.append("I predict a positive change of %(value)s%% in %(portfolio_name)s's portfolio. I'd start following %(him_her)s")

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                # messages.append("I don't think there is anyone you should start following right now")
                messages.append("I would not follow anyone right now")
                messages.append("I can't think of any other portfolio I would follow this month")
                messages.append("For now, I'm not going to follow anyone")
                messages.append("I believe no one else is worth following for now")
                messages.append("I don't think I should follow anyone else this month")
                messages.append("I'd advise against following anyone currently")
                messages.append("I don't think there is anyone else I would start following for now")
                messages.append("I wouldn't start following anyone else right now")
                messages.append("I wouldn't start following any other portfolio this month")

                buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
                if Portfolio.objects.filter(user=user, followed=False):
                    buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
                if Portfolio.objects.filter(user=user, followed=True):
                    buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        return [SlotSet("name", highest_changing_portfolio_name)]


class GiveUnfollowingAdvice(Action):
    def name(self) -> Text:
        return "action_give_unfollowing_advice"

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())
        user = get_user(tracker)

        followed_portfolios = Portfolio.objects.filter(user=user, followed=True)

        lowest_changing_portfolio_name = None

        messages = []

        buttons = []

        message_params = {}

        if not followed_portfolios:
            messages.append("I am not following any portfolios right now")
            messages.append("I'm not following any portfolios at the moment")
            messages.append("I haven't been following any portfolios")
            messages.append("I'm not following any portfolio currently")
            messages.append("I'm not following anyone for now")
            messages.append("I am not following any portfolios now")
            messages.append("I'm not following any anyone right now")
            messages.append("I am not keeping tabs on any portfolios now")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
        else:
            lowest_change = -1
            pronoun = ''
            him_her = ''

            for portfolio in followed_portfolios:
                chatbot_change = portfolio.chatbotNextChange

                if chatbot_change < lowest_change:
                    lowest_change = chatbot_change
                    lowest_changing_portfolio_name = portfolio.profile.name

                    if portfolio.profile.gender == 'Male':
                        pronoun = 'his'
                        him_her = 'him'
                    else:
                        pronoun = 'her'
                        him_her = 'him'
            
            message_params = {
                'portfolio_name': lowest_changing_portfolio_name, 
                'value': str(round(abs(lowest_change))),
                'pronoun': pronoun,
                'him_her': him_her
            }

            if lowest_changing_portfolio_name is not None:
                # messages.append("I think you should stop following " + lowest_changing_portfolio_name + ". I believe " + pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month")
                messages.append("I would stop follow %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%% next month")
                messages.append("I think %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I would stop following %(him_her)s")
                messages.append("I would unfollow %(portfolio_name)s. I predict %(pronoun)s portfolio will decrease by %(value)s%% next month")
                messages.append("I'd stop following %(portfolio_name)s. I predict a negative change of %(value)s%% in %(him_her)s portfolio next month")
                messages.append("I would stop following %(portfolio_name)s. I think %(pronoun)s portfolio will decrease by %(value)s%% next month")
                messages.append("I think it's time to stop following %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%%")
                messages.append("I predict %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I'd consider stopping following %(him_her)s")
                messages.append("My predictions indicate that %(portfolio_name)s's portfolio will decrease by %(value)s%%. I would end my following of %(him_her)s")
                messages.append("I predict the value of %(portfolio_name)s's portfolio will decrease by %(value)s%% next month. I would unfollow %(him_her)s")
                messages.append("I would unfollow %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%%")

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                messages.append("I would not stop following anyone right now")
                messages.append("I'd advise against unfollowing anyone currently")
                messages.append("I am not planning to unfollow anyone right now")
                messages.append("I wouldn't unfollow anyone at the moment")
                messages.append("I wouldn't stop following any portfolio for now")
                messages.append("I wouldn't unfollow anyone at the moment")
                messages.append("I would not stop following anyone right now")
                messages.append("I would keep following everyone at the moment")
                messages.append("I would keep following everyone right now")

                buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
                if Portfolio.objects.filter(user=user, followed=False):
                    buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
                if Portfolio.objects.filter(user=user, followed=True):
                    buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        return [SlotSet("name", lowest_changing_portfolio_name)]

class FetchPortfolio(Action):
    def name(self) -> Text:
        return "action_fetch_portfolio"

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())
        user = get_user(tracker)

        # TODO: check this
        profile_name = tracker.get_slot('name')
        # profile_name = ''
        # for e in tracker.latest_message['entities']:
        #     if e['entity'] == 'portfolio_name':
        #         profile_name = e['value']
        print('profile_name: ', profile_name)

        amount = None
        amount_query = None

        if profile_name is None or profile_name == '':
            portfolio_query = "invalid"
        else:
            portfolio_query = None

            amount = tracker.get_slot('amount')
            print('amount: ', amount)
            # for e in tracker.latest_message['entities']:
            #     if e['entity'] == 'amount':
            if amount:
                try:
                    # amount = round(Decimal(amount), 2)
                    amount = round(float(amount), 2)
                except (IndexError, InvalidOperation):
                    print('exception from amount')
                    amount_query = 'invalid'

            try:
                profile_object = Profile.objects.get(name__icontains=profile_name)
                profile_name = profile_object.name

                portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

                if portfolio.followed:
                    portfolio_query = "followed"
                else:
                    portfolio_query = "not_followed"

                if amount is not None and amount > 0:
                    amount_query = "valid"
                elif amount is not None and amount <= 0:
                    amount_query = "invalid"

            except (IndexError, MultipleObjectsReturned) as e:
                portfolio_query = "invalid"

            print('amount:', amount)
            print('amount_query:', amount_query)
            print('portfolio:', portfolio)
            print('portfolio_query:', portfolio_query)

        return [SlotSet("portfolio_query", portfolio_query), SlotSet("name", profile_name), SlotSet("amount_query", amount_query), SlotSet("amount", amount)]


class AskAddAmount(Action):
    def name(self) -> Text:
        return "action_ask_add_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())
        user = get_user(tracker)

        # TODO: check this
        profile_name = tracker.get_slot('name')

        balance = Balance.objects.get(user=user)
        available_amount = balance.available

        messages = []

        messages.append("How much should I invest?")
        messages.append("Got it. How much should I put in?")
        messages.append("Okay, what amount should I invest?")
        messages.append("Great. How much should I invest?")
        messages.append("Got it. How much can I invest?")
        messages.append("Ok. How much should I invest in this portfolio?")
        messages.append("Alright. How much should I allocate to this portfolio?")
        messages.append("Got it. What amount should I invest in this portfolio?")
        messages.append("Okay, what amount should I invest in this portfolio?")
        messages.append("Great. How much should I invest in this portfolio?")

        buttons = []
        tenPercent = int(50 * round(float(available_amount/10)/50))
        twentyPercent = tenPercent*2
        fourtyPercent = twentyPercent*2

        if tenPercent > 0:
            buttons.append({"title": "£" + str(tenPercent), "payload": "£" + str(tenPercent)})
        if twentyPercent > 0 and twentyPercent != tenPercent:
            buttons.append({"title": "£" + str(twentyPercent), "payload": "£" + str(twentyPercent)})
        if fourtyPercent > 0 and fourtyPercent != twentyPercent:
            buttons.append({"title": "£" + str(fourtyPercent), "payload": "£" + str(fourtyPercent)})

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons)

        return [SlotSet("name", profile_name)]


class AskWithdrawAmount(Action):
    def name(self) -> Text:
        return "action_ask_withdraw_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)

        profile_name = tracker.get_slot('name')

        profile_object = Profile.objects.get(name__icontains=profile_name)
        portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

        buttons = []
        tenPercent = int(10 * round(float(portfolio.invested/10)/10))
        twentyPercent = tenPercent*2
        fiftyPercent = tenPercent*5

        if tenPercent > 0:
            buttons.append({"title": "£" + str(tenPercent), "payload": "£" + str(tenPercent)})
        if twentyPercent > 0 and twentyPercent != tenPercent:
            buttons.append({"title": "£" + str(twentyPercent), "payload": "£" + str(twentyPercent)})
        if fiftyPercent > 0 and fiftyPercent != twentyPercent:
            buttons.append({"title": "£" + str(fiftyPercent), "payload": "£" + str(fiftyPercent)})

        messages = []

        messages.append("How much should I withdraw?") 
        messages.append("Got it. How much should I withdraw?")
        messages.append("Okay, what amount should I withdraw?")
        messages.append("Great. How much should I withdraw?")
        messages.append("Got it. How much can I withdraw?")
        messages.append("Ok. How much should I withdraw from this portfolio?")
        messages.append("Alright. How much money should I pull out?")
        messages.append("Got it. What amount should I withdraw from this portfolio?")
        messages.append("I see. What amount should should I withdraw?")
        messages.append("Okay. What amount should I withdraw from this portfolio?")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons)
        

        return [SlotSet("name", profile_name)]


class Follow(Action):
    def name(self) -> Text:
        return "action_follow"

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())

        user = get_user(tracker)

        profile_name = tracker.get_slot('name')
        # for e in tracker.latest_message['entities']:
        #     if e['entity'] == 'portfolio_name':
        #         profile_name = e['value']

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        messages = []
        
        message_params = {}

        if profile_name is None or profile_name == '':
            messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
            messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
            messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
            messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            condition = get_condition(user)
            if 'mistake' in condition or 'miss' in condition:
                print("'mistake' in condition or 'miss' in condition")
                # inject an error in the portfolio name
                if is_time_for_error(user):
                    if 'mistake' in condition:
                        # filter the portfolios that are not already followed
                        unfollowed_portfolio = Portfolio.objects.filter(user=user, followed=False)
                        # exclude the requested portfolio and take the first one
                        portfolio = unfollowed_portfolio.exclude(profile=profile_object.id).first()
                        # update the profile name
                        profile_name = portfolio.profile.name
                    elif 'miss' in condition:
                        profile_name = None
                        messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
                        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
                        return []

            amount_query = tracker.get_slot('amount_query')
            amount = tracker.get_slot('amount')

            # if amount is None:
            #     try:
            #         # amount = round(Decimal(tracker.latest_message['entities'][0]['value'].replace('£','')), 2)
            #         if amount > 0:
            #             amount_query = 'valid'
            #         else:
            #             amount_query = 'invalid'
            #     except IndexError:
            #         amount_query = 'invalid'
            # else:
            amount_query = 'valid'

            if amount_query == 'valid':
                # amount = str(amount).replace('£','')
                balance = Balance.objects.get(user=user)
                available_before = balance.available
                invested_before = balance.invested
                balance.available -= round(Decimal(amount), 2)

                if balance.available < 0:
                    messages.append("My current balance is not sufficient")
                    messages.append("My balance is not enough right now")
                    messages.append("At the moment, my balance is insufficient")
                    messages.append("I don't have enough in my current balance")
                    messages.append("My balance at present does not cover the amount")
                    messages.append("I don't think my available balance is enough")
                    messages.append("That amount is more than my available balance")
                    messages.append("I don't think my balance is sufficient")
                    messages.append("That amount is too large for my available balance")
                    messages.append("Well, my existing balance is not enough")
                else:
                    balance.save()

                    portfolio.followed = True
                    portfolio.invested += round(Decimal(amount), 2)
                    portfolio.save()

                    message_params = {
                        'profile_name': profile_name.title()
                    }

                    # messages.append("You are now following %(profile_name)s")
                    messages.append("I started following %(profile_name)s")
                    messages.append("I've started to follow %(profile_name)s")
                    messages.append("Okay, I'm now following %(profile_name)s")
                    messages.append("I have invested in %(profile_name)s 's portfolio")
                    messages.append("I am now following %(profile_name)s")
                    messages.append("Alright. I've added %(profile_name)s to my follow list")
                    messages.append("Cool. I am now following %(profile_name)s")
                    messages.append("Okay. I've put %(profile_name)s on my follow list")
                    messages.append("Alright, I have started following %(profile_name)s")
                    messages.append("Got it. I began following %(profile_name)s")

                    month_no = Month.objects.filter(user=user).order_by('number').last().number

                    user_action = UserAction(
                        user=user,
                        month=month_no,
                        available=available_before,
                        invested=invested_before,
                        portfolio=profile_name.title(),
                        chatbot_change=portfolio.chatbotNextChange,
                        newspost_change=portfolio.newspostNextChange,
                        action="Follow",
                        amount=amount
                    )
                    user_action.save()
            else:
                messages.append("I think that's not a valid amount")
                messages.append("I'm afraid that's not a valid amount")
                messages.append("I don't think that's a valid amount")
                messages.append("I reckon that's not a valid amount")
                messages.append("I don't believe that's a valid amount")
                messages.append("I'm afraid that amount doesn't look right")
                messages.append("I need to say that amount isn't valid")
                messages.append("I believe that amount isn't valid")
                messages.append("I feel that amount might not be valid")
                messages.append("I don't think that's a right amount")


        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        # return []
        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
            ]


class Unfollow(Action):
    def name(self) -> Text:
        return "action_unfollow"

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)
        
        profile_name = tracker.get_slot('name')

        messages = []

        message_params = {}

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
            messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
            messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
            messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")
        else:
            try:
                profile_object = Profile.objects.get(name__icontains=profile_name)
            except MultipleObjectsReturned:
                messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
                custom_utter_message(random.choice(messages), tracker, dispatcher, message_params=message_params)

                return[]
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            balance = Balance.objects.get(user=user)
            available_before = balance.available
            invested_before = balance.invested
            portfolio_invested_before = portfolio.invested
            balance.available += portfolio.invested
            balance.save()

            portfolio.followed = False
            portfolio.invested = 0.00
            portfolio.save()

            month_no = Month.objects.filter(user=user).order_by('number').last().number

            user_action = UserAction(user=user,
             month=month_no,
             available=available_before,
             invested=invested_before,
             portfolio=profile_name.title(),
             chatbot_change=portfolio.chatbotNextChange,
             newspost_change=portfolio.newspostNextChange,
             action="Unfollow",
             amount=portfolio_invested_before)
            user_action.save()

            message_params = {
                'profile_name': profile_name.title()
            }

            # messages.append("You have stopped following %(profile_name)s")
            messages.append("I stopped following %(profile_name)s")
            messages.append("I ended my follow of %(profile_name)s")
            messages.append("Alright. I have now unfollowed %(profile_name)s")
            messages.append("I have unfollowed %(profile_name)s")
            messages.append("Ok. I'm not following %(profile_name)s anymore")
            messages.append("Got it. I have now stopped following %(profile_name)s")
            messages.append("Alright. I'm not following %(profile_name)s anymore")
            messages.append("Got it. I've removed %(profile_name)s from my follow list")
            messages.append("Okay. I no longer follow %(profile_name)s")
            messages.append("Okay. I have unfollowed %(profile_name)s now")

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        # return[]
        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
            ]


class AddAmount(Action):
    def name(self) -> Text:
        return "action_add_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())
        user = get_user(tracker)

        profile_name = tracker.get_slot('name')
        print("profile_name:", profile_name)

        messages = []
        buttons = []

        message_params = {}

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
            messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
            messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
            messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            amount = tracker.get_slot('amount')
            print('amount:', amount)

            # if amount is None:
            #     try:
            #         amount = tracker.latest_message['entities'][0]['value'].replace('£','')

            #     except IndexError:
            #         # messages.append("That's not a valid amount")
            #         messages.append("I'm afraid that's not a valid amount")
            #         # messages.append("That amount is not valid")
            #         # messages.append("That's an invalid amount, I'm afraid")
            #         # messages.append("That amount doesn't look right")
            #         # messages.append("I'm afraid that amount doesn't look right")
            #         # messages.append("That amount doesn't look valid to me")
            #         # messages.append("I don't think that's a valid amount")
            #         # messages.append("That's not a right amount!")
            #         # messages.append("I don't think that's a right amount")

            if amount is not None:
                # amount = str(amount).replace('£','')
                amount = round(Decimal(amount), 2)

                if amount > 0:
                    balance = Balance.objects.get(user=user)
                    available_before = balance.available
                    invested_before = balance.invested
                    balance.available -= amount

                    if balance.available < 0:
                        messages.append("My current balance is not sufficient")
                        messages.append("My balance is not enough right now")
                        messages.append("At the moment, my balance is insufficient")
                        messages.append("I don't have enough in my current balance")
                        messages.append("My balance at present does not cover the amount")
                        messages.append("I don't think my available balance is enough")
                        messages.append("That amount is more than my available balance")
                        messages.append("I don't think my balance is sufficient")
                        messages.append("That amount is too large for my available balance")
                        messages.append("Well, my existing balance is not enough")
                    else:
                        balance.save()

                        portfolio.invested += amount
                        portfolio.save()

                        month_no = Month.objects.filter(user=user).order_by('number').last().number

                        user_action = UserAction(user=user,
                         month=month_no,
                         available=available_before,
                         invested=invested_before,
                         portfolio=profile_name.title(),
                         chatbot_change=portfolio.chatbotNextChange,
                         newspost_change=portfolio.newspostNextChange,
                         action="Add",
                         amount=amount)
                        user_action.save()

                        message_params = {
                            'value': str(amount),
                            'profile_name': profile_name.title()
                        }

                        # messages.append("You have invested another £%(value)s in %(profile_name)s")
                        messages.append("I invested another %(value)s in %(profile_name)s")
                        messages.append("Okay. I've put an additional %(value)s into %(profile_name)s")
                        messages.append("Alright. I have invested another %(value)s into %(profile_name)s 's portfolio")
                        messages.append("Got it. I've allocated another %(value)s towards %(profile_name)s")
                        messages.append("Ok. I have added %(value)s into %(profile_name)s 's portfolio")
                        messages.append("Got it. I have now invested another %(value)s into %(profile_name)s")
                        messages.append("Ok, I have put another %(value)s into %(profile_name)s")
                        messages.append("Alright. I've further invested %(value)s in %(profile_name)s")
                        messages.append("I have increased my investment in %(profile_name)s by %(value)s")
                        messages.append("OK. I have invested %(value)s more in %(profile_name)s 's portfolio")
                else:
                    # messages.append("That's not a valid amount")
                    messages.append("I think that's not a valid amount")
                    messages.append("I'm afraid that's not a valid amount")
                    messages.append("I don't think that's a valid amount")
                    messages.append("I reckon that's not a valid amount")
                    messages.append("I don't believe that's a valid amount")
                    messages.append("I'm afraid that amount doesn't look right")
                    messages.append("I need to say that amount isn't valid")
                    messages.append("I believe that amount isn't valid")
                    messages.append("I feel that amount might not be valid")
                    messages.append("I don't think that's a right amount")
            else:
                # messages.append("That's not a valid amount")
                messages.append("I think that's not a valid amount")
                messages.append("I'm afraid that's not a valid amount")
                messages.append("I don't think that's a valid amount")
                messages.append("I reckon that's not a valid amount")
                messages.append("I don't believe that's a valid amount")
                messages.append("I'm afraid that amount doesn't look right")
                messages.append("I need to say that amount isn't valid")
                messages.append("I believe that amount isn't valid")
                messages.append("I feel that amount might not be valid")
                messages.append("I don't think that's a right amount")

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        print('before custom_utter_message')
        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)
        print('after custom_utter_message')

        # return []
        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
            ]


class WithdrawAmount(Action):
    def name(self):
        return "action_withdraw_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        try:
            user = get_user(tracker)
            profile_name = tracker.get_slot('name')

            messages = []
            buttons = []

            message_params = {}

            if profile_name is None:
                messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
                messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
                messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
                messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
                messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
                messages.append("Sorry, I can't find that one. Have you spelt the name right?")
                messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
                messages.append("My bad. I can't find that portfolio, have you spelt it right?")
                messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
                messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")
            else:
                profile_object = Profile.objects.get(name__icontains=profile_name)
                portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

                amount = tracker.get_slot('amount')

                # if amount is None:
                #     try:
                #         amount = tracker.latest_message['entities'][0]['value'].replace('£','')

                #     except IndexError:
                #         # messages.append("That's not a valid amount")
                #         messages.append("I'm afraid that's not a valid amount")
                #         # messages.append("That amount is not valid")
                #         # messages.append("That's an invalid amount, I'm afraid")
                #         # messages.append("That amount doesn't look right")
                #         # messages.append("I'm afraid that amount doesn't look right")
                #         # messages.append("That amount doesn't look valid to me")
                #         # messages.append("I don't think that's a valid amount")
                #         # messages.append("That's not a right amount!")
                #         # messages.append("I don't think that's a right amount")

                if amount is not None:
                    # amount = str(amount).replace('£','')
                    amount = round(Decimal(amount), 2)

                    message_params = {
                        'profile_name': profile_name.title(),
                        'value': amount
                    }

                    portfolio.invested -= amount

                    if portfolio.invested < 0:
                        # messages.append("That's not a valid amount")
                        messages.append("I think that's not a valid amount")
                        messages.append("I'm afraid that's not a valid amount")
                        messages.append("I don't think that's a valid amount")
                        messages.append("I reckon that's not a valid amount")
                        messages.append("I don't believe that's a valid amount")
                        messages.append("I'm afraid that amount doesn't look right")
                        messages.append("I need to say that amount isn't valid")
                        messages.append("I believe that amount isn't valid")
                        messages.append("I feel that amount might not be valid")
                        messages.append("I don't think that's a right amount")
                    else:
                        balance = Balance.objects.get(user=user)
                        available_before = balance.available
                        invested_before = balance.invested
                        balance.available += amount
                        balance.save()

                        if portfolio.invested == 0:
                            portfolio.followed = False
                            # messages.append("You have stopped following " + profile_name.title())
                            messages.append("I stopped following %(profile_name)s")
                            messages.append("I ended my follow of %(profile_name)s")
                            messages.append("Alright. I have now unfollowed %(profile_name)s")
                            messages.append("I have unfollowed %(profile_name)s")
                            messages.append("Ok. I'm not following %(profile_name)s anymore")
                            messages.append("Got it. I have now stopped following %(profile_name)s")
                            messages.append("Alright. I'm not following %(profile_name)s anymore")
                            messages.append("Got it. I've removed %(profile_name)s from my follow list")
                            messages.append("Okay. I no longer follow %(profile_name)s")
                            messages.append("Okay. I have unfollowed %(profile_name)s now")
                        else:
                            messages.append("I withdrew %(value)s from %(profile_name)s")
                            messages.append("I have withdrawn %(value)s from %(profile_name)s")
                            messages.append("Ok, I have withdrawn %(value)s from %(profile_name)s's portfolio")
                            messages.append("Got it. I've taken out %(value)s from %(profile_name)s")
                            messages.append("Alright. I've withdrawn %(value)s from %(profile_name)s's portfolio")
                            messages.append("I took %(value)s out of %(profile_name)s's portfolio")
                            messages.append("I got it. A total of %(value)s was withdrawn from %(profile_name)s's portfolio")
                            messages.append("Okay, I have just withdrawn %(value)s from %(profile_name)s")
                            messages.append("Understood. I have just withdrawn %(value)s from %(profile_name)s")
                            messages.append("I got it. Withdrew %(value)s from %(profile_name)s")

                        portfolio.save()

                        month_no = Month.objects.filter(user=user).order_by('number').last().number

                        user_action = UserAction(user=user,
                        month=month_no,
                        available=available_before,
                        invested=invested_before,
                        portfolio=profile_name.title(),
                        chatbot_change=portfolio.chatbotNextChange,
                        newspost_change=portfolio.newspostNextChange,
                        action="Withdraw",
                        amount=amount)
                        user_action.save()
                else:
                    # messages.append("That's not a valid amount")
                    messages.append("I think that's not a valid amount")
                    messages.append("I'm afraid that's not a valid amount")
                    messages.append("I don't think that's a valid amount")
                    messages.append("I reckon that's not a valid amount")
                    messages.append("I don't believe that's a valid amount")
                    messages.append("I'm afraid that amount doesn't look right")
                    messages.append("I need to say that amount isn't valid")
                    messages.append("I believe that amount isn't valid")
                    messages.append("I feel that amount might not be valid")
                    messages.append("I don't think that's a right amount")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

            # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
            custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)
        except Exception as e:
            print(e)
        
        # return []
        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
            ]


class UnfollowEveryone(Action):
    def name(self):
        return "action_unfollow_everyone"

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)
        followed_portfolios = Portfolio.objects.filter(user=user, followed=True)

        messages = []

        if not followed_portfolios:
            # messages.append("You are not following anyone at the moment")
            messages.append("I am not following any portfolios right now")
            messages.append("I'm not following any portfolios at the moment")
            messages.append("I haven't been following any portfolios")
            messages.append("I'm not following any portfolio currently")
            messages.append("I'm not following anyone for now")
            messages.append("I am not following any portfolios now")
            messages.append("I'm not following any anyone right now")
            messages.append("I am not keeping tabs on any portfolios now")
        else:
            balance = Balance.objects.get(user=user)

            for portfolio in followed_portfolios:
                available_before = balance.available
                invested_before = balance.invested
                portfolio_invested_before = portfolio.invested
                balance.available += portfolio.invested

                portfolio.followed = False
                portfolio.invested = 0.00

                portfolio.save()

                month_no = Month.objects.filter(user=user).order_by('number').last().number

                user_action = UserAction(
                    user=user,
                    month=month_no,
                    available=available_before,
                    invested=invested_before,
                    portfolio=portfolio.profile.name.title(),
                    chatbot_change=portfolio.chatbotNextChange,
                    newspost_change=portfolio.newspostNextChange,
                    action="Unfollow",
                    amount=portfolio_invested_before
                )
                user_action.save()

            balance.save()

            messages.append("I stopped following everyone")
            messages.append("I have unfollowed everyone")
            messages.append("Got it. I have stopped following everyone")
            messages.append("Okay, I have now unfollowed everyone")
            messages.append("Alright. I have unfollowed everyone")
            messages.append("Ok. I've just unfollowed every portfolio")
            messages.append("I've removed everyone from my follow list")
            messages.append("Got it. I have unfollowed every portfolio")
            messages.append("OK. I have stopped following every portfolio")
            messages.append("Alright. I am no longer following anyone")

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons)

        # return []
        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
            ]


class ShouldIFollowAdvice(Action):
    def name(self):
        return 'action_should_i_follow_advice'

    @try_except
    def run(self, dispatcher, tracker, domain):
        print("\n", self.name())
        user = get_user(tracker)
        messages = []

        profile_name = tracker.get_slot('name')
        amount_query = tracker.get_slot('amount_query')

        messages = []
        buttons = []

        message_params = {}

        # if profile_name is None:
        #     profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
            messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
            messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
            messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            chatbot_change = round(portfolio.chatbotNextChange)

            # answers = []
            increase_or_decrease = ''

            if chatbot_change >= 30:
                # answers.append('Absolutely! ')
                # answers.append('Definitely! ')
                # answers.append('For sure! ')
                # answers.append('Certainly! ')
                # answers.append('Yes! ')
                # answers.append('Definitely yes! ')
                # answers.append('Totally! ')
                # answers.append('Without question! ')
                # answers.append('Yeah! ')
                # answers.append('Of course! ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > 0:
                # answers.append('Yes. ')
                # answers.append('Yep. ')
                # answers.append('Yeah. ')
                # answers.append('Sure. ')
                # answers.append('Yup. ')
                # answers.append('Yeah, ')
                # answers.append('Yes, ')
                # answers.append('Yup, ')
                # answers.append('Yep, ')
                # answers.append('Sure, ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change == 0:
                # answers.append('Not really. ')
                # answers.append('No, not really. ')
                # answers.append('Not really, no. ')
                # answers.append('Nope, not really. ')
                # answers.append('Nah. ')
                # answers.append('Not really, no. ')
                # answers.append('Hmm, not really. ')
                # answers.append('Nah, not really. ')
                # answers.append('Hmm, nah. ')
                # answers.append('No. Not really. ')
                increase_or_decrease = 'not change'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -10:
                # answers.append('Not really. ')
                # answers.append('No, not really. ')
                # answers.append('Not really, no. ')
                # answers.append('Nope, not really. ')
                # answers.append('Nah. ')
                # answers.append('Not really, no. ')
                # answers.append('Hmm, not really. ')
                # answers.append('Nah, not really. ')
                # answers.append('Hmm, nah. ')
                # answers.append('No. Not really. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -30:
                # answers.append('No. ')
                # answers.append('Nope. ')
                # answers.append('I don\'t think so. ')
                # answers.append('Nope, don\'t think so. ')
                # answers.append('That\'s a no from me. ')
                # answers.append('Negative. ')
                # answers.append('By no means. ')
                # answers.append('Hmm. Nope. ')
                # answers.append('Hmm. I don\'t think so. ')
                # answers.append('Hmm. No. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            else:
                # answers.append('Absolutely not! ')
                # answers.append('No way! ')
                # answers.append('Certainly not! ')
                # answers.append('Definitely not! ')
                # answers.append('No! ')
                # answers.append('Not at all! ')
                # answers.append('Most certainly not! ')
                # answers.append('Oh, no!')
                # answers.append('Oh, definitely not! ')
                # answers.append('Oh, no way! ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)

            # verbs = []
            # verbs.append('I believe ')
            # verbs.append('I predict ')
            # verbs.append('I think ')
            # verbs.append('I expect that ')

            message_params = {
                'profile_name': profile_name.title(),
                'increase_or_decrease': increase_or_decrease
            }

            # messages.append(random.choice(answers) + random.choice(verbs) + profile_name.title() + '\'s portfolio will ' + increase_or_decrease + ' next month')
            messages.append("I believe %(profile_name)s\'s portfolio will %(increase_or_decrease)s next month")

        #custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        return []

    def appendButtons(self, user, positive, followed, gender, amount_query, buttons):
        pronoun = ''
        if gender == "Male":
            pronoun = 'him'
        else:
            pronoun = 'her'

        if positive and followed:
            if amount_query == 'valid':
                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Withdraw from " + pronoun, "payload": "Withdraw from " + pronoun})
                buttons.append({"title": "Unfollow " + pronoun, "payload": "Unfollow " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                buttons.append({"title": "Invest more on " + pronoun, "payload": "Invest more on " + pronoun})
                buttons.append({"title": "Withdraw from " + pronoun, "payload": "Withdraw from " + pronoun})
                buttons.append({"title": "Unfollow " + pronoun, "payload": "Unfollow " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
        elif positive and not followed:
            if amount_query == 'valid':
                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                buttons.append({"title": "Follow " + pronoun, "payload": "Follow " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
        elif not positive and followed:
            if amount_query == 'valid':
                buttons.append({"title": "Do it anyway", "payload": "Do it anyway"})
                buttons.append({"title": "Unfollow " + pronoun, "payload": "Unfollow " + pronoun})
                buttons.append({"title": "Withdraw from " + pronoun, "payload": "Withdraw from " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                buttons.append({"title": "Unfollow " + pronoun, "payload": "Unfollow " + pronoun})
                buttons.append({"title": "Withdraw from " + pronoun, "payload": "Withdraw from " + pronoun})
                buttons.append({"title": "Invest more on " + pronoun, "payload": "Invest more on " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
        else:
            buttons.append({"title": "Do it anyway", "payload": "Do it anyway"})
            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})


class ShouldIUnfollowAdvice(Action):
    def name(self):
        return 'action_should_i_unfollow_advice'

    @try_except
    def run(self, dispatcher, tracker, domain):
        user = get_user(tracker)
        messages = []

        profile_name = tracker.get_slot('name')
        amount_query = tracker.get_slot('amount_query')

        buttons = []

        message_params = {}

        # if profile_name is None:
        #     profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Could you please check the spelling of the name for me?")
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            messages.append("Apologies, I can't find that portfolio. Have you spelt the name right?")
            messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            messages.append("Sorry, have you spelt the name right? I can't find that portfolio")
            messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            messages.append("Hmm, I can't find that portfolio. Could you check if the name is spelled correctly?")
            messages.append("Unfortunately, I can't find that portfolio. Have you spelt the name correctly?")

        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            chatbot_change = round(portfolio.chatbotNextChange)

            answers = []
            increase_or_decrease = ''

            if chatbot_change >= 30:
                answers.append('Absolutely not! ')
                answers.append('No way! ')
                answers.append('Certainly not! ')
                answers.append('Definitely not! ')
                answers.append('No! ')
                answers.append('Not at all! ')
                answers.append('Most certainly not! ')
                answers.append('Oh, no!')
                answers.append('Oh, definitely not! ')
                answers.append('Oh, no way! ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > 0:
                answers.append('No. ')
                answers.append('Nope. ')
                answers.append('I don\'t think so. ')
                answers.append('Nope, don\'t think so. ')
                answers.append('That\'s a no from me. ')
                answers.append('Negative. ')
                answers.append('By no means. ')
                answers.append('Hmm. Nope. ')
                answers.append('Hmm. I don\'t think so. ')
                answers.append('Hmm. No. ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change == 0:
                answers.append('Not really. ')
                answers.append('No, not really. ')
                answers.append('Not really, no. ')
                answers.append('Nope, not really. ')
                answers.append('Nah. ')
                answers.append('Not really, no. ')
                answers.append('Hmm, not really. ')
                answers.append('Nah, not really. ')
                answers.append('Hmm, nah. ')
                answers.append('No. Not really. ')
                increase_or_decrease = 'not change'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -10:
                answers.append('Not really. ')
                answers.append('No, not really. ')
                answers.append('Not really, no. ')
                answers.append('Nope, not really. ')
                answers.append('Nah. ')
                answers.append('Not really, no. ')
                answers.append('Hmm, not really. ')
                answers.append('Nah, not really. ')
                answers.append('Hmm, nah. ')
                answers.append('No. Not really. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -30:
                answers.append('Yes. ')
                answers.append('Yep. ')
                answers.append('Yeah. ')
                answers.append('Sure. ')
                answers.append('Yup. ')
                answers.append('Yeah, ')
                answers.append('Yes, ')
                answers.append('Yup, ')
                answers.append('Yep, ')
                answers.append('Sure, ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)
            else:
                answers.append('Absolutely! ')
                answers.append('Definitely! ')
                answers.append('For sure! ')
                answers.append('Certainly! ')
                answers.append('Yes! ')
                answers.append('Definitely yes! ')
                answers.append('Totally! ')
                answers.append('Without question! ')
                answers.append('Yeah! ')
                answers.append('Of course! ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)

            verbs = []
            verbs.append('I believe ')
            verbs.append('I predict ')
            verbs.append('I think ')
            verbs.append('I expect that ')

            message_params = {
                'profile_name': profile_name.title(),
                'increase_or_decrease': increase_or_decrease,
            }

            # messages.append(random.choice(answers) + random.choice(verbs) + profile_name.title() + '\'s portfolio will ' + increase_or_decrease + ' next month')
            messages.append("I believe %(profile_name)s\'s portfolio will %(increase_or_decrease)s next month")

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

        return[]

    def appendButtons(self, user, positive, gender, amount_query, buttons):
        pronoun = ''
        if gender == "Male":
            pronoun = 'him'
        else:
            pronoun = 'her'

        if positive:
            if amount_query == 'valid':
                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Invest more on " + pronoun, "payload": "Invest more on " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                buttons.append({"title": "Invest more on " + pronoun, "payload": "Invest more on " + pronoun})
                buttons.append({"title": "Withdraw from " + pronoun, "payload": "Withdraw from " + pronoun})
                buttons.append({"title": "Unfollow " + pronoun, "payload": "Unfollow " + pronoun})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
        else:
            buttons.append({"title": "Do it anyway", "payload": "Do it anyway"})
            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})


class ResetSlots(Action):
    def name(self) -> Text:
        return "action_reset_slots"

    # def run(self, dispatcher, tracker, domain):
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [
            SlotSet("portfolio_query", None), 
            # SlotSet("name", None), 
            SlotSet("amount_query", None), 
            # SlotSet("amount", None)
            ]


class FallbackAction(Action):
    def name(self) -> Text:
        return "action_fallback"

    # def run(self, dispatcher, tracker, domain):
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user = get_user(tracker)
        fallback_count = FallbackCount.objects.get(user=user)
        fallback_count.count += 1
        fallback_count.save()

        messages = []

        messages.append("Sorry, I didn't understand that, or it's something I cannot help with")
        messages.append("Sorry, that was unclear to me, or it's outside my scope of assistance")
        messages.append("I'm sorry, I didn't quite get that, or it is something I cannot help with")
        messages.append("Sorry, I'm afraid I didn't catch that, or it is something I cannot help with")
        messages.append("I'm sorry, that's not something I understood, or it is something I cannot help with. Could you rephrase that please?")
        messages.append("Apologies, I don't understand, or it's not something I can provide help with")
        messages.append("I'm sorry, that didn't make sense to me, or it's something beyond my help")
        messages.append("Hmm, not sure about that, or it is something I cannot help with. Could you rephrase?")
        messages.append("I'm not sure I understand, or it is something I cannot help with. Can you rephrase that?")
        messages.append("Please rephrase that. I'm not sure I understand, or it is something I cannot help with")

        # dispatcher.utter_message(random.choice(messages))
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [UserUtteranceReverted()]

class DefaultFallbackAction(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    # def run(self, dispatcher, tracker, domain):
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user = get_user(tracker)
        fallback_count = FallbackCount.objects.get(user=user)
        fallback_count.count += 1
        fallback_count.save()

        messages = []

        messages.append("Sorry, I didn't understand that, or it's something I cannot help with")
        messages.append("Sorry, that was unclear to me, or it's outside my scope of assistance")
        messages.append("I'm sorry, I didn't quite get that, or it is something I cannot help with")
        messages.append("Sorry, I'm afraid I didn't catch that, or it is something I cannot help with")
        messages.append("I'm sorry, that's not something I understood, or it is something I cannot help with. Could you rephrase that please?")
        messages.append("Apologies, I don't understand, or it's not something I can provide help with")
        messages.append("I'm sorry, that didn't make sense to me, or it's something beyond my help")
        messages.append("Hmm, not sure about that, or it is something I cannot help with. Could you rephrase?")
        messages.append("I'm not sure I understand, or it is something I cannot help with. Can you rephrase that?")
        messages.append("Please rephrase that. I'm not sure I understand, or it is something I cannot help with")


        # dispatcher.utter_message(random.choice(messages))
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [UserUtteranceReverted()]
