/**
 * Created by vinuth on 29/10/15.
 */
/* exported UTILS_LIB */

var fbase = {};
fbase.orgId = '';
fbase.root = new Firebase('https://trackrapp.firebaseio.com/');

fbase.queueDB = fbase.root.child('/queue/tasks');
fbase.queue = function(spec, task) {
    task.org = 'default_org';
    task._state = spec;
    fbase.queueDB.push(task);
};


setInterval(function(){
    superagent.post('/auth/refresh').end(function(){});
}, 3600000);

var ScriptRunner = (function() {
    var queue = [], is_auth_checked=false, auth_checked_queue=[], authData=null;

    return {
        onAuth: function(func) {
            queue.push(func);
        },

        onAuthReady: function(func) {
            if(is_auth_checked) {
                func(authData);
            }
            else {
                auth_checked_queue.push(func);
            }
        },

        markAuthReady: function(authDataP) {
            authData = authDataP;
            is_auth_checked = true;
            for(var i = 0; i < auth_checked_queue.length; i++) {
                auth_checked_queue[i](authData);
            }
        },

        callAuth: function(authData) {
            for(var i = 0; i < queue.length; i++) {
                queue[i](authData);
            }
        }
    };
})();
var onAuth = ScriptRunner.onAuth;
var onAuthReady = ScriptRunner.onAuthReady;

window.addEventListener('storage', function(e) {
    if (e.key === 'baseAuth') {
        ScriptRunner.callAuth(JSON.parse(e.newValue));
    }
    else if (e.key === 'isDemo') {
        location.reload();
    }
});


function _login() {
    window.location = 'app.html';
}

function _logout() {
    window.location = '/';
}

function login(authData) {
    if(!authData) {
        return;
    }

    fbase.root.authWithCustomToken(authData.fbaseToken, function(error, fbaseAuthData) {
        if (error) {
        } else {
            localStorage.setItem('baseAuth', JSON.stringify(authData));
            _login();
        }
    }, {
        remember: 'sessionOnly'
    });
}

onAuth(function(authData) {
    if(authData) {
        var fbaseAuthData = fbase.root.getAuth();
        if(fbaseAuthData) {
            _login();
        }
    }
    else {
        _logout();
    }
});

superagent.get('/auth/').end(function(err, res) {
    if(res.ok && res.body.status === 'success') {
        superagent.post('/auth/refresh').end(function() {
            var fbaseAuthData = fbase.root.getAuth();
            if(!fbaseAuthData) {
                login(res.body);
                return;
            }

            var existingAuth = JSON.parse(localStorage.getItem('baseAuth'));

            if(existingAuth && existingAuth.user !== res.body.user) {
                login(res.body);
                return;
            }

            if(fbaseAuthData.uid !== existingAuth.user) {
                login(res.body);
                return;
            }

            var cookieDemo = Cookies.get('is_demo') === 'True';
            var isDemo = (localStorage.getItem('isDemo') === 'true');

            if(cookieDemo !== isDemo) {
                localStorage.setItem('isDemo', cookieDemo);
                location.reload();
            }

            fbase.orgId = Cookies.get('org_id');
            if(isDemo) {
                fbase.orgId += '_demo';
            }

            fbase.db = fbase.root.child(fbase.orgId);
            fbase.log = fbase.db.child('activities');

            fbase.root.onAuth(function(authData) {
                if (!authData) {
                    localStorage.setItem('baseAuth', null);
                    _logout();
                }
            });

            ScriptRunner.markAuthReady(res.body);
        });
    }
    else {
        if(localStorage.getItem('baseAuth') !== null) {
            localStorage.removeItem('baseAuth');
        }
        ScriptRunner.markAuthReady(null);
    }
});
