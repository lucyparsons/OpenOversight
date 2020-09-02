import inspect
import locale
import json
import sys
from urllib.parse import urlparse

import requests
from flask import current_app, url_for
from TwitterAPI import TwitterAPI
from twitterwebhooks import TwitterWebhookAdapter

from .utils import NameMatcher, filter_by_form, compute_keyed_hash, verify_keyed_hash
from .models import Department, Job, Officer
from .main.choices import RACE_CHOICES, GENDER_CHOICES
from .main.forms import BrowseForm

locale.setlocale(locale.LC_ALL, '')


class TwitterBot:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        if not all([app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET'],
                    app.config['TWITTER_ACCESS_TOKEN'], app.config['TWITTER_ACCESS_TOKEN_SECRET'],
                    app.config['TWITTER_WEBHOOK_ENV'], app.config['TWITTER_WEBHOOK_URL']]):
            return

        self.twitter_adapter = TwitterWebhookAdapter(
            app.config['TWITTER_CONSUMER_SECRET'],
            urlparse(app.config['TWITTER_WEBHOOK_URL']).path,
            app
        )
        self.twitter_api = TwitterAPI(
            app.config['TWITTER_CONSUMER_KEY'],
            app.config['TWITTER_CONSUMER_SECRET'],
            app.config['TWITTER_ACCESS_TOKEN'],
            app.config['TWITTER_ACCESS_TOKEN_SECRET']
        )
        self.matcher = NameMatcher()
        self.register_handlers()

    def activate(self):
        self.delete_all_welcome_messages()
        self.set_welcome_message()
        self.delete_all_webhooks()
        self.register_webhook()

    def deactivate(self):
        self.delete_all_welcome_messages()
        self.delete_all_webhooks()

    def set_welcome_message(self):
        # Create new welcome message
        response = self.api_request(
            'direct_messages/welcome_messages/new',
            json.dumps({
                'welcome_message': {
                    'name': 'Default OpenOversight',
                    'message_data': self.generate_welcome_message()
                }
            })
        )
        welcome_message_id = response['welcome_message']['id']

        # Set rule to make welcome message the default
        self.api_request(
            'direct_messages/welcome_messages/rules/new',
            json.dumps({
                'welcome_message_rule': {
                    'welcome_message_id': welcome_message_id
                }
            })
        )

    def delete_all_welcome_messages(self):
        # Need to delete both rules and messages
        response = self.api_request('direct_messages/welcome_messages/rules/list')
        if 'welcome_message_rules' in response:
            for rule in response['welcome_message_rules']:
                self.api_request(
                    'direct_messages/welcome_messages/rules/destroy',
                    {'id': rule['id']}
                )
        response = self.api_request('direct_messages/welcome_messages/list')
        if 'welcome_messages' in response:
            for message in response['welcome_messages']:
                self.api_request(
                    'direct_messages/welcome_messages/destroy',
                    {'id': message['id']}
                )

    def register_webhook(self):
        self.delete_all_webhooks()
        self.api_request(
            'account_activity/all/:{}/webhooks'.format(current_app.config['TWITTER_WEBHOOK_ENV']),
            {'url': current_app.config['TWITTER_WEBHOOK_URL']}
        )

    def delete_all_webhooks(self):
        response = self.api_request('account_activity/all/webhooks')
        environments = {env['environment_name']: env['webhooks'] for env in response['environments']}
        webhooks = environments[current_app.config['TWITTER_WEBHOOK_ENV']]
        for webhook in webhooks:
            self.api_request('account_activity/all/:{}/webhooks/:{}'.format(
                current_app.config['TWITTER_WEBHOOK_ENV'],
                webhook['id']
            ))

    def api_request(self, endpoint, params=None):
        response = self.twitter_api.request(endpoint, params)
        if response.status_code >= 400:
            raise Exception(
                'Error submitting Twitter API request: {} {}'.format(
                    response.status_code, response.text)
            )
        try:
            response = response.json()
            if 'errors' in response:
                raise Exception(json.dumps(response['errors']))
        except json.decoder.JSONDecodeError:
            return response.text
        return response

    def get_account_id(self):
        ''' Helper for fetching the bot's ID '''
        credentials = self.api_request('account/verify_credentials')
        return credentials['id']

    def get_account_screen_name(self):
        ''' Helper for fetching the bot's screen_name '''
        credentials = self.api_request('account/verify_credentials')
        return credentials['screen_name']

    def match_one_from_message(self, message_data):
        current_app.logger.debug("Parsing tweet: {}".format(message_data['text']))
        officer = self.matcher.match_one_fuzzy([message_data['text']])
        if officer:
            return officer
        officer = self.matcher.match_one_basic([message_data['text']])
        if officer:
            return officer
        # Check text of any links
        link_texts = []
        for link in message_data['entities']['urls']:
            r = requests.get(link['expanded_url'])
            if r.status_code == 200:
                link_texts.append(r.text)
        officer = self.matcher.match_one_basic(link_texts)
        return officer

    def match_from_message(self, message_data):
        current_app.logger.debug("Parsing tweet: {}".format(message_data['text']))
        officers = self.matcher.match_fuzzy([message_data['text']])
        officers |= self.matcher.match_basic([message_data['text']])
        # Check text of any links
        link_texts = []
        for link in message_data['entities']['urls']:
            r = requests.get(link['expanded_url'])
            if r.status_code == 200:
                link_texts.append(r.text)
        officers |= self.matcher.match_basic(link_texts)
        return officers

    def register_handlers(self):
        @self.twitter_adapter.on("tweet_create_events")
        def handle_mentions(event_data):
            tweet = event_data['event']
            if self.get_account_id() not in [user['id'] for user in tweet['entities']['user_mentions']]:
                return
            other_mentions = [user['screen_name'] for user in tweet['entities']['user_mentions']]
            recipient_screen_names = set([tweet['user']['screen_name']] + other_mentions)
            recipient_screen_names.remove(self.get_account_screen_name())
            in_reply_to = tweet['id']

            matched_officer = self.match_one_from_message(tweet)
            # Check text of quote retweet
            if not matched_officer and tweet.get('is_quote_status'):
                matched_officer = self.match_one_from_message(tweet['quoted_status'])

            if matched_officer:
                tweet_text = ''
                for screen_name in sorted(recipient_screen_names):
                    tweet_text += '@{} '.format(screen_name)
                tweet_text += self.generate_response([matched_officer])
                self.api_request(
                    'statuses/update',
                    {
                        'status': tweet_text,
                        'in_reply_to_status_id': in_reply_to
                    }
                )

        @self.twitter_adapter.on("direct_message_events")
        def handle_direct_messages(event_data):
            event = event_data['event']
            if event['type'] == 'message_create':
                # Filter out bot messages
                sender_id = event['message_create']['sender_id']
                if str(sender_id) == str(self.get_account_id()):
                    return

                recipient_id = event['message_create']['target']['recipient_id']
                message_data = event['message_create']['message_data']

                # conversation response
                if 'quick_reply_response' in message_data and \
                        message_data['quick_reply_response']['type'] == 'options':
                    state = unpack_signed_metadata(message_data['quick_reply_response']['metadata'])
                    try:
                        conversation = Conversation(state)
                        response_data = conversation.handle_message(message_data)
                    except Exception:
                        return  # silently ignore

                # plaintext name search
                else:
                    matched_officers = self.match_from_message(message_data)
                    if len(matched_officers) > 0:
                        response = "Here's what we found for your query \"{}\":\n\n{}".format(
                            message_data['text'],
                            "\n\n".join([generate_tweet(officer) for officer in matched_officers]))
                    else:
                        response = "Sorry, we didn't find any matches for your query \"{}\".".format(
                            message_data['text'])
                    response_data = {'text': response}

                self.api_request(
                    'direct_messages/events/new',
                    {
                        'type': 'message_create',
                        'message_create': {
                            'target': {
                                'recipient_id': recipient_id
                            },
                            'message_data': response_data
                        }
                    }
                )

        @self.twitter_adapter.on("any")
        def handle_any_event(event_data):
            # Loop through events array and log received events
            for s in filter(lambda x: '_event' in x, list(event_data)):
                current_app.logger.info("[Twitter] Received event: {}".format(s))

        # Handler for error events
        @self.twitter_adapter.on("error")
        def error_handler(err):
            current_app.logger.error("[Twitter] {}".format(err))

    def generate_welcome_message(self):
        text = ("Hi there! You can select a police department below to find an officer, "
                "or message me the name of a police officer and I'll send you their public record.")
        options = [{
            'label': department.name,
            'metadata': generate_signed_metadata({
                'department_id': department.id,
                'step': ConversationStep0.__name__
            })
        } for department in Department.query.all()]
        message_data = {
            'text': text,
            'quick_reply': {
                'type': 'options',
                'options': options
            }
        }
        return message_data

    def generate_response(self, matched_officers):
        if len(matched_officers) > 1:
            link = self.generate_link(matched_officers)
            return 'We found {} potential matches. See the results here: {}'.format(
                len(matched_officers), link)
        elif len(matched_officers) == 1:
            return generate_tweet(matched_officers[0])

    def generate_link(self, officers):
        uiis = [officer.unique_internal_identifier for officer in officers]
        return url_for('main.list_officer', unique_internal_identifier=uiis.join(','))


