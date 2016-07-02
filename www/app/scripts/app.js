/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

var pageBasePath = '/app.html';
onAuthReady(function(authData) {
    if(!authData) {
      _logout();
    }
});

(function(document) {
  'use strict';

  // Grab a reference to our auto-binding template
  // and give it some initial binding values
  // Learn more about auto-binding templates at http://goo.gl/Dx1u2g
  var app = document.querySelector('#app');
  app.showingSearch = false;

  app.demo = (localStorage.getItem('isDemo') === 'true');
  app.isAdmin = false;
  app.isOps = true;

  app.demoToggle = function() {
    superagent.post('/auth/toggle_demo').end(function(err, res) {
      if (res.ok) {
        localStorage.setItem('isDemo', res.body.isDemo);
        location.reload();
      }
    });
    return false;
  };

  app.displayInstalledToast = function() {
    document.querySelector('#caching-complete').show();
  };

  // Listen for template bound event to know when bindings
  // have resolved and content has been stamped to the page
  app.addEventListener('dom-change', function() {

  });

  // See https://github.com/Polymer/polymer/issues/1381
  window.addEventListener('WebComponentsReady', function() {
    // imports are loaded and elements have been registered
  });

  // Close drawer after menu item is selected if drawerPanel is narrow
  app.onMenuSelect = function() {
    var drawerPanel = document.querySelector('#paperDrawerPanel');
    if (drawerPanel && drawerPanel.narrow) {
      drawerPanel.closeDrawer();
    }
  };

  app._computeListWidth = function(isMobile) {
    // when in mobile screen size, make the list be 100% width to cover the whole screen
    return isMobile ? '100%' : '400px';
  };

  app._mediumTall = function(headerClass) {
    return 'medium-tall ' + headerClass;
  };

  app._search = function(data) {
    app.fire('search', data.detail, {node: document.querySelector('#'+app.route)});
  };

  app._displayInPanel = function(el) {
    var more = app.$.moreActivity;
    while (more.firstChild) {
        more.removeChild(more.firstChild);
    }
    more.appendChild(el);

    app.$.mainDrawerPanel.openDrawer();
    ['updated', 'cancelled'].forEach(function(event) {
      el.addEventListener(event, function() {
        app.fire(event, {}, {node: document.querySelector('#'+app.route)});
        app.$.mainDrawerPanel.closeDrawer();
      });
    });
  };

  addEventListener('create-account', function(e) {
    app.subTitle = 'New Account';
    var el = document.createElement('user-edit');

    el.user = {'roles': []};
    app._displayInPanel(el);
  });

  addEventListener('set-title', function(e) {
    app.titlePage = e.detail;
  });

  addEventListener('set-title-nav', function(e) {
    app.titleNav = e.detail;
  });

  app.searchon = function(searchon) {
    if(document.querySelector('#search')) {
      document.querySelector('#search').placeholder = searchon;
    }
  };

  app.disableSearch = function() {
    if(document.querySelector('#search')) {
      document.querySelector('#search').enabled = false;
    }
  };

  app.enableSearch = function() {
    if(document.querySelector('#search')) {
      document.querySelector('#search').enabled = true;
    }
  };

  onAuthReady(function(authData) {
      if(authData) {
        app.isAdmin = fbase.acl.indexOf('Admin') > -1;
        app.isOps = fbase.acl.indexOf('Ops') > -1;
      }
  });
})(document);
