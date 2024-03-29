from boondi.routes import ControllerPrefixRoute as Controller, ActionRoute as Action


routes = [
    Controller("apps.trackr.app",   '/bkend', [
        Action('settings',              '/settings'),
        Action('create_payment',        '/payment/create'),
        Action('cancel_payment',        '/payment/cancel'),
        Action('entry',                 '/entry'),
        Action('new_invoice',           '/new_invoice'),
        Action('update_agent',          '/update_agent'),
    ]),

    Controller("apps.trackr.google",    '/bkend/google', [
        Action('auth_url',                  '/auth_url'),
        Action('authorize',                 '/authorize')
    ]),

    Controller("sys.accounts",  '/sys/accounts', [
        Action('new',               '/new'),
        Action('add_user',          '/add_user')
    ]),

    Controller("sys.prod",      '/sys/prod', [
        Action('show_config',       '/config')
    ]),

    Controller('auth',          '/auth', [
        Action('login',             '/login'),
        Action('refresh_auth',      '/refresh'),
        Action('get_auth',          '/'),
        Action('reset',             '/reset'),
        Action('change',            '/change'),
        Action('toggle_demo',        '/toggle_demo'),
    ]),

    Controller('home',          '/auth', [
        Action('logout',            '/logout'),
    ]),
]