def generate_tweet(officer):
    text = ""
    if officer.assignments.count() > 0:
        if officer.assignments[0].job.job_title != 'Not Sure':
            text += "{} ".format(officer.assignments[0].job.job_title)
        if officer.assignments[0].star_no:
            text += "{} ({})".format(officer.full_name(), officer.assignments[0].star_no.upper())
        elif officer.unique_internal_identifier:
            text += "{} ({})".format(officer.full_name(), officer.unique_internal_identifier.upper())
        else:
            text += officer.full_name()
    else:
        if officer.unique_internal_identifier:
            text += "{} ({})".format(officer.full_name(), officer.unique_internal_identifier.upper())
        else:
            text += officer.full_name()

    if officer.salaries and len(officer.salaries) > 0:
        total_pay = officer.salaries[0].salary + officer.salaries[0].overtime_pay
        text += " made {} in {}.".format(locale.currency(total_pay, grouping=True), officer.salaries[0].year)
    else:
        text += "."
    if officer.incidents:
        if len(officer.incidents) == 1:
            text += " {} was involved in 1 incident.".format(officer.last_name)
        else:
            text += " {} was involved in {} incidents.".format(officer.last_name, len(officer.incidents))
    text += " Full profile: https://bpdwatch.com/officer/{}.".format(officer.id)
    current_app.logger.info("[Twitter] Generated tweet: {}".format(text))
    return text


