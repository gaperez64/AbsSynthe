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

import pycudd
import log
import bdd

# the cudd manager
cudd = None
# next free variable
next_free_var = 0


class BDD(bdd.BDD_Base):
    """ A BDD object wrapper """
    _cudd_bdd = None

    def __init__(self, var=None):
        global next_free_var

        if var is None:
            return
        if next_free_var <= var:
            next_free_var = var + 1
        self._cudd_bdd = cudd.IthVar(var)

    def dump_dot(self):
        self._cudd_bdd.DumpDot()

    def get_index(self):
        return self._cudd_bdd.NodeReadIndex()

    def is_complement(self):
        return self._cudd_bdd.IsComplement()

    def then_child(self):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.T()
        return b

    def else_child(self):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.E()
        return b

    def get_one_minterm(self, vars):
        b = BDD()
        num_vars = len(vars)
        var_array = pycudd.DdArray(num_vars)
        for i in range(num_vars):
            var_array.Push(cudd.IthVar(vars[i]))
        b._cudd_bdd = self._cudd_bdd.PickOneMinterm(var_array, num_vars)
        return b

    def cofactor(self, var_bdd):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.Cofactor(var_bdd._cudd_bdd)
        return b

    def safe_restrict(self, r):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.Restrict(r._cudd_bdd)
        return min([b, self], key=lambda x: x.dag_size())

    def restrict(self, r):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.Restrict(r._cudd_bdd)
        return b

    def is_constant(self):
        return self._cudd_bdd.IsConstant()

    def and_abstract(self, other, cube):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.AndAbstract(other._cudd_bdd,
                                                 cube._cudd_bdd)
        return b

    def exist_abstract(self, cube):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.ExistAbstract(cube._cudd_bdd)
        return b

    def univ_abstract(self, cube):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd.UnivAbstract(cube._cudd_bdd)
        return b

    def __or__(self, other):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd | other._cudd_bdd
        return b

    def __and__(self, other):
        b = BDD()
        b._cudd_bdd = self._cudd_bdd & other._cudd_bdd
        return b

    def __invert__(self):
        b = BDD()
        b._cudd_bdd = ~self._cudd_bdd
        return b

    def __nonzero__(self):
        return self._cudd_bdd != cudd.Zero()

    def __eq__(self, other):
        return self._cudd_bdd == other._cudd_bdd

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._cudd_bdd.__hash__()

    def occ_sem(self, var_list=None):
        """ returns: a subset of var_list which occurs in the boolean function
        represented by bdd """
        if var_list is None:
            var_list = range(next_free_var)
        occ = []
        if self == BDD.false():
            return occ
        for v in var_list:
            if self != self.exist_abstract(BDD(v)):
                occ.append(v)
        return occ

    def occ_pos(self, var_list=None):
        if var_list is None:
            var_list = range(next_free_var)
        pos = []
        if self == BDD.false():
            return pos
        for v in var_list:
            if (self & ~BDD(v)) == BDD.false():
                pos.append(v)
        return pos

    def occ_neg(self, var_list=None):
        if var_list is None:
            var_list = range(next_free_var)
        neg = []
        if self == BDD.false():
            return neg
        for v in var_list:
            if (self & BDD(v)) == BDD.false():
                neg.append(v)
        return neg

    def dag_size(self):
        return self._cudd_bdd.DagSize()

    def swap_variables(self, cur_vars, new_vars):
        assert len(cur_vars) == len(new_vars)
        num_vars = len(cur_vars)
        next_var_array = pycudd.DdArray(num_vars)
        curr_var_array = pycudd.DdArray(num_vars)

        for i in range(num_vars):
            curr_var_array.Push(cudd.IthVar(cur_vars[i]))
            next_var_array.Push(cudd.IthVar(new_vars[i]))

        b = BDD()
        b._cudd_bdd = self._cudd_bdd.SwapVariables(next_var_array,
                                                   curr_var_array,
                                                   num_vars)
        return b

    def compose(self, cur_vars, new_funs):
        assert len(cur_vars) == len(new_funs)
        fun_array = pycudd.DdArray(next_free_var)

        for i in range(next_free_var):
            if i in cur_vars:
                fun_array.Push(new_funs[cur_vars.index(i)]._cudd_bdd)
            else:
                fun_array.Push(cudd.IthVar(i))

        b = BDD()
        b._cudd_bdd = self._cudd_bdd.VectorCompose(fun_array)
        return b

    def bdd2cnf(self):
        cache = dict()

        def _rec_bdd2cnf(a_bdd):
            if a_bdd in cache:
                return cache[a_bdd]

            if a_bdd.is_constant():
                if a_bdd == BDD.false():
                    return [[]]
                else:
                    return []

            # not a leaf
            a_lit = a_bdd.get_index()
            then_clauses = _rec_bdd2cnf(a_bdd.then_child())
            result = [(clause + [(a_lit * -1)]) for clause in
                      then_clauses]
            else_clauses = _rec_bdd2cnf(a_bdd.else_child())
            result.extend([(clause + [a_lit]) for clause in
                          else_clauses])
            cache[a_bdd] = result
            return result

        # start recursion
        return _rec_bdd2cnf(self)

    @staticmethod
    def true():
        b = BDD()
        b._cudd_bdd = cudd.One()
        return b

    @staticmethod
    def false():
        b = BDD()
        b._cudd_bdd = cudd.Zero()
        return b

    @staticmethod
    def make_eq(b, c):
        return BDD.make_impl(b, c) & BDD.make_impl(c, b)

    @staticmethod
    def make_impl(b, c):
        return ~b | c

    @staticmethod
    def get_clause(bs):
        assert bs
        bs
        clause = BDD.false()
        for b in bs:
            clause |= b
        return clause

    @staticmethod
    def get_cube(bs):
        assert bs

        cube = BDD.true()
        for b in bs:
            cube &= b
        return cube

    @staticmethod
    def init_cudd():
        global cudd

        cudd = pycudd.DdManager()
        cudd.SetDefault()
        cudd.AutodynEnable(4)  # SIFT

    @staticmethod
    def disable_reorder():
        cudd.AutodynDisable()

    @staticmethod
    def next_var():
        global next_free_var

        next_free_var += 1
        return next_free_var - 1

    @staticmethod
    def conciliate(F, G, var_list=None):
        """ Procedure based on the paper Abstract Refinement with Craig
        Interpolation by Esparza, Kiefer and Schwoon """
        # it is required that F implies G
        assert (F != BDD.true())
        assert (G != BDD.false())
        assert (~F | G) == BDD.true()
        # create variable list
        if var_list is None:
            var_list = range(next_free_var)

        def occ(x):
            return x.occ_sem(var_list)

        # more implication checks (non-trivial implication)
        if F == BDD.false():
            log.WRN_MSG("F is FALSE")
            return (set(occ(G)), G, G)
        if G == BDD.true():
            log.WRN_MSG("G is TRUE")
            return (set(occ(F)), F, F)
        # we now compute two interpolants that we will return
        I = F
        J = G
        Z = set(occ(F) + occ(G))
        Y = set([])
        while True:
            X = set(occ(I)) - set(occ(J))
            if X:
                I = I.exist_abstract(
                    BDD.get_cube([BDD(x) for x in X]))
                Z -= X
            Y = set(occ(J)) - set(occ(I))
            if Y:
                J = I.univ_abstract(
                    BDD.get_cube([BDD(y) for y in Y]))
                Z -= Y
            else:
                break
        # these are interpolants so they should be implied by F and imply G
        assert (~F | I) == BDD.true()
        assert (~F | J) == BDD.true()
        assert (~I | G) == BDD.true()
        assert (~J | G) == BDD.true()
        # return the conciliating set and both interpolants
        return (Z, I, J)


# initialize the whole thing
BDD.init_cudd()
