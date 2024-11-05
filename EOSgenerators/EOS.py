import numpy as np
import math
from scipy import optimize
from TOVsolver.unit import g_cm_3, dyn_cm_2, e0
from scipy.integrate import cumulative_simpson


c = 3e10
G = 6.67428e-8
Msun = 1.989e33

dyncm2_to_MeVfm3 = 1.0 / (1.6022e33)
gcm3_to_MeVfm3 = 1.0 / (1.7827e12)
oneoverfm_MeV = 197.33

m_e = 2.5896 * 10**-3
m_mu = 0.53544
m_n = 4.7583690772
m_p = 4.7583690772

J_B = 1 / 2.0
b_B = 1

m_l = [m_e, m_mu]
m_b = [m_p, m_n]

Matrix_b = np.array(
    [[1.0, 1.0, 1 / 2.0, 1.0, 1.0, 1.0], [1.0, 0.0, -1 / 2.0, 1.0, 1.0, 1.0]]
)

Matrix_l = np.array([[0.0, -1.0, 1 / 2.0], [0.0, -1.0, 1 / 2.0]])


def initial_values(rho, theta):
    """Outputs the the sigma, omega, rho term and chemical potential of electron and neutron at
    given initial density

    Args:
        rho (float): given nuclear density
        theta (array): paramters of determine a RMF model in lagrangian, here we have 10 parameters.

    Returns:
        sigma (float): sigma term in lagrangian
        omega (float): omega term in lagrangian
        rho_03 (float): rho term in lagrangian
        mu_n (float): chemical potential of neutron matter
        mu_e (float): chemical potential of electron portion

    """
    m_sig, m_w, m_rho, g_sigma, g_omega, g_rho, kappa, lambda_0, zeta, Lambda_w = theta

    m_e = 2.5896 * 10**-3
    m_mu = 0.53544
    m_n = 4.7583690772
    m_p = 4.7583690772

    rho_0 = 0.1505

    sigma = g_sigma * rho / (m_sig**2)
    rho_03 = -g_rho * rho / (2.0 * (m_rho**2))
    omega = rho * (
        (((m_w**2) / g_omega) + (2.0 * Lambda_w * ((g_rho * rho_03) ** 2) * g_omega))
        ** (-1.0)
    )
    m_eff = m_n - (g_sigma * sigma)
    mu_n = m_eff + g_omega * omega + g_rho * rho_03 * Matrix_b[1, 2]
    mu_e = 0.12 * m_e * (rho / rho_0) ** (2 / 3.0)

    return sigma, omega, rho_03, mu_n, mu_e


