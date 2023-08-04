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
from chatbot.models import Portfolio, Profile, Balance, Month, UserAction, FallbackCount
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Count
from django.core.exceptions import MultipleObjectsReturned
from random import randint
from django.db import connection
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
import random


class WhatICanDo(Action):
    def name(self) -> Text:
        return "action_what_I_can_do"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_template("utter_what_i_can_do", tracker)

        return []


class GiveGeneralAdvice(Action):
    def name(self) -> Text:
        return "action_give_general_advice"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

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

        if highest_changing_portfolio_name is None and lowest_changing_portfolio_name is None:
            messages.append("I don't think there is anyone else you should start or stop following at the moment")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
        elif lowest_changing_portfolio_name is None or higher_is_greater:
            messages.append("You should follow " + highest_changing_portfolio_name + ". I predict a positive change of " + str(round(highest_change)) + "% in " + highest_pronoun + " portfolio next month")

            profile_name = highest_changing_portfolio_name
            portfolio_query = "not_followed"
            buttons.append({"title": "Do it", "payload": "Do it"})
            buttons.append({"title": "Never mind", "payload": "Never mind"})
        else:
            messages.append("You should unfollow " + lowest_changing_portfolio_name + ". I predict " + lowest_pronoun + " porfolio will decrease by " + str(round(abs(lowest_change))) + "%")

            profile_name = lowest_changing_portfolio_name
            portfolio_query = "followed"
            buttons.append({"title": "Do it", "payload": "Do it"})
            buttons.append({"title": "Never mind", "payload": "Never mind"})

        selected_message = random.choice(messages)
        selected_message += '++ADVICE++'
        print(selected_message)
        dispatcher.utter_button_message(selected_message, buttons) 

        return [SlotSet("name", profile_name), SlotSet("portfolio_query", portfolio_query)]


class GiveFollowingAdvice(Action):
    def name(self) -> Text:
        return "action_give_following_advice"

    def run(self, dispatcher, tracker, domain):
        print("action_give_following_advice")
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        not_followed_portfolios = Portfolio.objects.filter(user=user, followed=False)

        highest_changing_portfolio_name = None

        messages = []

        buttons = []

        if not not_followed_portfolios:
            messages.append("You are following every portfolio at the moment!")
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

            if highest_changing_portfolio_name is not None:
                messages.append(highest_changing_portfolio_name + ". I predict a positive change of " + str(round(abs(highest_change))) + "% in " + pronoun + " portfolio. You should invest in " + him_her)

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                messages.append("There isn't anyone I think you should start follow this month")


                buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
                if Portfolio.objects.filter(user=user, followed=False):
                    buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
                if Portfolio.objects.filter(user=user, followed=True):
                    buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        selected_message = random.choice(messages)
        selected_message += '++ADVICE++'
        print(selected_message)
        dispatcher.utter_button_message(selected_message, buttons) 

        return [SlotSet("name", highest_changing_portfolio_name)]


class GiveUnfollowingAdvice(Action):
    def name(self) -> Text:
        return "action_give_unfollowing_advice"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        followed_portfolios = Portfolio.objects.filter(user=user, followed=True)

        lowest_changing_portfolio_name = None

        messages = []

        buttons = []

        if not followed_portfolios:
            messages.append("You're not following any portfolio currently")

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

            if lowest_changing_portfolio_name is not None:
                messages.append(lowest_changing_portfolio_name + ". I predict a negative change of " + str(round(abs(lowest_change))) + "% next month, so I suggest unfollowing " + him_her)

                buttons.append({"title": "Do it", "payload": "Do it"})
                buttons.append({"title": "Never mind", "payload": "Never mind"})
            else:
                messages.append("There isn't anyone I think you should stop following right now")

                buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
                if Portfolio.objects.filter(user=user, followed=False):
                    buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
                if Portfolio.objects.filter(user=user, followed=True):
                    buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        selected_message = random.choice(messages)
        selected_message += '++ADVICE++'
        print(selected_message)
        dispatcher.utter_button_message(selected_message, buttons) 

        return [SlotSet("name", lowest_changing_portfolio_name)]


