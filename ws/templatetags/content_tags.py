import json

from django import template

from ws import settings

register = template.Library()


@register.inclusion_tag('for_templatetags/cdn_fallback.html')
def cdn_fallback(lib_name, cdn_url, npm_path):
    """ Load the package from a CDN, but fall back to local service on failure. """
    return {'lib_name': lib_name,
            'cdn_url': cdn_url,
            'npm_path': npm_path}


@register.inclusion_tag('for_templatetags/raven_user_context.html', takes_context=True)
def raven_user_context(context, user, participant):
    """ Include JavaScript that should only be present in production. """
    user_context = {}
    if user and user.is_authenticated:
        user_context['email'] = user.email
        if participant:
            user_context['participant_id'] = participant.pk
            user_context['name'] = participant.name

    return {'DEBUG': settings.DEBUG, 'user_context': json.dumps(user_context)}
