import aig
import log


def run():
    load_file("../gaperez-svn/syntcomp/tool/benchmarking/benchmarks/add2n.aag")

def load_file(aiger_file_name):
    aig.parse_into_spec(aiger_file_name, True)
    log.DBG_MSG("AIG spec file parsed")
    log.LOG_MSG("Nr. of latches: " + str(aig.num_latches()))
    log.DBG_MSG("Latches: " + str([x.lit for x in
                                   aig.iterate_latches()]))
    log.DBG_MSG("U. Inputs: " + str([x.lit for x in
                                     aig.iterate_uncontrollable_inputs()]))
    log.DBG_MSG("C. Inputs: " + str([x.lit for x in
                                     aig.iterate_controllable_inputs()]))
    return aig.latch_dependency_map()