class FetchPortfolio(Action):
    def name(self) -> Text:
        return "action_fetch_portfolio"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        # print('action_fetch_portfolio')

        connection.close()
        user = User.objects.get(username=username)

        profile_name = ''
        for e in tracker.latest_message['entities']:
            if e['entity'] == 'portfolio_name':
                profile_name = e['value']
        # print('profile_name:', profile_name)

        amount = None
        amount_query = None

        if profile_name is None:
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
                # print('profile_object', profile_object)
                profile_name = profile_object.name
                # print('profile_name', profile_name)

                portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)
                # print('portfolio', portfolio)

                if portfolio.followed:
                    portfolio_query = "followed"
                else:
                    portfolio_query = "not_followed"

                if amount is not None and amount > 0:
                    amount_query = "valid"
                elif amount is not None and amount <= 0:
                    amount_query = "invalid"

            except (IndexError, MultipleObjectsReturned) as e:
                # print('exception:', e)
                portfolio_query = "invalid"

        # print('portfolio_query', portfolio_query)
        return [SlotSet("portfolio_query", portfolio_query), SlotSet("name", profile_name), SlotSet("amount_query", amount_query), SlotSet("amount", amount)]


class AskAddAmount(Action):
    def name(self) -> Text:
        return "action_ask_add_amount"

    def run(self, dispatcher, tracker, domain):
        connection.close()
        user = User.objects.get(username=(tracker.current_state())["sender_id"])

        profile_name = tracker.get_slot('name')

        balance = Balance.objects.get(user=user)
        available_amount = balance.available

        messages = []

        messages.append("Ok. How much do you want to invest in this portfolio?")

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

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return [SlotSet("name", profile_name)]


class AskWithdrawAmount(Action):
    def name(self) -> Text:
        return "action_ask_withdraw_amount"

    def run(self, dispatcher, tracker, domain):

        connection.close()
        user = User.objects.get(username=(tracker.current_state())["sender_id"])

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

        messages.append("Ok. How much do you want to invest in this portfolio?")

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return [SlotSet("name", profile_name)]


class Follow(Action):
    def name(self) -> Text:
        return "action_follow"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        print(user.username)

        profile_name = tracker.get_slot('name')

        messages = []

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")

        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

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
                    messages.append("I don't think you have enough in your available balance")
                else:
                    balance.save()

                    portfolio.followed = True
                    portfolio.invested = round(Decimal(amount), 2)
                    portfolio.save()
                    print(Portfolio.objects.filter(followed=True).aggregate(Sum('invested')).get('invested__sum'))
                    messages.append("Ok, you have started following " + profile_name.title())

                    month = Month.objects.get(user=user).number

                    user_action = UserAction(user=user,
                     month=month,
                     available=available_before,
                     invested=invested_before,
                     portfolio=profile_name.title(),
                     chatbot_change=portfolio.chatbotNextChange,
                     newspost_change=portfolio.newspostNextChange,
                     action="Follow",
                     amount=amount)
                    user_action.save()
            else:
                messages.append("That amount is not valid")

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return[]


class Unfollow(Action):
    def name(self) -> Text:
        return "action_unfollow"

    def run(self, dispatcher, tracker, domain):
        connection.close()
        user = User.objects.get(username=(tracker.current_state())["sender_id"])

        profile_name = tracker.get_slot('name')

        messages = []

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
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

            month = Month.objects.get(user=user).number

            user_action = UserAction(user=user,
             month=month,
             available=available_before,
             invested=invested_before,
             portfolio=profile_name.title(),
             chatbot_change=portfolio.chatbotNextChange,
             newspost_change=portfolio.newspostNextChange,
             action="Unfollow",
             amount=portfolio_invested_before)
            user_action.save()

            messages.append("Ok. You are not following " + profile_name.title() + " anymore")

        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return[]


