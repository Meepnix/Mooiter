#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mooiter
# Copyright 2010 Christopher Massey
# See LICENCE for details.

import sys
import os
import re
import datetime
import string
import base64
import functools

#Mooiter modules
import parser
import account

#Test 3rd party modules.
try:
    from PyQt4 import QtGui
    from PyQt4 import QtCore
    from PyQt4 import QtWebKit
    import tweepy
    import keyring
except ImportError as e:
    print "Import Error" + e

class TwitterWindow(QtGui.QMainWindow):
    def __init__(self, Parent=None):
        super(TwitterWindow, self).__init__(Parent)

        #Settings
        self.settings = QtCore.QSettings("cutiepie4", "Mooiter")

        self.resize(300, 550)
        self.setWindowTitle("Mooiter")

        #Menubar
        actionaccount = QtGui.QAction("&Account", self)
        self.connect(actionaccount, QtCore.SIGNAL('triggered()'), 
                     self.account_dialog)
        menubar = self.menuBar()
        menusettings = menubar.addMenu("&Settings")
        menusettings.addAction(actionaccount)
        
        #Main tabs
        self.tabmain = QtGui.QTabWidget()
        self.publicwid = QtGui.QWidget()
        self.publicvbox = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()

        #Twitter posting box
        self.label = QtGui.QLabel()
        self.label.setMinimumWidth(33)
        self.label.setText('140')
        self.intwit = TwitterEditBox(self)
        hbox.addWidget(self.intwit)
        hbox.addWidget(self.label)

        #Sub tabs
        self.subtab = TimelineTabs(self)

        #Static user home timeline tab.
        self.subwidget = QtGui.QWidget()
        self.homevbox = QtGui.QVBoxLayout()

        self.view = QtWebKit.QWebView()
        self.view.page().mainFrame().setScrollBarPolicy\
                                     (QtCore.Qt.Horizontal, 
                                      QtCore.Qt.ScrollBarAlwaysOff)

        self.view.page().setLinkDelegationPolicy(QtWebKit.QWebPage.\
                                                 DelegateAllLinks)

        self.homevbox.addWidget(self.view)
        self.subwidget.setLayout(self.homevbox)
        self.subtab.addTab(self.subwidget, "Home")

        #Static @user timeline tab. 
        self.atwidget = QtGui.QWidget()
        self.atvbox = QtGui.QVBoxLayout()

        self.viewat = QtWebKit.QWebView()
        self.viewat.page().mainFrame().setScrollBarPolicy\
                                       (QtCore.Qt.Horizontal, 
                                        QtCore.Qt.ScrollBarAlwaysOff)

        self.viewat.page().setLinkDelegationPolicy(QtWebKit.QWebPage.\
                                                   DelegateAllLinks)
        
        self.atvbox.addWidget(self.viewat)
        self.atwidget.setLayout(self.atvbox)
        self.subtab.addTab(self.atwidget, "@User")

        #Tab related to all aspects that are public
        self.publicvbox.addLayout(hbox)
        self.publicvbox.addWidget(self.subtab)
        self.publicwid.setLayout(self.publicvbox)
        self.tabmain.addTab(self.publicwid, "Public")
        self.setCentralWidget(self.tabmain)
        self.intwit.setFocus()
        self.view.load(QtCore.QUrl(u'file://localhost%s' % \
                       os.path.abspath('.')))

        self.timer = QtCore.QTimer()
        self.test_account()
            
        #Handle home webview links
        self.connect(self.view, QtCore.SIGNAL("linkClicked(QUrl)"), 
                     self.open_link)

        #Handle @User webview links
        self.connect(self.view, QtCore.SIGNAL("linkClicked(QUrl)"), 
                     self.open_link)

        #Count text length alterations
        self.connect(self.intwit, QtCore.SIGNAL("textChanged()"), 
                     self.twit_count)

        self.connect(self.intwit, QtCore.SIGNAL("status"), 
                     self.submit_twit)

    def account_dialog(self):
        """Account dialog window."""
        
        dialog = account.TwitterAccount(self)
        #Any changes to account, test new account details.
        self.connect(dialog, QtCore.SIGNAL("changed"), self.test_account)
        dialog.show()

    def test_account(self):
        """Load timeline if account exists"""

        self.timer.stop()
        if self.settings.contains("User") and self.settings.contains("use"):
            username = base64.b64decode(self.settings.value("User").toString())
            password = base64.b64decode(self.settings.value("use").toString())
            self.auth = tweepy.BasicAuthHandler(username, password)
            self.api = tweepy.API(self.auth)

            #Refresh static twitter timelines every 5 minutes.
            self.connect(self.timer, QtCore.SIGNAL("timeout()"), 
                         self.load_home_tweets)
            self.connect(self.timer, QtCore.SIGNAL("timeout()"), 
                         self.load_mentions_tweets)
            self.load_home_tweets()
            self.load_mentions_tweets()
            self.timer.start(300000)
        
    def open_link(self, url):
        """Determine url type.

            Create a dynamic tab containing user or tag timeline, or load url
            with default web browser.
            
            Args:
                url: Qurl object of link being accessed.
        """

        result = url.toString().split(":")
        if result[0] == "hash":
            tagwidget = TwitterTab(self, tag="hash", text=result[1],
                                   auth=self.api, time=self.timer)
            #Handle dynamic tab links.
            self.connect(tagwidget, QtCore.SIGNAL("linkClicked(QUrl)"), 
                         self.open_link)
            self.subtab.addTab(tagwidget, result[1])
        elif result[0] == "user":
            user = result[1]
            tagwidget = TwitterTab(self, tag="user", text=user[2:],
                                   auth=self.api, time=self.timer)
            #Handle dynamic tab links.
            self.connect(tagwidget, QtCore.SIGNAL("linkClicked(QUrl)"), 
                         self.open_link)
            self.subtab.addTab(tagwidget, ('@' + user[2:]))
        else:
            QtGui.QDesktopServices.openUrl(url)
        
    def load_home_tweets(self):
        """Load user timeline into default home tab."""
        
        #Html Header
        html = u'<html><head>\
                      <link rel="stylesheet" href="themes/theme_1/theme1.css"\
                        type="text/css" media="all" /></head><body>'
                        
        #Hmtl formatting of each tweet.              
        for twits in self.api.home_timeline():
            html += u'<div class="roundcorner_box">\
                      <div class="roundcorner_top"><div></div></div>\
                      <div class="roundcorner_content">'
            html += u'<div class="pic_left">'
            html += u'<img class="pic" src="' + twits.user.profile_image_url + \
                    u'" />'
            html += u'</div>'
            html += u'<div class="text_left">'
            html += u'<h2>' + twits.user.screen_name + u'</h2>'
            html += u'<p>' + parser.LinkParser().parse_links(twits.text) + \
                    u'</p>'
            html += u'<p>' + str(period_ago(twits.created_at)) + u'</p>'
            html += u'<p>via ' + twits.source + u'</p>'
            html += u'</div>'
            html += u'<div style="clear: both;"></div>'
            html += u'</div><div class="roundcorner_bottom"><div></div>\
                      </div></div><br />'

        html += u"</body></html>"
        self.view.setHtml(html, QtCore.QUrl(u'file://localhost%s' %\
                          os.path.abspath('./mooiter.py')))
    
    def load_mentions_tweets(self):
        """Load user mention timeline into default @user tab."""

        #Html header
        html = u'<html><head>\
                      <link rel="stylesheet" href="themes/theme_1/theme1.css"\
                      type="text/css" media="all" /></head><body>'
        #Html formatting of each twitter mention.
        for twits in self.api.mentions():
            html += u'<div class="roundcorner_box">\
                      <div class="roundcorner_top"><div></div></div>\
                      <div class="roundcorner_content">'
            html += u'<div class="pic_left">'
            html += u'<img class="pic" src="' + twits.user.profile_image_url + \
                    u'" />'
            html += u'</div>'
            html += u'<div class="text_left">'
            html += u'<h2>' + twits.user.screen_name + u'</h2>'
            html += u'<p>' + parser.LinkParser().parse_links(twits.text) + \
                    u'</p>'
            html += u'<p>' + str(period_ago(twits.created_at)) + u'</p>'
            html += u'<p>via ' + twits.source + u'</p>'
            html += u'</div>'
            html += u'<div style="clear: both;"></div>'
            html += u'</div><div class="roundcorner_bottom"><div></div>\
                      </div></div><br />'

        html += u"</body></html>"
        self.viewat.setHtml(html, QtCore.QUrl(u'file://localhost%s' %\
                          os.path.abspath('./mooiter.py')))
        
    def twit_count(self):
        """Display twitter message length."""

        self.label.setText(str(140 - len(self.intwit.toPlainText())))

    def submit_twit(self):
        """Post twitter status to user account"""

        try:
            self.api.update_status(unicode(self.intwit.toPlainText()))
        except tweepy.TweepError:
            QtGui.QMessageBox.warning(self, 'Warning',
                                      "Error posting twitter status", 
                                      QtGui.QMessageBox.Ok)
        finally:
            self.intwit.setText("")

