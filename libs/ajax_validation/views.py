from libs.decorators import ajax_request


@ajax_request
def validate(request, form_class):
    if form_class is not None:
        form = form_class(request.POST)
        form.is_valid()
        return form.errors
