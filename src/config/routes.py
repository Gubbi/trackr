from boondi.routes import ControllerPrefixRoute as Controller, ActionRoute as Action


routes = [
    Controller('auth', '/auth', [
        Action('login',                '/login'),
        Action('refresh_auth',         '/refresh'),
        Action('get_auth',             '/'),
        Action('reset',                '/reset'),
        Action('change',               '/change'),
    ]),

    Controller('home', '/auth', [
        Action('logout', '/logout'),
    ]),

    Controller("sys.accounts", '/sys/accounts', [
        Action('new',       '/new')
    ]),
]
