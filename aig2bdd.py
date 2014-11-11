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

from itertools import imap, chain
from utils import funcomp
from aig import (
    strip_lit,
    get_lit_type,
    lit_is_negated,
    iterate_latches,
    get_primed_var,
    symbol_lit,
    iterate_controllable_inputs,
    iterate_uncontrollable_inputs,
)
from cudd_bdd import BDD
import log


lit_to_bdd = dict()
bdd_to_lit = dict()


def get_bdd_for_lit(lit):
    """ Convert AIGER lit into BDD """
    # query cache
    if lit in lit_to_bdd:
        return lit_to_bdd[lit]
    # get stripped lit
    stripped_lit = strip_lit(lit)
    (intput, latch, and_gate) = get_lit_type(stripped_lit)
    # is it an input, latch, gate or constant
    if intput or latch:
        result = BDD(stripped_lit)
    elif and_gate:
        result = (get_bdd_for_lit(and_gate.rhs0) &
                  get_bdd_for_lit(and_gate.rhs1))
    else:  # 0 literal, 1 literal and errors
        result = BDD.false()
    # cache result
    lit_to_bdd[stripped_lit] = result
    bdd_to_lit[result] = stripped_lit
    # check for negation
    if lit_is_negated(lit):
        result = ~result
        lit_to_bdd[lit] = result
        bdd_to_lit[result] = lit
    return result


def prime_latches_in_bdd(b):
    # unfortunately swap_variables needs a list
    latches = [x.lit for x in iterate_latches()]
    platches = map(get_primed_var, latches)
    return b.swap_variables(latches, platches)


def prime_all_inputs_in_bdd(b):
    # unfortunately swap_variables needs a list
    inputs = [x.lit for x in chain(iterate_uncontrollable_inputs(),
                                   iterate_controllable_inputs())]
    pinputs = map(get_primed_var, inputs)
    return b.swap_variables(inputs, pinputs)


def unprime_all_inputs_in_bdd(b):
    # unfortunately swap_variables needs a list
    inputs = [x.lit for x in chain(iterate_uncontrollable_inputs(),
                                   iterate_controllable_inputs())]
    pinputs = map(get_primed_var, inputs)
    return b.swap_variables(pinputs, inputs)


def unprime_latches_in_bdd(b):
    # unfortunately swap_variables needs a list
    latches = [x.lit for x in iterate_latches()]
    platches = map(get_primed_var, latches)
    return b.swap_variables(platches, latches)


cached_transition = None


def trans_rel_bdd():
    global cached_transition

    # check cache
    if cached_transition:
        return cached_transition
    b = BDD.true()
    for x in iterate_latches():
        b &= BDD.make_eq(BDD(get_primed_var(x.lit)),
                         get_bdd_for_lit(x.next))
    cached_transition = b
    log.BDD_DMP(b, "Composed and cached the concrete transition relation.")
    return b


def init_state_bdd():
    b = BDD.true()
    for x in iterate_latches():
        b &= ~BDD(x.lit)
    return b


def over_post_bdd(src_states_bdd, sys_strat=None,
                  restrict_like_crazy=False):
    """ Over-approximated version of concrete post which can be done even
    without the transition relation """
    strat = BDD.true()
    if sys_strat is not None:
        strat &= sys_strat
    # to do this, we use an over-simplified transition relation, EXu,Xc
    b = BDD.true()
    for x in iterate_latches():
        temp = BDD.make_eq(BDD(get_primed_var(x.lit)),
                           get_bdd_for_lit(x.next))
        b &= temp.and_abstract(
            strat,
            BDD.get_cube(imap(
                funcomp(BDD, symbol_lit),
                iterate_controllable_inputs()
            )))
        if restrict_like_crazy:
            b = b.restrict(src_states_bdd)
    b &= src_states_bdd
    b = b.exist_abstract(
        BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                     chain(iterate_latches(),
                           iterate_uncontrollable_inputs()))))
    return unprime_latches_in_bdd(b)


