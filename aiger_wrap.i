%module aiger_wrap
%{
#include "aiger.h"
%}

%include "aiger.h"
%inline %{
aiger_symbol* get_aiger_symbol(aiger_symbol* s, int i) { return &s[i]; }
%}
