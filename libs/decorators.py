#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
import inspect

from annoying.decorators import *
from coffin.shortcuts import render_to_response
from coffin.template import RequestContext
from django.utils.functional import wraps

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
