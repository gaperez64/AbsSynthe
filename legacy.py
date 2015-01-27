# coding=utf-8

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

import argparse
import log
import bdd
import spred
import aig

# don't change status numbers since they are used by the performance script
EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20

# globals and caches
error_fake_latch = None
lit_to_bdd = dict()
bdd_to_lit = dict()
cached_transition = None
bdd_gate_cache = dict()
# abstraction variables
preds = None
cached_abs_transition = None
procd_blocks = dict()
block_funs = dict()
cached_block_funs = None
cached_abs_eq = None
abs_eq_procd_blocks = dict()
# algorithms' options
restrict_like_crazy = None
model_check = None
ini_latch = None
use_abs = None
use_trans = None
ini_reach_latches = None
most_precise = None
min_win = None
loss_steps = None
ini_reach = None


# ##################### AIG, BDD, Helper ALGOS #######################

def reset_caches():
    global cached_abs_transition, cached_block_funs,\
        block_funs, procd_blocks, cached_abs_eq,\
        abs_eq_procd_blocks

    cached_abs_transition = None
    cached_block_funs = None
    block_funs = dict()
    procd_blocks = dict()
    cached_abs_eq = None
    abs_eq_procd_blocks = dict()


def introduce_error_latch():
    global error_fake_latch

    if error_fake_latch is not None:
        return
    error_fake_latch = aig.new_aiger_symbol()
    error_symbol = aig.get_err_symbol()
    error_fake_latch.lit = aig.next_lit()
    error_fake_latch.name = "fake_error_latch"
    error_fake_latch.next = error_symbol.lit
    # lets save two variables for error and primed version
    # this also saves all variables <= error_symbol.lit + 1
    # for CONCRETE variables
    bdd.BDD(error_fake_latch.lit)
    bdd.BDD(get_primed_variable(error_fake_latch.lit))


def iterate_latches_and_error():
    introduce_error_latch()
    for l in aig.iterate_latches():
        yield l
    yield error_fake_latch


def get_primed_variable(lit):
    return aig.strip_lit(lit) + 1


def get_bdd_for_aig_lit(lit):
    """ Convert AIGER lit into BDD.
    param lit: 'signed' value of gate
    returns: BDD representation of the input literal
    """
    # query cache
    if lit in lit_to_bdd:
        return lit_to_bdd[lit]
    # get stripped lit
    stripped_lit = aig.strip_lit(lit)
    if stripped_lit == error_fake_latch.lit:
        (intput, latch, and_gate) = (None, error_fake_latch, None)
    else:
        (intput, latch, and_gate) = aig.get_lit_type(stripped_lit)
    # is it an input, latch, gate or constant
    if intput or latch:
        result = bdd.BDD(stripped_lit)
    elif and_gate:
        result = (get_bdd_for_aig_lit(and_gate.rhs0) &
                  get_bdd_for_aig_lit(and_gate.rhs1))
    else:  # 0 literal, 1 literal and errors
        result = bdd.false()
    # cache result
    lit_to_bdd[stripped_lit] = result
    bdd_to_lit[result] = stripped_lit
    # check for negation
    if aig.lit_is_negated(lit):
        result = ~result
        lit_to_bdd[lit] = result
        bdd_to_lit[result] = lit
    return result


def get_controllable_inputs_bdds():
    bdds = [bdd.BDD(i.lit) for i in
            aig.iterate_controllable_inputs()]
    return bdds


def get_uncontrollable_inputs_bdds():
    bdds = [bdd.BDD(i.lit) for i in
            aig.iterate_uncontrollable_inputs()]
    return bdds


def get_all_latches_as_bdds():
    bdds = [bdd.BDD(l.lit) for l in
            iterate_latches_and_error()]
    return bdds


def unprime_latches_in_bdd(states_bdd):
    # unfortunately swap_variables requires a list and not an iterator
    latches = [x.lit for x in iterate_latches()]
    platches = map(get_primed_variable, latches)
    return states_bdd.swap_variables(platches, latches)


def prime_latches_in_bdd(states_bdd):
    latches = [x.lit for x in iterate_latches_and_error()]
    platches = [get_primed_variable(x.lit) for x in
                iterate_latches_and_error()]
    return states_bdd.swap_variables(latches, platches)


def prime_uncontrollable_in_bdd(inputs_bdd):
    unc = [x.lit for x in aig.iterate_uncontrollable_inputs()]
    punc = [get_primed_variable(x.lit) for x in
            aig.iterate_uncontrollable_inputs()]
    return inputs_bdd.swap_variables(unc, punc)


def prime_controllable_in_bdd(inputs_bdd):
    ctrl = [x.lit for x in aig.iterate_controllable_inputs()]
    pctrl = [get_primed_variable(x.lit) for x in
             aig.iterate_controllable_inputs()]
    return inputs_bdd.swap_variables(ctrl, pctrl)


def unprime_blocks_in_bdd(states_bdd):
    blocks = [x for x in preds.abs_blocks]
    pblocks = [get_primed_variable(x) for x in preds.abs_blocks]
    return states_bdd.swap_variables(pblocks, blocks)


