""" 
Various fitting formulas provided by numerical relativity 

Archisman Ghosh, Nathan K. Johnson-McDaniel, P. Ajith, 2015-04-09 
"""

import numpy as np 
import scipy.optimize as so
try:
    import lal
except ImportError:
    print('Cannot import lal SWIG bindings')

# list of final mass and spin fit names
class bbh_final_state_fits:
    pan2011 = "Pan2011" # Pan et al.             [Phys Rev D 84, 124052 (2011)] (mass+spin, non-spinning)
    hlz2014 = "HLZ2014" # Healy et al.           [Phys Rev D 90, 104004 (2014)] (mass+spin, aligned)
    phenD   = "PhenomD" # Husa et al.            [Phys Rev D 93, 044006 (2016)] (mass+spin, aligned)
    uib2016 = "UIB2016" # Jimenez-Forteza et al. [LIGO-P1600270 (2016)]         (mass+spin, aligned)
    hbr2016 = "HBR2016" # Hofmann et al.         [ApJL 825:L19 (2016)]          (spin only, precessing)

# list of Kerr truncation behaviours
class bbh_Kerr_trunc_opts:
    trunc        = "TRUNCATE"       # truncate fit value to 1.0, with an info message
    trunc_silent = "TRUNCATESILENT" # truncate fit value to 1.0, without info message
    keep         = "KEEP"           # keep fit value, even if superextremal, but still give the info message
    ign          = "IGNORE"         # keep fit value, even if superextremal, without info message
    err          = "ERROR"          # abort with an error if fit value is superextremal

# Functions to check that input values are physical

def _check_m(m1,m2):
    if np.any(m1<=0):
        raise ValueError("m1 has to be positive")
    if np.any(m2<=0):
        raise ValueError("m2 has to be positive")

def _check_chi(chi1, chi2):
    if np.any(chi1>1):
      raise ValueError("chi1 has to be <= 1")
    if np.any(chi2>1):
      raise ValueError("chi2 has to be <= 1")
    if np.any(chi1<0):
      raise ValueError("chi1 has to be nonnegative")
    if np.any(chi2<0):
      raise ValueError("chi2 has to be nonnegative")

def _check_mchi(m1,m2,chi1,chi2):
    _check_m(m1,m2)
    _check_chi(chi1,chi2)

def _truncate_at_Kerr_limit(chif, behavior, fitname="this"):
    if behavior not in bbh_Kerr_trunc_opts.__dict__.values():
      raise ValueError("Unknown user option '%s' for Kerr truncation behavior." % behavior)
    if behavior!=bbh_Kerr_trunc_opts.ign and np.any(abs(chif)>1.0):
      if isinstance(chif,(list,np.ndarray)):
        idx_over = np.where(abs(chif)>1.0)
        if behavior==bbh_Kerr_trunc_opts.trunc or behavior==bbh_Kerr_trunc_opts.trunc_silent:
          chif_trunc = np.sign(chif[idx_over])*1.0
          if behavior==bbh_Kerr_trunc_opts.trunc:
            print "Truncating %d excessive chif values from %s fit to Kerr limit of +-1.0" % (np.size(idx_over), fitname)
          chif[idx_over] = chif_trunc
        elif behavior==bbh_Kerr_trunc_opts.keep:
          print "Note: %s fit predicts %d chif values in excess of the Kerr limit." % (fitname, np.size(idx_over))
        elif behavior==bbh_Kerr_trunc_opts.err:
          raise ValueError("%s fit predicts %d chif values in excess of the Kerr limit." % (fitname, np.size(idx_over)))
      else:
        if behavior==bbh_Kerr_trunc_opts.trunc or behavior==bbh_Kerr_trunc_opts.trunc_silent:
          chif_trunc = np.sign(chif)*1.0
          if behavior==bbh_Kerr_trunc_opts.trunc:
            print "Truncating excessive chif of %f from %s fit to Kerr limit of %f" % (chif, fitname, chif_trunc)
          chif = chif_trunc
        elif behavior==bbh_Kerr_trunc_opts.keep:
          print "Note: %s fit predicts chif of %f in excess of the Kerr limit." % (fitname, chif)
        elif behavior==bbh_Kerr_trunc_opts.err:
          raise ValueError("%s fit predicts chif of %f in excess of the Kerr limit." % (fitname, chif))
    return chif

# Final mass and spin functions

def bbh_final_mass_non_spinning_Panetal(m1, m2):
    """
    Calculate the mass of the final BH resulting from the merger of two non-spinning black holes using eqn. 29a of from Pan et al, Phys Rev D 84, 124052 (2011).
    
    Parameters
    ----------
    m1, m2 : component masses
    
    Returns
    ------
    final mass, mf
    """
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    
    m = m1 + m2
    eta = m1*m2/(m1+m2)**2.
    return m*(1. + (np.sqrt(8./9.)-1.)*eta - 0.4333*(eta**2.) - (0.4392*(eta**3)))

