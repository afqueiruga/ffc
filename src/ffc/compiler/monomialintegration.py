"This module provides efficient integration of monomial forms."

__author__ = "Anders Logg (logg@tti-c.org)"
__date__ = "2004-11-03 -- 2005-12-05"
__copyright__ = "Copyright (c) 2004 Anders Logg"
__license__  = "GNU GPL Version 2"

# Thanks to Robert C. Kirby for suggesting the initial algorithm that
# this implementation is based on.

# Python modules
import Numeric

# FIAT modules
from FIAT.quadrature import *
from FIAT.shapes import *

# FFC common modules
from ffc.common.debug import *
from ffc.common.progress import *

# FFC compiler modules
from algebra import *
from multiindex import *

def integrate(product):
    """Compute the reference tensor for a given monomial term of a
    multilinear form, given as a Product."""

    debug("Computing reference tensor, this may take some time...")

    # Initialize quadrature points and weights
    (points, weights, vscaling, dscaling) = __init_quadrature(product.basisfunctions)

    # Initialize quadrature table for basis functions
    table = __init_table(product.basisfunctions, points)

    # Compute table Psi for each factor
    psis = [__compute_psi(v, table, len(points), dscaling) for v in product.basisfunctions]

    # Compute product of all Psis
    A0 = __compute_product(psis, vscaling * product.numeric * weights)

    return A0

def __init_quadrature(basisfunctions):
    "Initialize quadrature for given monomial term."

    debug("Initializing quadrature.", 1)

    # Get shape (check first one, all should be the same)
    shape = basisfunctions[0].element.shape()

    # Compute number of points to match the degree
    q = __compute_degree(basisfunctions)
    m = (q + 1 + 1) / 2 # integer division gives 2m - 1 >= q
    debug("Total degree is %d, using %d quadrature point(s) in each dimension" % (q, m), 1)

    # Create quadrature rule and get points and weights
    quadrature = make_quadrature(shape, m)
    points = quadrature.get_points()
    weights = quadrature.get_weights()

    # Compensate for different choice of reference cells in FIAT
    # FIXME: Convince Rob to change his reference elements
    if shape == TRIANGLE:
        vscaling = 0.25  # Area 1/2 instead of 2
        dscaling = 2.0   # Scaling of derivative
    elif shape == TETRAHEDRON:
        vscaling = 0.125 # Volume 1/6 instead of 4/3
        dscaling = 2.0   # Scaling of derivative
        
    return (points, weights, vscaling, dscaling)

def __init_table(basisfunctions, points):
    """Initialize table of basis functions and their derivatives at
    the given quadrature points for each element."""

    debug("Precomputing table of basis functions at quadrature points.", 1)
    
    # Compute maximum number of derivatives for each element
    num_derivatives = {}
    for v in basisfunctions:
        element = v.element
        order = len(v.derivatives)
        if element in num_derivatives:
            num_derivatives[element] = max(order, num_derivatives[element])
        else:
            num_derivatives[element] = order

    # Call FIAT to tabulate the basis functions for each element
    table = {}
    for element in num_derivatives:
        order = num_derivatives[element]
        table[element] = element.tabulate(order, points)

    return table

def __compute_psi(v, table, num_points, dscaling):
    "Compute the table Psi for the given BasisFunction v."

    debug("Computing table for factor v = " + str(v), 1)

    # We just need to pick the values for Psi from the table, which is
    # somewhat tricky since the table created by tabulate_jet() is a
    # mix of list, dictionary and Numeric.array.
    #
    # The dimensions of the resulting table are ordered as follows:
    #
    #     one dimension  corresponding to quadrature points
    #     all dimensions corresponding to auxiliary Indices
    #     all dimensions corresponding to primary   Indices
    #     all dimensions corresponding to secondary Indices
    #
    # All fixed Indices are removed here. The first set of dimensions
    # corresponding to quadrature points and auxiliary Indices are removed
    # later when we sum over these dimensions.

    # Get FiniteElement for v
    element = v.element
    shapedim = element.shapedim()
    spacedim = element.spacedim()

    # Get Indices and shapes for Derivatives
    dindex = [d.index for d in v.derivatives]
    dshape = [shapedim for d in v.derivatives]
    dorder = len(dindex)

    # Get Indices and shapes for BasisFunction
    vindex = [v.index]
    vshape = [spacedim]

    # Get Indices and shapes for components
    if len(v.component) > 1:
        raise RuntimeError, "Can only handle rank 0 or rank 1 tensors."
    if len(v.component) > 0:
        cindex = [v.component[0]]
        cshape = [element.tensordim(0)]
    else:
        cindex = []
        cshape = []

    # Create list of Indices that label the dimensions of the tensor Psi
    indices = cindex + dindex + vindex
    shapes = cshape + dshape + vshape + [num_points]

    # Initialize tensor Psi: component, derivatives, basis function, points
    Psi = Numeric.zeros(shapes, Numeric.Float)

    # Iterate over derivative Indices
    dlists = build_indices(dshape) or [[]]
    if len(cindex) > 0:
        etable = table[element]
        for component in range(cshape[0]):
            for dlist in dlists:
                # Translate derivative multiindex to lookup tuple
                dtuple = __multiindex_to_tuple(dlist, shapedim)
                # Get values from table
                Psi[component][dlist] = etable[component][dorder][dtuple]
    else:
        etable = table[element][dorder]
        for dlist in dlists:
            # Translate derivative multiindex to lookup tuple
            dtuple = __multiindex_to_tuple(dlist, shapedim)
            # Get values from table
            Psi[dlist] = etable[dtuple]

    # Rearrange Indices as (fixed, auxiliary, primary, secondary)
    (rearrangement, num_indices) = __compute_rearrangement(indices)
    indices = [indices[i] for i in rearrangement]
    Psi = Numeric.transpose(Psi, rearrangement + (len(indices),))

    # Remove fixed indices
    for i in range(num_indices[0]):
        Psi = Psi[indices[i].index,...]
    indices = [index for index in indices if not index.type == "fixed"]

    # Put quadrature points first
    rank = Numeric.rank(Psi)
    Psi = Numeric.transpose(Psi, (rank - 1,) + tuple(range(0, rank - 1)))

    # Scale derivatives (FIAT uses different reference element)
    Psi = pow(dscaling, dorder) * Psi

    # Compute auxiliary index positions for current Psi
    bpart = [i.index for i in indices if i.type == "reference tensor auxiliary"]

    return (Psi, indices, bpart)

