import webapp2
import sys
import os

# Add packages in lib_dir to the path, along with lib_dir and app_dir.
app_dir = 'src'
lib_dir = "lib/"
sys.path = [app_dir, lib_dir] + ['%s/%s' % (lib_dir, n) for n in os.listdir(lib_dir) if n.endswith('.egg')] + sys.path
sys.path.append("lib/suds.zip")

# Workaround for latest setuptools importing mkdir
os.mkdir = lambda *x: None

from boondi.ext import custom_dispatcher
from config.routes import routes

app = webapp2.WSGIApplication(routes, debug=True)
app.router.set_dispatcher(custom_dispatcher)


def system_requests(request, *args, **kwargs):
    return webapp2.Response('Done.')


sys = webapp2.WSGIApplication([
    (r'/.*', system_requests),
])
