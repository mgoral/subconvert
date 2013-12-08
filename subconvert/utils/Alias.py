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

def acceptAlias(decoratedFunction):
    """This function should be used as a decorator. Each class method that is decorated will be able
    to accept alias or original names as a first function positional parameter."""
    def wrapper(self, *args, **kwargs):
        SubAssert(isinstance(self, AliasBase))

        if len(args) > 0:
            key = args[0]
            if args[0] in self._aliases.keys():
                key = self._aliases[args[0]]
            return decoratedFunction(self, key, *args[1:], **kwargs)
        return decoratedFunction(self, *args, **kwargs)
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

    def getAlias(self, alias):
        return self._aliases.get(alias)

    def registerAlias(self, alias, name):
        self._aliases[alias] = name

    def deregisterAlias(self, alias):
        if alias in self._aliases.keys():
            del self._aliases[alias]
