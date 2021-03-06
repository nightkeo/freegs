"""
Functions to impose boundary conditions on psi(plasma)

Copyright 2016 Ben Dudson, University of York. Email: benjamin.dudson@york.ac.uk

This file is part of FreeGS.

FreeGS is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FreeGS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with FreeGS.  If not, see <http://www.gnu.org/licenses/>.

"""

from .gradshafranov import Greens, mu0
from numpy import concatenate, sqrt

from scipy.integrate import romb # Romberg integration

def fixedBoundary(eq, Jtor, psi):
    """
    Set psi=0 on all boundaries
    
    Inputs
    ------
    
    eq    Equilibrium object (not used)
    Jtor  2D array of toroidal current (not used)
    psi   2D array of psi values (modified by call)
    
    Returns
    -------
    None
    """
    psi[0,:] = 0.0
    psi[:,0] = 0.0
    psi[-1,:] = 0.0
    psi[:,-1] = 0.0

def freeBoundary(eq, Jtor, psi):
    """
    Apply a free boundary condition using Green's functions
    
    Note: This method is inefficient because it requires
    an integral over the area of the domain for each point
    on the boundary. 

    Inputs
    ------
    
    eq    Equilibrium object (not used)
    Jtor  2D array of toroidal current (not used)
    psi   2D array of psi values (modified by call)

    Returns
    -------
    
    None
    """
    
    # Get the (R,Z) coordinates from the Equilibrium object
    R = eq.R
    Z = eq.Z

    nx,ny = psi.shape

    dR = R[1,0] - R[0,0]
    dZ = Z[0,1] - Z[0,0]
    
    # List of indices on the boundary
    bndry_indices = concatenate([
        [(x,0) for x in range(nx)],
        [(x,ny-1) for x in range(nx)],
        [(0,y) for y in range(ny)],
        [(nx-1,y) for y in range(ny)]])
    
    for x,y in bndry_indices:
        # Calculate the response of the boundary point
        # to each cell in the plasma domain
        greenfunc = Greens(R, Z, R[x,y], Z[x,y])

        # Prevent infinity/nan by removing (x,y) point
        greenfunc[x,y] = 0.0 
        
        # Integrate over the domain
        psi[x,y] = romb(romb(greenfunc*Jtor))*dR*dZ

