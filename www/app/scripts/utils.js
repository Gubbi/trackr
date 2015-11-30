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
            if(is_auth_checked) func(authData);
            else auth_checked_queue.push(func);
        },

        markAuthReady: function(authDataP) {
            authData = authDataP;
            is_auth_checked = true;
            for(var i = 0; i < auth_checked_queue.length; i++) auth_checked_queue[i](authData);
        },

        callAuth: function(authData) {
            for(var i = 0; i < queue.length; i++) queue[i](authData);
        }
    }
})();
var onAuth = ScriptRunner.onAuth;
var onAuthReady = ScriptRunner.onAuthReady;

window.addEventListener('storage', function(e) {
    if (e.key === 'baseAuth') {
        ScriptRunner.callAuth(JSON.parse(e.newValue));
    }
});


function _login() {
    window.location = 'app.html';
}

function _logout() {
    console.log('logging out');
    window.location = '/';
}

function setLoginCookies(authData) {
    Cookies.set('org_id', authData.org);
}

function login(authData) {
    console.log(authData);

    if(!authData) return;

    fbase.root.authWithCustomToken(authData.fbase_token, function(error, fbaseAuthData) {
        console.log(fbaseAuthData);

        if (error) {
            console.log('Login Failed!', error);
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
        console.log('Page logged out from somewhere');
        _logout();
    }
});

superagent.get('/auth/').end(function(err, res) {
    console.log(res.body);
    if(res.ok && res.body.status === 'success') {
        superagent.post('/auth/refresh').end(function() {
            var fbaseAuthData = fbase.root.getAuth();
            if(!fbaseAuthData) {
                login(res.body);
            }

            console.log(fbaseAuthData);

            var existingAuth = JSON.parse(localStorage.getItem('baseAuth'));

            if(existingAuth && existingAuth.user !== res.body.user) {
                console.log('Data stored different from logged in user.');
                login(res.body);
            }

            if(fbaseAuthData.uid !== existingAuth.user) {
                console.log('Fbase logged in user is different from current user.');
                login(res.body);
            }

            setLoginCookies(res.body);
            fbase.orgId = Cookies.get('org_id');
            fbase.db = fbase.root.child(fbase.orgId);
            fbase.log = fbase.db.child('activities');

            fbase.root.onAuth(function(authData) {
                if (!authData) {
                    Cookies.expire('org_id');
                    localStorage.setItem('baseAuth', null);
                    console.log('No auth data found during this fbase auth event. Logging out.');
                    _logout();
                }
            });

            ScriptRunner.markAuthReady(res.body);
        });
    }
    else {
        console.log('Auth check: ' + res.body.message);
        if(localStorage.getItem('baseAuth') !== null) {
            localStorage.removeItem('baseAuth');
        }
        ScriptRunner.markAuthReady(null);
    }
});
