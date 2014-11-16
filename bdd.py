"""
Copyright (c) 2014, Guillermo A. Perez, Universite Libre de Bruxelles

This file is part of the AbsSynthe tool.

AbsSynthe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

AbsSynthe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with AbsSynthe.  If not, see <http://www.gnu.org/licenses/>.


Guillermo A. Perez
Universite Libre de Bruxelles
gperezme@ulb.ac.be
"""

from abc import ABCMeta, abstractmethod


class BDD_Base:
    __metaclass__ = ABCMeta

    @abstractmethod
    def true():
        pass

    @abstractmethod
    def false():
        pass

    @abstractmethod
    def make_eq(b, c):
        pass

    @abstractmethod
    def make_impl(b, c):
        pass

    @abstractmethod
    def make_clause(bs):
        pass

    @abstractmethod
    def make_cube(bs):
        pass

    @abstractmethod
    def disable_reorder():
        pass

    @abstractmethod
    def next_var():
        pass

    @abstractmethod
    def __init__(self, var=None):
        pass

    @abstractmethod
    def __nonzero__(self):
        pass

    @abstractmethod
    def dump_dot(self):
        pass

    @abstractmethod
    def get_index(self):
        pass

    @abstractmethod
    def is_complement(self):
        pass

    @abstractmethod
    def then_child(self):
        pass

    @abstractmethod
    def else_child(self):
        pass

    @abstractmethod
    def get_one_minterm(self, vars):
        pass

    @abstractmethod
    def cofactor(self, var_bdd):
        pass

    @abstractmethod
    def safe_restrict(self, r):
        pass

    @abstractmethod
    def restrict(self, r):
        pass

    @abstractmethod
    def is_constant(self):
        pass

    @abstractmethod
    def and_abstract(self, other, cube):
        pass

    @abstractmethod
    def exist_abstract(self, cube):
        pass

    @abstractmethod
    def univ_abstract(self, cube):
        pass

    @abstractmethod
    def __or__(self, other):
        pass

    @abstractmethod
    def __and__(self, other):
        pass

    @abstractmethod
    def __invert__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __ne__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def dag_size(self):
        pass

    @abstractmethod
    def swap_variables(self, cur_vars, new_vars):
        pass

    @abstractmethod
    def compose(self, cur_vars, new_funs):
        pass

    @abstractmethod
    def bdd2cnf(self):
        pass
