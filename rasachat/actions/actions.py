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
r = reader(open('./responses_test.csv', 'r'))
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
    
    # no errors for odd numbered months
    if month.number % 2 == 1:
        return False
    
    # TODO: tweak this and possibly make it parametric
    if elapsed_time > 60 and month.errors_experienced == 0:
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

        custom_utter_message(
            "Ok",
            tracker,
            dispatcher)

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
            "I can follow or unfollow portfolios, add or withdraw amounts for you and provide advice like: \"Who should I follow?\", \"Who should I unfollow?\", \"Invest another 100 on Aricka\" or \"withdraw from alois\"",
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
            "I remind you: you can switch to Image Tagging by clicking the \"Task\" button in the top right corner",
            tracker,
            dispatcher)

        return []

class Newsfeed(Action):
    def name(self) -> Text:
        return "action_newsfeed"

    @try_except
    def run(self, dispatcher, tracker, domain):

        custom_utter_message(
            "I'm afraid I don't know much about the newsfeed",
            tracker,
            dispatcher)

        return []

class ImDoingMyBest(Action):
    def name(self) -> Text:
        return "action_im_doing_my_best"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "Sorry, I am doing my best: predictions and responses are meant to be as accurate as possible, but might contain errors",
            tracker,
            dispatcher
        )

        return []


class FollowOnePortfolioAtATime(Action):
    def name(self) -> Text:
        return "action_please_follow_one_portfolio_at_a_time"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "Sorry, I can only follow one portfolio at a time (one message for each portfolio)",
            tracker,
            dispatcher
        )

        return []

class UnfollowEveryone(Action):
    def name(self) -> Text:
        return "action_are_you_sure_unfollow_everyone"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "I want to confirm: shall I unfollow everyone?",
            tracker,
            dispatcher
        )

        return []

class InvalidAmount(Action):
    def name(self) -> Text:
        return "action_invalid_amount"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            #"That's not a valid amount!",
            "I'm afraid that's not a valid amount",
            tracker,
            dispatcher
        )

        return [
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
        ]

class InvalidPortfolio(Action):
    def name(self) -> Text:
        return "action_invalid_portfolio"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "Sorry, I can't find that portfolio. Have you spelt the name correctly?",
            tracker,
            dispatcher
        )

        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            ]

class AlreadyNotFollowedPortfolio(Action):
    def name(self) -> Text:
        return "action_already_not_followed_portfolio"
    
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "I don't think you're following that portfolio",
            tracker,
            dispatcher
        )

        return [
            SlotSet("portfolio_query", None), 
            SlotSet("name", None), 
            ]

