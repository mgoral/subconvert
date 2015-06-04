#-*- coding: utf-8 -*-

"""
Copyright (C) 2011, 2012, 2013 Michal Goral.

This file is part of Subconvert

Subconvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Subconvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Subconvert. If not, see <http://www.gnu.org/licenses/>.
"""

from subconvert.utils.SubException import SubAssert

import os
from PyQt5.QtCore import QSettings, QDir, QByteArray

def str2Bool(val):
    # Really, fuck pyqt
    if val is True or val.lower() == "true":
        return True
    if val is False or val.lower() == "false":
        return False

class SubSettings:
    """A wrapper to QSettings. Provides an interface to all available Subconvert options."""

    def __init__(self):
        # The following settings will cause saving config files to e.g.
        # ~/.config/subconvert/subconvert.ini
        organization = "subconvert"
        mainConfFile = "subconvert"
        programStateFile = "state"

        self._settings = QSettings(
            QSettings.IniFormat, QSettings.UserScope, organization, mainConfFile)
        self._programState = QSettings(
            QSettings.IniFormat, QSettings.UserScope, organization, programStateFile)

    def sync(self):
        self._settings.sync()
        self._programState.sync()

    def getUseDefaultDirectory(self):
        return self._settings.value("gui/use_default_dirs", True)

    def setUseDefaultDirectory(self, val):
        self._settings.setValue("gui/use_default_dirs", val)

    #
    # Last directory from which a file has been opened
    #

    def getLatestDirectory(self):
        if self.getUseDefaultDirectory():
            ret = self._programState.value("gui/latest_dir", QDir.homePath())
            if ret:
                return ret
        return QDir.homePath()

    def setLatestDirectory(self, val):
        self._programState.setValue("gui/latest_dir", val)

    #
    # Subtitle "property files" paths, number etc.
    #

    def getPropertyFilesPath(self):
        defaultDirName = "pfiles"
        defaultPath = os.path.join(os.path.dirname(self._programState.fileName()), defaultDirName)
        return self._programState.value("pfiles/path", defaultPath)

    def setPropertyFilesPath(self, val):
        self._programState.setValue("pfiles/path", val)

    def getMaxRememberedPropertyFiles(self):
        defaultMaxValue = 5
        return self._programState.value("pfiles/max", defaultMaxValue)

    def setMaxRememberedPropertyFiles(self, val):
        self._programState.setValue("pfiles/max", val)

    def getLatestPropertyFiles(self):
        return self._programState.value("pfiles/latest", [])

    def addPropertyFile(self, val):
        maxPropertyFiles = self.getMaxRememberedPropertyFiles() - 1
        propertyFiles = self.getLatestPropertyFiles()
        if val in propertyFiles:
            propertyFiles.remove(val)
        else:
            propertyFiles = propertyFiles[:maxPropertyFiles]
        propertyFiles.insert(0, val)
        self._programState.setValue("pfiles/latest", propertyFiles)

    def removePropertyFile(self, val):
        propertyFiles = self.getLatestPropertyFiles()
        try:
            index = propertyFiles.index(val)
            del propertyFiles[index]
            self._programState.setValue("pfiles/latest", propertyFiles)
        except ValueError:
            pass

    #
    # Generic functions for windows/widgets. Please note that passed QWidgets must have previously
    # set objects names via QWidget::setObjectName(str) method. The convention is to use underscores
    # as words separators (e.g. main_window, my_super_widget, etc.).
    #

    def setGeometry(self, widget, val):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        self._programState.setValue("gui/%s/geometry" % widget.objectName(), val)

    def getGeometry(self, widget, default = QByteArray()):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        return self._programState.value("gui/%s/geometry" % widget.objectName(), default)

    def setState(self, widget, val):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        self._programState.setValue("gui/%s/state" % widget.objectName(), val)

    def getState(self, widget, default = QByteArray()):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        return self._programState.value("gui/%s/state" % widget.objectName(), default)

    def setHidden(self, widget, val):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        self._programState.setValue("gui/%s/hidden" % widget.objectName(), val)

    def getHidden(self, widget, default = True):
        SubAssert(widget.objectName() != "", "Widget's name isn't set!")
        return str2Bool(self._programState.value("gui/%s/hidden" % widget.objectName(), default))
