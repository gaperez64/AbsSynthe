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

import aig
#import log
import sat


def load_file(aiger_file_name):
    aig.parse_into_spec(aiger_file_name, True)
    print sat.trans_rel_CNF().to_string()
    for i in range(1, 2):
        (c, m) = sat.unroll_CNF(i)
        print c.to_string()
        c.add_cube([x.lit * -1 for x in aig.iterate_latches()])
        c.add_clause([mm[aig.error_fake_latch.lit] for mm in m])
        print c.sat_solve()

if __name__ == "__main__":
    load_file("../gaperez-svn/syntcomp/tool/benchmarking/benchmarks/add2n.aag")
