from boondi.routes import ControllerPrefixRoute as Controller, ActionRoute as Action


routes = [
    Controller("apps.trackr",   '/bkend/trackr', [
        Action('app_settings',      '/app_settings'),
        Action('create_payment',    '/payment/create'),
        Action('cancel_payment',    '/payment/cancel'),
        Action('entry',             '/entry'),
        Action('new_invoice',       '/new_invoice'),
        Action('update_agent',      '/update_agent'),
    ]),

    Controller("sys.accounts",  '/sys/accounts', [
        Action('new',               '/new')
    ]),

    Controller('auth',          '/auth', [
        Action('login',             '/login'),
        Action('refresh_auth',      '/refresh'),
        Action('get_auth',          '/'),
        Action('reset',             '/reset'),
        Action('change',            '/change'),
    ]),

    Controller('home',          '/auth', [
        Action('logout',            '/logout'),
    ]),
]