def functie(x, args):
    """iterate the the sigma, omega, rho term and chemical potential of electron and neutron at
    any given density

    Args:
        x (array): initial sigma omega rho and chemical potential from initial_values function
        args (array): paramters of determine a RMF model in lagrangian, here we have 10 parameters.

    Returns:
        sigma (float): sigma term in lagrangian
        omega (float): omega term in lagrangian
        rho_03 (float): rho term in lagrangian
        mu_n (float): chemical potential of neutron matter
        mu_e (float): chemical potential of electron portion

    """
    m_sig = args[0]
    m_w = args[1]
    m_rho = args[2]
    g_sigma = args[3]
    g_omega = args[4]
    g_rho = args[5]
    kappa = args[6]
    lambda_0 = args[7]
    zeta = args[8]
    Lambda_w = args[9]
    rho = args[10]

    m_e = 2.5896 * 10**-3
    m_mu = 0.53544
    m_n = 4.7583690772
    m_p = 4.7583690772

    J_B = 1 / 2.0
    b_B = 1

    m_l = np.array([m_e, m_mu])
    m_b = np.array([m_p, m_n])

    Matrix_b = np.array(
        [[1.0, 1.0, 1 / 2.0, 1.0, 1.0, 1.0], [1.0, 0.0, -1 / 2.0, 1.0, 1.0, 1.0]]
    )

    Matrix_l = np.array([[0.0, -1.0, 1 / 2.0], [0.0, -1.0, 1 / 2.0]])

    sigma = x[0]
    omega = x[1]
    rho_03 = x[2]
    mu_n = x[3]
    mu_e = x[4]

    rho_B_list = []
    rho_SB_list = []
    q_list = []

    m_eff = m_n - (g_sigma * sigma)
    # i = 0
    # j = 0
    for i in range(len(Matrix_b)):
        # while i < len(Matrix_b):

        mu_b = Matrix_b[i, 0] * mu_n - Matrix_b[i, 1] * mu_e

        E_fb = mu_b - g_omega * omega - g_rho * rho_03 * Matrix_b[i, 2]

        k_fb_sq = E_fb**2 - m_eff**2
        if k_fb_sq < 0:
            k_fb_sq = np.clip(k_fb_sq, a_min=0.0, a_max=None)
            E_fb = m_eff

        k_fb = math.sqrt(k_fb_sq)

        rho_B = ((2 * J_B) + 1) * b_B * k_fb**3 / (6.0 * math.pi**2)
        rho_SB = (m_eff / (2.0 * math.pi**2)) * (
            E_fb * k_fb - (m_eff ** (2)) * np.log((E_fb + k_fb) / m_eff)
        )

        rho_B_list.append(rho_B)
        rho_SB_list.append(rho_SB)

        Q_B = ((2.0 * J_B) + 1.0) * Matrix_b[i, 1] * k_fb**3 / (6.0 * math.pi**2)
        q_list.append(Q_B)
        # i += 1

    for j in range(len(Matrix_l)):
        # while j < len(Matrix_l):

        mu_l = Matrix_l[j, 0] * mu_n - Matrix_l[i, 1] * mu_e
        E_fl = mu_l

        k_fl_sq = E_fl**2 - m_l[j] ** 2
        k_fl_sq = np.clip(k_fl_sq, a_min=0.0, a_max=None)
        k_fl = math.sqrt(k_fl_sq)

        Q_L = ((2.0 * J_B) + 1.0) * Matrix_l[i, 1] * (k_fl**3) / (6.0 * (math.pi**2))
        q_list.append(Q_L)

        # rho_l = k_fl**3 / (3.*(math.pi**2))
        # rho_list.append(rho_l)

    f = [
        (
            sigma * (m_sig**2) / g_sigma
            - sum(np.array(rho_SB_list) * Matrix_b[:, 3])
            + (kappa * (g_sigma * sigma) ** 2) / 2.0
            + (lambda_0 * (g_sigma * sigma) ** 3) / 6.0
        )
        ** 2,
        (
            omega * (m_w**2) / g_omega
            - sum(np.array(rho_B_list) * Matrix_b[:, 4])
            + (zeta * (g_omega * omega) ** 3) / 6.0
            + 2.0 * Lambda_w * g_omega * omega * (rho_03 * g_rho) ** 2
        )
        ** 2,
        (
            rho_03 * (m_rho**2) / g_rho
            - sum(np.array(rho_B_list) * Matrix_b[:, 5] * Matrix_b[:, 2])
            + 2.0 * Lambda_w * g_rho * rho_03 * (omega * g_omega) ** 2
        )
        ** 2,
        (rho - sum(rho_B_list)) ** 2,
        (sum(q_list)) ** 2,
    ]

    return f