def generate_signed_metadata(data):
    data_str = json.dumps(data)
    digest = compute_keyed_hash(data_str)
    obj = {
        'data': data,
        'digest': digest
    }
    return json.dumps(obj)


def unpack_signed_metadata(metadata):
    obj = json.loads(metadata)
    digest = obj['digest']
    data_str = json.dumps(obj['data'])
    if not verify_keyed_hash(digest, data_str):
        raise Exception('Signed metadata digest failed to verify:\n{}\n{}'.format(digest, data_str))
    return obj['data']


class Conversation:
    def __init__(self, state):
        classes = inspect.getmembers(
            sys.modules[__name__],
            lambda member: inspect.isclass(member) and member.__module__ == __name__
        )
        classes = {name: module_class for name, module_class in classes}
        self.step = classes[state['step']](state)

    def handle_message(self, message):
        return self.step.handle_message(message)


class ConversationStep:
    next_step_class = None

    def handle_message(self, message):
        raise NotImplementedError()

    def create_text_input_response(self, text, label, metadata):
        metadata['step'] = self.next_step_class.__name__
        response = {
            'text': text,
            'quick_reply': {
                'type': 'text_input',
                'text_input': {
                    "label": label,
                    "metadata": generate_signed_metadata(metadata)
                }
            }
        }
        return response

    def create_options_response(self, text, options):
        for option in options:
            option['metadata']['step'] = self.next_step_class.__name__
        response = {
            'text': text,
            'quick_reply': {
                'type': 'options',
                'options': [{
                    "label": options['label'],
                    "metadata": generate_signed_metadata(option['metadata'])
                } for option in options]
            }
        }
        return response