def prime_blocks_in_bdd(states_bdd):
    blocks = [x for x in preds.abs_blocks]
    pblocks = [get_primed_variable(x) for x in preds.abs_blocks]
    return states_bdd.swap_variables(blocks, pblocks)


def compose_transition_bdd():
    global cached_transition

    # check cache
    if cached_transition:
        return cached_transition
    b = bdd.true()
    for x in iterate_latches_and_error():
        b &= bdd.make_eq(bdd.BDD(get_primed_variable(x.lit)),
                         get_bdd_for_aig_lit(x.next))
    cached_transition = b
    log.BDD_DMP(b, "Composed and cached the concrete transition relation")
    return b


def compose_abs_eq_bdd():
    global cached_abs_eq, abs_eq_procd_blocks

    # check cache
    if cached_abs_eq is None:
        log.DBG_MSG("Rebuilding abs_eq")
        for b in preds.abs_blocks:
            abs_eq_procd_blocks[b] = False
        c = bdd.true()
    else:
        c = cached_abs_eq

    for b in preds.abs_blocks:
        if b not in procd_blocks or not procd_blocks[b]:
            c &= bdd.make_eq(bdd.BDD(b), preds.block_to_bdd[b])
    # cache c
    cached_abs_eq = c
    return c


def compose_abs_transition_bdd():
    global cached_abs_transition, procd_blocks

    # check cache
    if cached_abs_transition is None:
        log.DBG_MSG("Rebuilding abstract transition relation")
        for b in preds.abs_blocks:
            procd_blocks[b] = False
        c = bdd.true()
    else:
        c = cached_abs_transition

    latches = [x.lit for x in iterate_latches_and_error()]
    latches_bdd = bdd.get_cube(get_all_latches_as_bdds())
    latch_funs = [get_bdd_for_aig_lit(x.next) for x in
                  iterate_latches_and_error()]
    for b in preds.abs_blocks:
        if b not in procd_blocks or not procd_blocks[b]:
            procd_blocks[b] = True
            temp = bdd.make_eq(bdd.BDD(get_primed_variable(b)),
                               preds.block_to_bdd[b])
            c &= temp.compose(latches, latch_funs)
    # cache c
    cached_abs_transition = c
    return c.and_abstract(compose_abs_eq_bdd(), latches_bdd)


def alpha_over(conc_bdd):
    c = compose_abs_eq_bdd()
    latches_bdd = bdd.get_cube(get_all_latches_as_bdds())
    c = c.and_abstract(conc_bdd, latches_bdd)
    return c


def alpha_under(conc_bdd):
    return ~alpha_over(~conc_bdd)


def gamma(abs_bdd):
    return abs_bdd.compose(preds.block_to_bdd.keys(),
                           preds.block_to_bdd.values())


def compose_init_state_bdd():
    b = bdd.true()
    for x in iterate_latches_and_error():
        b &= ~bdd.BDD(x.lit)
    return b


def compose_abs_init_state_bdd():
    return alpha_over(compose_init_state_bdd())


def single_post_bdd(src_states_bdd, sys_strat=None):
    """ Over-approximated version of concrete post which can be done even
    without the transition relation """
    strat = bdd.true()
    if sys_strat is not None:
        strat &= sys_strat
    # to do this, we use an over-simplified transition relation, EXu,Xc
    b = bdd.true()
    for x in iterate_latches_and_error():
        temp = bdd.make_eq(bdd.BDD(get_primed_variable(x.lit)),
                           get_bdd_for_aig_lit(x.next))
        b &= temp.and_abstract(strat,
                               bdd.get_cube(get_controllable_inputs_bdds()))
        if restrict_like_crazy:
            b = b.restrict(src_states_bdd)
    b &= src_states_bdd
    b = b.exist_abstract(
        bdd.get_cube(get_all_latches_as_bdds() +
                     get_uncontrollable_inputs_bdds()))
    return unprime_latches_in_bdd(b)


def post_bdd(src_states_bdd, sys_strat=None):
    """
    POST = EL.EXu.EXc : src(L) ^ T(L,Xu,Xc,L') [^St(L,Xu,Xc)]
    optional argument fixes possible actions for the environment
    """
    if not use_trans:
        return single_post_bdd(src_states_bdd, sys_strat)
    transition_bdd = compose_transition_bdd()
    trans = transition_bdd
    if sys_strat is not None:
        trans &= sys_strat
    if restrict_like_crazy:
        trans = trans.restrict(src_states_bdd)

    suc_bdd = trans.and_abstract(
        src_states_bdd,
        bdd.get_cube(
            get_controllable_inputs_bdds() +
            get_uncontrollable_inputs_bdds() +
            get_all_latches_as_bdds()))
    return unprime_latches_in_bdd(suc_bdd)


def single_pre_bdd(dst_states_bdd, strat=None):
    if strat is None:
        strat = bdd.true()

    latches = [x.lit for x in iterate_latches_and_error()]
    latch_funs = [get_bdd_for_aig_lit(x.next) for x in
                  iterate_latches_and_error()]
    if restrict_like_crazy:
        latch_funs = [x.restrict(~dst_states_bdd) for x in latch_funs]
    # take a transition step backwards
    p_bdd = dst_states_bdd.compose(latches, latch_funs)
    # use the given strategy
    p_bdd &= strat
    p_bdd = p_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds() +
                     get_controllable_inputs_bdds()))
    return p_bdd


