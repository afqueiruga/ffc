__author__ = "Marie E. Rognes (meg@simula.no)"
__copyright__ = "Copyright (C) 2010 " + __author__
__license__  = "GNU LGPL version 3 or any later version"

# Last changed: 2010-11-04

from ufl import Coefficient
from ufl.algorithms import preprocess
from ffc.log import info, error
from ffc.compiler import compile_form
from ffc.formmanipulations import *
from ffc.errorcontrolwrappers import *

def _check_input(forms, object_names):
    """
    Can handle three variants of forms:

    (a, L, M): a has rank 2, L has rank a and M has rank 1

    (F, M): F has rank 1 and M has rank 0
    // (F, dF, M): F has rank 1, dF has rank 2 and M has rank 0
    """

    # Extract unknown (of None if not defined)
    unknown = object_names.get("unknown", None)

    if len(forms) == 2:
        (F, M) = forms

        #Check that unknown is defined
        assert (unknown), "Variable 'unknown' must be defined!"

        # Generate jacobian of F
        dF = derivative(F, unknown)
        return (dF, F, M), unknown, True

    assert(len(forms) == 3), "Wrong form input."

    (a, L, M) = forms

    # If unknown is undefined, define discrete solution as coefficient
    # on trial element and make M a functional (instead of a linear form)
    if unknown is None:
        V = extract_arguments(a)[1].element()
        unknown = Coefficient(V)
        object_names[id(unknown)] = "__discrete_primal_solution"
        M = action(M, unknown)
    else:
        error("Not implemented!")

    return (a, L, M), unknown, False

def generate_error_control(forms, object_names):

    info("Generating additionals")

    # Check input and extract appropriate forms
    forms, unknown, nonlinear = _check_input(forms, object_names)

    # Generate dual forms
    a_star, L_star = generate_dual_forms(forms, unknown)

    # Extract trial element as second argument of bilinear form
    V = unknown.element()

    # Generate extrapolation space by increasing order of trial space
    E = increase_order(V)

    # Dictionary for storing object names generated by error control
    ec_names = {}

    # Create coefficient for improved dual
    Ez_h = Coefficient(E)
    ec_names[id(Ez_h)] = "__improved_dual"

    # Create weak residual
    if nonlinear:
        weak_residual = generate_weak_residual(forms[1])
    else:
        weak_residual = generate_weak_residual(forms[:-1], unknown)

    # Generate error estimate (residual) (# FIXME: Add option here)
    eta_h = action(weak_residual, Ez_h)

    # Define approximation space for cell and facet residuals
    V_h = tear(V)

    # Create cell residual forms
    a_R_T, L_R_T, b_T = generate_cell_residual(weak_residual, V_h=V_h)
    ec_names[id(b_T)] = "__cell_bubble"

    # Create facet residual forms
    a_R_dT, L_R_dT, R_T, b_e = generate_facet_residual(weak_residual, V_h=V_h)
    ec_names[id(R_T)] = "__cell_residual"
    ec_names[id(b_e)] = "__cell_cone"

    # Define
    R_dT = Coefficient(V_h)
    z_h = Coefficient(extract_arguments(a_star)[1].element())
    ec_names[id(R_dT)] = "__facet_residual"
    ec_names[id(z_h)] = "__discrete_dual_solution"

    # Generate error indicators (# FIXME: Add option here)
    eta_T = generate_error_indicator(weak_residual, R_T, R_dT, Ez_h, z_h)

    ec_forms = (a_star, L_star, a_R_T, L_R_T, a_R_dT, L_R_dT, eta_h, eta_T)

    return (ec_forms, ec_names, forms)

def compile_with_error_control(forms, object_names, prefix, parameters):

    # Generate additional forms (and names) for error control
    ec_forms, ec_names, forms = generate_error_control(forms, object_names)

    # Check that there are no conflicts between user defined and
    # generated names
    comment = "%s are reserved error control names." % str(ec_names.keys())
    assert not (set(object_names.values()) & set(ec_names.values())), \
               "Conflict between user defined and generated names: %s" % comment
    for (name, value) in ec_names.iteritems():
        object_names[name] = value

    # Compile all forms (generated by error control, input and goal
    all_forms = ec_forms + forms

    compile_form(all_forms, object_names, prefix, parameters)

    maps = generate_wrapper_maps(ec_forms, forms)

    # Generate error_control DOLFIN wrapper
    (ec_code, typedefs) = generate_error_control_wrapper(prefix, maps)

    # Write code
    write_code(prefix, ec_code, typedefs)

    return 0