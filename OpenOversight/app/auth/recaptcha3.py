# Adapted from https://github.com/rlid/flask-recaptcha
import requests
from flask import Markup, current_app, json, request
from wtforms import ValidationError
from wtforms.fields import HiddenField
from wtforms.widgets import HiddenInput

JSONEncoder = json.JSONEncoder

RECAPTCHA_TEMPLATE = '''
<script src='https://www.google.com/recaptcha/api.js?render={public_key}&onload=executeRecaptcha{action}' async defer></script>
<script>
  var executeRecaptcha{action} = function() {{
    console.log("grecaptcha is ready!");
    grecaptcha.execute('{public_key}', {{action: '{action}'}}).then(function(token) {{
      console.log(token);
      document.getElementById("{field_name}").value = token;
    }});
  }};
</script>
<input type="hidden" id="{field_name}" name="{field_name}">
'''

RECAPTCHA_TEMPLATE_MANUAL = '''
<script src='https://www.google.com/recaptcha/api.js?render={public_key}' async defer></script>
<script>
  var executeRecaptcha{action} = function() {{
    console.log("executeRecaptcha{action}() is called!");
    grecaptcha.ready(function() {{
      console.log("grecaptcha is ready!");
      grecaptcha.execute('{public_key}', {{action: '{action}'}}).then(function(token) {{
        console.log(token);
        document.getElementById("{field_name}").value = token;
      }});
    }});
  }};
</script>
<input type="hidden" id="{field_name}" name="{field_name}">
'''

RECAPTCHA_VERIFY_SERVER = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_ERROR_CODES = {
    'missing-input-secret': 'The secret parameter is missing.',
    'invalid-input-secret': 'The secret parameter is invalid or malformed.',
    'missing-input-response': 'The response parameter is missing.',
    'invalid-input-response': 'The response parameter is invalid or malformed.'
}


def is_recaptcha_enabled():
    return current_app.config['RECAPTCHA3_PUBLIC_KEY'] and current_app.config['RECAPTCHA3_PRIVATE_KEY']


class Recaptcha3Validator(object):
    """Validates a ReCaptcha."""

    def __init__(self, message=None):
        if message is None:
            message = "We are not able to accept your registration at this time."
        self.message = message

    def __call__(self, form, field):
        if current_app.testing or not is_recaptcha_enabled():
            return True

        token = field.data
        if not token:
            current_app.logger.warning("Token is not ready or incorrect configuration (check JavaScript error log).")
            raise ValidationError(field.gettext(self.message))

        remote_ip = request.remote_addr
        if not Recaptcha3Validator._validate_recaptcha(field, token, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(field.gettext(self.message))

    @staticmethod
    def _validate_recaptcha(field, response, remote_addr):
        """Performs the actual validation."""
        if not is_recaptcha_enabled():
            return True

        try:
            private_key = current_app.config['RECAPTCHA3_PRIVATE_KEY']
        except KeyError:
            raise RuntimeError("RECAPTCHA3_PRIVATE_KEY is not set in app config.")

        data = {
            'secret': private_key,
            'remoteip': remote_addr,
            'response': response
        }

        http_response = requests.post(RECAPTCHA_VERIFY_SERVER, data)
        if http_response.status_code != 200:
            return False

        json_resp = http_response.json()
        if json_resp["success"] and json_resp["action"] == field.action and json_resp["score"] > field.score_threshold:
            current_app.logger.info(json_resp)
            return True
        else:
            current_app.logger.warning(json_resp)

        for error in json_resp.get("error-codes", []):
            if error in RECAPTCHA_ERROR_CODES:
                raise ValidationError(RECAPTCHA_ERROR_CODES[error])

        return False


class Recaptcha3Widget(HiddenInput):

    def __call__(self, field, **kwargs):
        """Returns the recaptcha input HTML."""
        if not is_recaptcha_enabled():
            return ''

        public_key_name = 'RECAPTCHA3_PUBLIC_KEY'
        try:
            public_key = current_app.config[public_key_name]
        except KeyError:
            raise RuntimeError(f"{public_key_name} is not set in app config.")

        return Markup(
            (RECAPTCHA_TEMPLATE if field.execute_on_load else RECAPTCHA_TEMPLATE_MANUAL).format(
                public_key=public_key, action=field.action, field_name=field.name))


class Recaptcha3Field(HiddenField):
    widget = Recaptcha3Widget()

    # error message if recaptcha validation fails
    recaptcha_error = None

    def __init__(self, action, score_threshold=0.5, execute_on_load=True, validators=None, **kwargs):
        '''If execute_on_load is False, recaptcha.execute needs to be manually bound to an event to obtain token,
        the JavaScript function to call is executeRecaptcha{action}, e.g. onsubmit="executeRecaptchaSignIn" '''
        if not action:
            # TODO: more validation on action, see https://developers.google.com/recaptcha/docs/v3#actions
            #   "actions may only contain alphanumeric characters and slashes, and must not be user-specific"
            raise RuntimeError("action must not be none or empty.")

        self.action = action
        self.execute_on_load = execute_on_load
        self.score_threshold = score_threshold
        validators = validators or [Recaptcha3Validator()]
        super(Recaptcha3Field, self).__init__(validators=validators, **kwargs)
