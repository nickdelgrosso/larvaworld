import numpy as np
import pandas as pd

from larvaworld.lib.aux import nam
from larvaworld.lib import reg, aux


@reg.funcs.preproc("interpolate_nans")
def interpolate_nan_values(s, c, pars=None, **kwargs):
    if pars is None:
        points = nam.midline(c.Npoints, type='point') + ['centroid', ''] + nam.contour(
            c.Ncontour)  # changed from N and Nc to N[0] and Nc[0] as comma above was turning them into tuples, which the naming function does not accept.
        pars = nam.xy(points, flat=True)
    for p in aux.existing_cols(pars, s):
        for id in s.index.unique('AgentID').values:
            s.loc[(slice(None), id), p] = aux.interpolate_nans(s[p].xs(id, level='AgentID', drop_level=True).values)
    reg.vprint('All parameters interpolated', 1)


@reg.funcs.preproc("filter_f")
def filter(s, c, filter_f=2.0, recompute=False, **kwargs):
    if filter_f in ['', None, np.nan]:
        return
    if 'filtered_at' in c and not recompute:
        reg.vprint(
            f'Dataset already filtered at {c["filtered_at"]}. If you want to apply additional filter set recompute to True',
            1)
        return
    c['filtered_at'] = filter_f

    points = nam.midline(c.Npoints, type='point') + ['centroid', '']
    pars = aux.existing_cols(nam.xy(points, flat=True), s)
    data = np.dstack(list(s[pars].groupby('AgentID').apply(pd.DataFrame.to_numpy)))
    f_array = aux.apply_filter_to_array_with_nans_multidim(data, freq=filter_f, fr=1 / c.dt)
    for j, p in enumerate(pars):
        s[p] = f_array[:, j, :].flatten()
    reg.vprint(f'All spatial parameters filtered at {filter_f} Hz', 1)


@reg.funcs.preproc("rescale_by")
def rescale(s, e, c, recompute=False, rescale_by=1.0, **kwargs):
    if rescale_by in ['', None, np.nan]:
        return
    if 'rescaled_by' in c and not recompute:
        reg.vprint(
            f'Dataset already rescaled by {c["rescaled_by"]}. If you want to rescale again set recompute to True', 1)
        return
    c['rescaled_by'] = rescale_by
    points = nam.midline(c.Npoints, type='point') + ['centroid', '']
    contour_pars = nam.xy(nam.contour(c.Ncontour), flat=True)
    pars = nam.xy(points, flat=True) + nam.dst(points) + nam.vel(points) + nam.acc(points) + [
        'spinelength'] + contour_pars
    for p in aux.existing_cols(pars,s):
        s[p] = s[p].apply(lambda x: x * rescale_by)
    if 'length' in e.columns:
        e['length'] = e['length'].apply(lambda x: x * rescale_by)
    reg.vprint(f'Dataset rescaled by {rescale_by}.', 1)

@reg.funcs.preproc("drop_collisions")
def exclude_rows(s, e, c, flag='collision_flag',  accepted=[0], rejected=None, **kwargs):
    if accepted is not None:
        s.loc[s[flag] != accepted[0]] = np.nan
    if rejected is not None:
        s.loc[s[flag] == rejected[0]] = np.nan

    for id in s.index.unique('AgentID').values:
        e.loc[id, 'cum_dur'] = len(s.xs(id, level='AgentID', drop_level=True).dropna()) * c.dt

    reg.vprint(f'Rows excluded according to {flag}.', 1)


@reg.funcs.proc("traj_colors")
def generate_traj_colors(s, sp_vel=None, ang_vel=None, **kwargs):
    N = len(s.index.unique('Step'))
    if sp_vel is None:
        sp_vel = reg.getPar('sv')
    if ang_vel is None:
        ang_vel = reg.getPar('fov')
    for p, c, l, lim in zip([sp_vel, ang_vel],
                            [[(255, 0, 0), (0, 255, 0)], [(255, 0, 0), (0, 255, 0)]],
                            ['lin_color', 'ang_color'],
                            [0.8, 300]):
        if p in s.columns:
            (r1, b1, g1), (r2, b2, g2) = c
            r, b, g = r2 - r1, b2 - b1, g2 - g1
            temp = np.clip(s[p].abs().values / lim, a_min=0, a_max=1)
            s[l] = [(r1 + r * t, b1 + b * t, g1 + g * t) for t in temp]
        else:
            s[l] = [(np.nan, np.nan, np.nan)] * N

