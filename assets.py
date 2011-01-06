#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from django_assets import Bundle, register
js = Bundle('coffee/sample.coffee', filters='coffeescript', output='gen/base.js')
css = Bundle('scss/screen.scss', 'scss/print.scss', 'scss/ie.scss', filters='compass', output='gen/base.css')

register('base.js', js)
register('base.css', css)