def single_pre_env_bdd(dst_states_bdd, env_strat=None, get_strat=False):
    if env_strat is not None:
        strat = env_strat
    else:
        strat = bdd.true()

    latches = [x.lit for x in iterate_latches_and_error()]
    latch_funs = [get_bdd_for_aig_lit(x.next) for x in
                  iterate_latches_and_error()]
    if restrict_like_crazy:
        latch_funs = [x.restrict(~dst_states_bdd) for x in latch_funs]
    # take a transition step backwards
    p_bdd = dst_states_bdd.compose(latches, latch_funs)
    # use the given strategy
    p_bdd &= strat
    # there is an uncontrollable action such that for all contro...
    temp_bdd = p_bdd.univ_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = temp_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))
    if get_strat:
        return temp_bdd
    else:
        return p_bdd


def single_pre_sys_bdd(dst_states_bdd, get_strat=False):
    latches = [x.lit for x in iterate_latches_and_error()]
    latch_funs = [get_bdd_for_aig_lit(x.next) for x in
                  iterate_latches_and_error()]
    # take a transition step backwards
    p_bdd = dst_states_bdd.compose(latches, latch_funs)
    # for all uncontrollable action there is a contro...
    # note: if argument as_strat == True then we leave the "good"
    # controllable actions in the bdd
    if not get_strat:
        p_bdd = p_bdd.exist_abstract(
            bdd.get_cube(get_controllable_inputs_bdds()))
        p_bdd = p_bdd.univ_abstract(
            bdd.get_cube(get_uncontrollable_inputs_bdds()))
    return p_bdd


def pre_env_bdd(dst_states_bdd, env_strat=None, get_strat=False):
    """
    UPRE = EXu.AXc.EL' : T(L,Xu,Xc,L') ^ dst(L') [^St(L,Xu)]
    optional arguments fix possible actions for the environment
    and possible actions for the controller
    """
    # can we use the transition relation?
    if not use_trans:
        return single_pre_env_bdd(dst_states_bdd, env_strat, get_strat)
    # do as promised
    transition_bdd = compose_transition_bdd()
    trans = transition_bdd
    if env_strat is not None:
        trans &= env_strat
    if restrict_like_crazy:
        trans = trans.restrict(~dst_states_bdd)

    primed_states = prime_latches_in_bdd(dst_states_bdd)
    primed_latches = prime_latches_in_bdd(bdd.get_cube(
        get_all_latches_as_bdds()))
    p_bdd = trans.and_abstract(primed_states,
                               primed_latches)
    temp_bdd = p_bdd.univ_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = temp_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    if get_strat:
        return temp_bdd
    else:
        return p_bdd


def pre_sys_bdd(dst_states_bdd):
    """ CPRE = AXu.EXc.EL' : T(L,Xu,Xc,L') ^ dst(L') """
    # can se use the transition relation?
    if not use_trans:
        return single_pre_sys_bdd(dst_states_bdd)
    # get the transition relation and do as usual
    transition_bdd = compose_transition_bdd()
    primed_states = prime_latches_in_bdd(dst_states_bdd)
    abstract_bdd = prime_latches_in_bdd(bdd.get_cube(
        get_all_latches_as_bdds() +
        get_controllable_inputs_bdds()))
    p_bdd = transition_bdd.and_abstract(primed_states,
                                        abstract_bdd)
    p_bdd = p_bdd.univ_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    return p_bdd


def update_block_funs():
    global cached_block_funs, block_funs

    latches = [x.lit for x in iterate_latches_and_error()]
    latch_funs = [get_bdd_for_aig_lit(x.next) for x in
                  iterate_latches_and_error()]
    # check cache
    if cached_block_funs is None:
        log.DBG_MSG("Rebuilding block_funs")
        block_funs = dict()
        for b in preds.abs_blocks:
            block_funs[b] = gamma(preds.block_to_bdd[b]).compose(latches,
                                                                 latch_funs)
    else:
        for b in preds.abs_blocks:
            if b not in block_funs:
                block_funs[b] = gamma(preds.block_to_bdd[b])
                block_funs[b] = block_funs[b].compose(latches,
                                                      latch_funs)
    # set cache
    cached_block_funs = bdd.true()


def single_pre_env_bdd_abs(dst_states_bdd, get_strat=False):
    # if we want the most precise version of the operator
    if most_precise:
        return alpha_over(single_pre_env_bdd(gamma(dst_states_bdd),
                                             get_strat=get_strat))
    # make sure the block_funs are current
    update_block_funs()
    # take one step backwards and over-app
    tmp_bdd = dst_states_bdd.compose(block_funs.keys(),
                                     block_funs.values())
    tmp_bdd = alpha_over(tmp_bdd)
    # there is an uncontrollable action, such that for all contro...
    tmp_bdd = tmp_bdd.univ_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = tmp_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    # was a strategy asked for?
    if get_strat:
        return tmp_bdd
    else:
        return p_bdd


