import pytest
import json as json_
from urllib.parse import urlparse
from flask import url_for, current_app
from mock import patch, MagicMock
import lorem
from datetime import date, time

from OpenOversight.app.models import Officer, Job, Assignment, Salary, Incident, Department
from OpenOversight.app.twitterbot import (generate_tweet, generate_signed_metadata,
                                          unpack_signed_metadata, Conversation)
from OpenOversight.app.main.choices import RACE_CHOICES, GENDER_CHOICES


def test_webhook_route(client):
    route = urlparse(url_for('crc_handshake')).path
    rv = client.get(route)
    assert rv.status_code == 404
    assert "These are not the twitter bots you're looking for." in rv.data.decode('utf-8')


def test_crc_handshake(client):
    with current_app.test_request_context():
        route = url_for('crc_handshake')
        rv = client.get(
            route,
            query_string={'crc_token': 'bacon'}
        )
        assert rv.status_code == 200

        expected_response_token = "sha256=0O1WaZ7pWGR3h6xnqhJJLBLoz7zXqKzzyn5BmcNc95E="
        response = json_.loads(rv.data.decode('utf-8'))
        assert 'response_token' in response
        assert response['response_token'] == expected_response_token


def test_twitter_api_request(app):
    response_mock = MagicMock(status_code=200, text='{"key": "value"}', json=MagicMock(return_value={"key": "value"}))
    request_mock = MagicMock(return_value=response_mock)
    with patch('TwitterAPI.TwitterAPI.request', request_mock) as mocked_function:
        response = current_app.twitter_bot.api_request('account/verify_credentials')

    assert response == {'key': 'value'}
    mocked_function.assert_called_once_with('account/verify_credentials', None)
    response_mock.json.assert_called_once_with()


def test_twitter_api_request_no_json(app):
    response_mock = MagicMock(status_code=200, text='foo', json=MagicMock(side_effect=json_.decoder.JSONDecodeError(None, '', 0)))
    request_mock = MagicMock(return_value=response_mock)
    with patch('TwitterAPI.TwitterAPI.request', request_mock) as mocked_function:
        response = current_app.twitter_bot.api_request('account/verify_credentials')

    assert response == 'foo'
    mocked_function.assert_called_once_with('account/verify_credentials', None)
    response_mock.json.assert_called_once_with()


def test_twitter_api_request_bad_response(app):
    response_mock = MagicMock(status_code=403, text='error', json=MagicMock(return_value={"key": "value"}))
    request_mock = MagicMock(return_value=response_mock)
    with patch('TwitterAPI.TwitterAPI.request', request_mock) as mocked_function:
        with pytest.raises(Exception):
            current_app.twitter_bot.api_request('account/verify_credentials')

    mocked_function.assert_called_once_with('account/verify_credentials', None)
    response_mock.json.assert_not_called()


def test_twitter_api_request_error_response(app):
    response_mock = MagicMock(status_code=200, text='{"errors": []}', json=MagicMock(return_value={"errors": []}))
    request_mock = MagicMock(return_value=response_mock)
    with patch('TwitterAPI.TwitterAPI.request', request_mock) as mocked_function:
        with pytest.raises(Exception):
            current_app.twitter_bot.api_request('account/verify_credentials')

    mocked_function.assert_called_once_with('account/verify_credentials', None)
    response_mock.json.assert_called_once_with()


def test_delete_welcome_messages(twitter_api_request, rules_list_response, messages_list_response):
    with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
        current_app.twitter_bot.delete_all_welcome_messages()

    mocked_function.assert_any_call('direct_messages/welcome_messages/rules/list')
    for rule in rules_list_response['welcome_message_rules']:
        mocked_function.assert_any_call(
            'direct_messages/welcome_messages/rules/destroy',
            {'id': rule['id']}
        )
    mocked_function.assert_any_call('direct_messages/welcome_messages/list')
    for message in messages_list_response['welcome_messages']:
        mocked_function.assert_any_call(
            'direct_messages/welcome_messages/destroy',
            {'id': message['id']}
        )


def test_set_welcome_message(mockdata, twitter_api_request, messages_new_response):
    with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
        current_app.twitter_bot.set_welcome_message()

    mocked_function.assert_any_call(
        'direct_messages/welcome_messages/rules/new',
        json_.dumps({
            'welcome_message_rule': {
                'welcome_message_id': messages_new_response['welcome_message']['id']
            }
        })
    )


