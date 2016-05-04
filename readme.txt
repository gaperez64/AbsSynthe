Swiss AbsSynthe - is the native version of the AbsSynthe tool, used to
synthesize controllers from succinct safety specifications.

Authors = Romain Brenguier, Ocan Sankur, Guillermo A. Perez, Jean-Francois Raskin
Insitute = Universite Libre de Bruxelles
Version = 2.0

Some dependencies:
The tool uses a simple version of the aiger library developed by the team of
Armin Biere (available at http://fmv.jku.at/aiger/). Specifically, we use
slightly modified versions of the aiger.c, aigtocnf.c, and aiger.h files.

We also make use of the cudd BDD library (version 2.5.1) included in the source
sub-folder.

UPDATES v2.0
============
For this new version of Swiss AbsSynthe we have implemented a new abstraction
algorithm and one more compositional algorithm.

Additionally, there are new options to output (1) an aag version of the winning
region if the given input spec is realizable and (2) a QDIMACS certificate of
the winning region being inductively invariant, that is there is some way to
choose controllable inputs -- which depends on the latches and uncontrollable
inputs -- which allows the controller to stay in the winning region if it
started from the winning region. The latter can be fed into a QBF solver to
obtain Skolem functions: a strategy.