def single_pre_env_bdd_uabs(dst_states_bdd, env_strat=None):
    # if we want the most precise version of the operator
    if most_precise:
        if env_strat is not None:
            strat = gamma(env_strat)
        else:
            strat = None
        return alpha_under(single_pre_env_bdd(gamma(dst_states_bdd),
                                              env_strat=strat))
    # make sure the block_funs are current
    update_block_funs()
    # take one step backwards and over-app
    tmp_bdd = ~dst_states_bdd
    tmp_bdd = tmp_bdd.compose(block_funs.keys(),
                              block_funs.values())
    tmp_bdd = alpha_over(tmp_bdd)
    if env_strat is not None:
        tmp_bdd &= env_strat
    # we are using the complement of the original formula so
    # we want that for all uncontrollable, there is a contro...
    tmp_bdd = tmp_bdd.exist_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = tmp_bdd.univ_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    return ~p_bdd


def over_post_bdd_abs(src_states_bdd, env_strat=None):
    # make sure the block_funs are current
    update_block_funs()
    # take the step forward and get rid of latches
    conc_src = gamma(src_states_bdd)
    if env_strat is not None:
        conc_strat = gamma(env_strat)
    else:
        conc_strat = bdd.true()
    # to do this, we use an over-simplified transition relation, EXu,Xc
    simple_trans = bdd.true()
    for b in preds.abs_blocks:
        trans_b = bdd.make_eq(bdd.BDD(b), block_funs[b])
        simple_trans &= trans_b.exist_abstract(
            bdd.get_cube(get_controllable_inputs_bdds()))
    simple_trans &= conc_strat & conc_src
    return simple_trans.exist_abstract(
        bdd.get_cube(get_all_latches_as_bdds() +
                     get_uncontrollable_inputs_bdds()))


def pre_env_bdd_abs(dst_states_bdd, get_strat=False):
    """ UPRE_abs = EXu.AXc.EP' : T_abs(P,Xu,Xc,P') ^ dst(P') """
    # if there is no transition bdd then return the version that can be
    # computed without one
    if not use_trans:
        return single_pre_env_bdd_abs(dst_states_bdd, get_strat)
    # if we are using the de Alfaro version of the operators, i.e.
    # the most precise ones
    if most_precise:
        return alpha_over(pre_env_bdd(gamma(dst_states_bdd),
                                      get_strat=get_strat))
    # else, compute as the initial comment reads
    transition_bdd = compose_abs_transition_bdd()
    primed_states = prime_blocks_in_bdd(dst_states_bdd)
    primed_blocks = bdd.get_cube([bdd.BDD(get_primed_variable(x))
                                  for x in preds.abs_blocks])
    tmp_bdd = transition_bdd.and_abstract(primed_states, primed_blocks)
    tmp_bdd = tmp_bdd.univ_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = tmp_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    # return the "good actions" if they are needed
    if get_strat:
        return tmp_bdd
    else:
        return p_bdd


def pre_env_bdd_uabs(dst_states_bdd, env_strat=None):
    """ UPRE_uabs = EXu.AXc.AP' : T_abs(P,Xu,Xc,P') [^St(L,Xu)] => dst(P') """
    # if there is no transition relation, use the single version
    if not use_trans:
        return single_pre_env_bdd_uabs(dst_states_bdd, env_strat)
    # if we want the most precise version of the operator
    if most_precise:
        if env_strat is not None:
            strat = gamma(env_strat)
        else:
            strat = None
        return alpha_under(pre_env_bdd(gamma(dst_states_bdd),
                                       env_strat=strat))
    # else, do as we promised in the first comment
    transition_bdd = compose_abs_transition_bdd()
    trans = transition_bdd
    if env_strat is not None:
        trans &= env_strat

    primed_states = prime_blocks_in_bdd(dst_states_bdd)
    primed_blocks = bdd.get_cube([bdd.BDD(get_primed_variable(x))
                                  for x in preds.abs_blocks])
    tmp_bdd = bdd.make_impl(transition_bdd, primed_states)
    tmp_bdd = tmp_bdd.univ_abstract(primed_blocks)
    tmp_bdd = tmp_bdd.univ_abstract(
        bdd.get_cube(get_controllable_inputs_bdds()))
    p_bdd = tmp_bdd.exist_abstract(
        bdd.get_cube(get_uncontrollable_inputs_bdds()))

    return p_bdd


def post_bdd_abs(src_states_bdd, env_strat=None):
    """
    POST_abs = EP.EXu.EXc : src(P) ^ T(P,Xu,Xc,P') [^St(P,Xu)]
    optional argument fixes possible actions for the environment
    """
    # if there is no transition_bdd we do what we can
    if not use_trans:
        return over_post_bdd_abs(src_states_bdd, env_strat)
    # otherwise, we compute as the first comment reads
    transition_bdd = compose_abs_transition_bdd()
    trans = transition_bdd
    if env_strat is not None:
        trans &= env_strat

    preds_as_bdds = [bdd.BDD(x) for x in preds.abs_blocks]
    suc_bdd = trans.and_abstract(
        src_states_bdd,
        bdd.get_cube(
            get_controllable_inputs_bdds() +
            get_uncontrollable_inputs_bdds() +
            preds_as_bdds))

    return unprime_blocks_in_bdd(suc_bdd)


