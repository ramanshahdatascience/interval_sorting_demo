#! /usr/bin/env python


import pandas as pd
from scipy.optimize import fmin, fsolve
from scipy.stats import beta
import warnings

def impute_incidents(incidents_string):
    if incidents_string == '<5':
        return 2.5
    else:
        return float(incidents_string)

def interval_endpoint(row, cred_mass=0.9):
    '''Construct highest-posterior-density credible interval for the event rate.'''
    incidents_string = row['incidents']
    population = row['population']
    if incidents_string == '0':
        # For zero incidents, the left endpoint of the
        # highest-posterior-density region is zero (since this is the mode of
        # the beta density for a=1).
        return (0.0, beta.ppf(1.0 - cred_mass, 1, population + 1))
    elif incidents_string == '<5':
        # Posterior is a mixture of four betas for 1, 2, 3, and 4 incidents
        iw = make_less_than_five_width(population, cred_mass=cred_mass)
        left_mass = fmin(iw, 1.0 - cred_mass, ftol=1e-8, disp=False)[0]
        return (less_than_five_ppf(left_mass, population),
                less_than_five_ppf(left_mass + cred_mass, population))
    else:
        incidents = float(incidents_string)
        iw = make_interval_width(incidents, population, cred_mass=cred_mass)
        left_mass = fmin(iw, 1.0 - cred_mass, ftol=1e-8, disp=False)[0]
        return (beta.ppf(left_mass, incidents + 1, population + 1),
                beta.ppf(left_mass + cred_mass, incidents + 1, population + 1))

def make_interval_width(incidents, population, cred_mass=0.9):
    def interval_width(left_mass):
        return beta.ppf(left_mass + cred_mass, incidents + 1, population + 1) \
            - beta.ppf(left_mass, incidents + 1, population + 1)
    return interval_width

def make_less_than_five_width(population, cred_mass=0.9):
    def interval_width(left_mass):
        return less_than_five_ppf(left_mass + cred_mass, population) \
            - less_than_five_ppf(left_mass, population)
    return interval_width

def less_than_five_ppf(left_mass, population):
    def less_than_five_cdf(x):
        return 0.25 * (beta.cdf(x, 2, population + 1) +
                       beta.cdf(x, 3, population + 1) +
                       beta.cdf(x, 4, population + 1) +
                       beta.cdf(x, 5, population + 1))

    def less_than_five_error(x):
        return less_than_five_cdf(x) - left_mass

    return fsolve(less_than_five_error, beta.ppf(left_mass, 3, population + 1))[0]

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