def bbh_final_spin_non_spinning_Panetal(m1, m2):
    """
    Calculate the spin of the final BH resulting from the merger of two non-spinning black holes using eqn. 29b of Pan et al, Phys Rev D 84, 124052 (2011).
    
    Parameters
    ----------
    m1, m2 : component masses
    
    Returns
    ------
    final dimensionless spin, chif
    """
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    
    eta = m1*m2/(m1+m2)**2.
    return np.sqrt(12.)*eta - 3.871*(eta**2.) + 4.028*(eta**3)

def calc_isco_radius(a):
    """
    Calculate the ISCO radius of a Kerr BH as a function of the Kerr parameter using eqns. 2.5 and 2.8 from Ori and Thorne, Phys Rev D 62, 24022 (2000)
    
    Parameters
    ----------
    a : Kerr parameter
    
    Returns
    -------
    ISCO radius
    """
     
    a = np.minimum(np.array(a),1.) # Only consider a <=1, to avoid numerical problems

    # Ref. Eq. (2.5) of Ori, Thorne Phys Rev D 62 124022 (2000)
    z1 = 1.+(1.-a**2.)**(1./3)*((1.+a)**(1./3) + (1.-a)**(1./3))
    z2 = np.sqrt(3.*a**2 + z1**2)
    a_sign = np.sign(a)
    return 3+z2 - np.sqrt((3.-z1)*(3.+z1+2.*z2))*a_sign

def _final_spin_diff_Healyetal(a_f, eta, delta_m, S, Delta):
    """ Internal function: the final spin is determined by minimizing this function """
    
    # calculate ISCO radius
    r_isco = calc_isco_radius(a_f)
    
    # angular momentum at ISCO -- Eq.(2.8) of Ori, Thorne Phys Rev D 62 124022 (2000)
    J_isco = (3*np.sqrt(r_isco)-2*a_f)*2./np.sqrt(3*r_isco)
    
    # fitting coefficients - Table XI of Healy et al Phys Rev D 90, 104004 (2014)
    # [fourth order fits]
    L0  = 0.686710
    L1  = 0.613247
    L2a = -0.145427
    L2b = -0.115689
    L2c = -0.005254
    L2d = 0.801838
    L3a = -0.073839
    L3b = 0.004759
    L3c = -0.078377
    L3d = 1.585809
    L4a = -0.003050
    L4b = -0.002968
    L4c = 0.004364
    L4d = -0.047204
    L4e = -0.053099
    L4f = 0.953458
    L4g = -0.067998
    L4h = 0.001629
    L4i = -0.066693
    
    a_f_new = (4.*eta)**2.*(L0  +  L1*S +  L2a*Delta*delta_m + L2b*S**2. + L2c*Delta**2 \
        + L2d*delta_m**2. + L3a*Delta*S*delta_m + L3b*S*Delta**2. + L3c*S**3. \
        + L3d*S*delta_m**2. + L4a*Delta*S**2*delta_m + L4b*Delta**3.*delta_m \
        + L4c*Delta**4. + L4d*S**4. + L4e*Delta**2.*S**2. + L4f*delta_m**4 + L4g*Delta*delta_m**3. \
        + L4h*Delta**2.*delta_m**2. + L4i*S**2.*delta_m**2.) \
        + S*(1. + 8.*eta)*delta_m**4. + eta*J_isco*delta_m**6.
    
    return abs(a_f-a_f_new)

def bbh_final_spin_non_precessing_Healyetal(m1, m2, chi1, chi2):
    """
    Calculate the spin of the final BH resulting from the merger of two black holes with non-precessing spins using fit from Healy et al Phys Rev D 90, 104004 (2014)
    
    Parameters
    ----------
    m1, m2 : component masses
    chi1, chi2 : dimensionless spins of two BHs
    
    Returns
    -------
    dimensionless final spin, chif
    """
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    chi1 = np.vectorize(float)(np.array(chi1))
    chi2 = np.vectorize(float)(np.array(chi2))
    
    if np.any(abs(chi1)>1):
      raise ValueError("chi1 has to be in [-1, 1]")
    if np.any(abs(chi2)>1):
      raise ValueError("chi2 has to be in [-1, 1]")
    
    # Vectorize the function if arrays are provided as input
    if np.size(m1) * np.size(m2) * np.size(chi1) * np.size(chi2) > 1:
        return np.vectorize(bbh_final_spin_non_precessing_Healyetal)(m1, m2, chi1, chi2)
    
    # binary parameters
    m = m1+m2
    q = m1/m2
    eta = q/(1.+q)**2.
    delta_m = (m1-m2)/m
    
    S1 = chi1*m1**2 # spin angular momentum 1
    S2 = chi2*m2**2 # spin angular momentum 2
    S = (S1+S2)/m**2 # symmetric spin (dimensionless -- called \tilde{S} in the paper)
    Delta = (S2/m2-S1/m1)/m # antisymmetric spin (dimensionless -- called tilde{Delta} in the paper
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # compute the final spin
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    
    x, cov_x = so.leastsq(_final_spin_diff_Healyetal, 0., args=(eta, delta_m, S, Delta))
    
    # The first element returned by so.leastsq() is a scalar in early versions of scipy (like 0.7.2) while it is a tuple of length 1 in later versions of scipy (like 0.10.1). The following bit ensures that a scalar is returned for a set of scalar inputs in a version-independent way.
    if hasattr(x, '__len__'):
      chif = x[0]
    else:
      chif = x
    
    return chif