def Energy_density_Pressure(x, rho, theta):
    """Generate pressure and energy density two EOS ingredient from given RMF term and given parameters,

    Args:
        x (array): An array that consists of the initial values of sigma, omega, rho, and chemical
        potential obtained from the initial_values function.
        rho (float): The central density from which the computation of the equation of state begins.
        theta (array): An array representing the parameters used to determine a RMF model in the
        Lagrangian. In this case, the RMF model is defined by 10 parameters.


    Returns:
        energy_density (float): EOS ingredient, energy density in g/cm3
        pressure (float): EOS ingredient, pressure in dyn/cm3

    """
    sigma, omega, rho_03, mu_n, mu_e = x

    m_sig, m_w, m_rho, g_sigma, g_omega, g_rho, kappa, lambda_0, zeta, Lambda_w = theta

    m_e = 2.5896 * 10**-3
    m_mu = 0.53544
    m_n = 4.7583690772
    m_p = 4.7583690772

    J_B = 1 / 2.0
    b_B = 1

    m_l = np.array([m_e, m_mu])
    m_b = np.array([m_p, m_n])

    energy_b = 0
    energy_l = 0
    multi = 0

    m_eff = m_n - (g_sigma * sigma)

    for i in range(len(Matrix_b)):
        mu_b = Matrix_b[i, 0] * mu_n - Matrix_b[i, 1] * mu_e

        E_fb = mu_b - g_omega * omega - g_rho * rho_03 * Matrix_b[i, 2]

        k_fb_sq = E_fb**2 - m_eff**2
        if k_fb_sq < 0:
            k_fb_sq = 0.0
            E_fb = m_eff

        k_fb = math.sqrt(k_fb_sq)

        rho_B = ((2.0 * J_B) + 1.0) * b_B * (k_fb**3) / (6.0 * math.pi**2)

        multi = multi + mu_b * rho_B
        energy_baryon = (1 / (8.0 * (math.pi**2))) * (
            k_fb * (E_fb**3)
            + (k_fb**3) * E_fb
            - np.log((k_fb + E_fb) / m_eff) * m_eff**4
        )

        energy_b = energy_b + energy_baryon

    for j in range(len(Matrix_l)):
        mu_l = Matrix_l[i, 0] * mu_n - Matrix_l[j, 1] * mu_e

        k_fl_sq = mu_l**2 - m_l[j] ** 2
        if k_fl_sq < 0.0:
            k_fl_sq = 0.0
        k_fl = math.sqrt(k_fl_sq)

        rho_l = k_fl**3 / (3.0 * math.pi**2)

        multi = multi + mu_l * rho_l
        energy_lepton = (1 / (8.0 * (math.pi**2))) * (
            k_fl * (mu_l**3)
            + mu_l * (k_fl**3)
            - (m_l[j] ** 4) * np.log((k_fl + mu_l) / m_l[j])
        )

        energy_l = energy_l + energy_lepton

    sigma_terms = (
        0.5 * ((sigma * m_sig) ** 2)
        + (kappa * ((g_sigma * sigma) ** 3)) / 6.0
        + (lambda_0 * ((g_sigma * sigma) ** 4)) / 24.0
    )

    omega_terms = 0.5 * ((omega * m_w) ** 2) + (zeta * ((g_omega * omega) ** 4)) / 8.0

    rho_terms = 0.5 * ((rho_03 * m_rho) ** 2) + +3.0 * Lambda_w * (
        (g_rho * rho_03 * g_omega * omega) ** 2
    )

    energy_density = energy_b + energy_l + sigma_terms + omega_terms + rho_terms

    Pressure = multi - energy_density

    return energy_density, Pressure


def RMF_compute_EOS(eps_crust, pres_crust, theta):
    """Generate core part equation of state, main function, from RMF model,

    Args:
        eps_crust (array): the energy density of crust EoS in MeV/fm3, times a G/c**2 factor
        pres_crust (array): the pressure from crust EoS model in MeV/fm3, times a G/c**4 factor
        theta (array): An array representing the parameters used to determine a RMF model in the
        Lagrangian. In this case, the RMF model is defined by 10 parameters.

    Returns:
        energy_density (float): EOS ingredient, energy density in g/cm3
        pressure (float): EOS ingredient, pressure in dyn/cm3

    """
    dt = 0.05
    rho_0 = 0.1505

    x_init = np.array(initial_values(0.1 * rho_0, theta))
    Energy = []
    Pressure = []
    for i in range(1, 125):
        rho = i * dt * rho_0
        arg = np.append(theta, rho)
        sol = optimize.root(functie, x_init, method="lm", args=arg)

        Re = Energy_density_Pressure(x_init, rho, theta)

        Energy.append(Re[0] * oneoverfm_MeV / gcm3_to_MeVfm3)
        Pressure.append(Re[1] * oneoverfm_MeV / dyncm2_to_MeVfm3)

        x_init = sol.x

    Energy = np.array(Energy)
    Pressure = np.array(Pressure)

    end = 0
    for i in range(0, len(Energy) - 1):
        if Energy[i] > max(eps_crust / g_cm_3) and i > 18:
            end = i + 2
            break
        end += 1
    ep = Energy[end::] * G / c**2
    pr = Pressure[end::] * G / c**4

    # tzzhou: migrating to new unit convention
    ep = ep * c**2 / G * g_cm_3
    pr = pr * c**4 / G * dyn_cm_2

    return ep, pr


