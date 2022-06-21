import itertools
import warnings

import numpy as np
import pandas as pd

from lib.aux import naming as nam, dictsNlists as dNl
from lib.conf.pars.pars import ParDict, getPar
from lib.plot.aux import scatter_hist
from lib.plot.base import BasePlot, AutoPlot, Plot


def module_endpoint_hists(module, valid, e=None, refID=None, Nbins=None, show_median=True, fig=None, axs=None,
                          **kwargs):
    if e is None and refID is not None:
        from lib.conf.stored.conf import loadRef
        d = loadRef(refID)
        d.load(step=False)
        e = d.endpoint_data
    if Nbins is None:
        Nbins = int(e.index.values.shape[0] / 10)
    yy = int(e.index.values.shape[0] / 7)
    from lib.conf.base.dtypes import par
    # from lib.conf.base.init_pars import InitDict
    d0 = ParDict.init_dict[module]
    N = len(valid)

    P = BasePlot(name=f'{module}_endpoint_hists', **kwargs)
    P.build(1, N, figsize=(7 * N, 6), sharey=True, fig=fig, axs=axs)

    for i, n in enumerate(valid):
        ax = P.axs[i]
        p0 = par(n, **d0[n])[n]
        vs = e[p0['codename']]
        v_mu = vs.median()
        P.axs[i].hist(vs.values, bins=Nbins)
        P.conf_ax(i, xlab=p0['label'], ylab='# larvae' if i == 0 else None, xMaxN=3, xlabelfontsize=18,
                  xticklabelsize=18,
                  yvis=False if i != 0 else True)

        if show_median:
            text = p0['symbol'] + f' = {np.round(v_mu, 2)}'
            P.axs[i].axvline(v_mu, color='red', alpha=1, linestyle='dashed', linewidth=3)
            P.axs[i].annotate(text, rotation=0, fontsize=15, va='center', ha='left',
                              xy=(0.55, 0.8), xycoords='axes fraction',
                              )
    P.adjust((0.2, 0.9), (0.2, 0.9), 0.01)
    return P.get()


def plot_ang_pars(absolute=False, include_rear=False, half_circles=False, subfolder='turn', Npars=5, Nbins=100, **kwargs):
    if Npars == 5:
        shorts = ['b', 'bv', 'ba', 'fov', 'foa']
        rs = [100, 200, 2000, 200, 2000]
    elif Npars == 3:
        shorts = ['b', 'bv', 'fov']
        rs = [100, 200, 200]
    else:
        raise ValueError('3 or 5 pars allowed')

    if include_rear:
        shorts += ['rov', 'roa']
        rs += [200, 2000]

    Nps = len(shorts)
    P = AutoPlot(name='ang_pars', subfolder=subfolder, Ncols=Nps, figsize=(Nps * 8, 8), sharey=True, **kwargs)
    P.init_fits(getPar(shorts))
    for i, (k,r) in enumerate(zip(shorts, rs)):
        p=ParDict.dict[k]
        vs=[ParDict.get(k,d) for d in P.datasets]
        bins, xlim = P.angrange(r, absolute, Nbins)
        P.plot_par(vs=vs, bins=bins, i=i, absolute=absolute, labels=p.disp, alpha=0.8, histtype='step', linewidth=3,
                   pvalues=False, half_circles=half_circles)
        P.conf_ax(i, ylab='probability', yvis=True if i == 0 else False, xlab=p.label, ylim=[0, 0.1], yMaxN=3)
    P.data_leg(0, loc='upper left' if half_circles else 'upper right')
    # dataset_legend(P.labels, P.colors, ax=P.axs[0], loc='upper left' if half_circles else 'upper right')
    P.adjust((0.3 / Nps, 0.99), (0.15, 0.95), 0.01)
    return P.get()