class TwitterEditBox(QtGui.QTextEdit):
    """Editbox posts twitter tweets."""

    def __init__(self, Parent):
        super(TwitterEditBox, self).__init__(Parent)
        self.setMinimumHeight(50)

    def keyPressEvent(self, event):
        """EditBox posts tweet on return keypress"""
        
        if event.key() == QtCore.Qt.Key_Return:
            self.emit(QtCore.SIGNAL("status"))
        else:
            QtGui.QTextEdit.keyPressEvent(self, event)

class TwitterTab(QtGui.QWidget):
    """Create user or hash tag timeline webview widget.

    Attributes:
        tag: datetime object
        text: string username or hash tag
        auth: tweepy object
        time: QTime object

    """
    def __init__(self, Parent, tag, text, auth, time):
        super(TwitterTab, self).__init__(Parent)
        self.api = auth
        self.view = QtWebKit.QWebView()

        vbox = QtGui.QVBoxLayout()
        self.view.page().mainFrame().setScrollBarPolicy\
                                (QtCore.Qt.Horizontal, 
                                 QtCore.Qt.ScrollBarAlwaysOff)

        self.view.page().setLinkDelegationPolicy(QtWebKit.QWebPage.\
                                                 DelegateAllLinks)
        
        vbox.addWidget(self.view)
        self.setLayout(vbox)
        self.mapper = QtCore.QSignalMapper(self)
        
        if tag == "user":
            self.load_user_tweets(text) 
            self.connect(self.mapper, QtCore.SIGNAL("mapped(const QString &)"), 
                                                    self.load_user_tweets)
            self.connect(time, QtCore.SIGNAL("timeout()"), self.mapper, 
                                             QtCore.SLOT("map()"))
            #Refresh timeline using the timer object used by the MainWindow.
            self.mapper.setMapping(time, text)
        else:
            self.load_hash_tweets(text)
            self.connect(self.mapper, QtCore.SIGNAL("mapped(const QString &)"), 
                                                    self.load_hash_tweets)
            self.connect(time, QtCore.SIGNAL("timeout()"), self.mapper,
                                             QtCore.SLOT("map()"))
            #Refresh timeline using the timer object used by the MainWindow.
            self.mapper.setMapping(time, text)

        #Handle webview links.
        self.connect(self.view, QtCore.SIGNAL("linkClicked(QUrl)"), 
                     self.signal_link)
            
    def load_user_tweets(self, text):
        """Create html timeline of selected @user."""
        #HTML Header 
        html = u'<html><head>\
                      <link rel="stylesheet" href="themes/theme_1/theme1.css"\
                      type="text/css" media="all" /></head><body>'
        #HTML formatted User.
        html += u'<div class="roundcorner_box">\
                  <div class="roundcorner_top"><div></div></div>\
                  <div class="roundcorner_content">'
        html += u'<h2>' + self.api.get_user(str(text)).screen_name + u'</h2>'
        html += u'</div><div class="roundcorner_bottom"><div></div>\
                  </div></div><br />'

        #HTML formatted timelines.
        for twits in self.api.user_timeline(str(text)):
            html += u'<div class="roundcorner_box">\
                      <div class="roundcorner_top"><div></div></div>\
                      <div class="roundcorner_content">'
            html += u'<div class="pic_left">'
            html += u'<img class="pic" src="' + twits.user.profile_image_url + \
                    u'" />'
            html += u'</div>'
            html += u'<div class="text_left">'
            html += u'<h2>' + twits.user.screen_name + u'</h2>'
            html += u'<p>' + parser.LinkParser().parse_links(twits.text) + \
                    u'</p>'
            html += u'<p>' + str(period_ago(twits.created_at)) + u'</p>'
            html += u'<p>via ' + twits.source + u'</p>'
            html += u'</div>'
            html += u'<div style="clear: both;"></div>'
            html += u'</div><div class="roundcorner_bottom"><div></div>\
                      </div></div><br />'

        html += u"</body></html>"
        self.view.setHtml(html, QtCore.QUrl(u'file://localhost%s' %\
                          os.path.abspath('./mooiter.py')))

    def load_hash_tweets(self, query):
        """Create html timeline of selected hash tag."""

        #HTML Header
        html = u'<html><head>\
                      <link rel="stylesheet" href="themes/theme_1/theme1.css"\
                      type="text/css" media="all" /></head><body>'
                      
        #HTML formatted timelines.
        for twits in self.api.search(str(query)):
            html += u'<div class="roundcorner_box">\
                      <div class="roundcorner_top"><div></div></div>\
                      <div class="roundcorner_content">'
            html += u'<div class="pic_left">'
            html += u'<img class="pic" src="' + twits.profile_image_url + u'" />'
            html += u'</div>'
            html += u'<div class="text_left">'
            html += u'<h2>' + twits.from_user + u'</h2>'
            html += u'<p>' + parser.LinkParser().parse_links(twits.text) + \
                    u'</p>'
            html += u'<p>' + str(period_ago(twits.created_at)) + u'</p>'
            html += u'<p>via ' + twits.source + u'</p>'
            html += u'</div>'
            html += u'<div style="clear: both;"></div>'
            html += u'</div><div class="roundcorner_bottom"><div></div>\
                      </div></div><br />'

        html += u"</body></html>"
        self.view.setHtml(html, QtCore.QUrl(u'file://localhost%s' %\
                          os.path.abspath('./mooiter.py')))

    def signal_link(self, link):
        self.emit(QtCore.SIGNAL("linkClicked(QUrl)"), link)
        

