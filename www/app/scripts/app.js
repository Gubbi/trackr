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

  // Main area's paper-scroll-header-panel custom condensing transformation of
  // the appName in the middle-container and the bottom title in the bottom-container.
  // The appName is moved to top and shrunk on condensing. The bottom sub title
  // is shrunk to nothing on condensing.
  // addEventListener('paper-header-transform', function(e) {
  //   var appName = document.querySelector('.app-name');
  //   var middleContainer = document.querySelector('.middle-container');
  //   var bottomContainer = document.querySelector('.bottom-container');
  //   var detail = e.detail;
  //   var heightDiff = detail.height - detail.condensedHeight;
  //   var yRatio = Math.min(1, detail.y / heightDiff);
  //   var maxMiddleScale = 0.50;  // appName max size when condensed. The smaller the number the smaller the condensed size.
  //   var scaleMiddle = Math.max(maxMiddleScale, (heightDiff - detail.y) / (heightDiff / (1-maxMiddleScale))  + maxMiddleScale);
  //   var scaleBottom = 1 - yRatio;
  //
  //   // Move/translate middleContainer
  //   Polymer.Base.transform('translate3d(0,' + yRatio * 100 + '%,0)', middleContainer);
  //
  //   // Scale bottomContainer and bottom sub title to nothing and back
  //   Polymer.Base.transform('scale(' + scaleBottom + ') translateZ(0)', bottomContainer);
  //
  //   // Scale middleContainer appName
  //   Polymer.Base.transform('scale(' + scaleMiddle + ') translateZ(0)', appName);
  // });

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
        app.$.mainDrawerPanel.closeDrawer();
      });
    });
  };

  app._newCustomer = function() {
    app.subTitle = 'New Customer';
    var el = document.createElement('customer-card');

    el.customer = {};
    el.key = null;
    el.editing = true;

    app._displayInPanel(el);
  };

  app._newAgent = function() {
    app.subTitle = 'New Agent';
    var el = document.createElement('agent-card');

    el.agent = {};
    el.key = null;
    el.editing = true;

    app._displayInPanel(el);
  };

  addEventListener('create-invoice', function(e) {
    app.subTitle = 'New Invoice';
    var el = document.createElement('invoice-card');

    el.invoice = {customer: e.detail.customerKey};
    el.key = null;
    el.customer = e.detail.customer;
    el.isNew = true;
    el.editing = true;

    app._displayInPanel(el);
  });

  addEventListener('create-deposit', function(e) {
    app.subTitle = 'New Deposit';
    var el = document.createElement('deposit-card');

    el.deposit = {agent: e.detail.agentKey};
    el.key = null;
    el.agent = e.detail.agent;
    el.isNew = true;
    el.editing = true;

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
})(document);
