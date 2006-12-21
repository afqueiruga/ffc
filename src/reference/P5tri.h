// Automatically generated by FFC, the FEniCS Form Compiler, version 0.3.5.
// For further information, go to http://www/fenics.org/ffc/.
// Licensed under the GNU GPL Version 2.

#ifndef __P5TRI_H
#define __P5TRI_H

#include <dolfin/Mesh.h>
#include <dolfin/Cell.h>
#include <dolfin/Point.h>
#include <dolfin/AffineMap.h>
#include <dolfin/FiniteElement.h>
#include <dolfin/FiniteElementSpec.h>

namespace dolfin
{

class P5tri : public dolfin::FiniteElement
{
public:

  P5tri() : dolfin::FiniteElement(), tensordims(0), subelements(0)
  {
    // Element is scalar, don't need to initialize tensordims

    // Element is simple, don't need to initialize subelements
  }

  ~P5tri()
  {
    if ( tensordims ) delete [] tensordims;
    if ( subelements )
    {
      for (unsigned int i = 0; i < elementdim(); i++)
        delete subelements[i];
      delete [] subelements;
    }
  }

  inline unsigned int spacedim() const
  {
    return 21;
  }

  inline unsigned int shapedim() const
  {
    return 2;
  }

  inline unsigned int tensordim(unsigned int i) const
  {
    dolfin_error("Element is scalar.");
    return 0;
  }

  inline unsigned int elementdim() const
  {
    return 1;
  }

  inline unsigned int rank() const
  {
    return 0;
  }

  void nodemap(int nodes[], const Cell& cell, const Mesh& mesh) const
  {
    static unsigned int edge_reordering_0[2][4] = {{0, 1, 2, 3}, {3, 2, 1, 0}};
    nodes[0] = cell.entities(0)[0];
    nodes[1] = cell.entities(0)[1];
    nodes[2] = cell.entities(0)[2];
    int alignment = cell.alignment(1, 0);
    int offset = mesh.topology().size(0);
    nodes[3] = offset + 4*cell.entities(1)[0] + edge_reordering_0[alignment][0];
    nodes[4] = offset + 4*cell.entities(1)[0] + edge_reordering_0[alignment][1];
    nodes[5] = offset + 4*cell.entities(1)[0] + edge_reordering_0[alignment][2];
    nodes[6] = offset + 4*cell.entities(1)[0] + edge_reordering_0[alignment][3];
    alignment = cell.alignment(1, 1);
    nodes[7] = offset + 4*cell.entities(1)[1] + edge_reordering_0[alignment][0];
    nodes[8] = offset + 4*cell.entities(1)[1] + edge_reordering_0[alignment][1];
    nodes[9] = offset + 4*cell.entities(1)[1] + edge_reordering_0[alignment][2];
    nodes[10] = offset + 4*cell.entities(1)[1] + edge_reordering_0[alignment][3];
    alignment = cell.alignment(1, 2);
    nodes[11] = offset + 4*cell.entities(1)[2] + edge_reordering_0[alignment][0];
    nodes[12] = offset + 4*cell.entities(1)[2] + edge_reordering_0[alignment][1];
    nodes[13] = offset + 4*cell.entities(1)[2] + edge_reordering_0[alignment][2];
    nodes[14] = offset + 4*cell.entities(1)[2] + edge_reordering_0[alignment][3];
    offset = offset + 4*mesh.topology().size(1);
    nodes[15] = offset + 6*cell.index() + 0;
    nodes[16] = offset + 6*cell.index() + 1;
    nodes[17] = offset + 6*cell.index() + 2;
    nodes[18] = offset + 6*cell.index() + 3;
    nodes[19] = offset + 6*cell.index() + 4;
    nodes[20] = offset + 6*cell.index() + 5;
  }

  void pointmap(Point points[], unsigned int components[], const AffineMap& map) const
  {
    points[0] = map(0.000000000000000e+00, 0.000000000000000e+00);
    points[1] = map(1.000000000000000e+00, 0.000000000000000e+00);
    points[2] = map(0.000000000000000e+00, 1.000000000000000e+00);
    points[3] = map(8.000000000000000e-01, 2.000000000000000e-01);
    points[4] = map(6.000000000000000e-01, 4.000000000000000e-01);
    points[5] = map(4.000000000000000e-01, 6.000000000000000e-01);
    points[6] = map(2.000000000000000e-01, 8.000000000000000e-01);
    points[7] = map(0.000000000000000e+00, 8.000000000000000e-01);
    points[8] = map(0.000000000000000e+00, 6.000000000000000e-01);
    points[9] = map(0.000000000000000e+00, 4.000000000000000e-01);
    points[10] = map(0.000000000000000e+00, 2.000000000000000e-01);
    points[11] = map(2.000000000000000e-01, 0.000000000000000e+00);
    points[12] = map(4.000000000000000e-01, 0.000000000000000e+00);
    points[13] = map(6.000000000000000e-01, 0.000000000000000e+00);
    points[14] = map(8.000000000000000e-01, 0.000000000000000e+00);
    points[15] = map(2.000000000000000e-01, 2.000000000000000e-01);
    points[16] = map(4.000000000000000e-01, 2.000000000000000e-01);
    points[17] = map(6.000000000000000e-01, 2.000000000000000e-01);
    points[18] = map(2.000000000000000e-01, 4.000000000000000e-01);
    points[19] = map(4.000000000000000e-01, 4.000000000000000e-01);
    points[20] = map(2.000000000000000e-01, 6.000000000000000e-01);
    components[0] = 0;
    components[1] = 0;
    components[2] = 0;
    components[3] = 0;
    components[4] = 0;
    components[5] = 0;
    components[6] = 0;
    components[7] = 0;
    components[8] = 0;
    components[9] = 0;
    components[10] = 0;
    components[11] = 0;
    components[12] = 0;
    components[13] = 0;
    components[14] = 0;
    components[15] = 0;
    components[16] = 0;
    components[17] = 0;
    components[18] = 0;
    components[19] = 0;
    components[20] = 0;
  }

  void vertexeval(uint vertex_nodes[], unsigned int vertex, const Mesh& mesh) const
  {
    // FIXME: Temporary fix for Lagrange elements
    vertex_nodes[0] = vertex;
  }

  const FiniteElement& operator[] (unsigned int i) const
  {
    return *this;
  }

  FiniteElement& operator[] (unsigned int i)
  {
    return *this;
  }

  FiniteElementSpec spec() const
  {
    FiniteElementSpec s("Lagrange", "triangle", 5);
    return s;
  }
  
private:

  unsigned int* tensordims;
  FiniteElement** subelements;

};

}

#endif