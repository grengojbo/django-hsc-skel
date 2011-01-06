===============
django-hsc-skel
===============

Установка зависимостей
======================

Node.JS
-------
::

    sudo apt-get install nodejs

Установите пакетный менеджер NPM для Node.JS по инструкции `node-and-npm-in-30-seconds.sh <https://gist.github.com/579814>`_

Compass и SASS
--------------
::

    sudo apt-get install ruby rubygems
    sudo gem install compass --no-rdoc --no-ri

Откройте файл setting/local.py и пропишите в переменных COMPASS_BIN, SASS_BIN, COFFEE_PATH пути к соответствующим утилитам.

Последний этап
--------------
::

    pip install -r REQUIREMENTS
    ./manage.py build_static

Запуск
======

Просто выполните команду::

    ./manage.py runserver

что бы посмотреть `демо-страницу <http://127.0.0.1:8000 >`_.

