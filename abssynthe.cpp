/**************************************************************************
 * Copyright (c) 2015, Guillermo A. Perez, Universite Libre de Bruxelles
 * 
 * This file is part of the (Swiss) AbsSynthe tool.
 * 
 * AbsSynthe is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * AbsSynthe is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with AbsSynthe.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * 
 * Guillermo A. Perez
 * Universite Libre de Bruxelles
 * gperezme@ulb.ac.be
 *************************************************************************/

#include <iostream>
#include <string>
#include <stdlib.h>
#include <getopt.h>

#include "abssynthe.h"
#include "logging.h"
#include "aig.h"

const char* ABSSYNTHE_VERSION = "Swiss-Abssynthe 1.0";
const int EXIT_STATUS_REALIZABLE = 10;
const int EXIT_STATUS_UNREALIZABLE = 20;

struct settings_struct settings;

static struct option long_options[] = {
    {"verbosity", required_argument, NULL, 'v'},
    {"use_trans", no_argument, NULL, 't'},
    {"help", no_argument, NULL, 'h'},
    {"comp_algo", required_argument, NULL, 'c'},
    {"out_file", required_argument, NULL, 'o'},
    {NULL, 0, NULL, 0}
};

void usage() {
    std::cout << ABSSYNTHE_VERSION << std::endl
<< "usage:" << std::endl
<<"./abssynthe [-h] [-t] [-ca {1,2,3}] [-v VERBOSE_LEVEL] [-o OUT_FILE] spec"
<< std::endl
<< "positional arguments:" << std::endl
<< "spec                               input specification in extended AIGER format"
<< std::endl
<< "optional arguments:" << std::endl
<< "-h, --help                         show this help message and exit"
<< std::endl
<< "-t, --use_trans                    compute a transition relation"
<< std::endl
<< "-ca {1,2,3}, --comp_algo {1,2,3}   choice of compositional algorithm"
<< std::endl
<< "-v VERBOSE_LEVEL, --verbose_level VERBOSE_LEVEL" << std::endl
<< "                                   Verbose level string, i.e. (D)ebug,"
<< std::endl
<< "                                   (W)arnings, (L)og messages" << std::endl
<< "-o OUT_FILE, --out_file OUT_FILE   Output file path. If the file extension"
<< std::endl
<< "                                   is .aig, binary output format will be used."
<< std::endl
<< "                                   With file extension .aag, ASCII output will"
<< std::endl
<< "                                   be used. The argument is ignored if spec"
<< std::endl
<< "                                   is not realizable." << std::endl;
}

void parse_arguments(int argc, char** argv) {
    // default values
    settings.comp_algo = 0;
    settings.use_trans = false;
    settings.out_file = NULL;
    settings.spec_file = NULL;

    // read values from argv
    int opt_key;
    int opt_index;
    while (true) {
        opt_key = getopt_long(argc, argv, "v:tc:o:", long_options,
                              &opt_index);
        if (opt_key == -1)
            break;
        switch (opt_key) {
            if (long_options[opt_index].flag != NULL)
                break;
            case 'h':
                usage();
                exit(0);
            case 'v':
                parseLogLevelString(optarg);
                break;
            case 't':
                logMsg("Using transition relation.");
                settings.use_trans = true;
                break;
            case 'c':
                settings.comp_algo = atoi(optarg);
                if (settings.comp_algo < 1 || settings.comp_algo > 3) {
                    errMsg(std::string("Expected comp_algo to be in {1,2,3} "
                                       "instead of ") + optarg);
                    usage();
                    exit(1);
                }
                break;
            case 'o':
                settings.out_file = optarg;
                break;
            default:
                usage();
                exit(1);
        }
    }
    argc -= optind;
    argv += optind;
    if (argc > 1) {
        errMsg("Too many arguments");
        usage();
    } else if (argc != 1) {
        errMsg("Too few arguments");
        usage();
    }
    settings.spec_file = argv[0];
}

int main (int argc, char** argv) {
    parse_arguments(argc, argv);
    // try to open the spec now
    AIG aig(settings.spec_file);
    // solve the synthesis problem
    bool result;
    if (settings.comp_algo == 1) {
        result = compSolve1(&aig);
    } else if (settings.comp_algo == 2){
        result = compSolve2(&aig);
    } else if (settings.comp_algo == 3){
        result = compSolve3(&aig);
#ifndef NDEBUG
				dbgMsg("Decomposition took: " + 
						std::to_string(getAccTime("decompose")/(double)CLOCKS_PER_SEC));
				dbgMsg("Local steps took: " + 
						std::to_string(getAccTime("localstep")/(double)CLOCKS_PER_SEC));
				dbgMsg("Global steps took: " + 
						std::to_string(getAccTime("globalstep")/(double)CLOCKS_PER_SEC));
#endif
    } else{
				// traditional fixpoint computation
        result = solve(&aig);
    }
    // return the realizability test result
    logMsg("Realizable? " + std::to_string(result));
    exit(result ? EXIT_STATUS_REALIZABLE : EXIT_STATUS_UNREALIZABLE);
}