def test_delete_webhooks(app, twitter_api_request, webhooks_list_response):
    with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
        current_app.twitter_bot.delete_all_webhooks()

    mocked_function.assert_any_call('account_activity/all/webhooks')
    mocked_function.assert_any_call(
        'account_activity/all/:{}/webhooks/:{}'.format(
            current_app.config['TWITTER_WEBHOOK_ENV'],
            webhooks_list_response['environments'][0]['webhooks'][0]['id']
        )
    )


def test_register_webhook(app, twitter_api_request, webhooks_list_response):
    with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
        current_app.twitter_bot.register_webhook()

    mocked_function.assert_any_call('account_activity/all/webhooks')
    mocked_function.assert_any_call(
        'account_activity/all/:{}/webhooks/:{}'.format(
            current_app.config['TWITTER_WEBHOOK_ENV'],
            webhooks_list_response['environments'][0]['webhooks'][0]['id']
        )
    )
    mocked_function.assert_any_call(
        'account_activity/all/:{}/webhooks'.format(current_app.config['TWITTER_WEBHOOK_ENV']),
        {'url': 'http://localhost:5000/webhooks/twitter'}
    )


def test_match_one_from_message(mockdata, session):
    officer = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr')
    session.add(officer)
    session.commit()

    text = '{} Ham A. McMuffin II {}'.format(
        lorem.sentence(), lorem.sentence())
    message_data = {
        'text': text,
        'entities': {
            'urls': []
        }
    }
    matched_officer = current_app.twitter_bot.match_one_from_message(message_data)
    assert matched_officer is not None
    assert matched_officer == officer


def test_match_multiple_from_message(mockdata, session):
    officer1 = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr')
    officer2 = Officer(
        first_name='Porkrinds',
        middle_initial='X',
        last_name='McFunyuns')
    session.add(officer1)
    session.add(officer2)
    session.commit()

    text = '{} Ham A. McMuffin II {} porkrinds x. mcfunyuns {}'.format(
        lorem.sentence(), lorem.sentence(), lorem.sentence())
    message_data = {
        'text': text,
        'entities': {
            'urls': []
        }
    }
    matched_officers = current_app.twitter_bot.match_from_message(message_data)
    assert matched_officers is not None
    assert len(matched_officers) == 2
    assert officer1 in matched_officers
    assert officer2 in matched_officers


def test_match_one_from_link(mockdata, session):
    officer = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr')
    session.add(officer)
    session.commit()

    link_text = '{} Ham A. McMuffin II {}'.format(
        lorem.text(), lorem.text())
    message_data = {
        'text': 'bacon',
        'entities': {
            'urls': [{'expanded_url': 'http://example.com'}]
        }
    }

    mocked_response = MagicMock(status_code=200, text=link_text)
    with patch('OpenOversight.app.twitterbot.requests.get', return_value=mocked_response) as mocked_function:
        matched_officer = current_app.twitter_bot.match_one_from_message(message_data)

    mocked_function.assert_called_once()
    assert matched_officer is not None
    assert matched_officer == officer


def test_match_multiple_from_link(mockdata, session):
    officer1 = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr')
    officer2 = Officer(
        first_name='Porkrinds',
        middle_initial='X',
        last_name='McFunyuns')
    session.add(officer1)
    session.add(officer2)
    session.commit()

    link_text = '{} Ham A. McMuffin II {} porkrinds x. mcfunyuns {}'.format(
        lorem.text(), lorem.text(), lorem.text())
    message_data = {
        'text': 'bacon',
        'entities': {
            'urls': [{'expanded_url': 'http://example.com'}]
        }
    }

    mocked_response = MagicMock(status_code=200, text=link_text)
    with patch('OpenOversight.app.twitterbot.requests.get', return_value=mocked_response) as mocked_function:
        matched_officers = current_app.twitter_bot.match_from_message(message_data)

    mocked_function.assert_called_once()
    assert matched_officers is not None
    assert len(matched_officers) == 2
    assert officer1 in matched_officers
    assert officer2 in matched_officers


