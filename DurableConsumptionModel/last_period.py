import numpy as np
from numba import njit, prange

# consav
from consav import golden_section_search

# local modules
import utility

# a. objective
@njit
def obj_last_period(d,x,par):
    """ objective function in last period """
    
    # implied consumption (rest)
    c = x-d

    return -utility.func(c,d,par)

# b. create optcreate_optimizer
opt_last_period = golden_section_search.create_optimizer(obj_last_period)

@njit(parallel=True)
def solve(t,sol,par):
    """ solve the problem in the last period """

    # unpack
    inv_v_keep = sol.inv_v_keep[t]
    c_keep = sol.c_keep[t]
    inv_v_adj = sol.inv_v_adj[t]
    d_adj = sol.d_adj[t]
    c_adj = sol.c_adj[t]

    # a. keep
    for i_p in prange(par.Np):
        for i_n in range(par.Nn):
            for i_m in range(par.Nm):
                            
                # i. states
                _p = par.grid_p[i_p]
                n = par.grid_n[i_n]
                m = par.grid_m[i_m]

                if m == 0: # forced c = 0 
                    c_keep[i_p,i_n,i_m] = 0
                    inv_v_keep[i_p,i_n,i_m] = 0
                    continue
                
                # ii. optimal choice
                c_keep[i_p,i_n,i_m] = m

                # iii. optimal value
                v_keep = utility.func(c_keep[i_p,i_n,i_m],n,par)
                inv_v_keep[i_p,i_n,i_m] = -1.0/v_keep

    # b. adj
    for i_p in prange(par.Np):
        for i_x in range(par.Nx):
            
            # i. states
            _p = par.grid_p[i_p]
            x = par.grid_x[i_x]

            if x == 0: # forced c = d = 0
                d_adj[i_p,i_x] = 0
                c_adj[i_p,i_x] = 0
                inv_v_adj[i_p,i_x] = 0
                continue

            # ii. optimal choices
            d_low = np.fmin(x/2,1e-8)
            d_high = np.fmin(x,par.n_max)            
            d_adj[i_p,i_x] = opt_last_period(d_low,d_high,par.tol,x,par)
            c_adj[i_p,i_x] = x-d_adj[i_p,i_x]

            # iii. optimal value
            v_adj = -obj_last_period(d_adj[i_p,i_x],x,par)
            inv_v_adj[i_p,i_x] = -1.0/v_adj