import aig
import sat
import log
import bdd


def test():
    cnf = aig.trans_rel_CNF()
    print cnf.to_string()
    for s in cnf.iter_solve():
        cnf2 = sat.CNF()
        cnf2.add_cube(s)
        if cnf2.to_bdd() & aig.trans_rel_bdd() == bdd.false():
            print "found an error!"
            aig.trans_rel_bdd().dump_dot()
            print str(s)
            print cnf2.to_string()
            exit()
        else:
            print str(s) + " works"



def main():
    log.parse_verbose_level("D")
    aig.parse_into_spec("../bench-syntcomp14/add2n.aag", intro_error_latch=True)
    test()


if __name__ == "__main__":
    main()
