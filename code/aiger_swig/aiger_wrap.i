%module aiger_wrap
%{
#include "aiger.h"
typedef struct aiger_private aiger_private;
struct aiger_private;
aiger_symbol* get_aiger_symbol(aiger_symbol*, int);
void aiger_redefine_input_as_and(aiger*, unsigned, unsigned, unsigned);
void aiger_delete_symbols(aiger_private*, aiger_symbol*, size_t);
%}

%ignore aiger_read_from_string(aiger*, const char*);
%include "aiger.h"
typedef struct aiger_private aiger_private;
struct aiger_private;
aiger_symbol* get_aiger_symbol(aiger_symbol*, int);
void aiger_redefine_input_as_and(aiger*, unsigned, unsigned, unsigned);
void aiger_delete_symbols(aiger_private*, aiger_symbol*, size_t);
