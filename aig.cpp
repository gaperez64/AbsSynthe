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

#include <stdlib.h>

#include "aiger.h"

#include "aig.h"
#include "logging.h"

unsigned AIG::nextLit() {
    return (this->spec->maxvar + 1) * 2;
}

void AIG::introduceErrorLatch() {
    if (this->error_fake_latch != NULL)
        return;
    this->error_fake_latch = (aiger_symbol*) malloc(sizeof(aiger_symbol));
    this->error_fake_latch->name = new char[6];
    strncpy(this->error_fake_latch->name, "error", 6);
    this->error_fake_latch->lit = this->nextLit();
    this->error_fake_latch->next = this->spec->outputs[0].lit;
    dbgMsg(std::string("Error fake latch = ") + 
           std::to_string(this->error_fake_latch->lit));
}

AIG::AIG(const char* aiger_file_name, bool intro_error_latch) {
    // default values for some local (for this instance) variables
    this->error_fake_latch = NULL;
    this->spec = NULL;
    // start lodaing
    this->spec = aiger_init();
    const char* err = aiger_open_and_read_from_file (spec, aiger_file_name);
    if (err) {
        errMsg(std::string("Error ") + err +
               " encountered while reading AIGER file " +
               aiger_file_name);
        exit(1);
    }
    if (spec->num_outputs != 1) {
        errMsg(std::string() +
               std::to_string(spec->num_outputs) + " > 1 number of outputs in " +
               "AIGER file " +
               aiger_file_name);
        exit(1);
    }
    // we now introduce a fake latch for the error function
    this->introduceErrorLatch();
    // let us now build the vector of latches, c_inputs, and u_inputs
    for (int i = 0; i <= spec->num_latches; i++)
        this->latches.push_back(spec->latches + i);
    for (int i = 0; i <= spec->num_inputs; i++) {
        aiger_symbol* symbol = spec->inputs + i;
        std::string name(symbol->name);
        if (name.find("controllable") == 0) // starts with "controllable"
            this->c_inputs.push_back(symbol);
        else
            this->u_inputs.push_back(symbol);
    }
    // print some debug information
    std::string litstring;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->latches.size()) + " Latches: " + litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
         i != this->c_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->c_inputs.size()) + " C.Inputs: " + litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
         i != this->u_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->u_inputs.size()) + " U.Inputs: " + litstring);
}
