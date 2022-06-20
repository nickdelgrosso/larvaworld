from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns

from lib.plot.base import Plot
from lib.plot.aux import confidence_ellipse, process_plot, suf


def plot_segmentation_definition(subfolder='metric_definition', axs=None, fig=None, **kwargs):
    P = Plot(name=f'segmentation_definition', subfolder=subfolder, **kwargs)
    P.build(1, P.Ndatasets * 2, figsize=(5 * P.Ndatasets, 5), sharex=False, sharey=False, fig=fig, axs=axs)
    Nbest = 5
    for ii, d in enumerate(P.datasets):
        ax1, ax2 = P.axs[ii * 2], P.axs[ii * 2 + 1]
        N = d.Nangles
        dic = d.load_vel_definition()
        df_reg = dic['/bend2or_regression']
        df_corr = dic['/bend2or_correlation']

        df_reg.sort_index(inplace=True)
        single_scores = df_reg['single_score'].values
        cum_scores = df_reg['cum_score'].values
        x = np.arange(1, N + 1)
        ax1.scatter(x, single_scores, c='blue', alpha=1.0, marker=",", label='single', s=200)
        ax1.plot(x, single_scores, c='blue')

        ax1.scatter(x, cum_scores, c='green', alpha=1.0, marker="o", label='cumulative', s=200)
        ax1.plot(x, cum_scores, c='green')

        P.conf_ax(ii * 2, xlab=r'angular velocity, $\dot{\theta}_{i}$', ylab='regression score',
                  xticks=x, yMaxN=4, leg_loc='lower left')

        df_corr.sort_values('corr', ascending=False, inplace=True)
        max_corrs = df_corr['corr'].values[:Nbest]
        best_combos = df_corr.index.values[:Nbest]
        xx = [','.join(map(str, cc)) for cc in best_combos]
        ax2.bar(x=xx, height=max_corrs, width=0.5, color='black')
        P.conf_ax(ii * 2 + 1, xlab='combined angular velocities', ylab='Pearson correlation', yMaxN=4, ylim=(0.5, 1))
        ax2.tick_params(axis='x', which='major', labelsize=20)
        P.adjust(LR=(0.1, 0.95), BT=(0.15, 0.95), W=0.3)
        return P.get()


def plot_stride_variability(component_vels=True, subfolder='metric_definition', axs=None, fig=None, **kwargs):
    P = Plot(name=f'stride_spatiotemporal_variation', subfolder=subfolder, **kwargs)
    P.build(1, P.Ndatasets, figsize=(5 * P.Ndatasets, 5), sharex=True, sharey=True, fig=fig, axs=axs)
    for ii, d in enumerate(P.datasets):
        ax = P.axs[ii]
        try:
            dic = d.load_vel_definition()
        except:
            d.save_vel_definition(component_vels=component_vels)
            dic = d.load_vel_definition()
        stvar = dic['/stride_variability']
        stvar.sort_values(by='idx', inplace=True)
        ps = stvar.index if component_vels else [p for p in stvar.index if 'lin' not in p]
        for p in ps:
            row = stvar.loc[p]
            ax.scatter(x=row['scaled_stride_dst_var'], y=row['stride_dur_var'], marker=row['marker'], s=200,
                       color=row['color'], label=row['symbol'])
        ax.legend(ncol=2, handleheight=1.7, labelspacing=0.01, loc='lower right')
        ax.set_ylabel(r'$\overline{cv}_{temporal}$')
        ax.set_xlabel(r'$\overline{cv}_{spatial}$')
    return P.get()


def plot_correlated_pars(dataset, pars, labels, save_to=None, save_as=f'correlated_pars.{suf}', return_fig=False):
    if len(pars) != 3:
        raise ValueError('Currently implemented only for 3 parameters')
    if save_to is None:
        save_to = dataset.plot_dir
    e = dataset.endpoint_data
    g = sns.PairGrid(e[pars])
    g.map_upper(sns.scatterplot)
    g.map_lower(sns.kdeplot, fill=True)
    g.map_diag(sns.histplot, kde=True, bins=20)

    for i, ax in enumerate(g.axes[-1, :]):
        ax.xaxis.set_label_text(labels[i])
    for j, ax in enumerate(g.axes[:, 0]):
        ax.yaxis.set_label_text(labels[j])
    for ax, (i, j) in zip([g.axes[0, 1], g.axes[0, 2], g.axes[1, 2]], [(1, 0), (2, 0), (2, 1)]):
        for std, a in zip([0.5, 1, 2, 3], [0.4, 0.3, 0.2, 0.1]):
            confidence_ellipse(x=e[pars[i]].values, y=e[pars[j]].values,
                               ax=ax, n_std=std, facecolor='red', alpha=a)
    return process_plot(g, save_to, save_as, return_fig)


