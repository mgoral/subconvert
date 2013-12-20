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

import unittest
from subconvert.utils.Alias import *
from subconvert.utils.SubException import SubException

class DummyClass(AliasBase):
    @acceptAlias
    def accessFirstArg(self, a="defaultAlias"):
        return a

    @acceptAlias
    def accessSecondArg(self, a=None, b=None):
        return b

    @acceptAlias
    def accessThirdArg(self, a=None, b=None, c=0):
        return c

class ClassWithoutAlias:
    @acceptAlias
    def incorrectlyDecoratedMethod(self, text):
        pass

class TestSubConverter(unittest.TestCase):
    """Utils (module) test suite."""

    def setUp(self):
        self.d = DummyClass()

    def test_RaiseAnExceptionWhenClassDoesntSubclass_AliasBase_(self):
        noAlias = ClassWithoutAlias()
        with self.assertRaises(SubException):
            noAlias.incorrectlyDecoratedMethod("name")

    def test_AliasBaseDoesntCreateAnyAliasesbyDefault(self):
        print (self.d._aliases)
        self.assertEqual(0, len(self.d._aliases))

    def test_AliasBaseProperlyRegistersAnAlias(self):
        self.d.registerAlias("alias", "name")
        self.assertEqual("name", self.d._aliases["alias"])

    def test_AliasBaseProperlyDeregistersAnAlias(self):
        self.d.registerAlias("alias", "name")
        self.d.deregisterAlias("alias")
        self.assertIsNone(self.d._aliases.get("alias"))

    def test_ItsPossibleToAssignMoreThanOneAliasToName(self):
        self.d.registerAlias("alias1", "name")
        self.d.registerAlias("alias2", "name")
        self.assertEqual("name", self.d._aliases["alias1"])
        self.assertEqual("name", self.d._aliases["alias2"])

    def test_AliasBaseDeregistersOnlyGivenAliasWhenMoreExists(self):
        self.d.registerAlias("alias1", "name")
        self.d.registerAlias("alias2", "name")
        self.d.deregisterAlias("alias1")
        self.assertEqual("name", self.d._aliases["alias2"])
        self.assertIsNone(self.d._aliases.get("alias1"))

    def test_DeregisteringNotExistingAliasDoesntDoAnything(self):
        self.d.deregisterAlias("alias")
        self.assertIsNone(self.d._aliases.get("alias"))

    def test_AcceptAliasDecoratorProperlyPassesGivenValueWhenNoAliasIsFound(self):
        self.assertEqual("noAlias", self.d.accessFirstArg("noAlias"))

    def test_AcceptAliasDecoratorProperlyPassesValueWhenAliasIsGiven(self):
        self.d.registerAlias("alias", "passedArg")
        self.assertEqual("passedArg", self.d.accessFirstArg("alias"))

    def test_AcceptAliasDecoratorProperlyPassesRemainingArgsWhenNoAliasIsFound(self):
        self.assertEqual(6, self.d.accessSecondArg("noAlias", 6))
        self.assertEqual(1, self.d.accessThirdArg("noAlias", 3, 1))

    def test_AcceptAliasDecoratorProperlyPassesRemainingArgsWhenAliasIsFound(self):
        self.d.registerAlias("alias", "passedArg")
        self.assertEqual(5, self.d.accessSecondArg("alias", 5))
        self.assertEqual(2, self.d.accessThirdArg("alias", 9, 2))

    def test_AcceptAliasDecoratorProperlyPassesRemainingDefaultArgsWhenNoAliasIsFound(self):
        self.assertEqual("defaultAlias", self.d.accessFirstArg())
        self.assertIsNone(self.d.accessSecondArg("noAlias"))

    def test_AcceptAliasDecoratorProperlyPassesRemainingDefaultArgsWhenAliasIsFound(self):
        self.d.registerAlias("alias", "passedArg")
        self.assertEqual("defaultAlias", self.d.accessFirstArg())
        self.assertIsNone(self.d.accessSecondArg())

    def test_AcceptAliasDecoratorAllowsUsingKwargsForRemainingArguments(self):
        self.d.registerAlias("alias", "passedArg")
        self.assertEqual(4, self.d.accessSecondArg("alias", b=4))

    def test_AliasesReturnsProperTupleOfAliases(self):
        self.d.registerAlias("alias1", "passedArg")
        self.d.registerAlias("alias2", "passedArg")
        self.d.registerAlias("alias3", "passedArg2")
        self.assertEqual(("alias1", "alias2"), self.d.aliases("passedArg"))

    def test_AliasesReturnEmptyTupleWhenNoAliasesAreAssigned(self):
        self.assertEqual(tuple(), self.d.aliases("passedArg"))

    def test_GetAliasReturnsRealNameToWhichAliasIsAssigned(self):
        self.d.registerAlias("alias", "passedArg")
        self.assertEqual("passedArg", self.d.getAlias("alias"))

    def test_GetAliasReturnsNoneIfGivenAliasIsNotAssigned(self):
        self.assertIsNone(self.d.getAlias("alias"))
