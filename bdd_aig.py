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
along with AbsSynthe. If not, see <http://www.gnu.org/licenses/>.


Guillermo A. Perez
Universite Libre de Bruxelles
gperezme@ulb.ac.be
"""

from itertools import imap, chain
from utils import funcomp
from aig import (
    AIG,
    strip_lit,
    lit_is_negated,
    symbol_lit,
    get_primed_var,
    negate_lit
)
from cudd_bdd import BDD
import log


class BDDAIG(AIG):
    def __init__(self, aig=None, aiger_file_name=None,
                 intro_error_latch=False):
        assert aig is not None or aiger_file_name is not None
        if aig is None:
            aig = AIG(aiger_file_name, intro_error_latch=intro_error_latch)
        self._copy_from_aig(aig)
        # initialize local attributes
        self.lit_to_bdd = dict()
        self.bdd_to_lit = dict()
        self._cached_transition = None
        self.bdd_gate_cache = dict()
        self.latch_restr = None

    def _copy_from_aig(self, aig):
        assert isinstance(aig, AIG)
        # shallow copy of all attributes of aig
        self.__dict__ = aig.__dict__.copy()

    def set_lit2bdd(self, lit, b):
        self.lit_to_bdd[lit] = b
        return self

    def rem_lit2bdd(self, lit):
        del self.lit_to_bdd[lit]
        return self

    # short-circuit the error bdd and restrict the whole thing to
    # the relevant latches
    def short_error(self, b):
        nu_bddaig = BDDAIG(aig=self)
        nu_bddaig.set_lit2bdd(self.error_fake_latch.next, b)
        bdd_latch_deps = set(b.occ_sem(imap(symbol_lit,
                                            self.iterate_latches())))
        latch_deps = reduce(set.union,
                            map(self.get_lit_latch_deps,
                                bdd_latch_deps))
        if log.debug:
            not_deps = [l.lit for l in self.iterate_latches()
                        if l.lit not in latch_deps]
            log.DBG_MSG(str(len(not_deps)) + " Latches not needed: " +
                        str(not_deps))
        self.latch_restr = latch_deps
        return nu_bddaig

    def iterate_latches(self):
        for l in AIG.iterate_latches(self):
            if self.latch_restr is not None and\
                    l not in self.latch_restr and\
                    l != self.error_fake_latch:
                continue
            yield l

    def lit2bdd(self, lit):
        """ Convert AIGER lit into BDD """
        # query cache
        if lit in self.lit_to_bdd:
            return self.lit_to_bdd[lit]
        # get stripped lit
        stripped_lit = strip_lit(lit)
        (intput, latch, and_gate) = self.get_lit_type(stripped_lit)
        # is it an input, latch, gate or constant
        if intput or latch:
            result = BDD(stripped_lit)
        elif and_gate:
            result = (self.lit2bdd(and_gate.rhs0) &
                      self.lit2bdd(and_gate.rhs1))
        else:  # 0 literal, 1 literal and errors
            result = BDD.false()
        # cache result
        self.lit_to_bdd[stripped_lit] = result
        self.bdd_to_lit[result] = stripped_lit
        # check for negation
        if lit_is_negated(lit):
            result = ~result
            self.lit_to_bdd[lit] = result
            self.bdd_to_lit[result] = lit
        return result

    def prime_latches_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        latches = [x.lit for x in self.iterate_latches()]
        platches = map(get_primed_var, latches)
        return b.swap_variables(latches, platches)

    def prime_all_inputs_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        inputs = [x.lit for x in chain(self.iterate_uncontrollable_inputs(),
                                       self.iterate_controllable_inputs())]
        pinputs = map(get_primed_var, inputs)
        return b.swap_variables(inputs, pinputs)

    def unprime_all_inputs_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        inputs = [x.lit for x in chain(self.iterate_uncontrollable_inputs(),
                                       self.iterate_controllable_inputs())]
        pinputs = map(get_primed_var, inputs)
        return b.swap_variables(pinputs, inputs)

    def unprime_latches_in_bdd(self, b):
        # unfortunately swap_variables needs a list
        latches = [x.lit for x in self.iterate_latches()]
        platches = map(get_primed_var, latches)
        return b.swap_variables(platches, latches)

    def trans_rel_bdd(self):
        # check cache
        if self._cached_transition is not None:
            return self._cached_transition
        b = BDD.true()
        for x in self.iterate_latches():
            b &= BDD.make_eq(BDD(get_primed_var(x.lit)),
                             self.lit2bdd(x.next))
        self._cached_transition = b
        log.BDD_DMP(b, "Composed and cached the concrete transition relation.")
        return b

    def init_state_bdd(self):
        b = BDD.true()
        for x in self.iterate_latches():
            b &= ~BDD(x.lit)
        return b

    def over_post_bdd(self, src_states_bdd, sys_strat=None,
                      restrict_like_crazy=False):
        """ Over-approximated version of concrete post which can be done even
        without the transition relation """
        strat = BDD.true()
        if sys_strat is not None:
            strat &= sys_strat
        # to do this, we use an over-simplified transition relation, EXu,Xc
        b = BDD.true()
        for x in self.iterate_latches():
            temp = BDD.make_eq(BDD(get_primed_var(x.lit)),
                               self.lit2bdd(x.next))
            b &= temp.and_abstract(
                strat,
                BDD.make_cube(imap(
                    funcomp(BDD, symbol_lit),
                    self.iterate_controllable_inputs()
                )))
            if restrict_like_crazy:
                b = b.restrict(src_states_bdd)
        b &= src_states_bdd
        b = b.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                          chain(self.iterate_latches(),
                                self.iterate_uncontrollable_inputs()))))
        return self.unprime_latches_in_bdd(b)

    def post_bdd(self, src_states_bdd, sys_strat=None,
                 restrict_like_crazy=False,
                 use_trans=False, over_approx=False):
        """
        POST = EL.EXu.EXc : src(L) ^ T(L,Xu,Xc,L') [^St(L,Xu,Xc)]
        optional argument fixes possible actions for the environment
        """
        if not use_trans or over_approx:
            return self.over_post_bdd(src_states_bdd, sys_strat)
        transition_bdd = self.trans_rel_bdd()
        trans = transition_bdd
        if sys_strat is not None:
            trans &= sys_strat
        if restrict_like_crazy:
            trans = trans.restrict(src_states_bdd)

        suc_bdd = trans.and_abstract(
            src_states_bdd,
            BDD.make_cube(imap(funcomp(BDD, symbol_lit), chain(
                self.iterate_controllable_inputs(),
                self.iterate_uncontrollable_inputs(),
                self.iterate_latches())
            )))
        return self.unprime_latches_in_bdd(suc_bdd)

    def substitute_latches_next(self, b, use_trans=False, restrict_fun=None):
        if use_trans:
            transition_bdd = self.trans_rel_bdd()
            trans = transition_bdd
            if restrict_fun is not None:
                trans = trans.restrict(restrict_fun)
            primed_bdd = self.prime_latches_in_bdd(b)
            primed_latches = BDD.make_cube(
                imap(funcomp(BDD, get_primed_var, symbol_lit),
                     self.iterate_latches()))
            return trans.and_abstract(primed_bdd,
                                      primed_latches)
        else:
            latches = [x.lit for x in self.iterate_latches()]
            latch_funs = [self.lit2bdd(x.next) for x in
                          self.iterate_latches()]
            if restrict_fun is not None:
                latch_funs = [x.restrict(restrict_fun) for x in latch_funs]
            # take a transition step backwards
            return b.compose(latches, latch_funs)

    def upre_bdd(self, dst_states_bdd, env_strat=None, get_strat=False,
                 restrict_like_crazy=False, use_trans=False):
        """
        UPRE = EXu.AXc.EL' : T(L,Xu,Xc,L') ^ dst(L') [^St(L,Xu)]
        """
        # take a transition step backwards
        p_bdd = self.substitute_latches_next(
            dst_states_bdd,
            restrict_fun=~dst_states_bdd,
            use_trans=use_trans)
        # use the given strategy
        if env_strat is not None:
            p_bdd &= env_strat
        # there is an uncontrollable action such that for all contro...
        temp_bdd = p_bdd.univ_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_controllable_inputs())))
        p_bdd = temp_bdd.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               self.iterate_uncontrollable_inputs())))
        # prepare the output
        if get_strat:
            return temp_bdd
        else:
            return p_bdd

    def cpre_bdd(self, dst_states_bdd, get_strat=False, use_trans=False,
                 restrict_like_crazy=False):
        """ CPRE = AXu.EXc.EL' : T(L,Xu,Xc,L') ^ dst(L') """
        # take a transition step backwards
        p_bdd = self.substitute_latches_next(dst_states_bdd,
                                             use_trans=use_trans)
        # for all uncontrollable action there is a contro...
        # note: if argument get_strat == True then we leave the "good"
        # controllable actions in the bdd
        if not get_strat:
            p_bdd = p_bdd.exist_abstract(
                BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                                   self.iterate_controllable_inputs())))
            p_bdd = p_bdd.univ_abstract(
                BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                                   self.iterate_uncontrollable_inputs())))
        return p_bdd

    def strat_is_inductive(self, strat, use_trans=False):
        strat_dom = strat.exist_abstract(
            BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                               chain(self.iterate_controllable_inputs(),
                                     self.iterate_uncontrollable_inputs()))))
        p_bdd = self.substitute_latches_next(strat_dom, use_trans=use_trans)
        return BDD.make_impl(strat, p_bdd) == BDD.true()

    def get_optimized_and_lit(self, a_lit, b_lit):
        if a_lit == 0 or b_lit == 0:
            return 0
        if a_lit == 1 and b_lit == 1:
            return 1
        if a_lit == 1:
            return b_lit
        if b_lit == 1:
            return a_lit
        if a_lit > 1 and b_lit > 1:
            a_b_lit = self.next_lit()
            self.add_gate(a_b_lit, a_lit, b_lit)
            return a_b_lit
        assert 0, 'impossible'

    def bdd2aig(self, a_bdd):
        """
        Walk given BDD node (recursively). If given input BDD requires
        intermediate AND gates for its representation, the function adds them.
        Literal representing given input BDD is `not` added to the spec.
        """
        if a_bdd in self.bdd_gate_cache:
            return self.bdd_gate_cache[a_bdd]

        if a_bdd.is_constant():
            res = int(a_bdd == BDD.true())   # in aiger 0/1 = False/True
            return res
        # get an index of variable,
        # all variables used in bdds also introduced in aiger,
        # except fake error latch literal,
        # but fake error latch will not be used in output functions (at least
        # we don't need this..)
        a_lit = a_bdd.get_index()
        assert (a_lit != self.error_fake_latch.lit),\
               ("using error latch in the " +
                "definition of output " +
                "function is not allowed")
        t_bdd = a_bdd.then_child()
        e_bdd = a_bdd.else_child()
        t_lit = self.bdd2aig(t_bdd)
        e_lit = self.bdd2aig(e_bdd)
        # ite(a_bdd, then_bdd, else_bdd)
        # = a*then + !a*else
        # = !(!(a*then) * !(!a*else))
        # -> in general case we need 3 more ANDs
        a_t_lit = self.get_optimized_and_lit(a_lit, t_lit)
        na_e_lit = self.get_optimized_and_lit(negate_lit(a_lit), e_lit)
        n_a_t_lit = negate_lit(a_t_lit)
        n_na_e_lit = negate_lit(na_e_lit)
        ite_lit = self.get_optimized_and_lit(n_a_t_lit, n_na_e_lit)
        res = negate_lit(ite_lit)
        if a_bdd.is_complement():
            res = negate_lit(res)
        # cache result
        self.bdd_gate_cache[a_bdd] = res
        return res

    # Given a bdd representing the set of safe states-action pairs for the
    # controller (Eve) we compute a winning strategy for her (trying to get a
    # minimal one via a greedy algo on the way).
    def extract_output_funs(self, strategy, care_set=None):
        """
        Calculate BDDs for output functions given non-deterministic winning
        strategy.
        """
        if care_set is None:
            care_set = BDD.true()

        output_models = dict()
        all_outputs = [BDD(x.lit) for x in self.iterate_controllable_inputs()]
        for c_symb in self.iterate_controllable_inputs():
            c = BDD(c_symb.lit)
            others = set(set(all_outputs) - set([c]))
            if others:
                others_cube = BDD.make_cube(others)
                c_arena = strategy.exist_abstract(others_cube)
            else:
                c_arena = strategy
            # pairs (x,u) in which c can be true
            can_be_true = c_arena.cofactor(c)
            # pairs (x,u) in which c can be false
            can_be_false = c_arena.cofactor(~c)
            must_be_true = (~can_be_false) & can_be_true
            must_be_false = (~can_be_true) & can_be_false
            local_care_set = care_set & (must_be_true | must_be_false)
            # Restrict operation:
            #   on care_set: must_be_true.restrict(care_set) <-> must_be_true
            c_model = min([must_be_true.safe_restrict(local_care_set),
                          (~must_be_false).safe_restrict(local_care_set)],
                          key=lambda x: x.dag_size())
            output_models[c_symb.lit] = c_model
            log.DBG_MSG("Size of function for " + str(c.get_index()) + " = " +
                        str(c_model.dag_size()))
            strategy &= BDD.make_eq(c, c_model)
        return output_models