# ################################ ALGOS ##############################

def extract_output_funcs(strategy, care_set=None):
    """ Calculate BDDs for output functions given non-deterministic winning
        strategy.
    """
    if care_set is None:
        care_set = bdd.true()

    output_models = dict()
    all_outputs = get_controllable_inputs_bdds()
    for c in get_controllable_inputs_bdds():
        others = set(set(all_outputs) - set([c]))
        if others:
            others_cube = bdd.get_cube(others)
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
                      key=bdd.dag_size)
        output_models[c] = c_model
        log.DBG_MSG("Size of function for " + str(c.get_index()) + " = " +
                    str(c_model.dag_size()))
        strategy &= bdd.make_eq(c, c_model)
    return output_models


def walk(a_bdd):
    global bdd_gate_cache
    """
    Walk given BDD node (recursively).  If given input BDD requires
    intermediate AND gates for its representation, the function adds them.
    Literal representing given input BDD is `not` added to the spec.
    """
    if a_bdd in bdd_gate_cache:
        return bdd_gate_cache[a_bdd]

    if a_bdd.is_constant():
        res = int(a_bdd == bdd.true())   # in aiger 0/1 = False/True
        return res
    # get an index of variable,
    # all variables used in bdds also introduced in aiger,
    # except fake error latch literal,
    # but fake error latch will not be used in output functions (at least we
    # don't need this..)
    a_lit = a_bdd.get_index()
    assert (a_lit != error_fake_latch.lit), ("using error latch in the " +
                                             "definition of output " +
                                             "function is not allowed")
    t_bdd = a_bdd.then_child()
    e_bdd = a_bdd.else_child()
    t_lit = walk(t_bdd)
    e_lit = walk(e_bdd)
    # ite(a_bdd, then_bdd, else_bdd)
    # = a*then + !a*else
    # = !(!(a*then) * !(!a*else))
    # -> in general case we need 3 more ANDs
    a_t_lit = aig.get_optimized_and_lit(a_lit, t_lit)
    na_e_lit = aig.get_optimized_and_lit(aig.negate_lit(a_lit), e_lit)
    n_a_t_lit = aig.negate_lit(a_t_lit)
    n_na_e_lit = aig.negate_lit(na_e_lit)
    ite_lit = aig.get_optimized_and_lit(n_a_t_lit, n_na_e_lit)
    res = aig.negate_lit(ite_lit)
    if a_bdd.is_complement():
        res = aig.negate_lit(res)
    # cache result
    bdd_gate_cache[a_bdd] = res
    return res


def model_to_aiger(c_bdd, func_bdd):
    c_lit = c_bdd.get_index()
    func_as_aiger_lit = walk(func_bdd)
    aig.input2and(c_lit, func_as_aiger_lit)


def synthesize():
    if use_trans:
        log.register_sum("trans_time",
                         "Time spent building transition relation: ")
        log.start_clock()
        compose_transition_bdd()
        log.stop_clock("trans_time")
    init_state_bdd = compose_init_state_bdd()
    error_bdd = bdd.BDD(error_fake_latch.lit)
    reach_over = []
    # use abstraction to minimize state space exploration
    if ini_reach:
        initial_abstraction()
        for j in range(ini_reach):
            preds.drop_latches()
            # add some latches
            make_vis = (aig.num_latches() + 1) // ini_reach_latches
            log.DBG_MSG("Making visible " + str(make_vis) + " latches")
            for i in range(make_vis):
                preds.loc_red()
            log.DBG_MSG("Computing reachable states over-app")
            abs_reach_region = fp(compose_abs_init_state_bdd(),
                                  fun=lambda x: x | post_bdd_abs(x))
            reach_over.append(gamma(abs_reach_region))
    # get the winning region for controller

    def min_pre(s):
        for r in reach_over:
            s = s.restrict(r)
        result = pre_env_bdd(s)
        for r in reach_over:
            result = result.restrict(r)
        return s | result

    log.DBG_MSG("Computing fixpoint of UPRE")
    win_region = ~fp(error_bdd,
                     fun=min_pre,
                     early_exit=lambda x: x & init_state_bdd != bdd.false())

    if win_region & init_state_bdd == bdd.false():
        log.LOG_MSG("The spec is unrealizable.")
        log.LOG_ACCUM()
        return (None, None)
    else:
        log.LOG_MSG("The spec is realizable.")
        log.LOG_ACCUM()
        return (win_region, reach_over)


# ########################## ABS ALGOS #############################

def never(x):
    return False


def fp(s, fun, early_exit=never):
    """ fixpoint of monotone function starting from s """
    prev = None
    cur = s
    cnt = 0
    while prev is None or prev != cur:
        prev = cur
        cur = fun(prev)
        cnt += 1
        if early_exit(cur):
            log.DBG_MSG("Early exit after " + str(cnt) + " steps.")
            return cur
    log.DBG_MSG("Fixpoint reached after " + str(cnt) + " steps.")
    return cur


