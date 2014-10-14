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
import random
import log
from aig import (
    iterate_latches,
    iterate_controllable_inputs,
    iterate_uncontrollable_inputs,
    get_primed_var,
    error_fake_latch,
    symbol_lit
)
from aig2bdd import (
    get_bdd_for_lit
)
from utils import funcomp
import bdd


class Abstraction:
    pred_to_bdd = dict()
    pred_to_lset = dict()
    fixed_self = dict()
    abs_preds = []
    cluster_threshold = None
    support_set = None
    support_set_rel = None
    loss_prob = None
    # caches
    cached_abs_transition = None
    cached_abs_eq = None
    procd_preds = dict()
    abs_eq_procd_preds = dict()

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
        all_latches = [x.lit for x in iterate_latches()]
        all_latches = list(all_latches + [error_fake_latch.lit])
        all_latches_next = (
            [get_bdd_for_lit(x.next)
             for x in iterate_latches()] +
            [get_bdd_for_lit(error_fake_latch.next)])
        self.initialize(supp=all_latches,
                        supp_next=all_latches_next)
        self.add_fixed_pred("unsafe", bdd.BDD(error_fake_latch.lit))
        self.add_fixed_pred("init", bdd.get_clause(imap(bdd.BDD,
                                                   iter(all_latches))))
        log.DBG_MSG("Initial abstraction of the system computed.")
        return self

    def iterate_preds(self):
        for a in self.abs_preds:
            yield a

    def prime_preds_in_bdd(self, bdd):
        preds = [x for x in self.iterate_preds()]
        ppreds = map(get_primed_var, preds)
        return bdd.swap_variables(preds, ppreds)

    def unprime_preds_in_bdd(self, bdd):
        preds = [x for x in self.iterate_preds()]
        ppreds = map(get_primed_var, preds)
        return bdd.swap_variables(ppreds, preds)

    # return true if insert was successful
    def direct_add_pred(self, f):
        latch_set = set(f.occ_sem())
        assert latch_set <= self.support_set or self.support_set is None
        if f == bdd.true() or f == bdd.false():
            log.DBG_MSG("Attempting to add trivial predicate T/F.")
            return False
        for a in self.abs_preds:
            if (f == self.pred_to_bdd[a]):
                log.BDD_DMP(f, "Predicate already exists.")
                return False
        self.abs_preds.append(bdd.next_var())
        log.BDD_DMP(f, "Adding predicate " + str(self.abs_preds[-1]))
        bdd.next_var()  # throw one away to save it for the primed version
        self.pred_to_bdd[self.abs_preds[-1]] = f
        self.pred_to_lset[self.abs_preds[-1]] = latch_set
        return True

    # all the methods below return True if they remove predicates, False
    # otherwise
    def remove_predicates(self, to_del):
        if not to_del:
            return False

        # clean object variables
        old = self.abs_preds
        self.abs_preds = [x for x in self.abs_preds if x not in to_del]
        for b in to_del:
            if b in self.pred_to_lset:
                del self.pred_to_lset[b]
            if b in self.pred_to_bdd:
                del self.pred_to_bdd[b]
        return old != self.abs_preds

    def drop_latches(self):
        to_del = []
        latch_bdds = [bdd.BDD(x) for x in self.support_set]
        for b in self.abs_preds:
            if self.pred_to_bdd[b] in latch_bdds:
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
            for b in self.abs_preds:
                if (bdd.make_impl(self.pred_to_bdd[b], f) == bdd.true() or
                        bdd.make_impl(~self.pred_to_bdd[b], f) == bdd.true()):
                    to_del.append(b)
                    log.DBG_MSG("Implicant " + str(b) +
                                " will be removed")
        rem = False
        # insert and update the new fixed pred, if possible
        if self.direct_add_pred(f):
            self.fixed_self[name] = self.abs_preds[-1]
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
                            self.pred_to_bdd.values()])
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
        clusters = [set([x]) for x in self.abs_preds]
        clusters_lset = [self.pred_to_lset[x] for x in self.abs_preds]
        change = True
        while change:
            change = False
            for i in range(len(self.abs_preds) - 1):
                if len(clusters[i]) > 0:
                    for j in range(i + 1, len(self.abs_preds)):
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
        for i in range(len(self.abs_preds)):
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
                    str(len(self.abs_preds)))
        return len(to_del) > 0

    """ WARNING!
    Methods implemented below use CACHE to achieve better
    efficiency. However, if the set of predicates is further modified after
    some element has been cached then cached information becomes trash (and
    this is not verified).
    """
    def compose_abs_eq_bdd(self):
        # check cache
        if self.cached_abs_eq is None:
            log.DBG_MSG("Rebuilding abs_eq")
            for b in self.abs_preds:
                self.abs_eq_procd_preds[b] = False
            c = bdd.true()
        else:
            c = self.cached_abs_eq

        for b in self.abs_preds:
            if b not in self.procd_preds or not self.procd_preds[b]:
                c &= bdd.make_eq(bdd.BDD(b), self.pred_to_bdd[b])
        # cache c
        self.cached_abs_eq = c
        return c

    def abs_trans_rel_bdd(self):
        # check cache
        if self.cached_abs_transition is None:
            log.DBG_MSG("Rebuilding abstract transition relation")
            for b in self.abs_preds:
                self.procd_preds[b] = False
            c = bdd.true()
        else:
            c = self.cached_abs_transition

        latches = [x.lit for x in iterate_latches()]
        latches_bdd = bdd.get_cube(
            imap(bdd.BDD, iterate_latches()))
        latch_funs = [get_bdd_for_lit(x.next) for x in
                      iterate_latches()]
        for b in self.abs_preds:
            if b not in self.procd_preds or not self.procd_preds[b]:
                self.procd_preds[b] = True
                temp = bdd.make_eq(bdd.BDD(get_primed_var(b)),
                                   self.pred_to_bdd[b])
                c &= temp.compose(latches, latch_funs)
        # cache c
        self.cached_abs_transition = c
        return c.and_abstract(self.compose_abs_eq_bdd(), latches_bdd)

    def alpha_over(self, conc_bdd):
        c = self.compose_abs_eq_bdd()
        latches_bdd = bdd.get_cube(imap(bdd.BDD, iterate_latches()))
        c = c.and_abstract(conc_bdd, latches_bdd)
        return c

    def alpha_under(self, conc_bdd):
        return ~self.alpha_over(~conc_bdd)

    def gamma(self, abs_bdd):
        return abs_bdd.compose(self.pred_to_bdd.keys(),
                               self.pred_to_bdd.values())

    """
    GAME operators are implemented here
    """
    def update_pred_funs(self):
        latches = [x.lit for x in iterate_latches()]
        latch_funs = [get_bdd_for_lit(x.next) for x in
                      iterate_latches()]
        # check cache
        if self.cached_pred_funs is None:
            log.DBG_MSG("Rebuilding pred_funs")
            pred_funs = dict()
            for b in self.abs_preds:
                pred_funs[b] = self.gamma(
                    self.pred_to_bdd[b]).compose(latches, latch_funs)
        else:
            for b in self.abs_preds:
                if b not in pred_funs:
                    pred_funs[b] = self.gamma(self.pred_to_bdd[b])
                    pred_funs[b] = pred_funs[b].compose(latches,
                                                        latch_funs)
        # set cache
        self.cached_pred_funs = bdd.true()

    def get_bdd_for_pred(self, pred):
        return self.pred_to_bdd[pred]

    def substitute_preds_under(self, b, use_trans=False, restrict_fun=None):
        self.update_pred_funs()
        if use_trans:
            transition_bdd = self.abs_trans_rel_bdd()
            trans = transition_bdd
            if restrict_fun is not None:
                trans = trans.restrict(restrict_fun)
            primed_bdd = self.prime_preds_in_bdd(b)
            primed_preds = bdd.get_cube(
                imap(funcomp(bdd.BDD, get_primed_var),
                     self.iterate_preds()))
            return trans.and_abstract(primed_bdd,
                                      primed_preds)
        else:
            preds = [x for x in self.iterate_preds()]
            pred_funs = [self.get_bdd_for_pred(x) for x in
                         self.iterate_preds()]
            if restrict_fun is not None:
                pred_funs = [x.restrict(restrict_fun) for x in pred_funs]
            # take a transition step backwards
            tmp_bdd = (~b).compose(preds, pred_funs)
            return self.alpha_over(tmp_bdd)

    def uupre_bdd():
        """
        UUPRE_abs = ~ AXu.EXc.AP' : T_a(P,Xu,Xc,P') ^ ~dst(P') [^St(P,Xu)]
        """

    def substitute_preds_over(self, b, use_trans=False, restrict_fun=None):
        self.update_pred_funs()
        if use_trans:
            transition_bdd = self.abs_trans_rel_bdd()
            trans = transition_bdd
            if restrict_fun is not None:
                trans = trans.restrict(restrict_fun)
            primed_bdd = self.prime_preds_in_bdd(b)
            primed_preds = bdd.get_cube(
                imap(funcomp(bdd.BDD, get_primed_var),
                     self.iterate_preds()))
            return trans.and_abstract(primed_bdd,
                                      primed_preds)
        else:
            preds = [x for x in self.iterate_preds()]
            pred_funs = [bdd.BDD(x) for x in
                         self.iterate_preds()]
            if restrict_fun is not None:
                pred_funs = [x.restrict(restrict_fun) for x in pred_funs]
            # take a transition step backwards
            tmp_bdd = b.compose(preds, pred_funs)
            return self.alpha_over(tmp_bdd)

    def oupre_bdd(self, dst_states_bdd, env_strat=None, get_strat=False,
                  restrict_like_crazy=False, use_trans=False):
        """
        OUPRE_abs = EXu.AXc.EP' : T_a(P,Xu,Xc,P') ^ dst(P') [^St(P,Xu)]
        """
        # take a transition step backwards
        p_bdd = self.substitute_preds_over(dst_states_bdd,
                                           restrict_fun=~dst_states_bdd,
                                           use_trans=use_trans)
        # use the given strategy
        if env_strat is not None:
            p_bdd &= env_strat
        # there is an uncontrollable action such that for all contro...
        temp_bdd = p_bdd.univ_abstract(
            bdd.get_cube(imap(funcomp(bdd.BDD, symbol_lit),
                              iterate_controllable_inputs())))
        p_bdd = temp_bdd.exist_abstract(
            bdd.get_cube(imap(funcomp(bdd.BDD, symbol_lit),
                              iterate_uncontrollable_inputs())))
        # prepare the output
        if get_strat:
            return temp_bdd
        else:
            return p_bdd