class ConversationStep5(ConversationStep):
    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        department_id = metadata['department_id']
        department = Department.query.filter(Department.id == department_id).one()

        form = BrowseForm()
        form_data = form.data
        form_data['race'] = metadata['race']
        form_data['gender'] = metadata['gender']
        form_data['rank'] = metadata['rank_id']
        form_data['min_age'] = 16
        form_data['max_age'] = 100
        form_data['name'] = metadata['last_name']
        if department.unique_internal_identifier_label:
            form_data['unique_internal_identifier'] = metadata['badge_or_uii']
        else:
            form_data['badge'] = metadata['badge_or_uii']

        matched_officers = filter_by_form(form_data, Officer.query, department_id)\
            .order_by(Officer.last_name).all()
        if len(matched_officers) > 0:
            response = "Here's what we found:\n\n{}".format(
                "\n\n".join([generate_tweet(officer) for officer in matched_officers]))
        else:
            response = "Sorry, we didn't find any matches!"

        response_data = {'text': response}
        return response_data


class ConversationStep4(ConversationStep):
    next_step_class = ConversationStep5

    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        text = "Do you know the Officer's gender?"
        options = [{
            'label': gender[1],
            'metadata': {
                'gender': gender[0]
            }.update(metadata)
        } for gender in GENDER_CHOICES]
        return self.create_options_response(text, options)


class ConversationStep3(ConversationStep):
    next_step_class = ConversationStep4

    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        text = "Do you know the Officer's race?"
        options = [{
            'label': race[1],
            'metadata': {
                'race': race[0]
            }.update(metadata)
        } for race in RACE_CHOICES]
        return self.create_options_response(text, options)


class ConversationStep2(ConversationStep):
    next_step_class = ConversationStep3

    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        department_id = metadata['department_id']
        badge_or_uii = message['text']
        text = "Do you know the Officer's rank?"
        ranks = Job.query.filter_by(department_id=department_id)\
            .filter_by(is_sworn_officer=True).order_by(Job.order.asc()).all()
        options = [{
            'label': rank.job_title,
            'metadata': {
                'badge_or_uii': badge_or_uii,
                'rank_id': rank.id
            }.update(metadata)
        } for rank in ranks]
        return self.create_options_response(text, options)


class ConversationStep1(ConversationStep):
    next_step_class = ConversationStep2

    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        metadata['last_name'] = message['text']
        department_id = metadata['department_id']
        department = Department.query.filter(Department.id == department_id).one()
        if department.unique_internal_identifier_label:
            text = "Do you know any part of the Officer's {}".format(
                department.unique_internal_identifier_label)
            label = department.unique_internal_identifier_label
        else:
            text = "Do you remember any part of the Officer's badge number?"
            label = "Badge number"
        return self.create_text_input_response(text, label, metadata)


class ConversationStep0(ConversationStep):
    next_step_class = ConversationStep1

    def handle_message(self, message):
        metadata = unpack_signed_metadata(message['quick_reply_response']['metadata'])
        text = "Do you remember any part of the Officer's last name?"
        return self.create_text_input_response(text, "Officer last name", metadata)