def plot_crawl_pars(subfolder='endpoint', par_legend=False, pvalues=False,type='sns.hist',
                    half_circles=False, kde=True, fig=None, axs=None,shorts=['str_N', 'run_tr', 'cum_d'], **kwargs):
    sns_kws={'kde' : kde, 'stat' : "probability", 'element': "step", 'fill':True, 'multiple' : "layer", 'shrink' :1}
    P = Plot(name='crawl_pars', subfolder=subfolder, **kwargs)
    Ncols=len(shorts)
    P.init_fits(getPar(shorts))
    P.build(1, Ncols, figsize=(Ncols * 5, 5), sharey=True, fig=fig, axs=axs)
    for i, k in enumerate(shorts):
        p=ParDict.dict[k]
        vs=[ParDict.get(k,d) for d in P.datasets]
        P.plot_par(vs=vs, bins='broad', nbins=40, labels=p.disp, i=i, sns_kws = sns_kws,
                   type=type, pvalues=pvalues, half_circles=half_circles, key='end')
        P.conf_ax(i, ylab='probability', yvis=True if i == 0 else False, xlab=p.label, xlim=p.lim, yMaxN=4,
                  leg_loc='upper right' if par_legend else None)
    P.data_leg(0, loc='upper left', fontsize=15)
    # dataset_legend(P.labels, P.colors, ax=P.axs[0], loc='upper left', fontsize=15)
    P.adjust((0.25 / Ncols, 0.99), (0.15, 0.95), 0.01)
    return P.get()


def plot_turn_duration(absolute=True, **kwargs):
    return plot_turn_amp(par_short='tur_t', mode='scatter', absolute=absolute, **kwargs)


def plot_turn_amp(par_short='tur_t', ref_angle=None, subfolder='turn', mode='hist', cumy=True, absolute=True, **kwargs):
    nn = 'turn_amp' if ref_angle is None else 'rel_turn_angle'
    name = f'{nn}_VS_{par_short}_{mode}'
    P = Plot(name=name, subfolder=subfolder, **kwargs)
    ypar, ylab, ylim = getPar('tur_fou', to_return=['d', 'l', 'lim'])

    if ref_angle is not None:
        A0 = float(ref_angle)
        p_ref = getPar(['tur_fo0', 'tur_fo1'])
        ys = []
        ylab = r'$\Delta\theta_{bearing} (deg)$'
        cumylab = r'$\bar{\Delta\theta}_{bearing} (deg)$'
        for d in P.datasets:
            y0 = d.get_par(p_ref[0]).dropna().values.flatten() - A0
            y1 = d.get_par(p_ref[1]).dropna().values.flatten() - A0
            y0 %= 360
            y1 %= 360
            y0[y0 > 180] -= 360
            y1[y1 > 180] -= 360
            y = np.abs(y0) - np.abs(y1)
            ys.append(y)

    else:
        cumylab = r'$\bar{\Delta\theta}_{or} (deg)$'
        ys = [d.get_par(ypar).dropna().values.flatten() for d in P.datasets]
        if absolute:
            ys = [np.abs(y) for y in ys]
    xpar, xlab = getPar(par_short, to_return=['d', 'l'])
    xs = [d.get_par(xpar).dropna().values.flatten() for d in P.datasets]

    if mode == 'scatter':
        P.build(1, 1, figsize=(10, 10))
        ax = P.axs[0]
        for x, y, l, c in zip(xs, ys, P.labels, P.colors):
            ax.scatter(x=x, y=y, marker='o', s=5.0, color=c, alpha=0.5)
            m, k = np.polyfit(x, y, 1)
            ax.plot(x, m * x + k, linewidth=4, color=c, label=l)
            P.conf_ax(xlab=xlab, ylab=ylab, ylim=ylim, yMaxN=4, leg_loc='upper left')
            P.adjust((0.15, 0.95), (0.1, 0.95), 0.01)
    elif mode == 'hist':
        P.fig = scatter_hist(xs, ys, P.labels, P.colors, xlabel=xlab, ylabel=ylab, ylim=ylim, cumylabel=cumylab,
                             cumy=cumy)
    return P.get()


