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

def acceptAlias(decoratedFunction):
    """This function should be used as a decorator. Each class method that is decorated will be able
    to accept alias or original names as a first function parameter."""
    def wrapper(self, alias, *args, **kwargs):
        assert(isinstance(self, AliasBase))

        key = alias
        if alias in self._aliases.keys():
            key = self._aliases[alias]
        return decoratedFunction(self, key, *args, **kwargs)
    return wrapper

class AliasBase:
    """Base class for all classes that should provide alias function."""
    def __init__(self):
        # Don't add a second underscore so it won't change name to _AliasBase__aliases. It's
        # protected rather than private...
        self._aliases = {}

    def aliases(self, name):
        aliasList = []
        for key in self._aliases.keys():
            if self._aliases[key] == name:
                aliasList.append(key)
        aliasList.sort()
        return tuple(aliasList)

    def get(self, alias):
        return self._aliases.get(alias)

    def registerAlias(self, alias, name):
        self._aliases[alias] = name

    def deregisterAlias(self, alias):
        if alias in self._aliases.keys():
            del self._aliases[alias]
