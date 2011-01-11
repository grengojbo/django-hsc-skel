_ajax_validate_form = null

ajax_validate = (form) ->
    _ajax_validate_form  = form
    form.find('span.error').remove()
    $.post(form.data('ajax-validate-url'), form.serialize(), _ajax_validate_callback, 'json')
    
_ajax_validate_callback = (data, textStatus, XMLHttpRequest) ->
    if _ajax_validate_form!=null and data.status=="ok"
        log.debug 'validate callback'
        i=0
        for key of data.response
            i+=1
            el = _ajax_validate_form.find('input[name='+key+']')
            el.before('<span class="error">'+data.response[key].join(' ')+'</span><div class="clearfix"></div>')
        if data.response.__all__!=undefined
            main_el = _ajax_validate_form.find('div.form')
            main_el.prepend('<span class="error">'+data.response[key].join(' ')+'</span><div class="clearfix"></div>')
        if i==0
            log.debug 'no errors'
            _ajax_validate_form.submit()
        else
            log.debug i+' errors'