def bbh_final_mass_non_precessing_Healyetal(m1, m2, chi1, chi2, chif=None):
    """
    Calculate the mass of the final BH resulting from the merger of two black holes with non-precessing spins using fit from Healy et al Phys Rev D 90, 104004 (2014)
    
    Parameters
    ----------
    m1, m2 : component masses
    chi1, chi2 : dimensionless spins of two BHs
    chif: final spin (optional), if already calculated
    
    Returns
    -------
    final mass, mf
    """
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    chi1 = np.vectorize(float)(np.array(chi1))
    chi2 = np.vectorize(float)(np.array(chi2))
    
    if np.any(abs(chi1)>1):
      raise ValueError("chi1 has to be in [-1, 1]")
    if np.any(abs(chi2)>1):
      raise ValueError("chi2 has to be in [-1, 1]")
    
    # binary parameters
    m = m1+m2
    q = m1/m2
    eta = q/(1.+q)**2.
    delta_m = (m1-m2)/m
    
    S1 = chi1*m1**2 # spin angular momentum 1
    S2 = chi2*m2**2 # spin angular momentum 2
    S = (S1+S2)/m**2 # symmetric spin (dimensionless -- called \tilde{S} in the paper)
    Delta = (S2/m2-S1/m1)/m # antisymmetric spin (dimensionless -- called tilde{Delta} in the paper
    
    if chif is None:
        chif = bbh_final_spin_non_precessing_Healyetal(m1, m2, chi1, chi2)
    else:
        chif = np.array(chif)
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # now compute the final mass
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    r_isco = calc_isco_radius(chif)
    
    # fitting coefficients - Table XI of Healy et al Phys Rev D 90, 104004 (2014)
    # [fourth order fits]
    M0  = 0.951507
    K1  = -0.051379
    K2a = -0.004804
    K2b = -0.054522
    K2c = -0.000022
    K2d = 1.995246
    K3a = 0.007064
    K3b = -0.017599
    K3c = -0.119175
    K3d = 0.025000
    K4a = -0.068981
    K4b = -0.011383
    K4c = -0.002284
    K4d = -0.165658
    K4e = 0.019403
    K4f = 2.980990
    K4g = 0.020250
    K4h = -0.004091
    K4i = 0.078441
    
    # binding energy at ISCO -- Eq.(2.7) of Ori, Thorne Phys Rev D 62 124022 (2000)
    E_isco = (1. - 2./r_isco + chif/r_isco**1.5)/np.sqrt(1. - 3./r_isco + 2.*chif/r_isco**1.5)
    
    # final mass -- Eq. (14) of Healy et al Phys Rev D 90, 104004 (2014)
    mf = (4.*eta)**2*(M0 + K1*S + K2a*Delta*delta_m + K2b*S**2 + K2c*Delta**2 + K2d*delta_m**2 \
        + K3a*Delta*S*delta_m + K3b*S*Delta**2 + K3c*S**3 + K3d*S*delta_m**2 \
        + K4a*Delta*S**2*delta_m + K4b*Delta**3*delta_m + K4c*Delta**4 + K4d*S**4 \
        + K4e*Delta**2*S**2 + K4f*delta_m**4 + K4g*Delta*delta_m**3 + K4h*Delta**2*delta_m**2 \
        + K4i*S**2*delta_m**2) + (1+eta*(E_isco+11.))*delta_m**6.
    
    return mf*m

def bbh_final_spin_projected_spin_Healyetal(m1, m2, chi1, chi2, tilt1, tilt2):
    """
    wrapper to bbh_final_spin_projected_spins() for backwards compatibility
    """
    return bbh_final_spin_projected_spins(m1, m2, chi1, chi2, tilt1, tilt2, "HLZ2014")

def bbh_final_mass_projected_spin_Healyetal(m1, m2, chi1, chi2, tilt1, tilt2, chif=None):
    """
    wrapper to bbh_final_mass_projected_spins() for backwards compatibility
    """
    return bbh_final_mass_projected_spins(m1, m2, chi1, chi2, tilt1, tilt2, "HLZ2014", chif)

def bbh_final_spin_precessing_Healyetal_extension_Minit(m1, m2, chi1, chi2, tilt1, tilt2, phi12):
   """
   wrapper to bbh_final_spin_precessing() for backwards compatibility
   """
   return bbh_final_spin_precessing(m1, m2, chi1, chi2, tilt1, tilt2, phi12, "HLZ2014")

