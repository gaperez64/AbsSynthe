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

import random
import log
import aig
import bdd


class Abstraction:
    block_to_bdd = dict()
    block_to_lset = dict()
    fixed_self = dict()
    abs_blocks = []
    cluster_threshold = None
    support_set = None
    support_set_rel = None
    loss_prob = None
    # caches
    cached_abs_transition = None
    cached_abs_eq = None
    procd_blocks = dict()
    abs_eq_procd_blocks = dict()

    def initialize(self, k=None, supp=None, loss=0, supp_next=None):
        self.cluster_threshold = k
        self.loss_prob = loss
        self.support_set = set(supp)
        if supp is not None and supp_next is not None:
            self.support_set_rel = dict()
            for i in range(len(supp)):
                v = supp[i]
                v_supp = set(supp_next[i].occ_sem())
                self.support_set_rel[v] = self.support_set & v_supp

    def __init__(self):
        all_latches = [x.lit for x in aig.aig.iterate_latches()]
        all_latches_and_error = list(all_latches + [aig.error_fake_latch.lit])
        all_latches_and_error_next = (
            [aig.aig.get_bdd_for_aig_lit(x.next) for x in aig.aig.iterate_latches()] +
            [aig.aig.get_bdd_for_aig_lit(aig.error_fake_latch.next)])
        self.initialize(supp=all_latches_and_error,
                        supp_next=all_latches_and_error_next)
        self.add_fixed_pred("unsafe", bdd.BDD(aig.error_fake_latch.lit))
        self.add_fixed_pred("init", bdd.aig.get_clause([bdd.BDD(l)
                                                     for l in all_latches]))
        log.DBG_MSG("Initial abstraction of the system computed.")
        return self

    # return true if insert was successful
    def direct_add_pred(self, f):
        latch_set = set(f.occ_sem())
        assert latch_set <= self.support_set or self.support_set is None
        if f == bdd.true() or f == bdd.false():
            log.DBG_MSG("Attempting to add trivial predicate T/F.")
            return False
        for a in self.abs_blocks:
            if (f == self.block_to_bdd[a]):
                log.BDD_DMP(f, "Predicate already exists.")
                return False
        self.abs_blocks.append(bdd.next_var())
        log.BDD_DMP(f, "Adding predicate " + str(self.abs_blocks[-1]))
        bdd.next_var()  # throw one away to save it for the primed version
        self.block_to_bdd[self.abs_blocks[-1]] = f
        self.block_to_lset[self.abs_blocks[-1]] = latch_set
        return True

    # all the methods below return True if they remove predicates, False
    # otherwise
    def remove_predicates(self, to_del):
        if not to_del:
            return False

        # clean object variables
        old = self.abs_blocks
        self.abs_blocks = [x for x in self.abs_blocks if x not in to_del]
        for b in to_del:
            if b in self.block_to_lset:
                del self.block_to_lset[b]
            if b in self.block_to_bdd:
                del self.block_to_bdd[b]
        return old != self.abs_blocks

    def drop_latches(self):
        to_del = []
        latch_bdds = [bdd.BDD(x) for x in self.support_set]
        for b in self.abs_blocks:
            if self.block_to_bdd[b] in latch_bdds:
                to_del.append(b)
        return self.remove_predicates(to_del)

    def random_latch_loss(self):
        if self.loss_prob != 0 and self.support_set is not None:
            r_prob = random.random()
            if r_prob >= (1 - self.loss_prob):
                log.DBG_MSG("Latch loss occurred!")
                return self.drop_latches()
        return False

    def add_fixed_pred(self, name, f, rem_implicants=False):
        # save the previous fixed predicate, if any
        to_del = []
        if name in self.fixed_self:
            to_del = [self.fixed_self[name]]
        if rem_implicants:
            for b in self.abs_blocks:
                if (bdd.make_impl(self.block_to_bdd[b], f) == bdd.true() or
                        bdd.make_impl(~self.block_to_bdd[b], f) == bdd.true()):
                    to_del.append(b)
                    log.DBG_MSG("Implicant " + str(b) +
                                " will be removed")
        rem = False
        # insert and update the new fixed pred, if possible
        if self.direct_add_pred(f):
            self.fixed_self[name] = self.abs_blocks[-1]
            rem = self.remove_predicates(to_del)
            log.DBG_MSG("Updated fixed predicate: " + str(name))
        return rem

    def loc_red(self, candidates=None, not_imply=None):
        # get candidates
        if candidates is not None:
            s = candidates
        else:
            s = self.support_set
        # visible latches
        visible_supp = set([b for b in self.support_set
                            if bdd.BDD(b) in
                            self.block_to_bdd.values()])
        not_visible = self.support_set - visible_supp
        if not not_visible:
            log.WRN_MSG("All latches visible already")
            return  # all latches are already visible
        # get rid of visible latches
        interesting = set(s) & not_visible
        # get rid of latches that imply something
        if not_imply is not None:
            interesting = set(
                [x for x in interesting if
                 bdd.make_impl(bdd.BDD(x), not_imply) != bdd.true() and
                 bdd.make_impl(~bdd.BDD(x), not_imply) != bdd.true()])
        # get rid of any latches that do not depend on the current visible ones
        useful = []
        if self.support_set_rel is not None:
            for v in interesting:
                if self.support_set_rel[v] & visible_supp:
                    useful.append(v)
        # try and return a useful one
        if useful:
            rand_list = list(useful)
            random.shuffle(rand_list)
            var = rand_list.pop()
            log.DBG_MSG("Making visible useful latch " + str(var))
            return self.direct_add_pred(bdd.BDD(var))
        # try and return an interesting one
        if interesting:
            rand_list = list(interesting)
            random.shuffle(rand_list)
            var = rand_list.pop()
            log.DBG_MSG("Making visible interesting latch " + str(var))
            return self.direct_add_pred(bdd.BDD(var))
        # desperate measures... SHOULD NOT HAPPEN!
        assert False
        rand_list = list(not_visible)
        random.shuffle(rand_list)
        var = rand_list.pop()
        log.DBG_MSG("Making visible (random) latch " + str(var))
        return self.direct_add_pred(bdd.BDD(var))

    def lossy_loc_red(self, s, not_imply=None):
        if self.random_latch_loss():
            return True
        else:
            return self.loc_red_from_list(s, not_imply)

    # returns True if there was some cleaning done
    def add_pred(self, f):
        # add the predicate
        self.direct_add_pred(f)
        if self.cluster_threshold is None:
            log.DBG_MSG("Clustering threshold set to NONE.")
            return False
        # clustering phase
        clusters = [set([x]) for x in self.abs_blocks]
        clusters_lset = [self.block_to_lset[x] for x in self.abs_blocks]
        change = True
        while change:
            change = False
            for i in range(len(self.abs_blocks) - 1):
                if len(clusters[i]) > 0:
                    for j in range(i + 1, len(self.abs_blocks)):
                        inter = (clusters_lset[i] &
                                 clusters_lset[j])
                        if len(inter) > self.cluster_threshold:
                            clusters[j] |= clusters[i]
                            clusters[i] = set([])
                            clusters_lset[j] |= clusters_lset[i]
                            clusters_lset[i] = set([])
                            break
        # cleaning predicate set based on clustering results
        to_del = []
        for i in range(len(self.abs_blocks)):
            if (len(clusters[i]) > 1 and
                    len(clusters[i]) >= len(clusters_lset[i])):
                log.DBG_MSG("Cleaning predicates " + str(clusters[i]))
                for b in clusters[i]:
                    latch = clusters_lset[i].pop()
                    self.direct_add_pred(bdd.BDD(latch))
                    to_del.append(b)
        # clean object variables
        self.remove_predicates(to_del)
        self.direct_add_pred(f)
        log.DBG_MSG("Current number of predicates: " +
                    str(len(self.abs_blocks)))
        return len(to_del) > 0

    """ WARNING!
    Methods implemented below use CACHE to achieve better
    efficiency. However, if the set of predicates is further modified after some
    element has been cached then cached information becomes trash (and this is
    not verified).
    """
    def compose_abs_eq_bdd(self):
        # check cache
        if self.cached_abs_eq is None:
            log.DBG_MSG("Rebuilding abs_eq")
            for b in self.abs_blocks:
                self.abs_eq_procd_blocks[b] = False
            c = bdd.true()
        else:
            c = self.cached_abs_eq

        for b in self.abs_blocks:
            if b not in self.procd_blocks or not self.procd_blocks[b]:
                c &= bdd.make_eq(bdd.BDD(b), self.block_to_bdd[b])
        # cache c
        self.cached_abs_eq = c
        return c


    def compose_abs_transition_bdd(self):
        # check cache
        if self.cached_abs_transition is None:
            log.DBG_MSG("Rebuilding abstract transition relation")
            for b in self.abs_blocks:
                self.procd_blocks[b] = False
            c = bdd.true()
        else:
            c = self.cached_abs_transition

        latches = [x.lit for x in aig.iterate_latches_and_error()]
        latches_bdd = bdd.aig.get_cube(aig.get_all_latches_as_bdds())
        latch_funs = [aig.get_bdd_for_aig_lit(x.next) for x in
                      aig.iterate_latches_and_error()]
        for b in self.abs_blocks:
            if b not in self.procd_blocks or not self.procd_blocks[b]:
                self.procd_blocks[b] = True
                temp = bdd.make_eq(bdd.BDD(aig.get_primed_variable(b)),
                                   self.block_to_bdd[b])
                c &= temp.compose(latches, latch_funs)
        # cache c
        self.cached_abs_transition = c
        return c.and_abstract(self.compose_abs_eq_bdd(), latches_bdd)


    def alpha_over(self, conc_bdd):
        c = self.compose_abs_eq_bdd()
        latches_bdd = bdd.aig.get_cube(aig.get_all_latches_as_bdds())
        c = c.and_abstract(conc_bdd, latches_bdd)
        return c


    def alpha_under(self, conc_bdd):
        return ~self.alpha_over(~conc_bdd)


    def gamma(self, abs_bdd):
        return abs_bdd.compose(self.block_to_bdd.keys(),
                               self.block_to_bdd.values())


    def abs_init_state_bdd(self):
        return self.alpha_over(aig.init_state_bdd())


    """
    GAME operators are implemented here
    """
    def update_block_funs():
        latches = [x.lit for x in aig.iterate_latches_and_error()]
        latch_funs = [aig.get_bdd_for_aig_lit(x.next) for x in
                      aig.iterate_latches_and_error()]
        # check cache
        if cached_block_funs is None:
            log.DBG_MSG("Rebuilding block_funs")
            block_funs = dict()
            for b in self.abs_blocks:
                block_funs[b] = gamma(self.block_to_bdd[b]).compose(latches,
                                                                     latch_funs)
        else:
            for b in self.abs_blocks:
                if b not in block_funs:
                    block_funs[b] = gamma(self.block_to_bdd[b])
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
            bdd.aig.get_cube(aig.get_controllable_inputs_bdds()))
        p_bdd = tmp_bdd.exist_abstract(
            bdd.aig.get_cube(aig.get_uncontrollable_inputs_bdds()))

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
            bdd.aig.get_cube(aig.get_controllable_inputs_bdds()))
        p_bdd = tmp_bdd.univ_abstract(
            bdd.aig.get_cube(aig.get_uncontrollable_inputs_bdds()))

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
        for b in self.abs_blocks:
            trans_b = bdd.make_eq(bdd.BDD(b), block_funs[b])
            simple_trans &= trans_b.exist_abstract(
                bdd.aig.get_cube(aig.get_controllable_inputs_bdds()))
        simple_trans &= conc_strat & conc_src
        return simple_trans.exist_abstract(
            bdd.aig.get_cube(aig.get_all_latches_as_bdds() +
                         aig.get_uncontrollable_inputs_bdds()))


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
        primed_blocks = bdd.aig.get_cube([bdd.BDD(aig.get_primed_variable(x))
                                      for x in self.abs_blocks])
        tmp_bdd = transition_bdd.and_abstract(primed_states, primed_blocks)
        tmp_bdd = tmp_bdd.univ_abstract(
            bdd.aig.get_cube(aig.get_controllable_inputs_bdds()))
        p_bdd = tmp_bdd.exist_abstract(
            bdd.aig.get_cube(aig.get_uncontrollable_inputs_bdds()))

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
        primed_blocks = bdd.aig.get_cube([bdd.BDD(aig.get_primed_variable(x))
                                      for x in self.abs_blocks])
        tmp_bdd = bdd.make_impl(transition_bdd, primed_states)
        tmp_bdd = tmp_bdd.univ_abstract(primed_blocks)
        tmp_bdd = tmp_bdd.univ_abstract(
            bdd.aig.get_cube(aig.get_controllable_inputs_bdds()))
        p_bdd = tmp_bdd.exist_abstract(
            bdd.aig.get_cube(aig.get_uncontrollable_inputs_bdds()))

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

        self_as_bdds = [bdd.BDD(x) for x in self.abs_blocks]
        suc_bdd = trans.and_abstract(
            src_states_bdd,
            bdd.aig.get_cube(
                aig.get_controllable_inputs_bdds() +
                aig.get_uncontrollable_inputs_bdds() +
                self_as_bdds))

        return unprime_blocks_in_bdd(suc_bdd)
