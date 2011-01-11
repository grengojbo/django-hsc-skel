#--- Вывод в консоль разработки
log =
    info: (msg) ->
        @log(msg, 'info')

    debug: (msg) ->
        @log(msg, 'debug')

    error: (msg) ->
        @log(msg, 'error')

    dir: (obj) ->
        console.dir(obj) if console? and console.log?
    
    log: (msg, type='log') ->
        if console? and console.log?
            switch type
                when "debug" then console.log msg
                when "info" then console.info msg
                when "error" then console.error msg
                else console.log msg

window.log = log