def bbh_final_mass_projected_spins(m1, m2, chi1, chi2, tilt1, tilt2, fitname, chif=None):
    """
    Calculate the mass of the final BH resulting from the merger of two black holes,
    only using the projected spins along the total angular momentum
    and some aligned-spin fit from the literature

    Parameters
    ----------
    m1, m2 : component masses
    chi1, chi2 : dimensionless spins of two BHs
    tilt1, tilt2 : tilts (in radians) in the new spin convention
    fitname: fit selection currently supports Pan2011 (non-spinning), HLZ2014, PhenomD, UIB2016
    chif: final spin (optional, only used for HLZ2014), if already calculated

    Returns
    -------
    final mass, mf
    """

    m1    = np.vectorize(float)(np.array(m1))
    m2    = np.vectorize(float)(np.array(m2))
    chi1  = np.vectorize(float)(np.array(chi1))
    chi2  = np.vectorize(float)(np.array(chi2))
    tilt1 = np.vectorize(float)(np.array(tilt1))
    tilt2 = np.vectorize(float)(np.array(tilt2))
    if chif is not None:
       chif = np.vectorize(float)(np.array(chif))

    _check_mchi(m1,m2,chi1,chi2) # Check that inputs are physical

    chi1proj = chi1*np.cos(tilt1)
    chi2proj = chi2*np.cos(tilt2)

    if fitname==bbh_final_state_fits.pan2011:
       if np.any(chi1!=0) or np.any(chi2!=0) or np.any(tilt1!=0) or np.any(tilt2!=0):
          print "Note: Pan2011 fit does not use spins."
       if chif is not None:
          print "Note: Precomputed chif not used by this fit."
       mf = bbh_final_mass_non_spinning_Panetal(m1, m2)
    elif fitname==bbh_final_state_fits.hlz2014:
       mf = bbh_final_mass_non_precessing_Healyetal(m1, m2, chi1proj, chi2proj, chif=chif)
    elif fitname==bbh_final_state_fits.phenD:
       if chif is not None:
          print "Note: Precomputed chif not used by this fit."
       mf = bbh_final_mass_non_precessing_Husaetal(m1, m2, chi1proj, chi2proj)
    elif fitname==bbh_final_state_fits.uib2016:
       if chif is not None:
          print "Note: Precomputed chif not used by this fit."
       mf = bbh_final_mass_non_precessing_UIB2016(m1, m2, chi1proj, chi2proj)
    else:
       raise ValueError("Unrecognized fit name.")

    return mf

def bbh_final_spin_projected_spins(m1, m2, chi1, chi2, tilt1, tilt2, fitname, truncate=bbh_Kerr_trunc_opts.trunc):
    """
    Calculate the (signed) dimensionless spin parameter of the final BH resulting from the merger of two black holes,
    only using the projected spins along the total angular momentum
    and some aligned-spin fit from the literature

    Parameters
    ----------
    m1, m2 : component masses
    chi1, chi2 : dimensionless spins of two BHs
    tilt1, tilt2 : tilts (in radians) in the new spin convention
    fitname: fit selection currently supports Pan2011 (non-spinning), HLZ2014, PhenomD, UIB2016

    Returns
    -------
    (signed) dimensionless final spin parameter, chif
    """

    m1    = np.vectorize(float)(np.array(m1))
    m2    = np.vectorize(float)(np.array(m2))
    chi1  = np.vectorize(float)(np.array(chi1))
    chi2  = np.vectorize(float)(np.array(chi2))
    tilt1 = np.vectorize(float)(np.array(tilt1))
    tilt2 = np.vectorize(float)(np.array(tilt2))

    _check_mchi(m1,m2,chi1,chi2) # Check that inputs are physical

    chi1proj = chi1*np.cos(tilt1)
    chi2proj = chi2*np.cos(tilt2)

    if fitname==bbh_final_state_fits.pan2011:
       if np.any(chi1!=0) or np.any(chi2!=0) or np.any(tilt1!=0) or np.any(tilt2!=0):
          print "Note: Pan2011 fit does not use spins."
       chif = bbh_final_spin_non_spinning_Panetal(m1, m2)
    elif fitname==bbh_final_state_fits.hlz2014:
       chif = bbh_final_spin_non_precessing_Healyetal(m1, m2, chi1proj, chi2proj)
    elif fitname==bbh_final_state_fits.phenD:
       chif = bbh_final_spin_non_precessing_Husaetal(m1, m2, chi1proj, chi2proj)
    elif fitname==bbh_final_state_fits.uib2016:
       chif = bbh_final_spin_non_precessing_UIB2016(m1, m2, chi1proj, chi2proj)
    else:
       raise ValueError("Unrecognized fit name.")

    chif = _truncate_at_Kerr_limit(chif, truncate, fitname) # optionally truncate and/or warn at Kerr limit, depending on user option

    return chif

