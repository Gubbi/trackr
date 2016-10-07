from boondi.routes import ControllerPrefixRoute as Controller, ActionRoute as Action


routes = [
    Controller("apps.trackr.app",   '/bkend', [
        Action('settings',                '/settings'),
        Action('payment_request',         '/payment/create'),
        Action('cancel_payment',          '/payment/cancel'),
        Action('entry',                   '/entry'),
        Action('new_invoice',             '/new_invoice'),
        Action('update_agent',            '/update_agent'),
        Action('verify_jobs',             '/verify_jobs'),
        Action('search_provider',         '/search_provider'),
        Action('get_acl',                 '/acl'),
        Action('get_api_id',              '/api_id'),
        Action('file_upload',             '/upload'),
        Action('generate_codes',          '/codes'),
    ]),

    Controller('apps.trackr.storage', '/storage', [
        Action('get', '/test'),
    ]),

    Controller("apps.trackr.callback", '/bkend', [
        Action('handle_payment',             '/payment/callback/<org_id>'),
    ]),

    Controller("apps.trackr.google_auth",    '/bkend/google', [
        Action('auth_url',                           '/auth_url'),
        Action('authorize',                          '/authorize')
    ]),

    Controller("apps.trackr.accounts",  '/bkend/accounts', [
        Action('list_users',                           '/list'),
        Action('add_user',                             '/add'),
        Action('remove_user',                          '/remove'),
    ]),

    Controller("sys.accounts",  '/sys/accounts', [
        Action('new',               '/new'),
        Action('add_user',          '/add_user')
    ]),

    Controller("sys.bigquery",  '/sys/bigquery', [
        Action('check_job_status',          '/status')
    ]),

    Controller("sys.prod",      '/sys/prod', [
        Action('show_config',       '/config')
    ]),

    Controller("sys.batch.transactions",      '/sys/batch', [
        Action('verify_uploaded_jobs',       '/verify'),
        Action('generate_kyash_codes',       '/codes')
    ]),

    Controller('auth',          '/auth', [
        Action('login',              '/login'),
        Action('refresh_auth',       '/refresh'),
        Action('get_auth',           '/'),
        Action('reset',              '/reset'),
        Action('change',             '/change'),
        Action('toggle_demo',        '/toggle_demo'),
    ]),

    Controller('home',          '/auth', [
        Action('logout',             '/logout'),
    ]),

]