class TimelineTabs(QtGui.QTabWidget):
    """Custom Tab Widget providing non-static closable tabs."""
    
    def __init__(self, Parent):
        super(TimelineTabs, self).__init__(Parent)
        self.positions = {}
        self.count = 0
        self.mapper = QtCore.QSignalMapper(self)
        self.connect(self.mapper, QtCore.SIGNAL("mapped(const QString &)"), 
                     self.close_tab)
    
    def tabInserted(self, number):
        """Add non-static closable tabs."""
        
        if number > 1:
            
            button = QtGui.QPushButton("x")
            button.setFixedSize(16, 16)
            self.tabBar().setTabButton(number, QtGui.QTabBar.LeftSide, button)
            #Create unique tab id.
            self.count += 1
            idtab = 'a' + str(self.count)
            #Store tab index location.
            self.positions[idtab] = number
            #Map tab ID location 
            self.connect(button, QtCore.SIGNAL("clicked()"), self.mapper, 
                         QtCore.SLOT("map()"))
            self.mapper.setMapping(button, idtab)

    def close_tab(self, tab):
        """Remove tab and cleanup related widget."""
        
        idtab = str(tab)
        #Decrement all tab locations that appear after the removed tab.
        for key, value in self.positions.iteritems():
            if value > self.positions[idtab]:
                self.positions[key] = self.positions[key] - 1
            
        self.widget(self.positions[idtab]).destroy(True)
        self.removeTab(self.positions[idtab])
        del(self.positions[idtab])
        