def bbh_final_spin_precessing(m1, m2, chi1, chi2, tilt1, tilt2, phi12, fitname, truncate=bbh_Kerr_trunc_opts.trunc):
    """
    Calculate the magnitude of the dimensionless spin parameter of the final BH resulting from the merger of two black holes,
    including the in-plane spin components;
    by either using a precessing fit from the literature;
    or by first projecting the spins along the angular momentum and using an aligned-spin fit from the literature,
    then adding in quadrature the in-plane dimensionful spin scaled by the initial mass squared.

    Parameters
    ----------
    m1, m2 : component masses
    chi1, chi2 : dimensionless spins of two BHs
    tilt1, tilt2 : tilts (in radians) in the new spin convention
    phi12: angle (in radians) between in-plane spin components
    fitname: fit selection currently supports Pan2011 (non-spinning), HLZ2014 (aligned+augmentation),
                                              PhenomD (aligned+augmentation), UIB2016 (aligned+augmentation),
                                              HBR2016 (precessing)

    Returns
    -------
    magnitude of the dimensionless final spin parameter, chif
    """

    m1    = np.vectorize(float)(np.array(m1))
    m2    = np.vectorize(float)(np.array(m2))
    chi1  = np.vectorize(float)(np.array(chi1))
    chi2  = np.vectorize(float)(np.array(chi2))
    tilt1 = np.vectorize(float)(np.array(tilt1))
    tilt2 = np.vectorize(float)(np.array(tilt2))
    phi12 = np.vectorize(float)(np.array(phi12))

    _check_mchi(m1,m2,chi1,chi2) # Check that inputs are physical

    if fitname==bbh_final_state_fits.pan2011 or fitname==bbh_final_state_fits.hlz2014 or fitname==bbh_final_state_fits.phenD or fitname==bbh_final_state_fits.uib2016:
       precfit = False
    elif fitname==bbh_final_state_fits.hbr2016:
       precfit = True
       raise ValueError("HBR2016 fit not yet implemented.")
       chif = bbh_final_spin_precessing_HBR2016(m1, m2, chi1, chi2, tilt1, tilt2, phi12)
    else:
       raise ValueError("Unrecognized fit name.")

    if not precfit:
       # First compute the final mass and parallel component of the final spin using the aligned components of the initial spins
       chifaligned = bbh_final_spin_projected_spins(m1, m2, chi1, chi2, tilt1, tilt2, fitname, truncate)

       # Now compute the squared magnitude of the in-plane dimensionful spin, first computing the magnitudes of the initial in-plane spins
       S1perpmag = m1*m1*chi1*np.sin(tilt1)
       S2perpmag = m2*m2*chi2*np.sin(tilt2)
       Sperpmag2 = S1perpmag*S1perpmag + S2perpmag*S2perpmag + 2.*S1perpmag*S2perpmag*np.cos(phi12)

       # Combine together
       chif = (chifaligned*chifaligned + Sperpmag2/(m1+m2)**4.)**0.5

    chif = _truncate_at_Kerr_limit(chif, truncate, "augmented "+fitname) # optionally truncate and/or warn at Kerr limit, depending on user option

    return chif

def bbh_final_mass_non_precessing_Husaetal(m1, m2, chi1, chi2):
    """ 
    Calculate the mass of the final BH resulting from the
    merger of two black holes with non-precessing spins using the fits
    used by IMRPhenomD, given in Eqs. (3.6) and (3.8) of Husa et al.
    arXiv:1508.07250. Note that Eq. (3.8) gives the radiated energy, not
    the final mass directly

    m1, m2: component masses
    chi1, chi2: dimensionless spins of two BHs
    """
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    chi1 = np.vectorize(float)(np.array(chi1))
    chi2 = np.vectorize(float)(np.array(chi2))
    
    if np.any(abs(chi1)>1):
      raise ValueError("chi1 has to be in [-1, 1]")
    if np.any(abs(chi2)>1):
      raise ValueError("chi2 has to be in [-1, 1]")
    
    # binary parameters 
    m = m1+m2  
    msq = m*m

    eta = m1*m2/msq
    eta2 = eta*eta
    eta3 = eta2*eta
    eta4 = eta3*eta

    S1 = chi1*m1**2/msq                   # spin angular momentum 1 (in m = 1 units) 
    S2 = chi2*m2**2/msq                   # spin angular momentum 2 (in m = 1 units)
    S = S1+S2                        # total spin
    Sh = S/(1. - 2.*eta)                    # rescaled total spin

    # Expressions copied from LALSimIMRPhenomD_internals.c (except with two notation differences: S is capitalized in chif and s -> Sh in Mf, in addition to the "m*(1. - ...)" to obtain the final mass from the radiated mass in m = 1 units which is calculated in the LAL code)

    Mf = m*(1. - ((0.055974469826360077*eta + 0.5809510763115132*eta2 - 0.9606726679372312*eta3 + 3.352411249771192*eta4)*
    (1. + (-0.0030302335878845507 - 2.0066110851351073*eta + 7.7050567802399215*eta2)*Sh))/(1. + (-0.6714403054720589 - 1.4756929437702908*eta + 7.304676214885011*eta2)*Sh))

    return Mf

