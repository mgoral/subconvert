#-*- coding: utf-8 -*-

"""
This file is part of SubConvert.

SubConvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SubConvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SubConvert.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt4.QtCore import QSettings, QDir

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

    def getLatestDirectory(self):
        if self.getUseDefaultDirectory():
            ret = self._settings.value("gui/latest_dir", QDir.homePath())
            if ret:
                return ret
        return QDir.homePath()

    def setLatestDirectory(self, val):
        self._settings.setValue("gui/latest_dir", val)