def plot_bout_ang_pars(absolute=True, include_rear=True, subfolder='turn', **kwargs):
    shorts = ['bv', 'fov', 'rov', 'ba', 'foa', 'roa'] if include_rear else ['bv', 'fov', 'ba', 'foa']
    ranges = [250, 250, 50, 2000, 2000, 500] if include_rear else [200, 200, 2000, 2000]

    pars, sim_ls, xlabels, disps = getPar(shorts, to_return=['d', 's', 'l', 'd'])
    Ncols = int(len(pars) / 2)
    chunks = ['stride', 'pause']
    chunk_cols = ['green', 'purple']
    P = AutoPlot(name='bout_ang_pars', subfolder=subfolder, Nrows=2, Ncols=Ncols, figsize=(Ncols * 7, 14), sharey=True,
                 **kwargs)
    p_labs = [[sl] * P.Ndatasets for sl in sim_ls]

    P.init_fits(pars, multiindex=False)

    for i, (p, r, p_lab, xlab, disp) in enumerate(zip(pars, ranges, p_labs, xlabels, disps)):
        bins, xlim = P.angrange(r, absolute, 200)
        ax = P.axs[i]
        for d, l in zip(P.datasets, P.labels):
            vs = []
            for c, col in zip(chunks, chunk_cols):
                v = d.step_data.dropna(subset=[nam.id(c)])[p].values
                if absolute:
                    v = np.abs(v)
                vs.append(v)
                ax.hist(v, color=col, bins=bins, label=c, weights=np.ones_like(v) / float(len(v)),
                        alpha=1.0, histtype='step', linewidth=2)
            P.comp_pvalue(l, vs[0], vs[1], p)
            P.plot_half_circle(p, ax, col1=chunk_cols[0], col2=chunk_cols[1], v=P.fit_df[p].loc[l], ind=l)

        P.conf_ax(i, xlab=xlab, xlim=xlim, yMaxN=3)
    P.conf_ax(0, ylab='probability', ylim=[0, 0.04], leg_loc='upper left')
    P.conf_ax(Ncols, ylab='probability', leg_loc='upper left')
    P.adjust((0.25 / Ncols, 0.95), (0.1, 0.9), 0.1, 0.3)
    return P.get()