def bbh_final_spin_non_precessing_Husaetal(m1, m2, chi1, chi2):
    """ 
    Calculate the spin of the final BH resulting from the
    merger of two black holes with non-precessing spins using the fits
    used by IMRPhenomD, given in Eqs. (3.6) and (3.8) of Husa et al.
    arXiv:1508.07250. Note that Eq. (3.8) gives the radiated energy, not
    the final mass directly

    m1, m2: component masses
    chi1, chi2: dimensionless spins of two BHs
    """
    # Vectorize the function if arrays are provided as input
    m1 = np.vectorize(float)(np.array(m1))
    m2 = np.vectorize(float)(np.array(m2))
    chi1 = np.vectorize(float)(np.array(chi1))
    chi2 = np.vectorize(float)(np.array(chi2))
    
    if np.any(abs(chi1)>1):
      raise ValueError("chi1 has to be in [-1, 1]")
    if np.any(abs(chi2)>1):
      raise ValueError("chi2 has to be in [-1, 1]")
    
    # binary parameters 
    m = m1+m2  
    msq = m*m

    eta = m1*m2/msq
    eta2 = eta*eta
    eta3 = eta2*eta
    eta4 = eta3*eta

    S1 = chi1*m1**2/msq                   # spin angular momentum 1 (in m = 1 units) 
    S2 = chi2*m2**2/msq                   # spin angular momentum 2 (in m = 1 units)
    S = S1+S2                        # total spin
    Sh = S/(1. - 2.*eta)                    # rescaled total spin

    Ssq = S*S
    Scu = Ssq*S
    Squ = Scu*S

    # Expressions copied from LALSimIMRPhenomD_internals.c (except with two notation differences: S is capitalized in chif and s -> Sh in Mf, in addition to the "m*(1. - ...)" to obtain the final mass from the radiated mass in m = 1 units which is calculated in the LAL code)

    chif = 3.4641016151377544*eta - 4.399247300629289*eta2 + 9.397292189321194*eta3 - 13.180949901606242*eta4 + (1 - 0.0850917821418767*eta - 5.837029316602263*eta2)*S + (0.1014665242971878*eta - 2.0967746996832157*eta2)*Ssq + (-1.3546806617824356*eta + 4.108962025369336*eta2)*Scu + (-0.8676969352555539*eta + 2.064046835273906*eta2)*Squ 

    return chif

def bbh_UIBfits_setup(m1, m2, chi1, chi2):
    """
    common setup function for UIB final-state and luminosity fit functions
    """

    # Vectorize the function if arrays are provided as input
    m1   = np.vectorize(float)(np.array(m1))
    m2   = np.vectorize(float)(np.array(m2))
    chi1 = np.vectorize(float)(np.array(chi1))
    chi2 = np.vectorize(float)(np.array(chi2))

    if np.any(m1<0):
      raise ValueError("m1 must not be negative")
    if np.any(m2<0):
      raise ValueError("m2 must not be negative")

    if np.any(abs(chi1)>1):
      raise ValueError("chi1 has to be in [-1, 1]")
    if np.any(abs(chi2)>1):
      raise ValueError("chi2 has to be in [-1, 1]")

    # binary masses
    m    = m1+m2
    if np.any(m<=0):
      raise ValueError("m1+m2 must be positive")
    msq  = m*m
    m1sq = m1*m1
    m2sq = m2*m2

    # symmetric mass ratio
    eta  = m1*m2/msq
    if np.any(eta>0.25):
      print "Truncating eta from above to 0.25. This should only be necessary in some rounding corner cases, but better check your m1 and m2 inputs..."
      eta = np.minimum(eta,0.25)
    if np.any(eta<0.0):
      print "Truncating negative eta to 0.0. This should only be necessary in some rounding corner cases, but better check your m1 and m2 inputs..."
      eta = np.maximum(eta,0.0)
    eta2 = eta*eta
    eta3 = eta2*eta
    eta4 = eta2*eta2

    # spin variables (in m = 1 units)
    S1    = chi1*m1sq/msq # spin angular momentum 1
    S2    = chi2*m2sq/msq # spin angular momentum 2
    Stot  = S1+S2         # total spin
    Shat  = (chi1*m1sq+chi2*m2sq)/(m1sq+m2sq) # effective spin, = msq*Stot/(m1sq+m2sq)
    Shat2 = Shat*Shat
    Shat3 = Shat2*Shat
    Shat4 = Shat2*Shat2

    # spin difference, assuming m1>m2
    chidiff  = chi1 - chi2
    if np.any(m2>m1): # fit assumes m1>m2
      chidiff = np.sign(m1-m2)*chidiff
    chidiff2 = chidiff*chidiff

    # typical squareroots and functions of eta
    sqrt2 = 2.**0.5
    sqrt3 = 3.**0.5
    sqrt1m4eta = (1. - 4.*eta)**0.5

    return m, eta, eta2, eta3, eta4, Stot, Shat, Shat2, Shat3, Shat4, chidiff, chidiff2, sqrt2, sqrt3, sqrt1m4eta

