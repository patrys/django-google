# django-google #

This project currently implements Google Calendar API as django objects. More APIs are likely to appear in the future.

## Authentication ##

There are two ways to specify authentication info.

### Using credentials ###

You need to pass both `email` and `password` to the `Account` object constructor:

```
import google

foo = google.models.Account(username = 'example@gmail.com', password = 'plaintext')
foo.save()
```

Please note that both full Google addresses and user names are supported.

### Using auth tokens ###

This should be the preferred method for hosted services as it does not require you to store the credentials in your database. To obtain a single use token, ask the user to click a link provided by the `google_calendar_auth` tag:

```
{% load google_tags %}

In order to use calendar functions <a href="{% google_calendar_auth "http://example.com/calendar/token/" %}">authenticate with Google</a>.
```

The only parameter passed to the tag is the full URI of the view the user will be redirected to once authentication is complete. If access is allowed, `request.GET` will containt the single use `token`.

In order to use the API you need the exchange the single use token to a session token and pass it to the `Account` object constructor:

```
import google

token = google.utils.upgrade_token(request.GET['token'])
foo = google.models.Account(token = token)
foo.save()
```