class AddAmount(Action):
    def name(self) -> Text:
        return "action_add_amount"

    def run(self, dispatcher, tracker, domain):
        connection.close()
        user = User.objects.get(username=(tracker.current_state())["sender_id"])

        profile_name = tracker.get_slot('name')

        messages = []
        buttons = []

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            amount = tracker.get_slot('amount')

            if amount is None:
                try:
                    amount = tracker.latest_message['entities'][0]['value'].replace('£','')

                except IndexError:
                    messages.append("That amount is not valid")


            if amount is not None:
                amount = str(amount).replace('£','')
                amount = round(Decimal(amount), 2)

                if amount > 0:
                    balance = Balance.objects.get(user=user)
                    available_before = balance.available
                    invested_before = balance.invested
                    balance.available -= amount

                    if balance.available < 0:
                        messages.append("I don't think you have enough in your available balance")
                    else:
                        balance.save()

                        portfolio.invested += amount
                        portfolio.save()

                        month = Month.objects.get(user=user).number

                        user_action = UserAction(user=user,
                         month=month,
                         available=available_before,
                         invested=invested_before,
                         portfolio=profile_name.title(),
                         chatbot_change=portfolio.chatbotNextChange,
                         newspost_change=portfolio.newspostNextChange,
                         action="Add",
                         amount=amount)
                        user_action.save()

                        messages.append("OK. You have invested £" + str(amount) + " more in " + profile_name.title() + "\'s portfolio")
                else:
                    messages.append("That amount is not valid")
            else:
                messages.append("That amount is not valid")


        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return []


class WithdrawAmount(Action):
    def name(self):
        return "action_withdraw_amount"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        profile_name = tracker.get_slot('name')

        messages = []
        buttons = []

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            amount = tracker.get_slot('amount')

            if amount is None:
                try:
                    amount = tracker.latest_message['entities'][0]['value'].replace('£','')

                except IndexError:
                    messages.append("That amount is not valid")

            if amount is not None:
                amount = str(amount).replace('£','')
                amount = round(Decimal(amount), 2)

                portfolio.invested -= amount

                if portfolio.invested < 0:
                    messages.append("That amount is not valid")
                else:
                    balance = Balance.objects.get(user=user)
                    available_before = balance.available
                    invested_before = balance.invested
                    balance.available += amount
                    balance.save()

                    if portfolio.invested == 0:
                        portfolio.followed = False
                        messages.append("Ok. You have unfollowed " + profile_name.title())
                    else:
                        messages.append("Ok, you have withdrawn £" + str(amount) + " from " + profile_name.title() + "'s portfolio")
                    portfolio.save()

                    month = Month.objects.get(user=user).number

                    user_action = UserAction(user=user,
                     month=month,
                     available=available_before,
                     invested=invested_before,
                     portfolio=profile_name.title(),
                     chatbot_change=portfolio.chatbotNextChange,
                     newspost_change=portfolio.newspostNextChange,
                     action="Withdraw",
                     amount=amount)
                    user_action.save()
            else:
                messages.append("That amount is not valid")


        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return []


class UnfollowEveryone(Action):
    def name(self):
        return "action_unfollow_everyone"

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        followed_portfolios = Portfolio.objects.filter(user=user, followed=True)

        messages = []

        if not followed_portfolios:
            messages.append("You're not following any portfolio currently")
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

                month = Month.objects.get(user=user).number

                user_action = UserAction(user=user,
                 month=month,
                 available=available_before,
                 invested=invested_before,
                 portfolio=portfolio.profile.name.title(),
                 chatbot_change=portfolio.chatbotNextChange,
                 newspost_change=portfolio.newspostNextChange,
                 action="Unfollow",
                 amount=portfolio_invested_before)
                user_action.save()

            balance.save()

            messages.append("Ok. You have just unfollowed every portfolio")
        buttons = []

        buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
        if Portfolio.objects.filter(user=user, followed=False):
            buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
        if Portfolio.objects.filter(user=user, followed=True):
            buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})

        dispatcher.utter_button_message(random.choice(messages), buttons)

        return []