def freeBoundaryHagenow(eq, Jtor, psi):
    """
    Apply a free boundary using von Hagenow's method
    
    Inputs
    ------
    
    eq    Equilibrium object (not used)
    Jtor  2D array of toroidal current (not used)
    psi   2D array of psi values (modified by call)

    Returns
    -------
    
    None
    """

    # Get the (R,Z) coordinates from the Equilibrium object
    R = eq.R
    Z = eq.Z

    nx,ny = psi.shape

    dR = R[1,0] - R[0,0]
    dZ = Z[0,1] - Z[0,0]
    
    # solver RHS
    rhs = eq.R * Jtor
    
    # Apply a zero-value boundary condition
    rhs[0,:] = 0.0
    rhs[:,0] = 0.0
    rhs[-1,:] = 0.0
    rhs[:,-1] = 0.0
    
    # Solve with a fixed boundary
    psi_fixed = eq.callSolver(psi, rhs)
    
    # Differentiate at the boundary
    
    #########################################################
    # First order accurate method
    
    #dUdn_L = (psi_fixed[0,:] - psi_fixed[1,:])/dR   # left boundary
    #dUdn_R = (psi_fixed[-1,:] - psi_fixed[-2,:])/dR # Right boundary
    #dUdn_D = (psi_fixed[:,0] - psi_fixed[:,1])/dZ  # Down boundary
    #dUdn_U = (psi_fixed[:,-1] - psi_fixed[:,-2])/dZ  # Upper boundary
    
    # Left down corner
    #dUdn_L[0] = dUdn_D[0] = (psi_fixed[0,0] - psi_fixed[1,1]) / dd
    # Left upper corner
    #dUdn_L[-1] = dUdn_U[0] = (psi_fixed[0,-1] - psi_fixed[1,-2]) / dd
    # Right down corner
    #dUdn_R[0] = dUdn_D[-1] = (psi_fixed[-1,0] - psi_fixed[-2,1]) / dd
    # Right upper corner
    #dUdn_R[-1] = dUdn_U[-1] = (psi_fixed[-1,-1] - psi_fixed[-2,-2]) / dd
    
    #########################################################
    # Second-order one-sided differences at the boundary
    
    dUdn_L = (1.5*psi_fixed[0,:] - 2.*psi_fixed[1,:] + 0.5*psi_fixed[2,:])/dR   # left boundary
    
    dUdn_R = (1.5*psi_fixed[-1,:] - 2.*psi_fixed[-2,:] + 0.5*psi_fixed[-3,:])/dR # Right boundary
    
    dUdn_D = (1.5*psi_fixed[:,0] - 2.*psi_fixed[:,1] + 0.5*psi_fixed[:,2])/dZ  # Down boundary
    
    dUdn_U = (1.5*psi_fixed[:,-1] - 2.*psi_fixed[:,-2] + 0.5*psi_fixed[:,-3])/dZ  # Upper boundary
    
    dd = sqrt(dR**2 + dZ**2) # Diagonal spacing

    # Left down corner 
    dUdn_L[0] = dUdn_D[0] = (1.5*psi_fixed[0,0] - 2.*psi_fixed[1,1] + 0.5*psi_fixed[2,2]) / dd
    
    # Left upper corner
    dUdn_L[-1] = dUdn_U[0] = (1.5*psi_fixed[0,-1] - 2.*psi_fixed[1,-2] + 0.5*psi_fixed[2,-3]) / dd

    # Right down corner
    dUdn_R[0] = dUdn_D[-1] = (1.5*psi_fixed[-1,0] - 2.*psi_fixed[-2,1] + 0.5*psi_fixed[-3,2]) / dd

    # Right upper corner
    dUdn_R[-1] = dUdn_U[-1] = (1.5*psi_fixed[-1,-1] - 2.*psi_fixed[-2,-2] + 0.5*psi_fixed[-3,-3]) / dd
    
    # Now for each point on the boundary perform a loop integral
    
    eps = 1e-2

    # List of indices on the boundary
    # (x index, y index, R change, Z change) 
    # where change in R,Z puts the observation point outside the boundary
    # to avoid the singularity in G(R,R') when R'=R
    
    bndry_indices = concatenate([
        [(x,0,    0.0,-eps) for x in range(nx)],  # Down boundary
        [(x,ny-1, 0.0, eps) for x in range(nx)], # Upper boundary
        [(0,y,   -eps, 0.0) for y in range(ny)],    # Left boundary
        [(nx-1,y, eps, 0.0) for y in range(ny)]]) # Right boundary

    ### APPLY FREE BOUNDARY USING GREENS METHOD
    #freeBoundary(eq, Jtor, psi)

    # Loop through points on boundary
    for x,y,Reps,Zeps in bndry_indices:
        # x and y can be floats here (Python 3.6.4)
        x = int(round(x))
        y = int(round(y))
        
        Rpos = R[x,y]+Reps
        Zpos = Z[x,y]+Zeps

        # Integrate over left boundary

        greenfunc = Greens(R[0,:], Z[0,:], Rpos, Zpos)
        result = romb(greenfunc * dUdn_L / R[0,:]) * dZ
        
        # Integrate over right boundary
        greenfunc = Greens(R[-1,:], Z[-1,:], Rpos, Zpos)
        result += romb(greenfunc * dUdn_R / R[-1,:]) * dZ
        
        # Integrate over down boundary
        greenfunc = Greens(R[:,0], Z[:,0], Rpos, Zpos)
        result += romb(greenfunc * dUdn_D / R[:,0]) * dR
        
        # Integrate over upper boundary
        greenfunc = Greens(R[:,-1], Z[:,-1], Rpos, Zpos)
        result += romb(greenfunc * dUdn_U / R[:,-1]) * dR
        
        ### Compare against Greens method
        #print("%d,%d, %e, %e, %e" % (x,y,psi[x,y], result, result/psi[x,y]))

        psi[x,y] = result
    
