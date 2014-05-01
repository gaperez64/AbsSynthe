# This file was automatically generated by SWIG (http://www.swig.org).
# Version 2.0.7
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.



from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_aiger_wrap', [dirname(__file__)])
        except ImportError:
            import _aiger_wrap
            return _aiger_wrap
        if fp is not None:
            try:
                _mod = imp.load_module('_aiger_wrap', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _aiger_wrap = swig_import_helper()
    del swig_import_helper
else:
    import _aiger_wrap
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


AIGER_VERSION = _aiger_wrap.AIGER_VERSION
aiger_false = _aiger_wrap.aiger_false
aiger_true = _aiger_wrap.aiger_true
aiger_binary_mode = _aiger_wrap.aiger_binary_mode
aiger_ascii_mode = _aiger_wrap.aiger_ascii_mode
aiger_stripped_mode = _aiger_wrap.aiger_stripped_mode
class aiger_and(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, aiger_and, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, aiger_and, name)
    __repr__ = _swig_repr
    __swig_setmethods__["lhs"] = _aiger_wrap.aiger_and_lhs_set
    __swig_getmethods__["lhs"] = _aiger_wrap.aiger_and_lhs_get
    if _newclass:lhs = _swig_property(_aiger_wrap.aiger_and_lhs_get, _aiger_wrap.aiger_and_lhs_set)
    __swig_setmethods__["rhs0"] = _aiger_wrap.aiger_and_rhs0_set
    __swig_getmethods__["rhs0"] = _aiger_wrap.aiger_and_rhs0_get
    if _newclass:rhs0 = _swig_property(_aiger_wrap.aiger_and_rhs0_get, _aiger_wrap.aiger_and_rhs0_set)
    __swig_setmethods__["rhs1"] = _aiger_wrap.aiger_and_rhs1_set
    __swig_getmethods__["rhs1"] = _aiger_wrap.aiger_and_rhs1_get
    if _newclass:rhs1 = _swig_property(_aiger_wrap.aiger_and_rhs1_get, _aiger_wrap.aiger_and_rhs1_set)
    def __init__(self): 
        this = _aiger_wrap.new_aiger_and()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _aiger_wrap.delete_aiger_and
    __del__ = lambda self : None;
aiger_and_swigregister = _aiger_wrap.aiger_and_swigregister
aiger_and_swigregister(aiger_and)

class aiger_symbol(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, aiger_symbol, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, aiger_symbol, name)
    __repr__ = _swig_repr
    __swig_setmethods__["lit"] = _aiger_wrap.aiger_symbol_lit_set
    __swig_getmethods__["lit"] = _aiger_wrap.aiger_symbol_lit_get
    if _newclass:lit = _swig_property(_aiger_wrap.aiger_symbol_lit_get, _aiger_wrap.aiger_symbol_lit_set)
    __swig_setmethods__["next"] = _aiger_wrap.aiger_symbol_next_set
    __swig_getmethods__["next"] = _aiger_wrap.aiger_symbol_next_get
    if _newclass:next = _swig_property(_aiger_wrap.aiger_symbol_next_get, _aiger_wrap.aiger_symbol_next_set)
    __swig_setmethods__["reset"] = _aiger_wrap.aiger_symbol_reset_set
    __swig_getmethods__["reset"] = _aiger_wrap.aiger_symbol_reset_get
    if _newclass:reset = _swig_property(_aiger_wrap.aiger_symbol_reset_get, _aiger_wrap.aiger_symbol_reset_set)
    __swig_setmethods__["size"] = _aiger_wrap.aiger_symbol_size_set
    __swig_getmethods__["size"] = _aiger_wrap.aiger_symbol_size_get
    if _newclass:size = _swig_property(_aiger_wrap.aiger_symbol_size_get, _aiger_wrap.aiger_symbol_size_set)
    __swig_setmethods__["lits"] = _aiger_wrap.aiger_symbol_lits_set
    __swig_getmethods__["lits"] = _aiger_wrap.aiger_symbol_lits_get
    if _newclass:lits = _swig_property(_aiger_wrap.aiger_symbol_lits_get, _aiger_wrap.aiger_symbol_lits_set)
    __swig_setmethods__["name"] = _aiger_wrap.aiger_symbol_name_set
    __swig_getmethods__["name"] = _aiger_wrap.aiger_symbol_name_get
    if _newclass:name = _swig_property(_aiger_wrap.aiger_symbol_name_get, _aiger_wrap.aiger_symbol_name_set)
    def __init__(self): 
        this = _aiger_wrap.new_aiger_symbol()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _aiger_wrap.delete_aiger_symbol
    __del__ = lambda self : None;
aiger_symbol_swigregister = _aiger_wrap.aiger_symbol_swigregister
aiger_symbol_swigregister(aiger_symbol)

class aiger(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, aiger, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, aiger, name)
    __repr__ = _swig_repr
    __swig_setmethods__["maxvar"] = _aiger_wrap.aiger_maxvar_set
    __swig_getmethods__["maxvar"] = _aiger_wrap.aiger_maxvar_get
    if _newclass:maxvar = _swig_property(_aiger_wrap.aiger_maxvar_get, _aiger_wrap.aiger_maxvar_set)
    __swig_setmethods__["num_inputs"] = _aiger_wrap.aiger_num_inputs_set
    __swig_getmethods__["num_inputs"] = _aiger_wrap.aiger_num_inputs_get
    if _newclass:num_inputs = _swig_property(_aiger_wrap.aiger_num_inputs_get, _aiger_wrap.aiger_num_inputs_set)
    __swig_setmethods__["num_latches"] = _aiger_wrap.aiger_num_latches_set
    __swig_getmethods__["num_latches"] = _aiger_wrap.aiger_num_latches_get
    if _newclass:num_latches = _swig_property(_aiger_wrap.aiger_num_latches_get, _aiger_wrap.aiger_num_latches_set)
    __swig_setmethods__["num_outputs"] = _aiger_wrap.aiger_num_outputs_set
    __swig_getmethods__["num_outputs"] = _aiger_wrap.aiger_num_outputs_get
    if _newclass:num_outputs = _swig_property(_aiger_wrap.aiger_num_outputs_get, _aiger_wrap.aiger_num_outputs_set)
    __swig_setmethods__["num_ands"] = _aiger_wrap.aiger_num_ands_set
    __swig_getmethods__["num_ands"] = _aiger_wrap.aiger_num_ands_get
    if _newclass:num_ands = _swig_property(_aiger_wrap.aiger_num_ands_get, _aiger_wrap.aiger_num_ands_set)
    __swig_setmethods__["num_bad"] = _aiger_wrap.aiger_num_bad_set
    __swig_getmethods__["num_bad"] = _aiger_wrap.aiger_num_bad_get
    if _newclass:num_bad = _swig_property(_aiger_wrap.aiger_num_bad_get, _aiger_wrap.aiger_num_bad_set)
    __swig_setmethods__["num_constraints"] = _aiger_wrap.aiger_num_constraints_set
    __swig_getmethods__["num_constraints"] = _aiger_wrap.aiger_num_constraints_get
    if _newclass:num_constraints = _swig_property(_aiger_wrap.aiger_num_constraints_get, _aiger_wrap.aiger_num_constraints_set)
    __swig_setmethods__["num_justice"] = _aiger_wrap.aiger_num_justice_set
    __swig_getmethods__["num_justice"] = _aiger_wrap.aiger_num_justice_get
    if _newclass:num_justice = _swig_property(_aiger_wrap.aiger_num_justice_get, _aiger_wrap.aiger_num_justice_set)
    __swig_setmethods__["num_fairness"] = _aiger_wrap.aiger_num_fairness_set
    __swig_getmethods__["num_fairness"] = _aiger_wrap.aiger_num_fairness_get
    if _newclass:num_fairness = _swig_property(_aiger_wrap.aiger_num_fairness_get, _aiger_wrap.aiger_num_fairness_set)
    __swig_setmethods__["inputs"] = _aiger_wrap.aiger_inputs_set
    __swig_getmethods__["inputs"] = _aiger_wrap.aiger_inputs_get
    if _newclass:inputs = _swig_property(_aiger_wrap.aiger_inputs_get, _aiger_wrap.aiger_inputs_set)
    __swig_setmethods__["latches"] = _aiger_wrap.aiger_latches_set
    __swig_getmethods__["latches"] = _aiger_wrap.aiger_latches_get
    if _newclass:latches = _swig_property(_aiger_wrap.aiger_latches_get, _aiger_wrap.aiger_latches_set)
    __swig_setmethods__["outputs"] = _aiger_wrap.aiger_outputs_set
    __swig_getmethods__["outputs"] = _aiger_wrap.aiger_outputs_get
    if _newclass:outputs = _swig_property(_aiger_wrap.aiger_outputs_get, _aiger_wrap.aiger_outputs_set)
    __swig_setmethods__["bad"] = _aiger_wrap.aiger_bad_set
    __swig_getmethods__["bad"] = _aiger_wrap.aiger_bad_get
    if _newclass:bad = _swig_property(_aiger_wrap.aiger_bad_get, _aiger_wrap.aiger_bad_set)
    __swig_setmethods__["constraints"] = _aiger_wrap.aiger_constraints_set
    __swig_getmethods__["constraints"] = _aiger_wrap.aiger_constraints_get
    if _newclass:constraints = _swig_property(_aiger_wrap.aiger_constraints_get, _aiger_wrap.aiger_constraints_set)
    __swig_setmethods__["justice"] = _aiger_wrap.aiger_justice_set
    __swig_getmethods__["justice"] = _aiger_wrap.aiger_justice_get
    if _newclass:justice = _swig_property(_aiger_wrap.aiger_justice_get, _aiger_wrap.aiger_justice_set)
    __swig_setmethods__["fairness"] = _aiger_wrap.aiger_fairness_set
    __swig_getmethods__["fairness"] = _aiger_wrap.aiger_fairness_get
    if _newclass:fairness = _swig_property(_aiger_wrap.aiger_fairness_get, _aiger_wrap.aiger_fairness_set)
    __swig_setmethods__["ands"] = _aiger_wrap.aiger_ands_set
    __swig_getmethods__["ands"] = _aiger_wrap.aiger_ands_get
    if _newclass:ands = _swig_property(_aiger_wrap.aiger_ands_get, _aiger_wrap.aiger_ands_set)
    __swig_setmethods__["comments"] = _aiger_wrap.aiger_comments_set
    __swig_getmethods__["comments"] = _aiger_wrap.aiger_comments_get
    if _newclass:comments = _swig_property(_aiger_wrap.aiger_comments_get, _aiger_wrap.aiger_comments_set)
    def __init__(self): 
        this = _aiger_wrap.new_aiger()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _aiger_wrap.delete_aiger
    __del__ = lambda self : None;
aiger_swigregister = _aiger_wrap.aiger_swigregister
aiger_swigregister(aiger)


def aiger_id():
  return _aiger_wrap.aiger_id()
aiger_id = _aiger_wrap.aiger_id

def aiger_version():
  return _aiger_wrap.aiger_version()
aiger_version = _aiger_wrap.aiger_version

def aiger_init():
  return _aiger_wrap.aiger_init()
aiger_init = _aiger_wrap.aiger_init

def aiger_init_mem(*args):
  return _aiger_wrap.aiger_init_mem(*args)
aiger_init_mem = _aiger_wrap.aiger_init_mem

def aiger_reset(*args):
  return _aiger_wrap.aiger_reset(*args)
aiger_reset = _aiger_wrap.aiger_reset

def aiger_add_input(*args):
  return _aiger_wrap.aiger_add_input(*args)
aiger_add_input = _aiger_wrap.aiger_add_input

def aiger_add_latch(*args):
  return _aiger_wrap.aiger_add_latch(*args)
aiger_add_latch = _aiger_wrap.aiger_add_latch

def aiger_add_output(*args):
  return _aiger_wrap.aiger_add_output(*args)
aiger_add_output = _aiger_wrap.aiger_add_output

def aiger_add_bad(*args):
  return _aiger_wrap.aiger_add_bad(*args)
aiger_add_bad = _aiger_wrap.aiger_add_bad

def aiger_add_constraint(*args):
  return _aiger_wrap.aiger_add_constraint(*args)
aiger_add_constraint = _aiger_wrap.aiger_add_constraint

def aiger_add_justice(*args):
  return _aiger_wrap.aiger_add_justice(*args)
aiger_add_justice = _aiger_wrap.aiger_add_justice

def aiger_add_fairness(*args):
  return _aiger_wrap.aiger_add_fairness(*args)
aiger_add_fairness = _aiger_wrap.aiger_add_fairness

def aiger_add_reset(*args):
  return _aiger_wrap.aiger_add_reset(*args)
aiger_add_reset = _aiger_wrap.aiger_add_reset

def aiger_add_and(*args):
  return _aiger_wrap.aiger_add_and(*args)
aiger_add_and = _aiger_wrap.aiger_add_and

def aiger_add_comment(*args):
  return _aiger_wrap.aiger_add_comment(*args)
aiger_add_comment = _aiger_wrap.aiger_add_comment

def aiger_check(*args):
  return _aiger_wrap.aiger_check(*args)
aiger_check = _aiger_wrap.aiger_check

def aiger_write_to_file(*args):
  return _aiger_wrap.aiger_write_to_file(*args)
aiger_write_to_file = _aiger_wrap.aiger_write_to_file

def aiger_write_to_string(*args):
  return _aiger_wrap.aiger_write_to_string(*args)
aiger_write_to_string = _aiger_wrap.aiger_write_to_string

def aiger_write_generic(*args):
  return _aiger_wrap.aiger_write_generic(*args)
aiger_write_generic = _aiger_wrap.aiger_write_generic

def aiger_open_and_write_to_file(*args):
  return _aiger_wrap.aiger_open_and_write_to_file(*args)
aiger_open_and_write_to_file = _aiger_wrap.aiger_open_and_write_to_file

def aiger_is_reencoded(*args):
  return _aiger_wrap.aiger_is_reencoded(*args)
aiger_is_reencoded = _aiger_wrap.aiger_is_reencoded

def aiger_reencode(*args):
  return _aiger_wrap.aiger_reencode(*args)
aiger_reencode = _aiger_wrap.aiger_reencode

def aiger_coi(*args):
  return _aiger_wrap.aiger_coi(*args)
aiger_coi = _aiger_wrap.aiger_coi

def aiger_read_from_file(*args):
  return _aiger_wrap.aiger_read_from_file(*args)
aiger_read_from_file = _aiger_wrap.aiger_read_from_file

def aiger_read_generic(*args):
  return _aiger_wrap.aiger_read_generic(*args)
aiger_read_generic = _aiger_wrap.aiger_read_generic

def aiger_error(*args):
  return _aiger_wrap.aiger_error(*args)
aiger_error = _aiger_wrap.aiger_error

def aiger_open_and_read_from_file(*args):
  return _aiger_wrap.aiger_open_and_read_from_file(*args)
aiger_open_and_read_from_file = _aiger_wrap.aiger_open_and_read_from_file

def aiger_write_symbols_to_file(*args):
  return _aiger_wrap.aiger_write_symbols_to_file(*args)
aiger_write_symbols_to_file = _aiger_wrap.aiger_write_symbols_to_file

def aiger_write_comments_to_file(*args):
  return _aiger_wrap.aiger_write_comments_to_file(*args)
aiger_write_comments_to_file = _aiger_wrap.aiger_write_comments_to_file

def aiger_strip_symbols_and_comments(*args):
  return _aiger_wrap.aiger_strip_symbols_and_comments(*args)
aiger_strip_symbols_and_comments = _aiger_wrap.aiger_strip_symbols_and_comments

def aiger_get_symbol(*args):
  return _aiger_wrap.aiger_get_symbol(*args)
aiger_get_symbol = _aiger_wrap.aiger_get_symbol

def aiger_lit2tag(*args):
  return _aiger_wrap.aiger_lit2tag(*args)
aiger_lit2tag = _aiger_wrap.aiger_lit2tag

def aiger_is_input(*args):
  return _aiger_wrap.aiger_is_input(*args)
aiger_is_input = _aiger_wrap.aiger_is_input

def aiger_is_latch(*args):
  return _aiger_wrap.aiger_is_latch(*args)
aiger_is_latch = _aiger_wrap.aiger_is_latch

def aiger_is_and(*args):
  return _aiger_wrap.aiger_is_and(*args)
aiger_is_and = _aiger_wrap.aiger_is_and

def get_aiger_symbol(*args):
  return _aiger_wrap.get_aiger_symbol(*args)
get_aiger_symbol = _aiger_wrap.get_aiger_symbol

def aiger_redefine_input_as_and(*args):
  return _aiger_wrap.aiger_redefine_input_as_and(*args)
aiger_redefine_input_as_and = _aiger_wrap.aiger_redefine_input_as_and

def aiger_delete_symbols(*args):
  return _aiger_wrap.aiger_delete_symbols(*args)
aiger_delete_symbols = _aiger_wrap.aiger_delete_symbols
# This file is compatible with both classic and new-style classes.