def plot_endpoint_params(axs=None, fig=None, mode='basic', par_shorts=None, subfolder='endpoint',
                         plot_fit=True, nbins=20, Ncols=None, use_title=True, **kwargs):
    warnings.filterwarnings('ignore')
    P = Plot(name=f'endpoint_params_{mode}', subfolder=subfolder, **kwargs)
    ylim = [0.0, 0.25]
    nbins = nbins
    l_par = 'l'  # 'l_mu
    if par_shorts is None:
        dic = {
            'basic': [l_par, 'fsv', 'sv_mu', 'sstr_d_mu',
                      'str_tr', 'pau_tr', 'Ltur_tr', 'Rtur_tr',
                      'tor20_mu', 'dsp_0_40_fin', 'b_mu', 'bv_mu'],
            'minimal': [l_par, 'fsv', 'sv_mu', 'sstr_d_mu',
                        'cum_t', 'str_tr', 'pau_tr', 'tor',
                        'tor5_mu', 'tor20_mu', 'dsp_0_40_max', 'dsp_0_40_fin',
                        'b_mu', 'bv_mu', 'Ltur_tr', 'Rtur_tr'],
            'tiny': ['fsv', 'sv_mu', 'str_tr', 'pau_tr',
                     'b_mu', 'bv_mu', 'Ltur_tr', 'Rtur_tr'],
            'stride_def': [l_par, 'fsv', 'sstr_d_mu', 'sstr_d_std'],
            'reorientation': ['str_fo_mu', 'str_fo_std', 'tur_fou_mu', 'tur_fou_std'],
            'tortuosity': ['tor2_mu', 'tor5_mu', 'tor10_mu', 'tor20_mu'],
            'result': ['sv_mu', 'str_tr', 'pau_tr', 'pau_t_mu'],
            'limited': [l_par, 'fsv', 'sv_mu', 'sstr_d_mu',
                        'cum_t', 'str_tr', 'pau_tr', 'pau_t_mu',
                        'tor5_mu', 'tor5_std', 'tor20_mu', 'tor20_std',
                        'tor', 'sdsp_mu', 'sdsp_0_40_max', 'sdsp_0_40_fin',
                        'b_mu', 'b_std', 'bv_mu', 'bv_std',
                        'Ltur_tr', 'Rtur_tr', 'Ltur_fou_mu', 'Rtur_fou_mu'],
            'full': [l_par, 'str_N', 'fsv',
                     'cum_d', 'cum_sd', 'v_mu', 'sv_mu',
                     'str_d_mu', 'str_d_std', 'sstr_d_mu', 'sstr_d_std',
                     'str_std_mu', 'str_std_std', 'sstr_std_mu', 'sstr_std_std',
                     'str_fo_mu', 'str_fo_std', 'str_ro_mu', 'str_ro_std',
                     'str_b_mu', 'str_b_std', 'str_t_mu', 'str_t_std',
                     'cum_t', 'str_tr', 'pau_tr',
                     'pau_N', 'pau_t_mu', 'pau_t_std', 'tor',
                     'tor2_mu', 'tor5_mu', 'tor10_mu', 'tor20_mu',
                     'tor2_std', 'tor5_std', 'tor10_std', 'tor20_std',
                     'dsp_mu', 'dsp_fin', 'dsp_0_40_fin', 'dsp_0_40_max',
                     'sdsp_mu', 'sdsp_fin', 'sdsp_0_40_fin', 'sdsp_0_40_max',
                     'Ltur_t_mu', 'Ltur_t_std', 'cum_Ltur_t', 'Ltur_tr',
                     'Rtur_t_mu', 'Rtur_t_std', 'cum_Rtur_t', 'Rtur_tr',
                     'Ltur_fou_mu', 'Ltur_fou_std', 'Rtur_fou_mu', 'Rtur_fou_std',
                     'b_mu', 'b_std', 'bv_mu', 'bv_std',
                     ],
            'deb': [
                'deb_f_mu', 'hunger', 'reserve_density', 'puppation_buffer',
                'cum_d', 'cum_sd', 'str_N', 'fee_N',
                'str_tr', 'pau_tr', 'fee_tr', 'f_am',
                l_par, 'm'
                # 'tor2_mu', 'tor5_mu', 'tor10_mu', 'tor20_mu',
                # 'v_mu', 'sv_mu',

            ]
        }
        if mode in dic.keys():
            par_shorts = dic[mode]
        else:
            raise ValueError('Provide parameter shortcuts or define a mode')
    ends = [d.read('end', file='endpoint_h5') for d in P.datasets]
    pars = getPar(par_shorts)

    pars = [p for p in pars if all([p in e.columns for e in ends])]
    xlabels, xlims, disps = getPar(par_shorts, to_return=['l', 'lim', 'd'])

    if mode == 'stride_def':
        xlims = [[2.5, 4.8], [0.8, 2.0], [0.1, 0.25], [0.02, 0.09]]
    P.init_fits(pars)

    lw = 3
    Npars = len(pars)
    if Npars == 0:
        return None
    elif Ncols is not None:
        Nrows = int(np.ceil(Npars / Ncols))
    elif Npars == 4:
        Ncols = 2
        Nrows = 2
    else:
        Ncols = int(np.min([Npars, 4]))
        Nrows = int(np.ceil(Npars / Ncols))
    fig_s = 5

    P.build(Nrows, Ncols, figsize=(fig_s * Ncols, fig_s * Nrows), sharey=True, fig=fig, axs=axs)
    for i, (p, xlabel, xlim, disp) in enumerate(zip(pars, xlabels, xlims, disps)):
        bins = nbins if xlim is None else np.linspace(xlim[0], xlim[1], nbins)
        ax = P.axs[i]
        vs = [e[p].values for e in ends]
        P.comp_pvalues(vs, p)

        Nvalues = [len(i) for i in vs]
        a = np.empty((np.max(Nvalues), len(vs),)) * np.nan
        for k in range(len(vs)):
            a[:Nvalues[k], k] = vs[k]
        df = pd.DataFrame(a, columns=P.labels)
        for j, (col, lab) in enumerate(zip(df.columns, P.labels)):

            try:
                v = df[[col]].dropna().values
                y, x, patches = ax.hist(v, bins=bins, weights=np.ones_like(v) / float(len(v)),
                                        color=P.colors[j], alpha=0.5)
                if plot_fit:
                    x = x[:-1] + (x[1] - x[0]) / 2
                    y_smooth = np.polyfit(x, y, 5)
                    poly_y = np.poly1d(y_smooth)(x)
                    ax.plot(x, poly_y, color=P.colors[j], label=lab, linewidth=lw)
            except:
                pass
        P.conf_ax(i, ylab='probability' if i % Ncols == 0 else None, xlab=xlabel, xlim=xlim, ylim=ylim,
                  xMaxN=4, yMaxN=4, xMath=True, title=disp if use_title else None)
        P.plot_half_circles(p, i)
    P.adjust((0.1, 0.97), (0.17 / Nrows, 1 - (0.1 / Nrows)), 0.1, 0.2 * Nrows)
    P.data_leg(0, loc='upper right', fontsize=15)
    # dataset_legend(P.labels, P.colors, ax=P.axs[0], loc='upper right', fontsize=15)
    return P.get()


