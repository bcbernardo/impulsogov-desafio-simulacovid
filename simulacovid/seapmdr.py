import pandas as pd
import numpy as np
from scipy.integrate import odeint


def _calculate_avg_time(place_specific_params, disease_params):
    """Calculates average infectious period from population and disease params.
    """

    t_E1 = disease_params["presymptomatic_period"]
    t_I0 = disease_params["asymptomatic_duration"]
    t_I1 = disease_params["mild_duration"]
    t_I2 = disease_params["severe_duration"]
    t_I3 = disease_params["critical_duration"]
    t_avg = (
        place_specific_params["i0_percentage"] * (t_E1 + t_I0)
        + place_specific_params["i1_percentage"] * (t_E1 + t_I1)
        + place_specific_params["i2_percentage"] * (t_E1 + t_I1 + t_I2)
        + place_specific_params["i3_percentage"] * (t_E1 + t_I1 + t_I2 + t_I3)
    )
    return t_avg


def _calculate_exposed(
    population_params, place_specific_params, disease_params, Rt
):
    """Estimates the number of exposed individuals in the population."""

    # calculate place-specific doubling rate of the epidemics, following The
    # Royal Society's (2020) methodology - SEE: https://royalsociety.org
    # /-/media/policy/projects/set-c/set-covid-19-R-estimates.pdf#page=11
    t_avg = _calculate_avg_time(place_specific_params, disease_params)
    doubling_time = np.log(2) / (Rt / t_avg)

    # calculate total number of exposed people
    e_perc = (doubling_time - 1) * disease_params["incubation_period"]
    exposed_total = population_params["I"] * (
        place_specific_params["i0_percentage"]
        + place_specific_params["i1_percentage"]
    ) * e_perc

    # true latent exposed population (not infectious yet)
    exposed_latent = (
        exposed_total * (disease_params["incubation_period"]
                         - disease_params["presymptomatic_period"])
        / disease_params["incubation_period"]
    )

    # exposed, pre-symptomatic population (already infectious)
    exposed_presymptomatic = (
        exposed_total * disease_params["presymptomatic_period"]
        / disease_params["incubation_period"]
    )

    return {
        "total": exposed_total,
        "latent": exposed_latent,
        "presymptomatic": exposed_presymptomatic,
    }


def prepare_states(
    population_params, place_specific_params, disease_params, Rt
):
    """
    Estimate non explicity population initial states

    Params
    --------
    population_param: dict
            Explicit population parameters:
                    - N: population
                    - I: infected
                    - R: recovered
                    - D: deaths

    place_specific_params: dict
            Place-specific fatality ratio, disease severity distribution and
            effetive transmission rate (most likely).
                    - fatality_ratio: Place-specific fatality ratio
                    - i0_percentage: Place-specific proportion of asymptomatic
                        cases
                    - i1_percentage: Place-specific proportion of mild cases
                    - i2_percentage: Place-specific proportion of severe cases
                    - i3_percentage: Place-specific proportion of critical
                        cases

    disease_params:
            Fixed epidemiological parameters for the disease.

    Rt:
            Estimated effective transmission rate in the state.

    Returns
    --------
    dict
           Explicit and implicit population parameters ready to be applied in the `model` function
    """

    exposed = _calculate_exposed(
        population_params,
        place_specific_params,
        disease_params,
        Rt
    )

    initial_pop_params = {
        "S": population_params["N"]
             - population_params["R"]
             - population_params["D"]
             - population_params["I"]
             - exposed["total"],
        "E0": exposed["latent"],
        "E1": exposed["presymptomatic"],
        "I0": population_params["I"] * place_specific_params["i0_percentage"],
        "I1": population_params["I"] * place_specific_params["i1_percentage"],
        "I2": population_params["I"] * place_specific_params["i2_percentage"],
        "I3": population_params["I"] * place_specific_params["i3_percentage"],
        "R": population_params["R"],
        "D": population_params["D"],
    }

    return initial_pop_params


