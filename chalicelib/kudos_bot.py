import logging

from chalicelib.global_constants import EMOJI_PLURAL
from chalicelib.persistence_adapter import add_points_to_user, get_user_points
from chalicelib.slack_api import send_message_to_slack, get_from_slack, GET_USERS, AUTH_TEST
from chalicelib.slack_message_builder import parse_message

user_mappings = {}
this_bot = {}


def populate_user_info():
    if not this_bot:
        this_bot['user_id'] = get_from_slack(AUTH_TEST)['user_id']
    if not user_mappings:
        user_info_response = get_from_slack(GET_USERS)
        for user in user_info_response['members']:
            user_mappings[user['id']] = user['profile']['display_name'] or user['profile']['real_name']


def handle_the_giving_of_emojis(slack_message):
    add_points_to_user(slack_message)
    response = f'{user_mappings[slack_message.recipient]} has now been given {slack_message.count_emojis_in_message()} {EMOJI_PLURAL}'
    send_message_to_slack(slack_message.channel, response)


def handle_direct_message(slack_message):
    if 'leaderboard' in slack_message.message:
        user_totals = get_user_points()

        response = '```\nThe all-time leaderboard is as follows:\n'
        for user, total in user_totals:
            response = response + f'\n{user_mappings[user]}: {total}'
        response = response + '\n```'

        send_message_to_slack(slack_message.channel, response)


def deal_with_slack_messages(event):
    slack_message = parse_message(event)
    if slack_message and slack_message.recipient:
        populate_user_info()
        if slack_message.recipient == this_bot['user_id']:
            handle_direct_message(slack_message)
        elif slack_message.recipient == slack_message.sender and slack_message.count_emojis_in_message():
            send_message_to_slack(slack_message.channel, f"Nice try, but you can't give yourself {EMOJI_PLURAL}")
        elif slack_message.count_emojis_in_message():
            handle_the_giving_of_emojis(slack_message)


def handle_message(data):
    if "challenge" in data:
        return data["challenge"]

    slack_event = data['event']

    if "bot_id" in slack_event:
        logging.warning("Ignore bot event")
    else:
        deal_with_slack_messages(slack_event)