def plot_endpoint_scatter(subfolder='endpoint', keys=None, **kwargs):
    pairs = list(itertools.combinations(keys, 2))
    Npairs = len(pairs)
    if Npairs % 3 == 0:
        Nx, Ny = 3, int(Npairs / 3)
    elif Npairs % 2 == 0:
        Nx, Ny = 2, int(Npairs / 2)
    elif Npairs % 5 == 0:
        Nx, Ny = 5, int(Npairs / 5)
    else:
        Nx, Ny = Npairs, 1
    if Nx * Ny > 1:
        name = f'endpoint_scatterplot'
    else:
        name = f'{keys[1]}_vs_{keys[0]}'
    P = Plot(name=name, subfolder=subfolder, **kwargs)
    P.build(Nx, Ny, figsize=(10 * Ny, 10 * Nx))
    for i, (p0, p1) in enumerate(pairs):
        pars, labs = getPar([p0, p1], to_return=['d', 'l'])

        v0_all = [d.endpoint_data[pars[0]].values for d in P.datasets]
        v1_all = [d.endpoint_data[pars[1]].values for d in P.datasets]
        r0, r1 = 0.9, 1.1
        v0_r = [np.min(np.array(v0_all)) * r0, np.max(np.array(v0_all)) * r1]
        v1_r = [np.min(np.array(v1_all)) * r0, np.max(np.array(v1_all)) * r1]

        for v0, v1, l, c in zip(v0_all, v1_all, P.labels, P.colors):
            P.axs[i].scatter(v0, v1, color=c, label=l)
        P.conf_ax(i, xlab=labs[0], ylab=labs[1], xlim=v0_r, ylim=v1_r, tickMath=(0, 0),
                  title=f'{pars[1]}_vs_{pars[0]}', leg_loc='upper right')

    return P.get()


def plot_turns(absolute=True, subfolder='turn', **kwargs):
    P = Plot(name='turn_amplitude', subfolder=subfolder, **kwargs)
    P.build()
    p, xlab = getPar('tur_fou', to_return=['d', 'l'])
    bins, xlim = P.angrange(150, absolute, 30)
    P.plot_par(p, bins, i=0, absolute=absolute, alpha=1.0, histtype='step')
    P.conf_ax(xlab=xlab, ylab='probability, $P$', xlim=xlim, yMaxN=4, leg_loc='upper right')
    P.adjust((0.25, 0.95), (0.15, 0.92), 0.05, 0.005)
    return P.get()