def initial_abstraction():
    global preds

    introduce_error_latch()
    all_latches = [x.lit for x in aig.iterate_latches()]
    all_latches_and_error = list(all_latches + [error_fake_latch.lit])
    all_latches_and_error_next = (
        [get_bdd_for_aig_lit(x.next) for x in aig.iterate_latches()] +
        [get_bdd_for_aig_lit(error_fake_latch.next)])
    preds = spred.SmartPreds(supp=all_latches_and_error,
                             supp_next=all_latches_and_error_next)
    preds.add_fixed_pred("unsafe", bdd.BDD(error_fake_latch.lit))
    preds.add_fixed_pred("init", bdd.get_clause([bdd.BDD(l)
                                                 for l in all_latches]))
    log.DBG_MSG("Initial abstraction of the system computed.")
    return True


def abs_sat_synthesis(compute_win_region=False):
    global use_abs

    # declare winner
    def declare_winner(controllable, conc_lose):
        log.LOG_MSG("Nr. of predicates: " + str(len(preds.abs_blocks)))
        log.LOG_ACCUM()
        if controllable:
            log.LOG_MSG("The spec is realizable.")
            return (~conc_lose, [])
        else:
            log.LOG_MSG("The spec is unrealizable.")
            return (None, [])

    # make sure that we have something to abstract
    if aig.num_latches() == 0:
        log.WRN_MSG("No latches in spec. Defaulting to regular synthesis.")
        use_abs = False
        return synthesize()
    # registered quants
    steps = 0
    log.register_sum("ref_cnt", "Nr. of refinements: ")
    log.register_sum("abs_time", "Time spent abstracting: ")
    log.register_sum("oabs_time", "Time spent computing over-app of fp: ")
    log.register_average("unsafe_bdd_size",
                         "Average unsafe iterate bdd size: ")
    # create the abstract game
    initial_abstraction()
    error_bdd = alpha_under(bdd.BDD(error_fake_latch.lit))

    # The REAL algo
    while True:
        log.start_clock()
        if use_trans:
            transition_bdd = compose_abs_transition_bdd()
            log.BDD_DMP(transition_bdd, "transition relation")
        init_state_bdd = compose_abs_init_state_bdd()
        log.BDD_DMP(init_state_bdd, "initial state set")
        log.BDD_DMP(error_bdd, "unsafe state set")
        log.stop_clock("abs_time")

        # STEP 1: check if the over-approx is winning
        log.DBG_MSG("Computing over approx of FP")
        over_fp = fp(error_bdd,
                     fun=lambda x: x | pre_env_bdd_abs(x))
        if (over_fp & init_state_bdd) == bdd.false():
            log.DBG_MSG("FP of the over-approx losing region not initial")
            return declare_winner(True, gamma(over_fp))
        log.stop_clock("oabs_time")

        # STEP 2: refine or declare controllable
        log.DBG_MSG("Concretizing the strategy of Env")
        conc_env_strats = gamma(env_strats)
        conc_reach = gamma(reach)
        conc_under_fp = gamma(under_fp)
        log.DBG_MSG("Taking one step of UPRE in the concrete game")
        conc_step = single_pre_env_bdd(conc_under_fp,
                                       env_strat=conc_env_strats)
        conc_step &= conc_reach
        if bdd.make_impl(conc_step, conc_under_fp) == bdd.true():
            log.DBG_MSG("The concrete step revealed we are at the FP")
            return declare_winner(True, conc_under_fp)
        else:
            # drop latches every number of steps
            reset = False
            if (steps != 0 and steps % local_loss_steps == 0):
                log.DBG_MSG("Dropping all visible latches!")
                reset = preds.drop_latches()
            # add new predicates and reset caches if necessary
            nu_losing_region = conc_step | conc_under_fp
            reset |= preds.add_fixed_pred("reach", conc_reach)
            reset |= preds.add_fixed_pred("unsafe", nu_losing_region)
            # find interesting set of latches
            log.DBG_MSG("Localization reduction step.")
            reset |= preds.loc_red(not_imply=nu_losing_region)
            log.DBG_MSG("# of predicates = " + str(len(preds.abs_blocks)))
            if reset:
                reset_caches()
            # update error bdd
            log.push_accumulated("unsafe_bdd_size",
                                 nu_losing_region.dag_size())
            error_bdd = alpha_under(nu_losing_region)
            # update reachable area
            reachable_bdd = alpha_over(conc_reach)
            steps += 1
            log.push_accumulated("ref_cnt", 1)