def Strangeon_compute_EOS(n, theta):
    """
    Compute the energy density and pressure based on the given parameters.

    Args:
        n (array): An array of n values. Input values of baryon number densities.
        theta (array): An array representing the parameters [epsilon, Nq, ns].
        epsilon: the depth of the potential well; MeV;
        Nq: the number of quarks in a strangeon;
        ns: the number density of baryons at the surface of the star; fm^-3

    Returns:
        tuple: Arrays of energy densities in units of gcm3 and pressures in units of dyncm2.
    """

    Nq, epsilon, ns = theta

    A12 = 6.2
    A6 = 8.4
    mq = 300
    """
    mq: the mass of the quark in this EOS.
    A12 and A6 are fixed throughout the calculation.
    """

    sigma = np.sqrt(A6 / (2 * A12)) * (Nq / (3 * ns))

    energy_density = (
        2 * epsilon * (A12 * sigma**4 * n**5 - A6 * sigma**2 * n**3) + n * Nq * mq
    )
    pressure = 4 * epsilon * (2 * A12 * sigma**4 * n**5 - A6 * sigma**2 * n**3)

    return energy_density, pressure


def polytrope(rho, theta):
    """
    Calculate the pressure of a neutron star based on density using a piecewise polytropic equation of state (EOS).

    This function computes the pressure (`pres`) as a function of density (`rho`) by applying different polytropic indices
    (`gamma1`, `gamma2`, `gamma3`) within specified density thresholds (`rho_t1`, `rho_t2`). The EOS is defined in three
    distinct regions:

    - **Low-density region:** `rho <= rho_t1`
    - **Intermediate-density region:** `rho_t1 < rho <= rho_t2`
    - **High-density region:** `rho > rho_t2`

    Parameters
    ----------
    rho : array-like
        An array of density values (in cgs units) at which to calculate the pressure.

    theta : array-like, length 5
        A list or tuple containing the EOS parameters in the following order:

        - `gamma1` (float): Polytropic index for the low-density region.
        - `gamma2` (float): Polytropic index for the intermediate-density region.
        - `gamma3` (float): Polytropic index for the high-density region.
        - `rho_t1` (float): Density threshold between the low and intermediate-density regions (in cgs units).
        - `rho_t2` (float): Density threshold between the intermediate and high-density regions (in cgs units).

    Returns
    -------
    pres : ndarray
        An array of pressure values (in cgs units) corresponding to the input density values.
    """
    gamma1, gamma2, gamma3, rho_t1, rho_t2 = theta
    c = 2.99792458e10  # cgs
    G = 6.6730831e-8  # cgs
    rho_ns = 267994004080000.03  # cgs
    rho_t = 4.3721e11 * G / c**2
    P_t = 7.7582e29 * G / c**4

    P_ts, k = np.zeros(3), np.zeros(3)
    P_ts[0] = P_t
    k[0] = P_t / ((rho_t / rho_ns) ** gamma1)
    P_ts[1] = k[0] * rho_t1**gamma1
    k[1] = P_ts[1] / (rho_t1**gamma2)
    P_ts[2] = k[1] * rho_t2**gamma2
    k[2] = P_ts[2] / (rho_t2**gamma3)

    # Calculate the pressure for the entire input array `rho`
    pres = np.where(
        rho <= rho_t1,
        k[0] * rho**gamma1,
        np.where(rho <= rho_t2, k[1] * rho**gamma2, k[2] * rho**gamma3),
    )

    return pres


