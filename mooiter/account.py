#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mooiter
# Copyright 2010 Christopher Massey
# See LICENCE for details.

import sys
import base64

#Test third party modules
try:
    import tweepy
    from PyQt4 import QtGui
    from PyQt4 import QtCore
except ImportError as e:
    print "Import Error" + e

class TwitterAccount(QtGui.QDialog):
    def __init__(self, Parent=None):
        super(TwitterAccount, self).__init__(Parent)
        #Garbage collect on dialog close
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.settings = QtCore.QSettings("cutiepie4", "Mooiter")
        
        self.setWindowTitle("Account")
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        vboxlabels = QtGui.QVBoxLayout()
        vboxedits = QtGui.QVBoxLayout()
        hboxbuttons = QtGui.QHBoxLayout()

        delete = QtGui.QPushButton('&Delete')
        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save|
                                           QtGui.QDialogButtonBox.Close)

        #Create horizontal line
        seperator = QtGui.QFrame()
        seperator.setFrameShape(QtGui.QFrame.HLine)
        seperator.setFrameShadow(QtGui.QFrame.Sunken)
        
        self.useredit = QtGui.QLineEdit()
        self.passwordedit = QtGui.QLineEdit()
        self.useredit.setMinimumWidth(200)
        self.passwordedit.setMinimumWidth(200)
        self.passwordedit.setEchoMode(QtGui.QLineEdit.Password)

        labeluser = QtGui.QLabel("&Username:")
        labelpassword = QtGui.QLabel("&Password:")
        labeluser.setBuddy(self.useredit)
        labelpassword.setBuddy(self.passwordedit)
        
        vboxlabels.addWidget(labeluser)
        vboxlabels.addWidget(labelpassword)

        vboxedits.addWidget(self.useredit)
        vboxedits.addWidget(self.passwordedit)

        hboxbuttons.addStretch()
        hboxbuttons.addWidget(delete)
        hboxbuttons.addWidget(buttonbox)

        hbox.addLayout(vboxlabels)
        hbox.addLayout(vboxedits)
        vbox.addLayout(hbox)
        vbox.addWidget(seperator)
        vbox.addLayout(hboxbuttons)

        self.setLayout(vbox)
        self.useredit.setFocus()
        self.setTabOrder(self.useredit, self.passwordedit)
        self.setTabOrder(delete, buttonbox)
        
        
        self.connect(buttonbox.button(QtGui.QDialogButtonBox.Save),
                     QtCore.SIGNAL("clicked()"), self.new_account)

        self.connect(buttonbox, QtCore.SIGNAL("rejected()"),
                     self, QtCore.SLOT("reject()"))
        
        self.connect(delete, QtCore.SIGNAL('clicked()'), self.delete_account)

        #Find out if an account already exists
        if self.settings.contains("User") and self.settings.contains("use"):
            username = base64.b64decode(self.settings.value("User").toString())
            password = base64.b64decode(self.settings.value("use").toString())
            self.useredit.setText(unicode(username))
            self.passwordedit.setText(unicode(password))

    def new_account(self):
        """Verfiy and store twitter account details"""

        username = self.useredit.text()
        password = self.passwordedit.text()
        #Verfiy twitter account exists
        
        auth = tweepy.BasicAuthHandler(username, password)
        api = tweepy.API(auth)
        if not api.verify_credentials():
            QtGui.QMessageBox.warning(self, 'Warning',
                                      "Could not authenticate twitter account", 
                                      QtGui.QMessageBox.Ok)
        else:
            #Store username and password
            self.settings.setValue("User", (QtCore.QVariant(base64.b64encode(str(username)))))
            self.settings.setValue("use", (QtCore.QVariant(base64.b64encode(str(password)))))
            #Signal account change to main window
            self.emit(QtCore.SIGNAL("changed"))
            print "pie"
          
    def delete_account(self):
        """Remove all twitter account details"""
        
        self.settings.remove("User")
        self.settings.remove("use")
        self.useredit.setText("")
        self.passwordedit.setText("")
        #Signal account change to main window
        self.emit(QtCore.SIGNAL("changed"))
        
if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    meep = TwitterAccount()
    meep.show()
    sys.exit(app.exec_())        