def prepare_disease_params(
    population_params, place_specific_params, disease_params, Rt
):
    """
    Estimate non explicity SEAPMDR model parameters

    Params
    --------
    population_params: dict
    place_specific_params: dict
    disease_params: dict
    Rt: int

    Returns
    --------
    dict
           Explicit and implicit disease parameters ready to be applied in the `model` function
    """

    population_params = prepare_states(
        population_params,
        place_specific_params,
        disease_params,
        Rt,
    )

    frac_mild_to_severe = place_specific_params["i2_percentage"] / (
        place_specific_params["i1_percentage"] + place_specific_params["i2_percentage"]
    )

    frac_severe_to_critical = place_specific_params["i3_percentage"] / (
        place_specific_params["i2_percentage"] + place_specific_params["i3_percentage"]
    )
    frac_critical_to_death = (
        place_specific_params["fatality_ratio"] / place_specific_params["i3_percentage"]
    )

    parameters = {
        "sigma0": 1
        / (disease_params["incubation_period"]
            - disease_params["presymptomatic_period"]),
        "sigma1": 1 / disease_params["presymptomatic_period"],

        "phi": disease_params["asymptomatic_proportion"],
        "gamma0": 1 / disease_params["asymptomatic_duration"],

        "gamma1": (1 - frac_mild_to_severe) / disease_params["mild_duration"],
        "p1": frac_mild_to_severe / disease_params["mild_duration"],

        "gamma2": (1 - frac_severe_to_critical) / disease_params["severe_duration"],
        "p2": frac_severe_to_critical / disease_params["severe_duration"],

        "gamma3": (1 - frac_critical_to_death) / disease_params["critical_duration"],
        "mu": frac_critical_to_death / disease_params["critical_duration"],
    }

    # RECALCULATING THE BETAS
    #
    # By definition of the betas (transmission rate for a compartment in a
    # period of time) and the effective reproduction number - Rt (average
    # number of infectees for each infectious individual, during the whole
    # duration of the disease), we can say that:
    #     E1*beta_E + I0*beta_0 + I1*beta_1 + I2*beta_2 + I3*beta_3
    #     = (E1 + I0 + I1 + I2 + I3) * Rt / t_avg
    # with `t_avg` being the average infectious period duration, that can be
    # calculated as the weighted average of how much time each particular
    # outcome stays in each compartment.

    # We assume the transmission rate is equal amongst all non-hospitalized 
    # compartiments (beta_e = beta_0 = beta_1), in one side; and amongst all 
    # hospitalized compartiments (beta_2 = beta_3), on the other side.

    # The disease params state that 5% of the transmissions affect healthcare
    # workers. For simplicity, we assume that all cases amongst healthcare
    # workers come from the contact with hospitalized (I2 and I3) patients,
    # and that these patients do not contribute for the transmission to 
    # non-healthcare workers. Therefore, we can state that:
    #     (E1*beta_E + I0*beta_0 + I1*beta_1)/(I2*beta_2 + I3*beta_3) 
    #     = 0.95/0.05 = 19

    # The following lines develop this assumptions to calculate the betas
    # from the disease and the place-specific parameters:

    # Calculate average infectious duration
    t_avg = _calculate_avg_time(place_specific_params, disease_params)

    # Calculate beta_2 and beta_3
    beta_2 = (
        (population_params["E1"] + population_params["I1"] +
         population_params["I2"] + population_params["I3"]) * Rt
        / (t_avg * (population_params["I2"] + population_params["I3"])
           * (1 + (1-disease_params["infected_health_care_proportion"])
           / disease_params["infected_health_care_proportion"]))
    )
    beta_3 = beta_2

    # Calculate beta_E, beta_0 and beta_1
    beta_E = (
        ((1-disease_params["infected_health_care_proportion"])
         / disease_params["infected_health_care_proportion"])
        * (population_params["I2"]*beta_2 + population_params["I3"]*beta_3)
        / (population_params["E1"] + population_params["I0"]
            + population_params["I1"])
    )
    beta_0 = beta_E
    beta_1 = beta_E

    print(f"Beta E/0/1: {beta_E}")
    print(f"Beta 2/3: {beta_2}")

    parameters.update({
        "betaE": beta_E,
        "beta0": beta_0,
        "beta1": beta_1,
        "beta2": beta_2,
        "beta3": beta_3,
    })
    # # Assuming betaE with 0.25 * R (as does Hill(2020))
    # parameters["betaE"] = (
    #     0.25
    #     * (1 / disease_params["presymptomatic_period"])
    #     * Rt
    #     / population_params["N"]
    # )

    # # beta0 = beta1, with both summing (0.9 - 0.25) * R0 = 0.65 * R0
    # # and ( R_I0 / R_I1 ) = ( i0_percentage * asymptomatic_duration
    # #                        / i1_percentage * mild_duration)
    # # (each compartiment's relative contribution to R0 depends only on the
    # #  proportion of people on each one of them and their duration)
    # parameters["beta1"] = (
    #     (0.65 * Rt)
    #     / (1 + (
    #             place_specific_params["i0_percentage"]
    #             * disease_params["asymptomatic_duration"]
    #         ) / (
    #             place_specific_params["i1_percentage"]
    #             * disease_params["mild_duration"]
    #         )
    #     )
    #     * (1 / disease_params["mild_duration"])
    #     / population_params["N"]
    # )
    # parameters["beta0"] = parameters["beta1"]

    # # And beta2 = beta3 with 0.1 * R0
    # x = (
    #     (1 / disease_params["mild_duration"])
    #     * (1 / disease_params["severe_duration"])
    #     * (1 / disease_params["critical_duration"])
    # )
    # y = (
    #     parameters["p1"] * (1 / disease_params["critical_duration"])
    #     + parameters["p1"] * parameters["p2"]
    # )

    # parameters["beta3"] = 0.1 * (x / y) * Rt / population_params["N"]
    # parameters["beta2"] = parameters["beta3"]

    return parameters


