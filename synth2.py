import cProfile

import aig
import log
import bdd
import abstract

def synth(argv):
    # lets have some abstractions with different visible latches and see if the
    # winning region is NOT everything
    preds = abstract.init_abstraction()
    error_bdd = alpha_under(bdd.BDD(error_fake_latch.lit))
    # add some latches
    for i in range(5):
        preds.loc_red()
    # first over-approx of the reachable region
    reachable_bdd = bdd.true()


def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in AIGER format")
    args = parser.parse_args()


if __name__ == "__main__":
    cProfile.run("main()")
