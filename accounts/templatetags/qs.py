from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, page):
    """Build a ?...&page=N URL that preserves the current filters/search."""
    params = context['request'].GET.copy()
    params['page'] = page
    return '?' + params.urlencode()