def abs_synthesis(compute_win_region=False):
    global use_abs

    # declare winner
    def declare_winner(controllable, conc_lose):
        log.LOG_MSG("Nr. of predicates: " + str(len(preds.abs_blocks)))
        log.LOG_ACCUM()
        if controllable:
            log.LOG_MSG("The spec is realizable.")
            if compute_win_region:
                # make sure we reached the fixpoint
                log.DBG_MSG("Get winning region")
                return (~fp(bdd.BDD(error_fake_latch.lit) | conc_lose,
                            fun=lambda x: x | pre_env_bdd(x)), [])
            else:
                return (~conc_lose, [])
            log.LOG_MSG("The spec is unrealizable.")
            return (None, [])

    # make sure that we have something to abstract
    if aig.num_latches() == 0:
        log.WRN_MSG("No latches in spec. Defaulting to regular synthesis.")
        use_abs = False
        return synthesize()
    # update loss steps
    local_loss_steps = (aig.num_latches() + 1) // loss_steps
    log.DBG_MSG("Loss steps = " + str(local_loss_steps))
    # registered quants
    steps = 0
    log.register_sum("ref_cnt", "Nr. of refinements: ")
    log.register_sum("abs_time", "Time spent abstracting: ")
    log.register_sum("uabs_time", "Time spent computing under-app of fp: ")
    log.register_sum("oabs_time", "Time spent exhausting info of over-app: ")
    log.register_average("unsafe_bdd_size",
                         "Average unsafe iterate bdd size: ")
    # create the abstract game
    initial_abstraction()
    error_bdd = alpha_under(bdd.BDD(error_fake_latch.lit))
    # add some latches
    if ini_latch:
        make_vis = (aig.num_latches() + 1) // ini_latch
        log.DBG_MSG("Making visible " + str(make_vis) + " latches")
        for i in range(make_vis):
            preds.loc_red()
    # first over-approx of the reachable region
    reachable_bdd = bdd.true()

    # The REAL algo
    while True:
        log.start_clock()
        if use_trans:
            transition_bdd = compose_abs_transition_bdd()
            log.BDD_DMP(transition_bdd, "transition relation")
        init_state_bdd = compose_abs_init_state_bdd()
        log.BDD_DMP(init_state_bdd, "initial state set")
        log.BDD_DMP(error_bdd, "unsafe state set")
        log.stop_clock("abs_time")

        # STEP 1: check if under-approx is losing
        log.DBG_MSG("Computing over approx of FP")
        log.start_clock()
        under_fp = fp(error_bdd,
                      fun=lambda x: (reachable_bdd &
                                     (x | pre_env_bdd_uabs(x))))
        log.stop_clock("uabs_time")
        if (init_state_bdd & under_fp) != bdd.false():
            return declare_winner(False)

        # STEP 2: exhaust information from the abstract game, i.e.
        # update the reachability information we have
        log.start_clock()
        prev_reach = bdd.false()
        reach = reachable_bdd
        while prev_reach != reach:
            prev_reach = reach
            # STEP 2.1: check if the over-approx is winning
            log.DBG_MSG("Computing over approx of FP")
            over_fp = fp(under_fp,
                         fun=lambda x: (reach &
                                        (x | pre_env_bdd_abs(x))))
            if (over_fp & init_state_bdd) == bdd.false():
                log.DBG_MSG("FP of the over-approx losing region not initial")
                return declare_winner(True, gamma(under_fp))
            # if there is no early exit we compute a strategy for Env
            env_strats = pre_env_bdd_abs(over_fp, get_strat=True)
            log.DBG_MSG("Computing over approx of Reach")
            reach = fp(init_state_bdd,
                       fun=lambda x: (reach & (x | post_bdd_abs(x,
                                               env_strats))))
        log.stop_clock("oabs_time")

        # STEP 3: refine or declare controllable
        log.DBG_MSG("Concretizing the strategy of Env")
        conc_env_strats = gamma(env_strats)
        conc_reach = gamma(reach)
        conc_under_fp = gamma(under_fp)
        log.DBG_MSG("Taking one step of UPRE in the concrete game")
        conc_step = single_pre_env_bdd(conc_under_fp,
                                       env_strat=conc_env_strats)
        conc_step &= conc_reach
        if bdd.make_impl(conc_step, conc_under_fp) == bdd.true():
            log.DBG_MSG("The concrete step revealed we are at the FP")
            return declare_winner(True, conc_under_fp)
        else:
            # drop latches every number of steps
            reset = False
            if (steps != 0 and steps % local_loss_steps == 0):
                log.DBG_MSG("Dropping all visible latches!")
                reset = preds.drop_latches()
            # add new predicates and reset caches if necessary
            nu_losing_region = conc_step | conc_under_fp
            reset |= preds.add_fixed_pred("reach", conc_reach)
            reset |= preds.add_fixed_pred("unsafe", nu_losing_region)
            # find interesting set of latches
            log.DBG_MSG("Localization reduction step.")
            reset |= preds.loc_red(not_imply=nu_losing_region)
            log.DBG_MSG("# of predicates = " + str(len(preds.abs_blocks)))
            if reset:
                reset_caches()
            # update error bdd
            log.push_accumulated("unsafe_bdd_size",
                                 nu_losing_region.dag_size())
            error_bdd = alpha_under(nu_losing_region)
            # update reachable area
            reachable_bdd = alpha_over(conc_reach)
            steps += 1
            log.push_accumulated("ref_cnt", 1)


