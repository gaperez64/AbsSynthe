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

debug = False
log = False
warn = True
bdd_dmp = False


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
