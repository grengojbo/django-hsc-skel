#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
import logging

from coffin.shortcuts import render_to_response
from coffin.template import RequestContext
from django.http import HttpResponse
from django.utils.functional import wraps
from annoying.decorators import *


def render_to(template=None, mimetype="text/html"):
    def renderer(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            output = function(request, *args, **kwargs)
            if not isinstance(output, dict):
                return output
            tmpl = output.pop('TEMPLATE', template)
            return render_to_response(tmpl, output, \
                        context_instance=RequestContext(request), mimetype=mimetype)
        return wrapper
    return renderer


def ajax_request(func):
    """
    If view returned serializable dict, returns JsonResponse with this dict as content.

    example:

        @ajax_request
        def my_view(request):
            news = News.objects.all()
            news_titles = [entry.title for entry in news]
            return {'news_titles': news_titles}
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            response = func(request, *args, **kwargs)
            if isinstance(response, HttpResponse):
                return response
        except Exception, e:
            logging.error('AJAX - %s raises %s: %s', func.func_name, str(e.__class__), e.message)
            return JsonResponse({'status': 'error', 'response': '%s: %s' % (str(e.__class__), e.message)})
        else:
            return JsonResponse({'status': 'ok', 'response': response})

    return wrapper