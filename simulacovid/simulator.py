import os
import pandas as pd
import numpy as np
from scipy.integrate import odeint
import sys
from pathlib import Path

from .seir import entrypoint as seir
from .seapmdr import entrypoint as seapmdr
import datetime as dt


def get_dday(dfs, col, resource_number):
    """
    Calcula número de dias até demanda ultrapassar oferta de leitos.
    Caso não ocorra em 90 dias (máximo de dias da projeção), retorna -1.

    Params
    ------
    dfs : Dict
        Dicionário com as tabelas de projeção para pior e melhor
        cenário.
    col : str
        Tipo de demanda hospitalar para cálculo: casos severos/críticos
        [ I2 | I3 ]
    resource_number : str
        Tipo de oferta hospitalar para cálculo: leito enfermaria/UTI [
        number_beds | number_icu_beds ]

    Returns
    -------
    dday : int
        Número de dias até demanda ultrapassar oferta de leitos.
    """

    dday = dict()
    for case in ["worst", "best"]:
        df = dfs[case]

        if max(df[col]) > resource_number:
            dday[case] = df[df[col] > resource_number].index[0]
        else:
            dday[case] = -1  # change here!

    return dday


def run_simulation(params, config, model):
    """
    Roda a simulação para projeção de demanda por leitos enferemaria e
    UTI com o modelo SEIR.

    Params
    ------
    params : Dict
        Dicionário de parâmetros de entrada do simulador.
    config : Dict
        Dicionário de configuração com parâmetros fixos.
    model : str
        Tipo de modelo a utilizar na simulação. Atualmente, aceita "SEIR" e
            "SEAPMDR". 

    Returns
    -------
    dfs : Dicionário com as tabelas de projeção para pior e melhor cenário.
    """    

    model = model.upper()  # make sure model name is uppercase

    dfs = {"worst": np.nan, "best": np.nan}

    # Run worst scenario
    for bound in dfs.keys():

        # pack parameters for models' entrypoints
        model_params = {
            "population_params": params["population_params"],
            "place_specific_params": params["place_specific_params"],
            "disease_params": config["br"]["seir_parameters"],
            "phase": {
                "scenario": "projection_current_rt",
                "R0": params["R0"][bound],
                "n_days": 90,
            },
            "initial": True,
        }
        # Run model projection
        if  model == "SEIR":
            res = seir(**model_params)
        elif model == "SEAPMDR":
            res = seapmdr(**model_params)

        res = res.reset_index(drop=True)
        res.index += 1
        res.index.name = "dias"
        res["model"] = model

        dfs[bound] = res

    return dfs
    # dday = dict()
    # dday["beds"] = get_dday(dfs, "I2", params["n_beds"])
    # dday["icu_beds"] = get_dday(dfs, "I3", params["n_icu_beds"])
    # return dday


if __name__ == "__main__":
    pass
