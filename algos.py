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


from itertools import imap
from utils import fixpoint, funcomp
import log
import aig
import aig2bdd
import bdd
from bdd_abs import Abstraction


class ABS_TECH:
    LOC_RED = 1,
    PRED_ABS = 2,
    NONE = 3


# Explicit OTFUR based on the transition relation and using smart simulation
# relation abstraction
def forward_explicit_synth():
    uinputs = [x.lit for x in aig.iterate_uncontrollable_inputs()]
    latches = [x.lit for x in aig.iterate_latches()]
    trans = aig2bdd.trans_rel_bdd()
    latch_cube = bdd.get_cube(imap(funcomp(bdd.BDD,
                                           aig.symbol_lit),
                                   aig.iterate_latches()))
    platch_cube = bdd.get_cube(imap(funcomp(bdd.BDD, aig.get_primed_var,
                                            aig.symbol_lit),
                                    aig.iterate_latches()))
    cinputs_cube = bdd.get_cube(imap(funcomp(bdd.BDD,
                                             aig.symbol_lit),
                                     aig.iterate_controllable_inputs()))
    uinputs_cube = bdd.get_cube(imap(funcomp(bdd.BDD,
                                             aig.symbol_lit),
                                     aig.iterate_uncontrollable_inputs()))
    init_state_bdd = aig2bdd.init_state_bdd()
    error_bdd = aig2bdd.get_bdd_for_lit(aig.error_fake_latch.lit)
    Venv = dict()
    Venv[init_state_bdd] = True
    succ_cache = dict()

    def succ_env(q):
        if q in succ_cache:
            return succ_cache[q]
        A = bdd.true()
        M = set()
        while A != bdd.false():
            a = A.get_one_minterm(uinputs)
            lhs = trans.and_abstract(a & q, latch_cube)
            rhs = aig2bdd.prime_all_inputs_in_bdd(trans & q)\
                .exist_abstract(latch_cube)
            simd = bdd.make_impl(lhs, rhs).univ_abstract(platch_cube)\
                .exist_abstract(cinputs_cube)\
                .univ_abstract(uinputs_cube)
            simd = aig2bdd.unprime_all_inputs_in_bdd(simd)

            A &= ~simd
            for m in M:
                if bdd.make_impl(m, simd) == bdd.true():
                    M.remove(m)
            M.add(a)
        log.DBG_MSG("|M| = " + str(len(M)))
        succ_cache[q] = M
        return set([(q,m) for m in M])

    def succ_ctrl(q, au):
        s = tuple([q, au])
        if s in succ_cache:
            return succ_cache[s]
        L = aig2bdd.unprime_latches_in_bdd(
            trans.and_abstract(q & au, latch_cube & uinputs_cube & cinputs_cube))
        R = set()
        while L != bdd.false():
            l = L.get_one_minterm(latches)
            R.add(l)
            L &= ~l
            Venv[l] = True
        log.DBG_MSG("|R| = " + str(len(R)))
        succ_cache[s] = R
        return R

    # OTFUR
    passed = set([init_state_bdd])
    depend = dict()
    depend[init_state_bdd] = set()
    losing = dict()
    losing[init_state_bdd] = False
    waiting = [(init_state_bdd, x) for x in succ_env(init_state_bdd)]
    while waiting and not losing[init_state_bdd]:
        (s, sp) = waiting.pop()
        if sp not in passed:
            passed.add(sp)
            losing[sp] = sp in Venv and (sp & error_bdd != bdd.false())
            if sp in depend:
                depend[sp].add((s, sp))
            else:
                depend[sp] = set([(s, sp)])
            if losing[sp]:
                waiting.append((s, sp))
            else:
                if sp in Venv:
                    waiting.extend([(sp, x) for x in succ_env(sp)])
                else:
                    waiting.extend([(sp, x) for x in succ_ctrl(*sp)])
        else:
            is_loser = lambda x: x in losing and losing[x]
            local_lose = (s in Venv and any(imap(is_loser, succ_env(s))) or
                          all(imap(is_loser, succ_ctrl(*s))))
            if local_lose:
                losing[s] = True
                waiting.extend(depend[s])
            if sp not in losing or not losing[sp]:
                depend[sp] = depend[sp] | set([(s, sp)])
    log.DBG_MSG("OTFUR, losing[init_state_bdd] = " +
                str(losing[init_state_bdd]))
    return None if losing[init_state_bdd] else True