class ShouldIFollowAdvice(Action):
    def name(self):
        return 'action_should_i_follow_advice'

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)
        messages = []

        profile_name = tracker.get_slot('name')
        amount_query = tracker.get_slot('amount_query')

        messages = []
        buttons = []

        if profile_name is None:
            profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")

            buttons.append({"title": "Give me some advice", "payload": "Give me some advice"})
            if Portfolio.objects.filter(user=user, followed=False):
                buttons.append({"title": "Who should I follow?", "payload": "Who should i follow?"})
            if Portfolio.objects.filter(user=user, followed=True):
                buttons.append({"title": "Who should I stop following?", "payload": "Who should I stop following?"})
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            chatbot_change = round(portfolio.chatbotNextChange)

            answers = []
            increase_or_decrease = ''

            if chatbot_change >= 30:
                answers.append('Yes! ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > 0:
                answers.append('Yes. ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change == 0:
                answers.append('No. Not really. ')
                increase_or_decrease = 'not change'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -10:
                answers.append('No. Not really. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -30:
                answers.append('No. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)
            else:
                answers.append('No! ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, portfolio.followed, profile_object.gender, amount_query, buttons)

            verbs = []
            verbs.append('I predict ')

            messages.append(random.choice(answers) + random.choice(verbs) + profile_name.title() + '\'s portfolio will ' + increase_or_decrease + ' next month')

        selected_message = random.choice(messages)
        selected_message += '++ADVICE++'
        print(selected_message)
        dispatcher.utter_button_message(selected_message, buttons) 

        return[]

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

    def run(self, dispatcher, tracker, domain):
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        messages = []

        profile_name = tracker.get_slot('name')
        amount_query = tracker.get_slot('amount_query')

        buttons = []

        if profile_name is None:
            profile_name = tracker.latest_message['entities'][0]['value']

        if profile_name is None:
            messages.append("Sorry, I'm having trouble finding that portfolio. Have you spelt the name correctly?")
        else:
            profile_object = Profile.objects.get(name__icontains=profile_name)
            portfolio = Portfolio.objects.get(user=user, profile=profile_object.id)

            chatbot_change = round(portfolio.chatbotNextChange)

            answers = []
            increase_or_decrease = ''

            if chatbot_change >= 30:
                answers.append('No! ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > 0:
                answers.append('No. ')
                increase_or_decrease = 'increase by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change == 0:
                answers.append('No. Not really. ')
                increase_or_decrease = 'not change'
                self.appendButtons(False, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -10:
                answers.append('No. Not really. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)
            elif chatbot_change > -30:
                answers.append('Yes. ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)
            else:
                answers.append('Yes! ')
                increase_or_decrease = 'decrease by ' + str(abs(chatbot_change)) + '%'
                self.appendButtons(True, user, profile_object.gender, amount_query, buttons)

            verbs = []
            verbs.append('I predict ')

            messages.append(random.choice(answers) + random.choice(verbs) + profile_name.title() + '\'s portfolio will ' + increase_or_decrease + ' next month')

        selected_message = random.choice(messages)
        selected_message += '++ADVICE++'
        print(selected_message)
        dispatcher.utter_button_message(selected_message, buttons) 

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
        username = tracker.current_state()["sender_id"]

        connection.close()
        user = User.objects.get(username=username)

        fallback_count = FallbackCount.objects.get(user=user)
        fallback_count.count += 1
        fallback_count.save()

        messages = []

        messages.append("I'm not sure I understand. Can you rephrase that please?")

        dispatcher.utter_message(random.choice(messages))

        return [UserUtteranceReverted()]
