# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os, sys
from aqt.qt import *

appName="Anki"
appVersion="1.99"
appWebsite="http://ankisrs.net/"
appHelpSite="http://ankisrs.net/docs/dev/"
appDonate="http://ankisrs.net/support/"
modDir=os.path.dirname(os.path.abspath(__file__))
runningDir=os.path.split(modDir)[0]
mw = None # set on init
# py2exe
if hasattr(sys, "frozen"):
    sys.path.append(modDir)
    modDir = os.path.dirname(sys.argv[0])

def openHelp(name):
    if "#" in name:
        name = name.split("#")
        name = name[0] + ".html#" + name[1]
    else:
        name = name + ".html"
    QDesktopServices.openUrl(QUrl(appHelpSite + name))

# Dialog manager - manages modeless windows
##########################################################################

class DialogManager(object):

    def __init__(self):
        from aqt import addcards, browser
        self._dialogs = {
            "AddCards": [addcards.AddCards, None],
            "Browser": [browser.Browser, None],
        }

    def open(self, name, *args):
        (creator, instance) = self._dialogs[name]
        if instance:
            instance.activateWindow()
            instance.raise_()
            return instance
        else:
            instance = creator(*args)
            self._dialogs[name][1] = instance
            return instance

    def close(self, name):
        self._dialogs[name] = [self._dialogs[name][0], None]

    def closeAll(self):
        for (n, (creator, instance)) in self._dialogs.items():
            if instance:
                instance.forceClose = True
                instance.close()
                self.close(n)

dialogs = DialogManager()

# Splash screen
##########################################################################

class SplashScreen(object):

    def __init__(self, max=100):
        self.finished = False
        self.pixmap = QPixmap(":/icons/anki-logo.png")
        self.splash = QSplashScreen(self.pixmap)
        self.prog = QProgressBar(self.splash)
        self.prog.setMaximum(max)
        if QApplication.instance().style().objectName() != "plastique":
            self.style = QStyleFactory.create("plastique")
            self.prog.setStyle(self.style)
        self.prog.setStyleSheet("""* {
color: #ffffff;
background-color: #061824;
margin:0px;
border:0px;
padding: 0px;
text-align: center;}
*::chunk {
color: #13486c;
}
""")
        x = 8
        self.prog.setGeometry(self.splash.width()/10, 8.85*self.splash.height()/10,
                                x*self.splash.width()/10, self.splash.height()/10)
        self.splash.show()
        self.val = 1

    def update(self):
        self.prog.setValue(self.val)
        self.val += 1
        QApplication.instance().processEvents()

    def finish(self, obj):
        self.splash.finish(obj)
        self.finished = True

# App initialisation
##########################################################################

class AnkiApp(QApplication):

    def event(self, evt):
        from anki.hooks import runHook
        if evt.type() == QEvent.FileOpen:
            runHook("macLoadEvent", unicode(evt.file()))
            return True
        return QApplication.event(self, evt)

def run():
    global mw
    from anki.utils import isWin, isMac

    # home on win32 is broken
    mustQuit = False
    if isWin:
        # use appdata if available
        if 'APPDATA' in os.environ:
            os.environ['HOME'] = os.environ['APPDATA']
        else:
            mustQuit = True
        # make and check accessible
        try:
            os.makedirs(os.path.expanduser("~/.anki"))
        except:
            pass
        try:
            os.listdir(os.path.expanduser("~/.anki"))
        except:
            mustQuit = True

    # on osx we'll need to add the qt plugins to the search path
    rd = runningDir
    if isMac and getattr(sys, 'frozen', None):
        rd = os.path.abspath(runningDir + "/../../..")
        QCoreApplication.setLibraryPaths([rd])

    # create the app
    app = AnkiApp(sys.argv)
    QCoreApplication.setApplicationName("Anki")
    if mustQuit:
        QMessageBox.warning(
            None, "Anki", "Can't open APPDATA, nor c:\\anki.\n"
            "Please try removing foreign characters from your username.")
        sys.exit(1)
    splash = SplashScreen(3)

    # parse args
    import optparse
    parser = optparse.OptionParser()
    parser.usage = "%prog [<deck.anki>]"
    parser.add_option("-c", "--config", help="path to config dir",
                      default=os.path.expanduser("~/.anki"))
    (opts, args) = parser.parse_args(sys.argv[1:])

    # setup config
    import aqt.config
    conf = aqt.config.Config(
        unicode(os.path.abspath(opts.config), sys.getfilesystemencoding()))

    # qt translations
    translationPath = ''
    if not isWin and not isMac:
        translationPath = "/usr/share/qt4/translations/"
    if translationPath:
        long = conf['interfaceLang']
        short = long.split('_')[0]
        qtTranslator = QTranslator()
        if qtTranslator.load("qt_" + long, translationPath) or \
               qtTranslator.load("qt_" + short, translationPath):
            app.installTranslator(qtTranslator)

    # load main window
    splash.update()
    import aqt.main
    mw = aqt.main.AnkiQt(app, conf, args, splash)
    app.exec_()

if __name__ == "__main__":
    run()