#####################  SPEED-OF-SOUND-EOS  BEGIN  ##############################


class SpeedOfSoundEOS:
    def __init__(self, x_last, y_last, dydx_last, enablePTcheck=False) -> None:
        """
        Speed of sound EOS class.
        See https://arxiv.org/abs/1812.08188 for details.
        Since the speed of sound core eos need to fit the last point and derivative of outer eos,
        the initial values are provided here.

        Args:
            x_last (float): Last energy density value.
            y_last (float): Last pressure value.
            dydx_last (float): Last derivative value.
            enablePTcheck (bool, optional): Enable phase transition check. Defaults to False.
        """
        self.x_last = x_last
        self.y_last = y_last
        self.dydx_last = dydx_last
        self.enablePTcheck = enablePTcheck

    def cs2(self, x, a):
        a1, a2, a3, a4, a5, a6 = a
        ret = (
            a1 * np.exp(-0.5 * (((x - a2) / a3) ** 2))
            + a6
            + (1 / 3 - a6) / (1 + np.exp(-a5 * (x - a4)))
        )
        return np.clip(ret, 0, 1)  # requirement 2 and 4

    def cal_a6(self, a1, a2, a3, a4, a5):
        A = a1 * np.exp(-0.5 * (((self.x_last - a2) / a3) ** 2)) + (1 / 3) / (
            1 + np.exp(-a5 * (self.x_last - a4))
        )
        B = 1 - 1 / (1 + np.exp(-a5 * (self.x_last - a4)))
        # cs2 = A + B * a6 = dydx
        return (self.dydx_last - A) / B

    def uniform_prior(self, a, b, r):
        return a + (b - a) * r

    def gen_a(self, cube5_):
        """
        Generate the EOS parameters from the given cube.

        Args:
            cube5_ (array): The input cube. The shape is (5,). The values are in the range of [0, 1].

        Returns:
            tuple: The EOS parameters.
        """
        a1 = self.uniform_prior(0.1, 1.5, cube5_[0])
        a2 = self.uniform_prior(1.5, 12, cube5_[1])
        a3 = self.uniform_prior(0.05 * a2, 2 * a2, cube5_[2])
        a4 = self.uniform_prior(1.5, 37, cube5_[3])
        a5 = self.uniform_prior(0.1, 1, cube5_[4])
        a6 = self.cal_a6(a1, a2, a3, a4, a5)
        return (a1, a2, a3, a4, a5, a6)

    def check_a(self, a):
        a1, a2, a3, a4, a5, a6 = a

        # PT requirement
        if self.enablePTcheck and a6 > 0:
            return False

        # requirement 5
        if np.any(self.cs2(np.linspace(0.5 * e0, 1.5 * e0, 16), a) > 0.163):
            return False

        # requirement 3
        if a6 > 1 / 3:
            return False
        if np.any(self.cs2(np.linspace(49 * e0, 50 * e0, 16), a) > 1 / 3):
            return False

        return True

    def cal_core_p(self, core_e, a):
        """
        Calculate the core pressure.

        Args:
            core_e (array): The core energy density.
            a (array): The EOS parameters.

        Returns:
            array: The core pressure.
        """
        core_p = cumulative_simpson(self.cs2(core_e, a), x=core_e, initial=self.y_last)
        return core_p
        # fix check dpde < 0 issue
        # dif_p = np.diff(core_p, prepend=self.y_last)
        # dif_p = np.maximum(dif_p, 0)
        # return np.cumsum(dif_p)


#####################  SPEED-OF-SOUND-EOS  END  ###########################  ###