def period_ago(period):
    """Provides the time and date difference of a tweet.

    Args:
        period: datetime object

    Returns:
        Formatted time and date difference as a unicode string.
    """
        
    if not isinstance(period, datetime.datetime):

        return "error"
    #Determine time and date difference
    difference = datetime.datetime.utcnow() - period
    diff_day = string.split(str(difference))

    #More than 1 day old use full date and time
    if len(diff_day) > 1:
        return period.strftime("%c")
    else:
        diff_split = string.split(str(difference), ":")
        hour = int(diff_split[0])
        minute = int(diff_split[1])
        second = int(string.split(str(diff_split[2]), ".")[0])
        return_diff = ""

        #Format time while determining the plurals
        if hour > 0:
            if hour == 1:
                return_diff += u"(%s hour " % hour
            else:
                return_diff += u"(%s hours " % hour

            if minute == 1:
                return_diff += u"%s minute " % minute
            else:
                return_diff += u"%s minutes " % minute

            if second == 1:
                return_diff += u"%s second ago)" % second
            else:
                return_diff += u"%s seconds ago)" % second

        elif minute > 0:
            if minute == 1:
                return_diff += u"(%s minute " % minute
            else:
                return_diff += u"(%s minutes " % minute

            if second == 1:
                return_diff += u"%s second ago)" % second
            else:
                return_diff += u"%s seconds ago)" % second
                
        else:
            if second == 1:
                return_diff += u"(%s second ago)" % second
            else:
                return_diff += u"(%s seconds ago)" % second

        return return_diff        

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    meep = TwitterWindow()
    meep.show()
    sys.exit(app.exec_())