def main(aiger_file_name, out_file):
    aig.parse_into_spec(aiger_file_name)
    log.DBG_MSG("AIG spec file parsed")
    log.LOG_MSG("Nr. of latches: " + str(aig.num_latches()))
    log.DBG_MSG("Latches: " + str([x.lit for x in
                                   iterate_latches_and_error()]))
    log.DBG_MSG("U. Inputs: " + str([x.lit for x in
                                     aig.iterate_uncontrollable_inputs()]))
    log.DBG_MSG("C. Inputs: " + str([x.lit for x in
                                     aig.iterate_controllable_inputs()]))
    # realizability and preliminary synthesis
    if use_abs:
        (win_region, reach_over) = abs_synthesis(out_file is not None)
    else:
        (win_region, reach_over) = synthesize()

    if out_file and win_region:
        log.LOG_MSG("Win region bdd node count = " +
                    str(win_region.dag_size()))
        strategy = single_pre_sys_bdd(win_region, get_strat=True)
        log.LOG_MSG("Strategy bdd node count = " +
                    str(strategy.dag_size()))
        func_by_var = extract_output_funcs(strategy, win_region)
        # attempt to minimize the winning region
        for r in reach_over:
            for (c_bdd, func_bdd) in func_by_var.items():
                func_by_var[c_bdd] = func_bdd.safe_restrict(r)
                log.DBG_MSG("Min'd version size " +
                            str(func_by_var[c_bdd].dag_size()))
        # attempt to minimize the winning region
        if min_win:
            bdd.disable_reorder()
            strategy = bdd.true()
            for (c_bdd, func_bdd) in func_by_var.items():
                strategy &= bdd.make_eq(c_bdd, func_bdd)
            win_region = fp(compose_init_state_bdd(),
                            fun=lambda x: x | post_bdd(x, strategy))
            for (c_bdd, func_bdd) in func_by_var.items():
                func_by_var[c_bdd] = func_bdd.safe_restrict(win_region)
                log.DBG_MSG("Min'd version size " +
                            str(func_by_var[c_bdd].dag_size()))
        # model check?
        if model_check:
            strategy = bdd.true()
            for (c_bdd, func_bdd) in func_by_var.items():
                strategy &= bdd.make_eq(c_bdd, func_bdd)
            assert (fp(bdd.BDD(error_fake_latch.lit),
                       fun=lambda x: x | single_pre_bdd(x, strategy)) &
                    compose_init_state_bdd()) == bdd.false()
        # print out the strategy
        total_dag = 0
        for (c_bdd, func_bdd) in func_by_var.items():
            total_dag += func_bdd.dag_size()
            model_to_aiger(c_bdd, func_bdd)
        log.LOG_MSG("Sum of func dag sizes = " + str(total_dag))
        log.LOG_MSG("# of added gates = " + str(len(bdd_gate_cache)))
        aig.write_spec(out_file)
        return True
    elif win_region:
        return True
    else:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("aiger", metavar="aiger", type=str,
                        help="input specification in AIGER format")
    parser.add_argument("-a", "--abstract", action="store_true",
                        dest="use_abs", default=False,
                        help="use CEGAR approach")
    parser.add_argument("-m", "--minimize", action="store_true",
                        default=False, dest="min_win",
                        help="Minimization using restrict and reach")
    parser.add_argument("-r", "--ini_reach", default=0,
                        type=int, dest="ini_reach",
                        help="Do reachability restriction ini_reach times")
    parser.add_argument("-ri", "--ini_reach_latches", default=2,
                        dest="ini_reach_latches", type=int,
                        help="Do reachability restriction with " +
                             "#latches/ini_reach_latches latches visible")
    parser.add_argument("-t", "--transition", action="store_true",
                        dest="use_trans", default=False,
                        help="Compute a transition relation")
    parser.add_argument("-rc", "--restrict_crazy", action="store_true",
                        dest="restrict_like_crazy", default=False,
                        help="Use restrict to minimize BDDs everywhere")
    parser.add_argument("-mc", "--model_check", action="store_true",
                        dest="model_check", default=False,
                        help="Model check resulting strategy")
    # parser.add_argument("-p", "--precise", action="store_true",
    #                     dest="most_precise", default=False,
    #                     help="Use the most precise abstract operators")
    parser.add_argument("-v", "--verbose", dest="verbose_level",
                        default="", required=False,
                        help="Verbose level = (D)ebug, (W)arnings, " +
                             "(L)og messages, (B)DD dot dumps")
    parser.add_argument("-i", "--initial", dest="ini_latch",
                        default=0, type=int, required=False,
                        help="Number latches to start with = " +
                             "#latches/ini_latch")
    parser.add_argument("-l", "--lossiness", dest="loss_steps",
                        default=1, type=int, required=False,
                        help="Number of steps before dropping latches = " +
                             "#latches/loss_steps")
    parser.add_argument("--out", "-o", dest="out_file", type=str,
                        required=False, default=None,
                        help="output file in AIGER format (if realizable)")
    args = parser.parse_args()
    model_check = args.model_check
    loss_steps = args.loss_steps
    use_abs = args.use_abs
    use_trans = args.use_trans
    ini_reach = args.ini_reach
    ini_reach_latches = args.ini_reach_latches
    min_win = args.min_win
    restrict_like_crazy = args.restrict_like_crazy
    ini_latch = args.ini_latch
    # most_precise = args.most_precise
    log.parse_verbose_level(args.verbose_level)
    is_realizable = main(args.aiger, args.out_file)
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])
