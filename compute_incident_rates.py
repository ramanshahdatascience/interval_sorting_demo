#! /usr/bin/env python


import pandas as pd
from scipy.optimize import fmin, fsolve
from scipy.stats import beta
import warnings

# These parameters give a mode at the national overdose death rate of 14.3 per
# 100k per year. They offer a reasonably broad distribution with a 95% highest
# density interval of [1.896e-4, 198] per 100k per year, allowing for
# signficant multiples in either direction of the national average without
# departing from exact math.
BETA_A = 1.25
BETA_B = 1750

def impute_incidents(incidents_string):
    if incidents_string == '<5':
        return 2.5
    else:
        return float(incidents_string)

def interval_endpoint(row, cred_mass=0.9):
    '''Construct highest-posterior-density credible interval for the event rate.'''
    # Plug an imputed 2.5 events into the towns with <5 events
    incidents = impute_incidents(row['incidents'])
    population = row['population']
    iw = make_interval_width(incidents, population, cred_mass=cred_mass)
    left_mass = fmin(iw, 1.0 - cred_mass, ftol=1e-8, disp=False)[0]
    return (beta.ppf(left_mass, BETA_A + incidents, BETA_B + population),
            beta.ppf(left_mass + cred_mass, BETA_A + incidents,
                     BETA_B + population))

def make_interval_width(incidents, population, cred_mass=0.9):
    def interval_width(left_mass):
        return beta.ppf(left_mass + cred_mass, BETA_A + incidents, BETA_B + population) \
            - beta.ppf(left_mass, BETA_A + incidents, BETA_B + population)
    return interval_width

# The SciPy function solvers and minimizers can throw off RuntimeWarnings in
# typical use.
warnings.simplefilter('ignore', category=RuntimeWarning)

incidents = pd.read_csv('transformed/incidents.csv', index_col='municipality')
populations = pd.read_csv('transformed/populations.csv', index_col='municipality')
result = incidents.join(populations)
result['imputed_incidents'] = result['incidents'].apply(impute_incidents)
result['incidents_per_100k'] = 1e5 * result['imputed_incidents'] / result['population']

result['left_endpoint'], result['right_endpoint'] \
    = zip(*result.apply(interval_endpoint, axis=1))
result['left_per_100k'] = 1e5 * result['left_endpoint']
result['right_per_100k'] = 1e5 * result['right_endpoint']

left_rank = result['left_per_100k'].rank(method='max', pct=True)
right_rank = result['right_per_100k'].rank(method='max', pct=True)
result['score'] = right_rank + 0.5 * left_rank * left_rank \
    - 0.5 * right_rank * right_rank

result.to_csv('./transformed/incident_rates.csv')