def test_match_multiple_from_message_and_link(mockdata, session):
    officer1 = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr')
    officer2 = Officer(
        first_name='Porkrinds',
        middle_initial='X',
        last_name='McFunyuns')
    session.add(officer1)
    session.add(officer2)
    session.commit()

    message_text = '{} Ham A. McMuffin II {}'.format(
        lorem.text(), lorem.text())
    link_text = '{} porkrinds x. mcfunyuns {}'.format(
        lorem.text(), lorem.text())
    message_data = {
        'text': message_text,
        'entities': {
            'urls': [{'expanded_url': 'http://example.com'}]
        }
    }

    mocked_response = MagicMock(status_code=200, text=link_text)
    with patch('OpenOversight.app.twitterbot.requests.get', return_value=mocked_response) as mocked_function:
        matched_officers = current_app.twitter_bot.match_from_message(message_data)

    mocked_function.assert_called_once()
    assert matched_officers is not None
    assert len(matched_officers) == 2
    assert officer1 in matched_officers
    assert officer2 in matched_officers


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
def test_handle_mention_basic(mockdata, session, client, twitter_api_request):
    department_id = 1
    officer = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr',
        department_id=department_id)
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=department_id).filter(Job.job_title != "Not Sure").first()
    assignment = Assignment(
        officer_id=officer.id,
        star_no='1312',
        job_id=job.id,
        star_date=date(2020, 9, 1)
    )
    session.add(assignment)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "user_has_blocked": "false",
        "tweet_create_events": [
            {
                "created_at": "Wed Oct 10 20:19:24 +0000 2018",
                "id": 1050118621198921728,
                "id_str": "1050118621198921728",
                "text": "@openoversight @lucyparsonslabs tell me about Ham AndCheese McMuffin please.",
                "user": {
                    'id': 1337,
                    'screen_name': 'copwatcher',
                },
                "entities": {
                    'user_mentions': [
                        {
                            'id': 123456789,
                            'screen_name': 'openoversight'
                        },
                        {
                            'id': 987654321,
                            'screen_name': 'lucyparsonslabs'
                        }
                    ]
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        expected_tweet_text = (
            '@copwatcher @lucyparsonslabs {} Ham AndCheese. McMuffin Jr ({}). Full profile: {}.'
            .format(job.job_title, assignment.star_no, url_for('main.officer_profile', officer_id=officer.id, _external=True)))
        mocked_function.assert_any_call(
            'statuses/update',
            {
                'status': expected_tweet_text,
                'in_reply_to_status_id': payload['tweet_create_events'][0]['id']
            }
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.TwitterBot.generate_response')
def test_handle_tweet_no_mention(mocked_generate_response, mockdata, session, client, twitter_api_request):
    department_id = 1
    officer = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr',
        department_id=department_id)
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=department_id).filter(Job.job_title != "Not Sure").first()
    assignment = Assignment(
        officer_id=officer.id,
        star_no='1312',
        job_id=job.id,
        star_date=date(2020, 9, 1)
    )
    session.add(assignment)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "user_has_blocked": "false",
        "tweet_create_events": [
            {
                "created_at": "Wed Oct 10 20:19:24 +0000 2018",
                "id": 1050118621198921728,
                "id_str": "1050118621198921728",
                "text": "@lucyparsonslabs tell me about Ham AndCheese McMuffin please.",
                "user": {
                    'id': 1337,
                    'screen_name': 'copwatcher',
                },
                "entities": {
                    'user_mentions': [
                        {
                            'id': 987654321,
                            'screen_name': 'lucyparsonslabs'
                        }
                    ]
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_called_once_with('account/verify_credentials')
        mocked_generate_response.assert_not_called()


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
def test_handle_mention_quoted_status(mockdata, session, client, twitter_api_request):
    department_id = 1
    officer = Officer(
        first_name='Ham',
        middle_initial='AndCheese',
        last_name='McMuffin',
        suffix='Jr',
        department_id=department_id)
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=department_id).filter(Job.job_title != "Not Sure").first()
    assignment = Assignment(
        officer_id=officer.id,
        star_no='1312',
        job_id=job.id,
        star_date=date(2020, 9, 1)
    )
    session.add(assignment)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "user_has_blocked": "false",
        "tweet_create_events": [
            {
                "created_at": "Wed Oct 10 20:19:24 +0000 2018",
                "id": 1050118621198921728,
                "id_str": "1050118621198921728",
                "user": {
                    'id': 1337,
                    'screen_name': 'copwatcher',
                },
                "entities": {
                    'user_mentions': [
                        {
                            'id': 123456789,
                            'screen_name': 'openoversight'
                        }
                    ],
                    'urls': []
                },
                "text": "@openoversight check the quoted tweet",
                "is_quote_status": True,
                "quoted_status": {
                    "created_at": "Wed Oct 10 20:19:23 +0000 2018",
                    "id": 1050118621198921727,
                    "id_str": "1050118621198921727",
                    "user": {
                        'id': 1337,
                        'screen_name': 'copwatcher',
                    },
                    "entities": {
                        'user_mentions': [],
                        'urls': []
                    },
                    "text": "Ham AndCheese McMuffin stole my donut.",
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        expected_tweet_text = (
            '@copwatcher {} Ham AndCheese. McMuffin Jr ({}). Full profile: {}.'
            .format(job.job_title, assignment.star_no, url_for('main.officer_profile', officer_id=officer.id, _external=True)))
        mocked_function.assert_any_call(
            'statuses/update',
            {
                'status': expected_tweet_text,
                'in_reply_to_status_id': payload['tweet_create_events'][0]['id']
            }
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.TwitterBot.generate_response')
def test_handle_mention_no_match(mocked_generate_response, mockdata, session, client, twitter_api_request):
    payload = {
        "for_user_id": "2244994945",
        "user_has_blocked": "false",
        "tweet_create_events": [
            {
                "created_at": "Wed Oct 10 20:19:24 +0000 2018",
                "id": 1050118621198921728,
                "id_str": "1050118621198921728",
                "text": "@openoversight tell me about the Hamburgler.",
                "user": {
                    'id': 1337,
                    'screen_name': 'copwatcher',
                },
                "entities": {
                    'user_mentions': [
                        {
                            'id': 123456789,
                            'screen_name': 'openoversight'
                        }
                    ],
                    'urls': []
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request):
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_generate_response.assert_not_called()


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
def test_direct_message_name_search(mockdata, session, client, twitter_api_request):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
    )
    session.add(officer)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'text': 'Donut Eater',
                        'entities': {
                            'urls': []
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        mocked_function.assert_any_call(
            'direct_messages/events/new',
            {
                'type': 'message_create',
                'message_create': {
                    'target': {
                        'recipient_id': 987654321
                    },
                    'message_data': {
                        'text': "Here's what we found for your query \"Donut Eater\":\n\nDonut Eater. Full profile: {}.".format(
                            url_for('main.officer_profile', officer_id=officer.id, _external=True))
                    }
                }
            }
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.TwitterBot.get_account_id')
def test_direct_message_filter_sent(get_account_id, mockdata, client, twitter_api_request):
    get_account_id.return_value = 123456789
    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 123456789,
                    'target': {
                        'recipient_id': 987654321
                    },
                    'message_data': {
                        'text': 'dummy message',
                        'entities': {
                            'urls': []
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as api_request:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        get_account_id.assert_called_once_with()
        api_request.assert_not_called()


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
def test_direct_message_name_search_no_match(mockdata, client, twitter_api_request):
    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'text': 'Donut Eater',
                        'entities': {
                            'urls': []
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        mocked_function.assert_any_call(
            'direct_messages/events/new',
            {
                'type': 'message_create',
                'message_create': {
                    'target': {
                        'recipient_id': 987654321
                    },
                    'message_data': {
                        'text': "Sorry, we didn't find any matches for your query \"Donut Eater\"."
                    }
                }
            }
        )


def test_gen_tweet_no_assignments(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr'
    )
    session.add(officer)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut A. Eater Jr. Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_no_assignments_uii(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        unique_internal_identifier='666'
    )
    session.add(officer)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut A. Eater Jr (666). Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_job_title_not_sure(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        department_id=1
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title == 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id,
    )
    session.add(assignment)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut A. Eater Jr. Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_job_title_no_badge_no_uii(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        department_id=1
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id
    )
    session.add(assignment)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = '{} Donut A. Eater Jr. Full profile: http://localhost:5000/officer/{}.'.format(
        job.job_title, officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_job_title_badge(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        unique_internal_identifier='666',
        department_id=1
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id,
        star_no='1234'
    )
    session.add(assignment)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = '{} Donut A. Eater Jr (1234). Full profile: http://localhost:5000/officer/{}.'.format(
        job.job_title, officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_job_title_uii(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        unique_internal_identifier='666',
        department_id=1
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id,
    )
    session.add(assignment)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = '{} Donut A. Eater Jr (666). Full profile: http://localhost:5000/officer/{}.'.format(
        job.job_title, officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_salary(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        department_id=1
    )
    session.add(officer)
    session.flush()
    salary = Salary(
        officer_id=officer.id,
        salary=123456.78,
        overtime_pay=87654.32,
        year=2020,
        is_fiscal_year=False
    )
    session.add(salary)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut Eater made $211,111.10 in 2020. Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_one_incident(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        department_id=1
    )
    session.add(officer)
    session.flush()
    incident = Incident(
        date=date(2016, 3, 16),
        time=time(4, 20),
        report_number='42',
        description='A thing happened',
        department_id=1,
        officers=[officer],
    )
    session.add(incident)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut Eater. Eater was involved in 1 incident. Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_multiple_incidents(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        department_id=1
    )
    session.add(officer)
    session.flush()
    incident1 = Incident(
        date=date(2016, 3, 16),
        time=time(4, 20),
        report_number='42',
        description='A thing happened',
        department_id=1,
        officers=[officer],
    )
    incident2 = Incident(
        date=date(2016, 3, 16),
        time=time(4, 20),
        report_number='24',
        description='Another thing happened',
        department_id=1,
        officers=[officer],
    )
    session.add(incident1)
    session.add(incident2)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = 'Donut Eater. Eater was involved in 2 incidents. Full profile: http://localhost:5000/officer/{}.'.format(officer.id)
    assert tweet == expected_tweet


def test_gen_tweet_all(mockdata, session):
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        unique_internal_identifier='666',
        department_id=1
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id,
        star_no='1234'
    )
    session.add(assignment)
    salary = Salary(
        officer_id=officer.id,
        salary=123456.78,
        overtime_pay=87654.32,
        year=2020,
        is_fiscal_year=False
    )
    session.add(salary)
    incident1 = Incident(
        date=date(2016, 3, 16),
        time=time(4, 20),
        report_number='42',
        description='A thing happened',
        department_id=1,
        officers=[officer],
    )
    incident2 = Incident(
        date=date(2016, 3, 16),
        time=time(4, 20),
        report_number='24',
        description='Another thing happened',
        department_id=1,
        officers=[officer],
    )
    session.add(incident1)
    session.add(incident2)
    session.commit()

    tweet = generate_tweet(officer)
    expected_tweet = '{} Donut A. Eater Jr (1234) made $211,111.10 in 2020. Eater was involved in 2 incidents. Full profile: http://localhost:5000/officer/{}.'.format(
        job.job_title, officer.id)
    assert tweet == expected_tweet


def test_signed_metadata(app):
    app.config['SECRET_KEY'] = 'porkchops'
    metadata = {
        'department_id': 1,
        'step': 'foo'
    }
    signed_metadata = generate_signed_metadata(metadata)
    assert '"department_id": 1' in signed_metadata
    assert '"step": "foo"' in signed_metadata
    assert '"digest": "7d7b29c4b029c468128a640e28c9f872af278f7d968db2e0a74149419d9cf213"' in signed_metadata

    unpacked_metadata = unpack_signed_metadata(signed_metadata)
    assert unpacked_metadata == metadata


def test_conversation_init(app):
    ''' Make sure it can load module classes and instatiate steps without throwing an Exception '''
    Conversation({'step': 'ConversationStep0'})
    Conversation({'step': 'ConversationStep1'})
    Conversation({'step': 'ConversationStep2'})
    Conversation({'step': 'ConversationStep3'})
    Conversation({'step': 'ConversationStep4'})
    Conversation({'step': 'ConversationStep5'})


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_text_input_response')
def test_conversation_step_0(create_text_input_response, unpack_signed_metadata, mockdata, client, twitter_api_request):
    metadata = {'step': 'ConversationStep0'}
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_text_input_response.assert_any_call(
            "Do you remember any part of the Officer's last name?",
            "Officer last name",
            metadata
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_text_input_response')
def test_conversation_step_1_uii(create_text_input_response, unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    department_id = 1
    metadata = {
        'step': 'ConversationStep1',
        'department_id': department_id
    }
    unpack_signed_metadata.return_value = metadata

    department = Department.query.filter_by(id=department_id).one()
    department.unique_internal_identifier_label = 'Sequence Number'
    session.add(department)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'text': 'Bacon',
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_text_input_response.assert_any_call(
            "Do you know any part of the Officer's Sequence Number",
            "Sequence Number",
            metadata
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_text_input_response')
def test_conversation_step_1_badge(create_text_input_response, unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    department_id = 1
    metadata = {
        'step': 'ConversationStep1',
        'department_id': department_id,
    }
    unpack_signed_metadata.return_value = metadata

    department = Department.query.filter_by(id=department_id).one()
    department.unique_internal_identifier_label = None
    session.add(department)
    session.commit()

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'text': 'Bacon',
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_text_input_response.assert_any_call(
            "Do you remember any part of the Officer's badge number?",
            "Badge number",
            metadata
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_options_response')
def test_conversation_step_2(create_options_response, unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    department_id = 1
    metadata = {
        'step': 'ConversationStep2',
        'department_id': department_id,
    }
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'text': '666',
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    options = [{
        'label': rank.job_title,
        'metadata': {
            'badge_or_uii': '666',
            'rank_id': rank.id
        }.update(metadata)
    } for rank in Job.query.filter_by(department_id=department_id).filter_by(is_sworn_officer=True).all()]

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_options_response.assert_any_call(
            "Do you know the Officer's rank?",
            options
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_options_response')
def test_conversation_step_3(create_options_response, unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    metadata = {
        'step': 'ConversationStep3',
    }
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    options = [{
        'label': race[1],
        'metadata': {
            'race': race[0]
        }.update(metadata)
    } for race in RACE_CHOICES]

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_options_response.assert_any_call(
            "Do you know the Officer's race?",
            options
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
@patch('OpenOversight.app.twitterbot.ConversationStep.create_options_response')
def test_conversation_step_4(create_options_response, unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    metadata = {
        'step': 'ConversationStep4',
    }
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    options = [{
        'label': gender[1],
        'metadata': {
            'gender': gender[0]
        }.update(metadata)
    } for gender in GENDER_CHOICES]

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        create_options_response.assert_any_call(
            "Do you know the Officer's gender?",
            options
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
def test_conversation_step_5(unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    department_id = 1
    department = Department.query.filter_by(id=department_id).one()
    department.unique_internal_identifier_label = None
    session.add(department)
    officer = Officer(
        first_name='Donut',
        last_name='Eater',
        middle_initial='A',
        suffix='Jr',
        unique_internal_identifier='666',
        department_id=department_id,
        gender='M',
        race='BLACK'
    )
    session.add(officer)
    session.flush()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()
    assignment = Assignment(
        officer_id=officer.id,
        job_id=job.id,
        star_no='1234'
    )
    session.add(assignment)
    session.commit()

    metadata = {
        'step': 'ConversationStep5',
        'department_id': department_id,
        'race': 'BLACK',
        'gender': 'M',
        'rank_id': job.id,
        'last_name': 'Eater',
        'badge_or_uii': '1234'
    }
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        mocked_function.assert_any_call(
            'direct_messages/events/new',
            {
                'type': 'message_create',
                'message_create': {
                    'target': {
                        'recipient_id': 987654321
                    },
                    'message_data': {
                        'text': "Here's what we found:\n\n{} Donut A. Eater Jr (1234). Full profile: http://localhost:5000/officer/{}.".format(
                            job.job_title, officer.id)
                    }
                }
            }
        )


@patch('twitterwebhooks.server.WebhookServer.verify_request', MagicMock(return_value=True))
@patch('OpenOversight.app.twitterbot.unpack_signed_metadata')
def test_conversation_step_5_no_match(unpack_signed_metadata, mockdata, session, client, twitter_api_request):
    department_id = 1
    department = Department.query.filter_by(id=department_id).one()
    department.unique_internal_identifier_label = None
    session.add(department)
    session.commit()
    job = Job.query.filter_by(department_id=1).filter(Job.job_title != 'Not Sure').first()

    metadata = {
        'step': 'ConversationStep5',
        'department_id': department_id,
        'race': 'BLACK',
        'gender': 'M',
        'rank_id': job.id,
        'last_name': 'Robocop',
        'badge_or_uii': '1337'
    }
    unpack_signed_metadata.return_value = metadata

    payload = {
        "for_user_id": "2244994945",
        "direct_message_events": [
            {
                'type': 'message_create',
                'message_create': {
                    'sender_id': 987654321,
                    'target': {
                        'recipient_id': 123456789
                    },
                    'message_data': {
                        'quick_reply_response': {
                            'type': 'options',
                            'metadata': 'foo'
                        }
                    }
                }
            }
        ]
    }

    with current_app.test_request_context():
        with patch('OpenOversight.app.twitterbot.TwitterBot.api_request', side_effect=twitter_api_request) as mocked_function:
            route = url_for('event')
            rv = client.post(
                route,
                data=json_.dumps(payload),
                content_type='application/json',
                follow_redirects=True
            )
        assert rv.status_code == 200
        assert len(rv.data.decode('utf-8')) == 0
        mocked_function.assert_any_call('account/verify_credentials')
        mocked_function.assert_any_call(
            'direct_messages/events/new',
            {
                'type': 'message_create',
                'message_create': {
                    'target': {
                        'recipient_id': 987654321
                    },
                    'message_data': {
                        'text': "Sorry, we didn't find any matches!"
                    }
                }
            }
        )
