"""
Copyright (c) 2014, Guillermo A. Perez, Universite Libre de Bruxelles

This file is part of a the AbsSynthe tool.

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

import time

debug = False
log = False
warn = False
bdd_dmp = False
reg_accum = dict()
run_clk = None


def parse_verbose_level(lvl_str):
    global debug, log, warn, bdd_dmp

    debug = "D" in lvl_str
    log = "L" in lvl_str
    warn = "W" in lvl_str
    bdd_dmp = "B" in lvl_str


def DBG_MSG(message):
    if debug:
        print "[DBG] " + message


def WRN_MSG(message):
    if warn:
        print "[WRN] " + message


def LOG_MSG(message):
    if log:
        print "[LOG] " + message


def BDD_DMP(b, message):
    DBG_MSG(message)
    if bdd_dmp:
        DBG_MSG("boolean function on vars: " + str(b.occ_sem()))
        DBG_MSG("positive: " + str(b.occ_pos()))
        DBG_MSG("negative: " + str(b.occ_neg()))
        DBG_MSG("bdd node count: " + str(b.dag_size()))
        b.dump_dot()
        raw_input("Press ENTER to continue...")


def LOG_ACCUM():
    if log:
        for name in reg_accum:
            vals = reg_accum[name]
            x = vals[1](vals[2:])
            LOG_MSG(vals[0] + str(x))


def register_accumulated(name, msg, func):
    if log:
        if name not in reg_accum:
            reg_accum[name] = [msg, func]


def get_accumulated(name):
    if log:
        vals = reg_accum[name]
        return vals[1](vals[2:])
    else:
        return None


def register_average(name, msg):
    def avg(l):
        result = 0
        for x in l:
            result += x
        return result / len(l)

    register_accumulated(name, msg, avg)
    push_accumulated(name, 0)


def register_sum(name, msg):
    def sum(l):
        result = 0
        for x in l:
            result += x
        return result

    register_accumulated(name, msg, sum)


def start_clock():
    global run_clk

    if log:
        run_clk = time.clock()
        return run_clk


def push_accumulated(name, val):
    if log:
        assert name in reg_accum
        reg_accum[name].append(val)


def stop_clock(name=None):
    if log:
        t = time.clock() - run_clk
        if name is not None:
            push_accumulated(name, t)
        return t
