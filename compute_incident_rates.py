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
    incidents_string = row['incidents']
    population = row['population']
    if incidents_string == '<5':
        # Posterior is a mixture of four betas for 1, 2, 3, and 4 incidents
        iw = make_less_than_five_width(population, cred_mass=cred_mass)
        left_mass = fmin(iw, 1.0 - cred_mass, ftol=1e-8, disp=False)[0]
        return (less_than_five_ppf(left_mass, population),
                less_than_five_ppf(left_mass + cred_mass, population))
    else:
        incidents = float(incidents_string)
        iw = make_interval_width(incidents, population, cred_mass=cred_mass)
        left_mass = fmin(iw, 1.0 - cred_mass, ftol=1e-8, disp=False)[0]
        return (beta.ppf(left_mass, BETA_A + incidents, BETA_B + population),
                beta.ppf(left_mass + cred_mass, BETA_A + incidents, BETA_B + population))

def make_interval_width(incidents, population, cred_mass=0.9):
    def interval_width(left_mass):
        return beta.ppf(left_mass + cred_mass, BETA_A + incidents, BETA_B + population) \
            - beta.ppf(left_mass, BETA_A + incidents, BETA_B + population)
    return interval_width

def make_less_than_five_width(population, cred_mass=0.9):
    def interval_width(left_mass):
        return less_than_five_ppf(left_mass + cred_mass, population) \
            - less_than_five_ppf(left_mass, population)
    return interval_width

def less_than_five_ppf(left_mass, population):
    '''Shady.

    Need to unpack the implicit assumptions in this unweighted sum or switch to
    a Poisson likelihood.
    '''
    def less_than_five_cdf(x):
        return 0.25 * (beta.cdf(x, BETA_A + 1, BETA_B + population) +
                       beta.cdf(x, BETA_A + 2, BETA_B + population) +
                       beta.cdf(x, BETA_A + 3, BETA_B + population) +
                       beta.cdf(x, BETA_A + 4, BETA_B + population))
    def less_than_five_error(x):
        return less_than_five_cdf(x) - left_mass

    return fsolve(less_than_five_error, beta.ppf(left_mass, BETA_A + 2, BETA_B + population))[0]

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
