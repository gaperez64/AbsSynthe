import aig
import log


error_fake_latch = None


def introduce_error_latch():
    global error_fake_latch

    if error_fake_latch is not None:
        return
    error_fake_latch = aig.new_aiger_symbol()
    error_symbol = aig.get_err_symbol()
    error_fake_latch.lit = aig.next_lit()
    error_fake_latch.name = "fake_error_latch"
    error_fake_latch.next = error_symbol.lit


def iterate_latches_and_error():
    introduce_error_latch()
    for l in aig.iterate_latches():
        yield l
    yield error_fake_latch


def load_file(aiger_file_name):
    aig.parse_into_spec(aiger_file_name)
    log.DBG_MSG("AIG spec file parsed")
    log.LOG_MSG("Nr. of latches: " + str(aig.num_latches()))
    log.DBG_MSG("Latches: " + str([x.lit for x in
                                   iterate_latches_and_error()]))
    log.DBG_MSG("U. Inputs: " + str([x.lit for x in
                                     aig.iterate_uncontrollable_inputs()]))
    log.DBG_MSG("C. Inputs: " + str([x.lit for x in
                                     aig.iterate_controllable_inputs()]))