def SEAPMDR(y, t, model_params, initial=False):
    """
    The SEAPMDR model differential equations.

    Params
    --------
    y: dict
         Population parameters:
              - S: susceptible
              - E0: exposed latent
              - E1: exposed pre-symptomatic
              - I1: infected mild
              - I2: infected severe
              - I3: infected critical
              - R: recovered
              - D: deaths

    model_params: dict
           Parameters of model dynamic (transmission, progression, recovery
           and death rates)

    Return
    -------
    pd.DataFrame
            Evolution of population parameters.
    """

    S, E0, E1, I0, I1, I2, I3, R, D = y

    # Exposition of susceptible rate
    exposition_rate = (
        (model_params["betaE"] * E1)
        + (model_params["beta0"] * I0)
        + (model_params["beta1"] * I1)
        + (model_params["beta2"] * I2)
        + (model_params["beta3"] * I3)
    )

    # Susceptible
    dSdt = -exposition_rate * S

    # Exposed (latent)
    dE0dt = exposition_rate * S - model_params["sigma0"] * E0

    # Exposed (pre-symptomatic)
    dE1dt = model_params["sigma0"] * E0 - model_params["sigma1"] * E1

    # Infected (asymptomatic)
    dI0dt = (
        model_params["sigma1"] * E1 * model_params["phi"]
        - model_params["gamma0"] * I0
    )

    # Infected (mild)
    dI1dt = (
        model_params["sigma1"] * E1 * (1 - model_params["phi"])
        - (model_params["gamma1"] + model_params["p1"]) * I1
    )

    # Infected (severe)
    dI2dt = model_params["p1"] * I1 - (model_params["gamma2"] + model_params["p2"]) * I2

    # Infected (critical)
    dI3dt = model_params["p2"] * I2 - (model_params["gamma3"] + model_params["mu"]) * I3

    # Recovered
    dRdt = (
        model_params["gamma0"] * I0
        + model_params["gamma1"] * I1
        + model_params["gamma2"] * I2
        + model_params["gamma3"] * I3
    )

    # Deaths
    dDdt = model_params["mu"] * I3

    return dSdt, dE0dt, dE1dt, dI0dt, dI1dt, dI2dt, dI3dt, dRdt, dDdt


def entrypoint(
    population_params, place_specific_params, disease_params, phase, initial=False
):
    """
    Function to receive user input and run model.
    
    Params
    --------
    population_params: dict
         Population parameters:
              - S: susceptible
              - E0: exposed latent
              - E1: exposed pre-symptomatic
              - I_0: infected asymptomatic
              - I_1: infected mild
              - I_2: infected severe
              - I_3: infected critical
              - R: recovered
              - D: deaths

    place_specific_params: pd.DataFrame
        Parameters for specific places

    disease_params: dict
        Parameters of model dynamic (transmission, progression, recovery and death rates)
                                 
    phase: dict
       Scenario and days to run 
            - scenario
            - date      

    Return
    -------
    pd.DataFrame
            Evolution of population parameters.
    """

    if initial:  # Get E0, E1, I0, I1, I2 and I3
        population_params, disease_params = (
            prepare_states(
                population_params, place_specific_params, disease_params, phase["R0"]
            ),
            prepare_disease_params(
                population_params, place_specific_params, disease_params, phase["R0"]
            ),
        )
    else:
        disease_params = prepare_disease_params(
            population_params, place_specific_params, disease_params, phase["R0"]
        )
        del population_params["N"]

    # Run model
    params = {
        "y0": list(population_params.values()),
        "t": np.linspace(0, phase["n_days"], phase["n_days"] + 1),
        "args": (disease_params, initial),
    }

    result = pd.DataFrame(
        odeint(SEAPMDR, **params),
        columns=["S", "E0", "E1", "I0", "I1", "I2", "I3", "R", "D"]
    )
    result["N"] = result.sum(axis=1)
    result["E"] = result["E0"] + result["E1"]
    result["scenario"] = phase["scenario"]
    result.index.name = "dias"

    return result
