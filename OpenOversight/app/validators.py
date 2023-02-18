from urllib.parse import urlparse

from us import states


def state_validator(state):
    list_of_states = [st.abbr for st in states.STATES]

    if state not in list_of_states and state != "DC" and state is not None:
        raise ValueError("Not a valid US state")

    return state


def url_validator(url):
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Not a valid URL")

    return url