def post_bdd(src_states_bdd, sys_strat=None, restrict_like_crazy=False,
             use_trans=False, over_approx=False):
    """
    POST = EL.EXu.EXc : src(L) ^ T(L,Xu,Xc,L') [^St(L,Xu,Xc)]
    optional argument fixes possible actions for the environment
    """
    if not use_trans or over_approx:
        return over_post_bdd(src_states_bdd, sys_strat)
    transition_bdd = trans_rel_bdd()
    trans = transition_bdd
    if sys_strat is not None:
        trans &= sys_strat
    if restrict_like_crazy:
        trans = trans.restrict(src_states_bdd)

    suc_bdd = trans.and_abstract(
        src_states_bdd,
        BDD.get_cube(imap(funcomp(BDD, symbol_lit), chain(
            iterate_controllable_inputs(),
            iterate_uncontrollable_inputs(),
            iterate_latches())
        )))
    return unprime_latches_in_bdd(suc_bdd)


def substitute_latches_next(b, use_trans=False, restrict_fun=None):
    if use_trans:
        transition_bdd = trans_rel_bdd()
        trans = transition_bdd
        if restrict_fun is not None:
            trans = trans.restrict(restrict_fun)
        primed_bdd = prime_latches_in_bdd(b)
        primed_latches = BDD.get_cube(
            imap(funcomp(BDD, get_primed_var, symbol_lit),
                 iterate_latches()))
        return trans.and_abstract(primed_bdd,
                                  primed_latches)
    else:
        latches = [x.lit for x in iterate_latches()]
        latch_funs = [get_bdd_for_lit(x.next) for x in
                      iterate_latches()]
        if restrict_fun is not None:
            latch_funs = [x.restrict(restrict_fun) for x in latch_funs]
        # take a transition step backwards
        return b.compose(latches, latch_funs)


def upre_bdd(dst_states_bdd, env_strat=None, get_strat=False,
             restrict_like_crazy=False, use_trans=False):
    """
    UPRE = EXu.AXc.EL' : T(L,Xu,Xc,L') ^ dst(L') [^St(L,Xu)]
    """
    # take a transition step backwards
    p_bdd = substitute_latches_next(dst_states_bdd,
                                    restrict_fun=~dst_states_bdd,
                                    use_trans=use_trans)
    # use the given strategy
    if env_strat is not None:
        p_bdd &= env_strat
    # there is an uncontrollable action such that for all contro...
    temp_bdd = p_bdd.univ_abstract(
        BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                          iterate_controllable_inputs())))
    p_bdd = temp_bdd.exist_abstract(
        BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                          iterate_uncontrollable_inputs())))
    # prepare the output
    if get_strat:
        return temp_bdd
    else:
        return p_bdd


def cpre_bdd(dst_states_bdd, get_strat=False, use_trans=False):
    """ CPRE = AXu.EXc.EL' : T(L,Xu,Xc,L') ^ dst(L') """
    # take a transition step backwards
    p_bdd = substitute_latches_next(dst_states_bdd,
                                    use_trans=use_trans)
    # for all uncontrollable action there is a contro...
    # note: if argument get_strat == True then we leave the "good"
    # controllable actions in the bdd
    if not get_strat:
        p_bdd = p_bdd.exist_abstract(
            BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                              iterate_controllable_inputs())))
        p_bdd = p_bdd.univ_abstract(
            BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                              iterate_uncontrollable_inputs())))
    return p_bdd


def strat_is_inductive(strat, use_trans=False):
    strat_dom = strat.exist_abstract(
        BDD.get_cube(imap(funcomp(BDD, symbol_lit),
                          chain(iterate_controllable_inputs(),
                                iterate_uncontrollable_inputs()))))
    p_bdd = substitute_latches_next(strat_dom, use_trans=use_trans)
    return BDD.make_impl(strat, p_bdd) == BDD.true()
