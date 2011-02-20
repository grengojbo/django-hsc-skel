#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from django_assets import Bundle, register

js = Bundle('coffee/sample.coffee', filters='coffeescript', output='gen/all.js')

css = Bundle('scss/screen.scss', 'scss/print.scss', 'scss/ie.scss', filters='compass', output='gen/all.css')

register('all.js', js)
register('all.css', css)