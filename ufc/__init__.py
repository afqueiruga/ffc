__author__ = "Johan Hake (hake.dev@gmail.com)"
__copyright__ = "Copyright (C) 2010-2014 Johan Hake"
__date__ = "2010-08-19 -- 2014-02-14"
__license__  = "Released to the public domain"

# Import Python versions of the abstract classes in the UFC interface
from .ufc import (cell,
                 function,
                 form,
                 finite_element,
                 dofmap,
                 cell_integral,
                 exterior_facet_integral,
                 interior_facet_integral,
                 point_integral,
                 custom_integral,
                 __version__,
                 __swigversion__)
