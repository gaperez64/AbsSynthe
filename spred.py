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
import bdd


class SmartPreds:
    block_to_bdd = dict()
    block_to_lset = dict()
    fixed_preds = dict()
    abs_blocks = []
    cluster_threshold = None
    support_set = None
    support_set_rel = None
    loss_prob = None

    def __init__(self, k=None, supp=None, loss=0, supp_next=None):
        self.cluster_threshold = k
        self.loss_prob = loss
        self.support_set = set(supp)
        if supp is not None and supp_next is not None:
            self.support_set_rel = dict()
            for i in range(len(supp)):
                v = supp[i]
                v_supp = set(supp_next[i].occ_sem())
                self.support_set_rel[v] = self.support_set & v_supp

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
        if name in self.fixed_preds:
            to_del = [self.fixed_preds[name]]
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
            self.fixed_preds[name] = self.abs_blocks[-1]
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
