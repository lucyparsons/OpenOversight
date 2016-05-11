# Deployment

When this application is deployed you should do some extra things.

## CSRF attacks

Change the ***REMOVED*** key used for generating tokens to prevent cross-site request forgery (CSRF) attacks in `config.py`:

```
WTF_CSRF_ENABLED = True
SECRET_KEY = 'changemeplzorelsehax'
```