def __compute_product(psis, weights):
    "Compute special product of list of Psis."

    debug("Computing product of tables", 1)

    # The reference tensor is obtained by summing over quadrature
    # points and auxiliary Indices the outer product of all the Psis
    # with the first dimension (corresponding to quadrature points)
    # and all auxiliary dimensions removed.

    # Initialize zero reference tensor (will be rearranged later)
    (shape, indices) = __compute_shape(psis)
    A0 = Numeric.zeros(shape, Numeric.Float)

    # Initialize list of auxiliary multiindices
    bshape = __compute_auxiliary_shape(psis)
    bindices = build_indices(bshape) or [[]]

    # Sum over quadrature points and auxiliary indices
    num_points = len(weights)
    progress = Progress(num_points * len(bindices))
    for q in range(num_points):
        for b in bindices:
            
            # Compute outer products of subtables for current (q, b)
            B = 1.0
            for (Psi, index, bpart) in psis:
                B = Numeric.multiply.outer(B, Psi[[q] + [b[i] for i in bpart]])

            # Add product to reference tensor
            A0 = A0 + weights[q] * B

            # Update progress
            progress += 1

    # Rearrange Indices as (primary, secondary)
    (rearrangement, num_indices) = __compute_rearrangement(indices)
    A0 = Numeric.transpose(A0, rearrangement)

    return A0

def __compute_degree(basisfunctions):
    "Compute total degree for given monomial term."
    q = 0
    for v in basisfunctions:
        q += v.element.degree()
        for d in v.derivatives:
            q -= 1
    return q

def __compute_rearrangement(indices):
    """Compute rearrangement tuple for given list of Indices, so that
    the tuple reorders the given list of Indices with fixed, primary,
    secondary and auxiliary Indices in rising order."""
    fixed     = __find_indices(indices, "fixed")
    auxiliary = __find_indices(indices, "reference tensor auxiliary")
    primary   = __find_indices(indices, "primary")
    secondary = __find_indices(indices, "secondary")
    assert len(fixed + auxiliary + primary + secondary) == len(indices)
    return (tuple(fixed + auxiliary + primary + secondary), \
            (len(fixed), len(auxiliary), len(primary), len(secondary)))

def __compute_shape(psis):
    "Compute shape of reference tensor from given list of tables."
    shape, indices = [], []
    for (Psi, index, bpart) in psis:
        num_auxiliary = len([0 for i in index if i.type == "reference tensor auxiliary"])
        shape += Numeric.shape(Psi)[1 + num_auxiliary:]
        indices += index[num_auxiliary:]
    return (shape, indices)
    
def __compute_auxiliary_shape(psis):
    """Compute shape for auxiliary indices from given list of tables.
    Also compute a list of  mappings from each table to the auxiliary
    dimensions associated with that table."""
    # First find the number of different auxiliary indices (check maximum)
    bs = [b for (Psi, index, bpart) in psis for b in bpart]
    if len(bs) == 0: return []
    bmax = max(bs)
    # Find the dimension for each auxiliary index
    bshape = [0 for i in range(bmax + 1)]
    for (Psi, index, bpart) in psis:
        for i in range(len(bpart)):
            bshape[bpart[i]] = Numeric.shape(Psi)[i + 1]
    # Check that we found the shape for each auxiliary index
    if 0 in bshape:
        raise RuntimeError, "Unable to compute the shape for each auxiliary index."
    return bshape

def __find_indices(indices, type):
    "Return sorted list of positions for given Index type."
    pos = [i for i in range(len(indices)) if indices[i].type == type]
    val = [indices[i].index for i in range(len(indices)) if indices[i].type == type]
    return [pos[i] for i in Numeric.argsort(val)]

def __multiindex_to_tuple(dindex, shapedim):
    """Compute lookup tuple from given derivative
    multiindex. Necessary since the table we get from FIAT is a
    dictionary with the tuples as keys. A derivative tuple specifies
    the number of derivatives in each space dimension, rather than
    listing the space dimensions for the derivatives."""
    dtuple = [0 for i in range(shapedim)]
    for d in dindex:
        dtuple[d] += 1
    return tuple(dtuple)