class AlreadyFollowedPortfolio(Action):
    def name(self) -> Text:
        return "action_already_followed_portfolio"

    @try_except
    def run(self, dispatcher, tracker, domain):
        
        custom_utter_message(
            "I think you are already following that portfolio",
            tracker,
            dispatcher
        )

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
            messages.append("I don't think there is anyone you should follow or unfollow currently")
            # messages.append("You're doing great! I don't think you should follow or unfollow anyone else this month")
            # messages.append("You're doing great! I don't think there is anyone else you should follow or unfollow at the moment")
            # messages.append("I don't think you should follow or unfollow anyone else at the moment")
            # messages.append("That's it! I don't think there is any other portfolio you should follow or unfollow this month")
            # messages.append("That's it, you're doing great! I don't think there is anyone else you should follow or unfollow")
            # messages.append("I can't think of anyone else you should follow or unfollow at the moment. You're doing great!")
            # messages.append("I don't think there is anyone else you should start or stop following at the moment")
            # messages.append("You're doing great! I can't think of anyone else to follow or unfollow")
            # messages.append("I don't think you should follow or unfollow anyone else this month")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
   
            custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)

        elif lowest_changing_portfolio_name is None or higher_is_greater:
            # messages.append("I think you should start following " + highest_changing_portfolio_name + ". I believe " + highest_pronoun + " portfolio will increase by " + str(round(highest_change)) + "% next month")
            messages.append("I think you should start following %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")

            # messages.append("You should follow " + highest_changing_portfolio_name + ". I think " + highest_pronoun + " portfolio will increase by " + str(round(highest_change)) + "%")
            # messages.append("I think  " + highest_changing_portfolio_name + "'s portfolio will increase by " + str(round(highest_change)) + "% next month, so you should follow " + highest_him_her)
            # messages.append("I believe " + highest_changing_portfolio_name + "'s portfolio will increase by " + str(round(highest_change)) + "%. I think you should start following " + highest_him_her)
            # messages.append("I predict a positive change of " + str(round(highest_change)) + "% in " + highest_changing_portfolio_name + "'s portfolio next month. I think you should follow " + highest_him_her)
            # messages.append("You should follow " + highest_changing_portfolio_name + ". I predict a positive change of " + str(round(highest_change)) + "% in " + highest_pronoun + " portfolio next month")
            # messages.append("I'd start following " + highest_changing_portfolio_name + " if I were you. I think " + highest_pronoun + " portfolio will increase by " + str(round(highest_change)) + "%")
            # messages.append("I would start following " + highest_changing_portfolio_name + ". I believe " + highest_pronoun + " portfolio will grow by " + str(round(highest_change)) + "% next month")
            # messages.append("You should follow " + highest_changing_portfolio_name + "\'s portfolio. I think it will increase by " + str(round(highest_change)) + "% next month")
            # messages.append("I predict a positive change of " + str(round(highest_change)) + "% in " + highest_changing_portfolio_name + "\'s portfolio. I think you should start following " + highest_him_her)

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
            messages.append("I think you should stop following %(portfolio_name)s. I believe %(pronoun)s portfolio will decrease by %(value)s%% next month")
            # messages.append("I think " + lowest_changing_portfolio_name + "'s portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month. You should stop following " + lowest_him_her)
            # messages.append("You should unfollow " + lowest_changing_portfolio_name + ". I predict " + lowest_pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "%")
            # messages.append("I predict a negative change of " + str(round(abs(lowest_change)))  + " in " + lowest_changing_portfolio_name + "'s portfolio next month. I think you should stop following " + lowest_him_her)
            # messages.append("If I were you, I would stop following " + lowest_changing_portfolio_name + ". I think " + lowest_pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month")
            # messages.append("You should stop following " + lowest_changing_portfolio_name + ". I believe " + lowest_pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "%")
            # messages.append("I think " + lowest_changing_portfolio_name + "\'s portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month. You should unfollow " + lowest_him_her)
            # messages.append("My predictions tell me " + lowest_changing_portfolio_name + "\'s portfolio will decrease by " + str(round(abs(lowest_change))) + "%. You should consider unfollowing " + lowest_him_her)
            # messages.append("I predict the value of " + lowest_changing_portfolio_name + "\'s portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month. I would unfollow " + lowest_him_her + " if I were you")
            # messages.append("You should unfollow " + lowest_changing_portfolio_name + ". I think " + lowest_pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "%")

            profile_name = lowest_changing_portfolio_name
            portfolio_query = "followed"
            buttons.append({"title": "Do it", "payload": "Do it"})
            buttons.append({"title": "Never mind", "payload": "Never mind"})

            message_params = {
                'portfolio_name': lowest_changing_portfolio_name, 
                'value': str(round(lowest_change)),
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
            # messages.append("You are following everyone at the moment!")
            # messages.append("There is no one left to follow!")
            # messages.append("You are following every portfolio at the moment!")
            # messages.append("You are following everyone currently!")
            # messages.append("Every portfolio is being followed at the moment!")
            # messages.append("There's no one left to follow!")
            # messages.append("There's no portfolio left to follow!")
            messages.append("I'm afraid there's no one left to follow!")
            # messages.append("You're following everyone already!")
            # messages.append("You're already following everyone!")
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
                messages.append("I think you should start following %(portfolio_name)s. I believe %(pronoun)s portfolio will increase by %(value)s%% next month")
                # messages.append("I believe " + highest_changing_portfolio_name + "'s portfolio will increase by " + str(round(abs(highest_change))) + "% next month, so I think you should follow " + him_her)
                # messages.append("Well, I think you should invest in " + highest_changing_portfolio_name + ". I believe " + pronoun + " portfolio will increase by " + str(round(abs(highest_change))) + "% next month")
                # messages.append("I predict a positive change of " + str(round(abs(highest_change))) + "% in " + highest_changing_portfolio_name + "'s portfolio next month, so I think you should start following " + him_her)
                # messages.append(highest_changing_portfolio_name + ". I believe " + pronoun + " portfolio will increase by " + str(round(abs(highest_change))) + "% next month")
                # messages.append(highest_changing_portfolio_name + ". I think " + pronoun + " portfolio will grow by " + str(round(abs(highest_change))) + "%")
                # messages.append("That would be " + highest_changing_portfolio_name + ". I predict a positive change of " + str(round(abs(highest_change))) + "% in " + pronoun + " portfolio")
                # messages.append("Well, I think " + highest_changing_portfolio_name + "\'s portfolio will grow by " + str(round(abs(highest_change))) + "% next month. You should follow " + him_her)
                # messages.append("That would be " + highest_changing_portfolio_name + ". My predictions tell me " + pronoun + " portfolio will increase by " + str(round(abs(highest_change))) + "%")
                # messages.append(highest_changing_portfolio_name + ". I predict a positive change of " + str(round(abs(highest_change))) + "% in " + pronoun + " portfolio. You should invest in " + him_her)

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                # messages.append("I don't think there is anyone you should start following right now")
                messages.append("I don't think there is anyone you should start following right now")
                # messages.append("I can't think of any other portfolio you should follow this month")
                # messages.append("I don't think there aren't any other portfolio you should start following for now")
                # messages.append("I believe no one else is worth following for now")
                # messages.append("I don't think you should follow anyone else this month")
                # messages.append("There isn't anyone I think you should start follow this month")
                # messages.append("I don't think there is anyone else I would start following for now")
                # messages.append("I wouldn't start following anyone else right now")
                # messages.append("I wouldn't start following any other portfolio this month")
                # messages.append("There isn't anyone else worth following this month")

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
            # messages.append("You are not following anyone at the moment")
            # messages.append("There is no one to unfollow")
            # messages.append("You're not following any portfolio currently")
            # messages.append("No portfolio is being followed right now")
            # messages.append("You're not following anyone for now")
            # messages.append("But you're not following anyone at the moment!")
            # messages.append("But there is no one to unfollow!")
            messages.append("I'm afraid you're not following any portfolios right now")
            # messages.append("No portfolios are being followed right now!")
            # messages.append("You're not following any portfolio for now")

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
                messages.append("I think you should stop following %(portfolio_name)s . I believe %(pronoun)s portfolio will decrease by %(value)s%% next month")
                # messages.append("I believe " + lowest_changing_portfolio_name + "'s portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month. You should probably stop following " + him_her)
                # messages.append("Well, I would stop following " + lowest_changing_portfolio_name + " if I were you. I think " + pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month")
                # messages.append("You should unfollow " + lowest_changing_portfolio_name + "'s portfolio. I think its value will decrease by " + str(round(abs(lowest_change))) + "% next month")
                # messages.append("I predict a negative change of " + str(round(abs(lowest_change))) + "% in " + lowest_changing_portfolio_name + "'s portfolio. I think you should stop following " + him_her)
                # messages.append(lowest_changing_portfolio_name + ". I think " + pronoun + " portfolio will decreasy by " + str(round(abs(lowest_change))) + "%. You should unfollow " + him_her)
                # messages.append(lowest_changing_portfolio_name + ". I predict a negative change of " + str(round(abs(lowest_change))) + "% next month, so I suggest unfollowing " + him_her)
                # messages.append(lowest_changing_portfolio_name + ". I believe the value of " + pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month. I suggest unfollowing " + him_her)
                # messages.append(lowest_changing_portfolio_name + "\'s portfolio should decrease by " + str(round(abs(lowest_change))) + "% next month. I think you should stop following " + him_her)
                # messages.append("I would stop following " + lowest_changing_portfolio_name + ". I believe " + pronoun + " portfolio will decrease by " + str(round(abs(lowest_change))) + "% next month")

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                messages.append("I don't think there is anyone you should stop following right now")
                # messages.append("I don't think you should stop following anyone for now")
                # messages.append("I don't think anyone is currently worth unfollowing")
                # messages.append("I wouldn't unfollow anyone at the moment")
                # messages.append("I wouldn't stop following any portfolio for now")
                # messages.append("There isn't anyone I think you should stop following right now")
                # messages.append("Right now, I don't think there is anyone you should stop following")
                # messages.append("Hmm. I can't think of anyone you should stop following")
                # messages.append("Hmm. There isn't anyone you should stop following in my opinion")
                # messages.append("In my opinion, you shouldn't unfollow anyone at the moment")

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
        # profile_name = tracker.get_slot('name')
        profile_name = ''
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'portfolio_name':
                profile_name = e['value']

        amount = None
        amount_query = None

        if profile_name is None or profile_name == '':
            portfolio_query = "invalid"
        else:
            portfolio_query = None

            for e in tracker.latest_message['entities']:
                if e['entity'] == 'amount':
                    try:
                        amount = round(Decimal(e['value'].replace('£','')), 2)
                    except (IndexError, InvalidOperation):
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

        messages.append("How much would you like to invest?")
        # messages.append("Got it. How much do you want to invest?")
        # messages.append("Okay, how much do you want to invest?")
        # messages.append("Great, how much would you like to invest?")
        # messages.append("Alright. How much do you want to invest?")
        # messages.append("Great. How much should you invest?")
        # messages.append("Ok. How much do you want to invest in this portfolio?")
        # messages.append("How much would you like to invest in this portfolio?")
        # messages.append("What is the amount you would like to invest?")
        # messages.append("Got it. How much to invest?")

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

        messages.append("How much should I withdraw for you?") 
        # messages.append("How much would you like to withdraw?")
        # messages.append("Okay, how much do you want to withdraw?")
        # messages.append("Alright. How much would you like to withdraw?")
        # messages.append("Great, how much do you want to withdraw?")
        # messages.append("Got it. How much would you like to withdraw?")
        # messages.append("Great. How much should you invest?")
        # messages.append("Ok. How much do you want to invest in this portfolio?")
        # messages.append("How much would you like to invest in this portfolio?")
        # messages.append("What is the amount you would like to invest?")
        # messages.append("Got it. How much to invest?")

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
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'portfolio_name':
                profile_name = e['value']

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        messages = []
        
        message_params = {}

        if profile_name is None or profile_name == '':
            messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
            # messages.append("I can't seem to find that portfolio. Have you spelt the name right?")
            # messages.append("I'm sorry, I can't find that portfolio. Have you spelt it correctly?")
            # messages.append("Apologies, I can't seem to find that portfolio. Have you spelt the name right?")
            # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            # messages.append("Have you spelt the name right? I can't find that portfolio!")
            # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")
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
                        messages.append("I can't seem to find that portfolio. Have you spelt the name right?")
                        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons)
                        return []

            amount_query = tracker.get_slot('amount_query')
            amount = tracker.get_slot('amount')

            if amount is None:
                try:
                    amount = round(Decimal(tracker.latest_message['entities'][0]['value'].replace('£','')), 2)
                    if amount > 0:
                        amount_query = 'valid'
                    else:
                        amount_query = 'invalid'
                except IndexError:
                    amount_query = 'invalid'
            else:
                amount_query = 'valid'

            if amount_query == 'valid':
                amount = str(amount).replace('£','')
                balance = Balance.objects.get(user=user)
                available_before = balance.available
                invested_before = balance.invested
                balance.available -= round(Decimal(amount), 2)

                if balance.available < 0:
                    messages.append("I'm afraid your current balance is not sufficient")
                    # messages.append("I'm afraid your current balance is insufficient")
                    # messages.append("I don't think your available balance is sufficient!")
                    # messages.append("I don't think you have enough in your available balance")
                    # messages.append("That's more than your available balance!")
                    # messages.append("I don't think your available balance is enough!")
                    # messages.append("That amount is more than your available balance, I'm afraid")
                    # messages.append("I don't think your balance is enough!")
                    # messages.append("That amount is too large for your available balance")
                    # messages.append("Your available balance isn't enough!")
                else:
                    balance.save()

                    portfolio.followed = True
                    portfolio.invested += round(Decimal(amount), 2)
                    portfolio.save()

                    message_params = {
                        'profile_name': profile_name.title()
                    }

                    # messages.append("You are now following %(profile_name)s")
                    messages.append("I started following %(profile_name)s for you")
                    # messages.append("You have started following " + profile_name.title())
                    # messages.append("Okay, you are now following " + profile_name.title() + "'s portfolio")
                    # messages.append("You have invested in " + profile_name.title() + "'s portfolio")
                    # messages.append("Ok, you have started following " + profile_name.title())
                    # messages.append("Alright. You are now following " + profile_name.title())
                    # messages.append("Cool. You have started following " + profile_name.title() + "\'s portfolio")
                    # messages.append("Okay. You have invested in " + profile_name.title() + "\'s portfolio")
                    # messages.append("Alright, you have started following " + profile_name.title())
                    # messages.append("Got it. You are now following " + profile_name.title())

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
                # messages.append("That's not a valid amount")
                messages.append("I'm afraid that's not a valid amount")
                # messages.append("That amount is not valid")
                # messages.append("That's an invalid amount, I'm afraid")
                # messages.append("That amount doesn't look right!")
                # messages.append("I'm afraid that amount doesn't look right")
                # messages.append("That amount doesn't look valid to me")
                # messages.append("I don't think that's a valid amount")
                # messages.append("That's not a right amount!")
                # messages.append("I don't think that's a right amount")


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
            messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Sorry, have you spelt the name correctly? I can't find that portfolio")
            # messages.append("I'm sorry, I can't find that portfolio. Have you spelt the name right?")
            # messages.append("I can't seem to find that portfolio. Have you spelt it correctly?")
            # messages.append("Sorry, have you spelt the name right? I can't seem to find that portfolio")
            # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            # messages.append("Have you spelt the name right? I can't find that portfolio!")
            # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")
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
            messages.append("I stopped following %(profile_name)s for you")
            # messages.append("Okay, you have now stopped following " + profile_name.title())
            # messages.append("Alright. You have now unfollowed " + profile_name.title())
            # messages.append("You have unfollowed " + profile_name.title())
            # messages.append("Ok. You are not following " + profile_name.title() + " anymore")
            # messages.append("Got it. You have now stopped following " + profile_name.title())
            # messages.append("Alright. You're not following " + profile_name.title() + " anymore")
            # messages.append("Got it. You have now unfollowed " + profile_name.title())
            # messages.append("You are not following " + profile_name.title() + " anymore")
            # messages.append("Okay. You have unfollowed " + profile_name.title())

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
        user = get_user(tracker)

        profile_name = tracker.get_slot('name')

        messages = []
        buttons = []

        message_params = {}

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Sorry, have you spelt the name correctly? I can't find that portfolio")
            # messages.append("I'm sorry, I can't find that portfolio. Have you spelt the name right?")
            # messages.append("I can't seem to find that portfolio. Have you spelt it correctly?")
            # messages.append("Sorry, have you spelt the name right? I can't seem to find that portfolio")
            # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            # messages.append("Have you spelt the name right? I can't find that portfolio!")
            # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            amount = tracker.get_slot('amount')

            if amount is None:
                try:
                    amount = tracker.latest_message['entities'][0]['value'].replace('£','')

                except IndexError:
                    # messages.append("That's not a valid amount")
                    messages.append("I'm afraid that's not a valid amount")
                    # messages.append("That amount is not valid")
                    # messages.append("That's an invalid amount, I'm afraid")
                    # messages.append("That amount doesn't look right")
                    # messages.append("I'm afraid that amount doesn't look right")
                    # messages.append("That amount doesn't look valid to me")
                    # messages.append("I don't think that's a valid amount")
                    # messages.append("That's not a right amount!")
                    # messages.append("I don't think that's a right amount")

            if amount is not None:
                amount = str(amount).replace('£','')
                amount = round(Decimal(amount), 2)

                if amount > 0:
                    balance = Balance.objects.get(user=user)
                    available_before = balance.available
                    invested_before = balance.invested
                    balance.available -= amount

                    if balance.available < 0:
                        messages.append("I'm afraid your current balance is not sufficient")
                        # messages.append("I'm afraid your current balance is insufficient")
                        # messages.append("I don't think your available balance is sufficient!")
                        # messages.append("I don't think you have enough in your available balance")
                        # messages.append("That's more than your available balance!")
                        # messages.append("I don't think your available balance is enough!")
                        # messages.append("That amount is more than your available balance, I'm afraid")
                        # messages.append("I don't think your balance is enough!")
                        # messages.append("That amount is too large for your available balance")
                        # messages.append("Your available balance isn't enough!")
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
                        messages.append("I invested another %(value)s in %(profile_name)s for you")
                        # messages.append("Okay. You have added £" + str(amount) + " to " + profile_name.title())
                        # messages.append("Alright. You have invested another £" + str(amount) + " in " + profile_name.title() + "'s portfolio")
                        # messages.append("You have put another £" + str(amount) + " in " + profile_name.title() + "'s portfolio")
                        # messages.append("You have added £" + str(amount) + " to " + profile_name.title() + "'s portfolio")
                        # messages.append("Got it. You have now invested another £" + str(amount) + " in " + profile_name.title())
                        # messages.append("Ok, you have put another £" + str(amount) + " in " + profile_name.title())
                        # messages.append("Another £" + str(amount) + " was invested in " + profile_name.title() + "\'s portfolio")
                        # messages.append("You have increased the amount invested in " + profile_name.title() + "\'s portfolio by £" + str(amount))
                        # messages.append("OK. You have invested £" + str(amount) + " more in " + profile_name.title() + "\'s portfolio")
                else:
                    # messages.append("That's not a valid amount")
                    messages.append("I'm afraid that's not a valid amount")
                    # messages.append("That amount is not valid")
                    # messages.append("That's an invalid amount, I'm afraid")
                    # messages.append("That amount doesn't look right")
                    # messages.append("I'm afraid that amount doesn't look right")
                    # messages.append("That amount doesn't look valid to me")
                    # messages.append("I don't think that's a valid amount")
                    # messages.append("That's not a right amount!")
                    # messages.append("I don't think that's a right amount")
            else:
                # messages.append("That's not a valid amount")
                messages.append("I'm afraid that's not a valid amount")
                # messages.append("That amount is not valid")
                # messages.append("That's an invalid amount, I'm afraid")
                # messages.append("That amount doesn't look right")
                # messages.append("I'm afraid that amount doesn't look right")
                # messages.append("That amount doesn't look valid to me")
                # messages.append("I don't think that's a valid amount")
                # messages.append("That's not a right amount!")
                # messages.append("I don't think that's a right amount")

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        # custom_utter_message(random.choice(messages), tracker, dispatcher, buttons, message_params)
        custom_utter_message(random.choice(messages), tracker, dispatcher, buttons=buttons, message_params=message_params)

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
                messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
                # messages.append("Sorry, have you spelt the name correctly? I can't find that portfolio")
                # messages.append("I'm sorry, I can't find that portfolio. Have you spelt the name right?")
                # messages.append("I can't seem to find that portfolio. Have you spelt it correctly?")
                # messages.append("Sorry, have you spelt the name right? I can't seem to find that portfolio")
                # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
                # messages.append("Have you spelt the name right? I can't find that portfolio!")
                # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
                # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
                # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")
            else:
                profile_object = Profile.objects.get(name__icontains=profile_name)
                portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

                amount = tracker.get_slot('amount')

                if amount is None:
                    try:
                        amount = tracker.latest_message['entities'][0]['value'].replace('£','')

                    except IndexError:
                        # messages.append("That's not a valid amount")
                        messages.append("I'm afraid that's not a valid amount")
                        # messages.append("That amount is not valid")
                        # messages.append("That's an invalid amount, I'm afraid")
                        # messages.append("That amount doesn't look right")
                        # messages.append("I'm afraid that amount doesn't look right")
                        # messages.append("That amount doesn't look valid to me")
                        # messages.append("I don't think that's a valid amount")
                        # messages.append("That's not a right amount!")
                        # messages.append("I don't think that's a right amount")

                if amount is not None:
                    amount = str(amount).replace('£','')
                    amount = round(Decimal(amount), 2)

                    message_params = {
                        'profile_name': profile_name.title(),
                        'value': amount
                    }

                    portfolio.invested -= amount

                    if portfolio.invested < 0:
                        # messages.append("That's not a valid amount")
                        messages.append("I'm afraid that's not a valid amount")
                        # messages.append("That amount is not valid")
                        # messages.append("That's an invalid amount, I'm afraid")
                        # messages.append("That amount doesn't look right")
                        # messages.append("I'm afraid that amount doesn't look right")
                        # messages.append("That amount doesn't look valid to me")
                        # messages.append("I don't think that's a valid amount")
                        # messages.append("That's not a right amount!")
                        # messages.append("I don't think that's a right amount")
                    else:
                        balance = Balance.objects.get(user=user)
                        available_before = balance.available
                        invested_before = balance.invested
                        balance.available += amount
                        balance.save()

                        if portfolio.invested == 0:
                            portfolio.followed = False
                            # messages.append("You have stopped following " + profile_name.title())
                            messages.append("You have stopped following %(profile_name)s")

                            # messages.append("Okay, you have now stopped following " + profile_name.title())
                            # messages.append("Alright. You have now unfollowed " + profile_name.title())
                            # messages.append("You have unfollowed " + profile_name.title())
                            # messages.append("Ok. You are not following " + profile_name.title() + " anymore")
                            # messages.append("Got it. You have stopped following " + profile_name.title())
                            # messages.append("Ok, you have just unfollowed " + profile_name.title())
                            # messages.append("Got it. You're not following " + profile_name.title() + "\'s portfolio anymore")
                            # messages.append("You have stopped following " + profile_name.title())
                            # messages.append("OK. You have unfollowed " + profile_name.title())
                        else:
                            messages.append("I withdrew %(value)s from %(profile_name)s for you")
                            # messages.append("You have withdrawn £%(value)s from %(profile_name)s")
                            # messages.append("Ok, you have withdrawn £" + str(amount) + " from " + profile_name.title() + "'s portfolio")
                            # messages.append("Got it. You have withdrawn £" + str(amount) + " from " + profile_name.title())
                            # messages.append("Alright. You have withdrawn £" + str(amount) + " from " + profile_name.title() + "'s portfolio")
                            # messages.append("You have withdrawn £" + str(amount) + " from " + profile_name.title() + "'s portfolio")
                            # messages.append("£" + str(amount) + " was withdrawn from " + profile_name.title() + "\'s portfolio")
                            # messages.append("£" + str(amount) + " was withdrawn from " + profile_name.title())
                            # messages.append("Okay, you have just withdrawn £" + str(amount) + " from " + profile_name.title())
                            # messages.append("Understood. You have withdrawn £" + str(amount) + " from " + profile_name.title() + "\'s portfolio")
                            # messages.append("Got it. Withdrew £" + str(amount) + " from " + profile_name.title())

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
                    messages.append("I'm afraid that's not a valid amount")
                    # messages.append("That amount is not valid")
                    # messages.append("That's an invalid amount, I'm afraid")
                    # messages.append("That amount doesn't look right")
                    # messages.append("I'm afraid that amount doesn't look right")
                    # messages.append("That amount doesn't look valid to me")
                    # messages.append("I don't think that's a valid amount")
                    # messages.append("That's not a right amount!")
                    # messages.append("I don't think that's a right amount")

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
            messages.append("I'm afraid that you are not following anyone at the moment")
            # messages.append("There is no one to unfollow")
            # messages.append("You're not following any portfolio currently")
            # messages.append("No portfolio is being followed right now")
            # messages.append("You're not following anyone for now")
            # messages.append("There isn't anyone you can unfollow right now")
            # messages.append("You can't unfollow anyone at the moment")
            # messages.append("But you're not following anyone currently!")
            # messages.append("But there is no one to unfollow!")
            # messages.append("But no one is being followed right now!")
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

            messages.append("I stopped following everyone for you")
            # messages.append("You have unfollowed everyone")
            # messages.append("Got it. You have stopped following everyone")
            # messages.append("Okay, you have now unfollowed everyone")
            # messages.append("Alright. You have unfollowed everyone")
            # messages.append("Ok. You have just unfollowed every portfolio")
            # messages.append("Everyone was unfollowed")
            # messages.append("Got it. You have unfollowed every portfolio")
            # messages.append("OK. You have stopped following every portfolio")
            # messages.append("You have stopped following everyone")
            # messages.append("Alright. Every portfolio was unfollowed")

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

        if profile_name is None:
            profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Sorry, have you spelt the name correctly? I can't find that portfolio")
            # messages.append("I'm sorry, I can't find that portfolio. Have you spelt the name right?")
            # messages.append("I can't seem to find that portfolio. Have you spelt it correctly?")
            # messages.append("Sorry, have you spelt the name right? I can't seem to find that portfolio")
            # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            # messages.append("Have you spelt the name right? I can't find that portfolio!")
            # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")

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

        if profile_name is None:
            profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Sorry, have you spelt the name correctly? I can't find that portfolio")
            # messages.append("I'm sorry, I can't find that portfolio. Have you spelt the name right?")
            # messages.append("I can't seem to find that portfolio. Have you spelt it correctly?")
            # messages.append("Sorry, have you spelt the name right? I can't seem to find that portfolio")
            # messages.append("Sorry, I can't find that one. Have you spelt the name right?")
            # messages.append("Have you spelt the name right? I can't find that portfolio!")
            # messages.append("My bad. I can't find that portfolio, have you spelt it right?")
            # messages.append("Hmm, I can't find that portfolio. Have you spelt the name correctly?")
            # messages.append("Have you spelt the name correctly? I can't seem to find that portfolio")
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
            SlotSet("name", None), 
            SlotSet("amount_query", None), 
            SlotSet("amount", None)
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

        messages.append("Sorry, I didn't quite catch that")
        # messages.append("Sorry, could you rephrase that?")
        # messages.append("I'm sorry, I didn't quite get that")
        # messages.append("Sorry, I'm afraid I didn't catch that")
        # messages.append("Could you rephrase that please?")
        # messages.append("Apologies, I don't understand")
        # messages.append("Sorry, can you rephrase that please?")
        # messages.append("Hmm, not sure about that. Could you rephrase?")
        # messages.append("I'm not sure I understand. Can you rephrase that please?")
        # messages.append("Please rephrase that. I'm not sure I understand")

        # dispatcher.utter_message(random.choice(messages))
        custom_utter_message(random.choice(messages), tracker, dispatcher)

        return [UserUtteranceReverted()]