def bbh_final_mass_non_precessing_UIB2016(m1, m2, chi1, chi2):
    """
    Calculate the final mass with the aligned-spin NR fit
    by Xisco Jimenez Forteza, David Keitel, Sascha Husa et al.
    [LIGO-P1600270] [https://arxiv.org/abs/1611.00332]

    m1, m2: component masses
    chi1, chi2: dimensionless spins of two BHs
    Note: Here it is assumed that m1>m2.
    """

    m, eta, eta2, eta3, eta4, Stot, Shat, Shat2, Shat3, Shat4, chidiff, chidiff2, sqrt2, sqrt3, sqrt1m4eta = bbh_UIBfits_setup(m1, m2, chi1, chi2)

    # fit coefficients from Tables VII-X of 1611.00332v1
    # exact expressions copied from https://gravity.astro.cf.ac.uk/cgit/cardiff_uib_share/tree/Luminosity_and_Radiated_Energy/UIBfits/LALInference/EradUIB2016_pyform_coeffs.txt
    # git commit 636e5a71462ecc448060926890aa7811948d5a53
    a2 = 0.5635376058169299
    a3 = -0.8661680065959881
    a4 = 3.181941595301782
    b1 = -0.15800074104558132
    b2 = -0.15815904609933157
    b3 = -0.14299315232521553
    b5 = 8.908772171776285
    f20 = 3.8071100104582234
    f30 = 25.99956516423936
    f50 = 1.552929335555098
    f10 = 1.7004558922558886
    f21 = 0.
    d10 = -0.12282040108157262
    d11 = -3.499874245551208
    d20 = 0.014200035799803777
    d30 = -0.01873720734635449
    d31 = -5.1830734185518725
    f11 = 14.39323998088354
    f31 = -232.25752840151296
    f51 = -0.8427987782523847

    # Calculate the radiated-energy fit from Eq. (27) of 1611.00332v1
    # exact expression copied from https://gravity.astro.cf.ac.uk/cgit/cardiff_uib_share/tree/Luminosity_and_Radiated_Energy/UIBfits/LALInference/EradUIB2016_pyform_ansatz.txt
    # git commit 636e5a71462ecc448060926890aa7811948d5a53
    Erad = (((1. + -2.0/3.0*sqrt2)*eta + a2*eta2 + a3*eta3 + a4*eta4)*(1. + 0.487*b1*Shat*(f10 + f11*eta + (16. - 16.*f10 - 4.*f11)*eta2) + 0.295*b2*Shat2*(f20 + f21*eta + (16. - 16.*f20 - 4.*f21)*eta2) + 0.17*b3*Shat3*(f30 + f31*eta + (16. - 16.*f30 - 4.*f31)*eta2)))/(1. - 0.0717*b5*Shat*(f50 + f51*eta + (16. - 16.*f50 - 4.*f51)*eta2)) + d10*sqrt1m4eta*eta2*(1. + d11*eta)*chidiff + d30*Shat*sqrt1m4eta*eta*(1. + d31*eta)*chidiff + d20*eta3*chidiff2

    # Convert to actual final mass
    Mf = m*(1.-Erad)

    return Mf