# Construct an initial abstraction of the game
def init_abstraction():
    all_latches = [x.lit for x in aig.iterate_latches()]
    all_latches_next = (
        [aig2bdd.get_bdd_for_lit(x.next) for x in aig.iterate_latches()] +
        [aig2bdd.get_bdd_for_lit(aig.error_fake_latch.next)])
    preds = Abstraction(supp=all_latches,
                        supp_next=all_latches_next)
    preds.add_fixed_pred("unsafe", bdd.BDD(aig.error_fake_latch.lit))
    preds.add_fixed_pred("init", bdd.get_clause([bdd.BDD(l)
                                                 for l in all_latches]))
    log.DBG_MSG("Initial abstraction of the system computed.")
    return preds


# Returns None if Eve loses the game and a bdd with the winning states
# if Eve wins and only_real == True
def backward_upre_synth(restrict_like_crazy=False, use_trans=False,
                        abs_tech=ABS_TECH.NONE, only_real=False):
    # all algo versions require initial and error states
    init_state_bdd = aig2bdd.init_state_bdd()
    error_bdd = aig2bdd.get_bdd_for_lit(aig.error_fake_latch.lit)
    # make sure that we have something to abstract
    if abs_tech != ABS_TECH.NONE and aig.num_latches() == 0:
        log.WRN_MSG("No latches in spec. Defaulting to regular synthesis.")
        abs_tech = ABS_TECH.NONE

    if abs_tech == ABS_TECH.LOC_RED:
        preds = init_abstraction()
        abs_error_bdd = preds.alpha_under(bdd.BDD(aig.error_fake_latch.lit))
        abs_init_bdd = preds.alpha_under(aig.init_state_bdd())

        while True:
            # STEP 1: check if under-approx is losing
            under_fp = fixpoint(abs_error_bdd,
                                fun=lambda x: x | preds.uupre_bdd(x))
            if (init_state_bdd & under_fp) != bdd.false():
                return None
            # STEP 2: check if over-approx is winning
            over_fp = fixpoint(under_fp,
                               fun=lambda x: x | preds.oupre_bdd(x))
            if (over_fp & abs_init_bdd) == bdd.false():
                log.DBG_MSG("FP of the over-approx losing region not initial")
                if not only_real:
                    error_bdd = preds.gamma(under_fp)
                    break
                else:
                    return True
            # STEP 3: refine or declare controllable
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
            error_bdd = alpha_under(nu_losing_region)

    elif abs_tech == ABS_TECH.PRED_ABS:
        log.WRN_MSG("Not implemented")
        exit()

    # If this is executed then either a strategy is required or
    # abs_tech == ABS_TECH.NONE
    log.DBG_MSG("Computing fixpoint of UPRE.")
    win_region = ~fixpoint(
        error_bdd,
        fun=lambda x: x | aig2bdd.upre_bdd(
            x, restrict_like_crazy=restrict_like_crazy,
            use_trans=use_trans),
        early_exit=lambda x: x & init_state_bdd != bdd.false()
    )

    if win_region & init_state_bdd == bdd.false():
        return None
    else:
        log.DBG_MSG("Win region bdd node count = " +
                    str(win_region.dag_size()))
        return win_region


# Given a bdd representing the set of safe states-action paris for the
# controller (Eve) we compute a winning strategy for her (trying to get a
# minimal one via a greedy algo on the way).
def extract_output_funs(strategy, care_set=None):
    """
    Calculate BDDs for output functions given non-deterministic winning
    strategy.
    """
    if care_set is None:
        care_set = bdd.true()

    output_models = dict()
    all_outputs = [bdd.BDD(x.lit) for x in aig.iterate_controllable_inputs()]
    for c_symb in aig.iterate_controllable_inputs():
        c = bdd.BDD(c_symb.lit)
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
        output_models[c_symb.lit] = c_model
        log.DBG_MSG("Size of function for " + str(c.get_index()) + " = " +
                    str(c_model.dag_size()))
        strategy &= bdd.make_eq(c, c_model)
    return output_models