def bbh_final_spin_non_precessing_UIB2016(m1, m2, chi1, chi2):
    """
    Calculate the final spin with the aligned-spin NR fit
    by Xisco Jimenez Forteza, David Keitel, Sascha Husa et al.
    [LIGO-P1600270] [https://arxiv.org/abs/1611.00332]

    m1, m2: component masses
    chi1, chi2: dimensionless spins of two BHs
    Note: Here it is assumed that m1>m2.
    """

    m, eta, eta2, eta3, eta4, Stot, Shat, Shat2, Shat3, Shat4, chidiff, chidiff2, sqrt2, sqrt3, sqrt1m4eta = bbh_UIBfits_setup(m1, m2, chi1, chi2)

    # fit coefficients from Tables I-IV of 1611.00332v1
    # exact expressions copied from https://gravity.astro.cf.ac.uk/cgit/cardiff_uib_share/tree/Luminosity_and_Radiated_Energy/UIBfits/LALInference/FinalSpinUIB2016_pyform_coeffs.txt
    # git commit 636e5a71462ecc448060926890aa7811948d5a53
    a2 = 3.772362507208651
    a3 = -9.627812453422376
    a5 = 2.487406038123681
    b1 = 1.0005294518146604
    b2 = 0.8823439288807416
    b3 = 0.7612809461506448
    b5 = 0.9139185906568779
    f21 = 8.887933111404559
    f31 = 23.927104476660883
    f50 = 1.8981657997557002
    f11 = 4.411041530972546
    f52 = 0.
    d10 = 0.2762804043166152
    d11 = 11.56198469592321
    d20 = -0.05975750218477118
    d30 = 2.7296903488918436
    d31 = -3.388285154747212
    f12 = 0.3642180211450878
    f22 = -40.35359764942015
    f32 = -178.7813942566548
    f51 = -5.556957394513334

    # Calculate the fit for the Lorb' quantity from Eq. (16) of 1611.00332v1
    # exact expression copied from https://gravity.astro.cf.ac.uk/cgit/cardiff_uib_share/tree/Luminosity_and_Radiated_Energy/UIBfits/LALInference/FinalSpinUIB2016_pyform_ansatz.txt
    # git commit 636e5a71462ecc448060926890aa7811948d5a53
    Lorb = (2.*sqrt3*eta + 5.28*a2*eta2 + 1.27*a3*eta3)/(1. + 2.89*a5*eta) + (-0.194*b1*Shat*(f11*eta + f12*eta2 + (64. - 16.*f11 - 4.*f12)*eta3) + 0.075*b2*Shat2*(f21*eta + f22*eta2 + (64. - 16.*f21 - 4.*f22)*eta3) + 0.00782*b3*Shat3*(f31*eta + f32*eta2 + (64. - 16.*f31 - 4.*f32)*eta3))/(1. - 0.527*b5*Shat*(f50 + f51*eta + f52*eta2 + (64. - 64.*f50 - 16.*f51 - 4.*f52)*eta3)) + d10*sqrt1m4eta*eta2*(1. + d11*eta)*chidiff + d30*Shat*sqrt1m4eta*eta3*(1. + d31*eta)*chidiff + d20*eta3*chidiff2

    # Convert to actual final spin
    chif = Lorb + Stot

    return chif

def bbh_aligned_Lpeak_6mode_SHXJDK(q, chi1para, chi2para):
    """
    Calculate the peak luminosity (using modes 22, 21, 33, 32, 44, and 43) of a binary black hole with aligned spins using the fit made by Sascha Husa, Xisco Jimenez Forteza, David Keitel [LIGO-T1500598] using 5th order in chieff and return results in units of 10^56 ergs/s

    q: mass ratio (here m2/m1, where m1>m2)
    chi1para: the component of the dimensionless spin of m1 along the angular momentum (z)
    chi2para: the component of the dimensionless spin of m2 along the angular momentum (z)
    
    Note: Here it is assumed that m1>m2.
    """
    # Vectorize the function if arrays are provided as input
    q = np.vectorize(float)(np.array(q))
    chi1para = np.vectorize(float)(np.array(chi1para))
    chi2para = np.vectorize(float)(np.array(chi2para))
    
    if np.any(q<=0.):
      raise ValueError("q has to be > 0.")
    if np.any(q>1.):
      raise ValueError("q has to be <= 1.")
    
    if np.any(abs(chi1para)>1):
      raise ValueError("chi1para has to be in [-1, 1]")
    if np.any(abs(chi2para)>1):
      raise ValueError("chi2para has to be in [-1, 1]")

    # Calculate eta and the effective spin
    
    # This function is designed for bayespputils.py that expects q = m2/m1, where m1>m2. Expressions in reference above are for q = m1/m2. Here we do the appropriate conversion.
    q_inv = 1./q

    eta = q_inv/(1.+q_inv)**2.

    eta2 = eta*eta
    eta3 = eta2*eta
    eta4 = eta3*eta

    dm2 = 1. - 4.*eta

    chi_eff = (q_inv*chi1para + chi2para)/(1. + q_inv)

    chi_eff2 = chi_eff*chi_eff
    chi_eff3 = chi_eff2*chi_eff
    chi_eff4 = chi_eff3*chi_eff
    chi_eff5 = chi_eff4*chi_eff

    chi_diff = chi1para - chi2para
    chi_diff2 = chi_diff*chi_diff

    # Calculate best fit (from [https://dcc.ligo.org/T1500598-v4])

    Lpeak = (0.012851338846828302 + 0.007822265919928252*chi_eff + 0.010221856361035788*chi_eff2 + 0.015805535732661396*chi_eff3 + 0.0011356206806770043*chi_eff4 - 0.009868152529667197*chi_eff5)*eta2 + (0.05681786589129071 - 0.0017473702709303457*chi_eff - 0.10150706091341818*chi_eff2 - 0.2349153289253309*chi_eff3 + 0.015657737820040145*chi_eff4 + 0.19556893194885075*chi_eff5)*eta4 + 0.026161288241420833*dm2**0.541825641769908*eta**3.1629576945611757*chi_diff + 0.0007771032100485481*dm2**0.4499151697918658*eta**1.7800346166040835*chi_diff2

    # Convert to 10^56 ergs/s units
    
    # We first define the "Planck luminosity" of c^5/G in 10^56 ergs/s units. Note: 10^56 ergs/s = 10^49 J/s
    LumPl_ergs_per_sec = lal.LUMPL_SI*1e-49 # Approximate value = 3628.505 
    
    return LumPl_ergs_per_sec*Lpeak
