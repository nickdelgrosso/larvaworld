import itertools
import os

import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt, patches, transforms, ticker

from lib.conf.pars.pars import getPar, ParDict

from lib.aux.colsNstr import N_colors
import lib.aux.dictsNlists as dNl

plt_conf = {'axes.labelsize': 20,
            'axes.titlesize': 25,
            'figure.titlesize': 25,
            'xtick.labelsize': 20,
            'ytick.labelsize': 20,
            'legend.fontsize': 20,
            'legend.title_fontsize': 20}
plt.rcParams.update(plt_conf)


class BasePlot:
    def __init__(self, name, save_to='.', save_as=None, return_fig=False, show=False, suf='pdf', text_xy0=(0.05, 0.98),
                 **kwargs):
        self.filename = f'{name}.{suf}' if save_as is None else save_as
        self.return_fig = return_fig
        self.show = show
        self.fit_df = None
        self.save_to = save_to

        self.cur_idx = 0
        self.text_x0, self.text_y0 = text_xy0
        self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        self.letter_dict = {}
        self.x0s, self.y0s = [], []

    def build(self, Nrows=1, Ncols=1, figsize=None, fig=None, axs=None, dim3=False, azim=115, elev=15, **kwargs):
        if fig is None and axs is None:
            if figsize is None:
                figsize = (12 * Ncols, 10 * Nrows)
            if not dim3:
                self.fig, axs = plt.subplots(Nrows, Ncols, figsize=figsize, **kwargs)
                self.axs = axs.ravel() if Nrows * Ncols > 1 else [axs]
            else:
                from mpl_toolkits.mplot3d import Axes3D
                self.fig = plt.figure(figsize=(15, 10))
                ax = Axes3D(self.fig, azim=azim, elev=elev)
                self.axs = [ax]
        else:
            self.fig = fig
            self.axs = axs if type(axs) == list else [axs]

    def conf_ax(self, idx=0, xlab=None, ylab=None, zlab=None, xlim=None, ylim=None, zlim=None, xticks=None,
                xticklabels=None, yticks=None, xticklabelrotation=None, yticklabelrotation=None,
                yticklabels=None, zticks=None, zticklabels=None, xtickpos=None, xtickpad=None, ytickpad=None,
                ztickpad=None, xlabelfontsize=None, xticklabelsize=None, yticklabelsize=None, zticklabelsize=None,
                xlabelpad=None, ylabelpad=None, zlabelpad=None, equal_aspect=None,
                xMaxN=None, yMaxN=None, zMaxN=None, xMath=None, yMath=None, tickMath=None, ytickMath=None, leg_loc=None,
                leg_handles=None, xvis=None, yvis=None, zvis=None,
                title=None):
        ax = self.axs[idx]
        if equal_aspect is not None:
            ax.set_aspect('equal', adjustable='box')
        if xvis is not None:
            ax.xaxis.set_visible(xvis)
        if yvis is not None:
            ax.yaxis.set_visible(yvis)
        if zvis is not None:
            ax.zaxis.set_visible(zvis)
        if ylab is not None:
            ax.set_ylabel(ylab, labelpad=ylabelpad)
        if xlab is not None:
            if xlabelfontsize is not None:
                ax.set_xlabel(xlab, labelpad=xlabelpad, fontsize=xlabelfontsize)
            else:
                ax.set_xlabel(xlab, labelpad=xlabelpad)
        if zlab is not None:
            ax.set_zlabel(zlab, labelpad=zlabelpad)
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        if zlim is not None:
            ax.set_zlim(zlim)
        if xticks is not None:
            ax.set_xticks(ticks=xticks)
        if xticklabelrotation is not None:
            ax.tick_params(axis='x', which='major', rotation=xticklabelrotation)
        if xticklabelsize is not None:
            ax.tick_params(axis='x', which='major', labelsize=xticklabelsize)
        if yticklabelsize is not None:
            ax.tick_params(axis='y', which='major', labelsize=yticklabelsize)
        if zticklabelsize is not None:
            ax.tick_params(axis='z', which='major', labelsize=zticklabelsize)
        if xticklabels is not None:
            ax.set_xticklabels(labels=xticklabels, rotation=xticklabelrotation)
        if yticks is not None:
            ax.set_yticks(ticks=yticks)
        if yticklabels is not None:
            ax.set_yticklabels(labels=yticklabels, rotation=yticklabelrotation)
        if zticks is not None:
            ax.set_zticks(ticks=zticks)
        if zticklabels is not None:
            ax.set_zticklabels(labels=zticklabels)
        if tickMath is not None:
            ax.ticklabel_format(useMathText=True, scilimits=tickMath)
        if ytickMath is not None:
            ax.ticklabel_format(axis='y', useMathText=True, scilimits=ytickMath, useOffset=True)
        if xMaxN is not None:
            ax.xaxis.set_major_locator(ticker.MaxNLocator(xMaxN))
        if yMaxN is not None:
            ax.yaxis.set_major_locator(ticker.MaxNLocator(yMaxN))
        if zMaxN is not None:
            ax.zaxis.set_major_locator(ticker.MaxNLocator(zMaxN))
        if xMath is not None:
            ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=True, useMathText=True))
        if yMath is not None:
            ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=True, useMathText=True))
        if xtickpos is not None:
            ax.xaxis.set_ticks_position(xtickpos)
        if title is not None:
            ax.set_title(title)
        if xtickpad is not None:
            ax.xaxis.set_tick_params(pad=xtickpad)
        if ytickpad is not None:
            ax.yaxis.set_tick_params(pad=ytickpad)
        if ztickpad is not None:
            ax.zaxis.set_tick_params(pad=ztickpad)

        if leg_loc is not None:
            if leg_handles is not None:
                ax.legend(handles=leg_handles, loc=leg_loc)
            else:
                ax.legend(loc=leg_loc)

    def adjust(self, LR=None, BT=None, W=None, H=None):
        kws = {}
        if LR is not None:
            kws['left'] = LR[0]
            kws['right'] = LR[1]
        if BT is not None:
            kws['bottom'] = BT[0]
            kws['top'] = BT[1]
        if W is not None:
            kws['wspace'] = W
        if H is not None:
            kws['hspace'] = H
        self.fig.subplots_adjust(**kws)

    def set(self, fig):
        self.fig = fig

    def get(self):
        if self.fit_df is not None:
            self.fit_df.to_csv(self.fit_filename, index=True, header=True)
        return process_plot(self.fig, self.save_to, self.filename, self.return_fig, self.show)

    def add_letter(self, ax, letter=True, x0=False, y0=False):
        if letter:
            self.letter_dict[ax] = self.letters[self.cur_idx]
            self.cur_idx += 1
            if x0:
                self.x0s.append(ax)
            if y0:
                self.y0s.append(ax)

    def annotate(self, dx=-0.05, dy=0.005, full_dict=False):
        if full_dict:

            for i, ax in enumerate(self.axs):
                self.letter_dict[ax] = self.letters[i]
        for i, (ax, text) in enumerate(self.letter_dict.items()):
            X = self.text_x0 if ax in self.x0s else ax.get_position().x0 + dx
            Y = self.text_y0 if ax in self.y0s else ax.get_position().y1 + dy
            self.fig.text(X, Y, text, size=30, weight='bold')


class ParPlot(BasePlot):
    def __init__(self, name, pref=None, **kwargs):
        if pref is not None:
            name = f'{pref}_{name}'
        super().__init__(name, **kwargs)

    def conf_ax_3d(self, vars, target, lims=None, title=None, maxN=3, labelpad=15, tickpad=5, idx=0):
        if lims is None:
            xlim, ylim, zlim = None, None, None
        else:
            xlim, ylim, zlim = lims
        self.conf_ax(idx=idx, xlab=vars[0], ylab=vars[1], zlab=target, xlim=xlim, ylim=ylim, zlim=zlim,
                     xtickpad=tickpad, ytickpad=tickpad, ztickpad=tickpad,
                     xlabelpad=labelpad, ylabelpad=labelpad, zlabelpad=labelpad,
                     xMaxN=maxN, yMaxN=maxN, zMaxN=maxN, title=title)


class Plot(BasePlot):
    def __init__(self, name, datasets, labels=None, subfolder=None, save_fits_as=None, save_to=None, add_samples=False,
                 **kwargs):

        if add_samples:
            from lib.conf.stored.conf import loadRef, kConfDict
            targetIDs = dNl.unique_list([d.config['sample'] for d in datasets])

            targets = [loadRef(id) for id in targetIDs if id in kConfDict('Ref')]
            datasets += targets
            if labels is not None:
                labels += targetIDs
        self.Ndatasets, self.colors, save_to, self.labels = plot_config(datasets, labels, save_to,
                                                                        subfolder=subfolder)
        super().__init__(name, save_to=save_to, **kwargs)
        self.datasets = datasets
        ff = f'{name}_fits.csv' if save_fits_as is None else save_fits_as
        self.fit_filename = os.path.join(self.save_to, ff) if ff is not None and self.save_to is not None else None
        self.fit_ind = None

    def init_fits(self, pars, names=('dataset1', 'dataset2'), multiindex=True):
        if self.Ndatasets > 1:
            if multiindex:
                fit_ind = np.array([np.array([l1, l2]) for l1, l2 in itertools.combinations(self.labels, 2)])
                self.fit_ind = pd.MultiIndex.from_arrays([fit_ind[:, 0], fit_ind[:, 1]], names=names)
                self.fit_df = pd.DataFrame(index=self.fit_ind,
                                           columns=pars + [f'S_{p}' for p in pars] + [f'P_{p}' for p in pars])
            else:
                self.fit_df = pd.DataFrame(index=self.labels,
                                           columns=pars + [f'S_{p}' for p in pars] + [f'P_{p}' for p in pars])

    def comp_pvalues(self, values, p):
        if self.fit_ind is not None:
            for ind, (v1, v2) in zip(self.fit_ind, itertools.combinations(values, 2)):
                self.comp_pvalue(ind, v1, v2, p)

    def comp_pvalue(self, ind, v1, v2, p):
        from scipy.stats import ttest_ind
        st, pv = ttest_ind(v1, v2, equal_var=False)
        if not pv <= 0.01:
            self.fit_df[p].loc[ind] = 0
        else:
            self.fit_df[p].loc[ind] = 1 if np.nanmean(v1) < np.nanmean(v2) else -1
        self.fit_df[f'S_{p}'].loc[ind] = st
        self.fit_df[f'P_{p}'].loc[ind] = np.round(pv, 11)

    def plot_half_circles(self, p, i):
        if self.fit_df is not None:
            ax = self.axs[i]
            ii = 0
            for z, (l1, l2) in enumerate(self.fit_df.index.values):
                col1, col2 = self.colors[self.labels.index(l1)], self.colors[self.labels.index(l2)]
                res = self.plot_half_circle(p, ax, col1, col2, v=self.fit_df[p].iloc[z], ind=(l1, l2), coef=z - ii)
                if not res:
                    ii += 1
                    continue

    def plot_half_circle(self, p, ax, col1, col2, v, ind, coef=0):
        res = True
        if v == 1:
            c1, c2 = col1, col2
        elif v == -1:
            c1, c2 = col2, col1
        else:
            res = False

        if res:
            rad = 0.04
            yy = 0.95 - coef * 0.08
            xx = 0.75
            dual_half_circle(center=(xx, yy), radius=rad, angle=90, ax=ax, colors=(c1, c2), transform=ax.transAxes)
            pv = self.fit_df[f'P_{p}'].loc[ind]
            if pv == 0:
                pvi = -9
            else:
                for pvi in np.arange(-1, -10, -1):
                    if np.log10(pv) > pvi:
                        pvi += 1
                        break
            ax.text(xx + 0.05, yy + rad / 1.5, f'p<10$^{{{pvi}}}$', ha='left', va='top', color='k',
                    fontsize=15, transform=ax.transAxes)
        return res

    @property
    def Nticks(self):
        Nticks_list = [len(d.step_data.index.unique('Step')) for d in self.datasets]
        return np.max(dNl.unique_list(Nticks_list))

    @property
    def fr(self):
        fr_list = [d.fr for d in self.datasets]
        return np.max(dNl.unique_list(fr_list))

    @property
    def dt(self):
        dt_list = dNl.unique_list([d.dt for d in self.datasets])
        # print(dt_list)
        return np.max(dt_list)

    @property
    def tlim(self):
        return (0, int(self.Nticks * self.dt))
        # return (0, int(self.Nticks / self.fr))

    def trange(self, unit='min'):
        if unit == 'min':
            T = 60
        elif unit == 'sec':
            T = 1
        t0, t1 = self.tlim
        x = np.linspace(t0 / T, t1 / T, self.Nticks)
        # print(t1, self.fr, self.dt, T, t1/T, self.Nticks)
        # raise
        return x

    def angrange(self, r, absolute=False, nbins=200):
        lim = (r0, r1) = (0, r) if absolute else (-r, r)
        x = np.linspace(r0, r1, nbins)
        return x, lim

    def plot_par(self, short=None, par=None, vs=None, bins='broad', i=0, labels=None, absolute=False, nbins=None,
                 type='plt.hist', sns_kws={},
                 pvalues=False, half_circles=False, key='step', **kwargs):
        if labels is None:
            labels = self.labels
        if vs is None:
            vs = []
            for d in self.datasets:
                if key == 'step':
                    try:
                        v = d.step_data[par]
                    except:
                        v = d.get_par(par, key=key)
                elif key == 'end':
                    try:
                        v = d.endpoint_data[par]
                    except:
                        v = d.get_par(par, key=key)
                if v is not None:
                    v = v.dropna().values
                else:
                    continue
                if absolute:
                    v = np.abs(v)
                vs.append(v)
        if bins == 'broad' and nbins is not None:
            bins = np.linspace(np.min([np.min(v) for v in vs]), np.max([np.max(v) for v in vs]), nbins)
        for v, c, l in zip(vs, self.colors, labels):
            if type == 'sns.hist':
                sns.histplot(v, color=c, bins=bins, ax=self.axs[i], label=l, **sns_kws, **kwargs)
            elif type == 'plt.hist':
                self.axs[i].hist(v, bins=bins, weights=np.ones_like(v) / float(len(v)), label=l, color=c, **kwargs)
        if pvalues:
            self.comp_pvalues(vs, par)
        if half_circles:
            self.plot_half_circles(par, i)
        return vs


class AutoPlot(Plot):
    def __init__(self, Nrows=1, Ncols=1, figsize=None, fig=None, axs=None, sharex=False, sharey=False, **kwargs):
        super().__init__(**kwargs)
        self.build(Nrows=Nrows, Ncols=Ncols, figsize=figsize, fig=fig, axs=axs, sharex=sharex, sharey=sharey)


def plot_quantiles(df, from_np=False, x=None, **kwargs):
    if from_np:
        df_m = np.nanquantile(df, q=0.5, axis=0)
        df_u = np.nanquantile(df, q=0.75, axis=0)
        df_b = np.nanquantile(df, q=0.25, axis=0)
        if x is None:
            x = np.arange(len(df_m))
    else:
        df_m = df.groupby(level='Step').quantile(q=0.5)
        df_u = df.groupby(level='Step').quantile(q=0.75)
        df_b = df.groupby(level='Step').quantile(q=0.25)
    plot_mean_and_range(x=x, mean=df_m, lb=df_b, ub=df_u, **kwargs)


def plot_mean_and_range(x, mean, lb, ub, axis, color_shading, color_mean=None, label=None, linewidth=2):
    if x.shape[0] > mean.shape[0]:
        xx = x[:mean.shape[0]]
    elif x.shape[0] == mean.shape[0]:
        xx = x
    if color_mean is None:
        color_mean = color_shading
    # plot the shaded range of e.g. the confidence intervals
    axis.fill_between(xx, ub, lb, color=color_shading, alpha=.2, zorder=0)
    # plot the mean on top
    if label is not None:
        axis.plot(xx, mean, color_mean, label=label, linewidth=linewidth, alpha=1.0, zorder=10)
    else:
        axis.plot(xx, mean, color_mean, linewidth=linewidth, alpha=1.0, zorder=10)

    # pass


def circular_hist(ax, x, bins=16, density=True, offset=0, gaps=True, **kwargs):
    """
    Produce a circular histogram of angles on ax.

    Parameters
    ----------
    ax : matplotlib.axes._subplots.PolarAxesSubplot
        axis instance created with subplot_kw=dict(projection='polar').

    x : array
        Angles to plot, expected in units of radians.

    bins : int, optional
        Defines the number of equal-width bins in the range. The default is 16.

    density : bool, optional
        If True plot frequency proportional to area. If False plot frequency
        proportional to radius. The default is True.

    offset : float, optional
        Sets the offset for the location of the 0 direction in units of
        radians. The default is 0.

    gaps : bool, optional
        Whether to allow gaps between bins. When gaps = False the bins are
        forced to partition the entire [-pi, pi] range. The default is True.

    Returns
    -------
    n : array or list of arrays
        The number of values in each bin.

    bins : array
        The edges of the bins.

    patches : `.BarContainer` or list of a single `.Polygon`
        Container of individual artists used to create the histogram
        or list of such containers if there are multiple input datasets.
    """
    # Wrap angles to [-pi, pi)
    x = (x + np.pi) % (2 * np.pi) - np.pi

    # Force bins to partition entire circle
    if not gaps:
        bins = np.linspace(-np.pi, np.pi, num=bins + 1)

    # Bin data and record counts
    n, bins = np.histogram(x, bins=bins)

    # Compute width of each bin
    widths = np.diff(bins)

    # By default plot frequency proportional to area
    if density:
        # Area to assign each bin
        area = n / x.size
        # Calculate corresponding bin radius
        radius = (area / np.pi) ** .5
    # Otherwise plot frequency proportional to radius
    else:
        radius = n

    # Plot data on ax
    patches = plt.bar(bins[:-1], radius, zorder=1, align='edge', width=widths,
                      edgecolor='black', fill=True, linewidth=2, **kwargs)

    # Set the direction of the zero angle
    ax.set_theta_offset(offset)

    # Remove ylabels for area plots (they are mostly obstructive)
    if density:
        ax.set_yticks([])

    return n, bins, patches


def circNarrow(ax, data, alpha, label, color):
    circular_hist(ax, data, bins=16, alpha=alpha, label=label, color=color, offset=np.pi / 2)
    arrow = patches.FancyArrowPatch((0, 0), (np.mean(data), 0.3), zorder=2, mutation_scale=30, alpha=alpha,
                                    facecolor=color, edgecolor='black', fill=True, linewidth=0.5)
    ax.add_patch(arrow)


def dual_half_circle(center, radius, angle=0, ax=None, colors=('W', 'k'), **kwargs):
    """
    Add two half circles to the axes *ax* (or the current axes) with the
    specified facecolors *colors* rotated at *angle* (in degrees).
    """
    if ax is None:
        ax = plt.gca()
    theta1, theta2 = angle, angle + 180
    w1 = patches.Wedge(center, radius, theta1, theta2, fc=colors[0], **kwargs)
    w2 = patches.Wedge(center, radius, theta2, theta1, fc=colors[1], **kwargs)
    for wedge in [w1, w2]:
        ax.add_artist(wedge)
    return [w1, w2]


def confidence_ellipse(x, y, ax, n_std=3.0, facecolor='none', **kwargs):
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.

    Parameters
    ----------
    x, y : array-like, shape (n, )
        Input data.

    ax : matplotlib.axes.Axes
        The axes object_class to draw the ellipse into.

    n_std : float
        The number of standard deviations to determine the ellipse'sigma radiuses.

    **kwargs
        Forwarded to `~matplotlib.patches.Ellipse`

    Returns
    -------
    matplotlib.patches.Ellipse
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = patches.Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                              facecolor=facecolor, **kwargs)

    # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the stdandard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mean_x, mean_y)

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def save_plot(fig, filepath, filename=None):
    fig.savefig(filepath, dpi=300, facecolor=None)
    print(f'Plot saved as {filepath}')
    # print(fig.get_size_inches(), filename)
    # fig.clear()
    plt.close(fig)
    if filename is not None:
        pass
        # print(f'Plot saved as {filename}')


def plot_config(datasets, labels, save_to, subfolder=None):
    if labels is None:
        labels = [d.id for d in datasets]
    Ndatasets = len(datasets)
    if Ndatasets != len(labels):
        raise ValueError(f'Number of labels {len(labels)} does not much number of datasets {Ndatasets}')

    def get_colors(datasets):
        try:
            cs = [d.config['color'] for d in datasets]
            u_cs = dNl.unique_list(cs)
            if len(u_cs) == len(cs) and None not in u_cs:
                colors = cs
            elif len(u_cs) == len(cs) - 1 and cs[-1] in cs[:-1] and 'black' not in cs:
                cs[-1] = 'black'
                colors = cs
            else:
                colors = N_colors(Ndatasets)
        except:
            colors = N_colors(Ndatasets)
        return colors

    cols = get_colors(datasets)
    if save_to is not None:
        if subfolder is not None:
            save_to = f'{save_to}/{subfolder}'
        os.makedirs(save_to, exist_ok=True)
    return Ndatasets, cols, save_to, labels


def dataset_legend(labels, colors, ax=None, loc=None, anchor=None, fontsize=None, handlelength=0.5, handleheight=0.5,
                   **kwargs):
    if ax is None:
        leg = plt.legend(
            bbox_to_anchor=anchor,
            handles=[patches.Patch(facecolor=c, label=l, edgecolor='black') for c, l in zip(colors, labels)],
            labels=labels, loc=loc, handlelength=handlelength, handleheight=handleheight, fontsize=fontsize, **kwargs)
    else:
        leg = ax.legend(
            bbox_to_anchor=anchor,
            handles=[patches.Patch(facecolor=c, label=l, edgecolor='black') for c, l in zip(colors, labels)],
            labels=labels, loc=loc, handlelength=handlelength, handleheight=handleheight, fontsize=fontsize, **kwargs)
        ax.add_artist(leg)
    return leg


def process_plot(fig, save_to, filename, return_fig=False, show=False):
    if show:
        plt.show()
    fig.patch.set_visible(False)
    if return_fig:
        res = fig, save_to, filename
    else:
        res = fig
        if save_to is not None:
            os.makedirs(save_to, exist_ok=True)
            filepath = os.path.join(save_to, filename)
            save_plot(fig, filepath, filename)
    return res


def label_diff(i, j, text, X, Y, ax):
    x = (X[i] + X[j]) / 2
    y = 1.5 * max(Y[i], Y[j])
    dx = abs(X[i] - X[j])

    props = {'connectionstyle': 'bar', 'arrowstyle': '-', \
             'shrinkA': 20, 'shrinkB': 20, 'linewidth': 2}
    ax.annotate(text, xy=(X[i], y), zorder=10)
    # ax.annotate(text, xy=(X[i], y), zorder=10)
    ax.annotate('', xy=(X[i], y), xytext=(X[j], y), arrowprops=props)


def boolean_indexing(v, fillval=np.nan):
    lens = np.array([len(item) for item in v])
    mask = lens[:, None] > np.arange(lens.max())
    out = np.full(mask.shape, fillval)
    out[mask] = np.concatenate(v)
    return out


def annotate_plot(data, x, y, hue=None, show_ns=True, target_only=None, **kwargs):
    from statannotations.Annotator import Annotator
    from lib.anal.fitting import pvalue_star
    from scipy.stats import mannwhitneyu
    subIDs0 = np.unique(data[x].values)
    # print(subIDs0)
    if hue is not None:
        h1, h2 = np.unique(data[hue].values)

        pairs = [((subID, h1), (subID, h2)) for subID in subIDs0]
        pvs = []
        for subID in subIDs0:
            dd = data[data[x] == subID]
            dd0 = dd[dd[hue] == h1][y].dropna().values.tolist()
            dd1 = dd[dd[hue] == h2][y].dropna().values.tolist()
            pvs.append(mannwhitneyu(dd0, dd1, alternative="two-sided").pvalue)
    else:
        if target_only is None:
            pairs = list(itertools.combinations(subIDs0, 2))
            pvs = []
            for subID0, subID1 in pairs:
                dd0 = data[data[x] == subID0][y].dropna().values.tolist()
                dd1 = data[data[x] == subID1][y].dropna().values.tolist()
                pvs.append(mannwhitneyu(dd0, dd1, alternative="two-sided").pvalue)
        else:
            pairs = []
            pvs = []
            dd0 = data[data[x] == target_only][y].dropna().values.tolist()
            for subID in subIDs0:
                if subID != target_only:
                    pairs.append((target_only, subID))
                    dd1 = data[data[x] == subID][y].dropna().values.tolist()
                    pvs.append(mannwhitneyu(dd0, dd1, alternative="two-sided").pvalue)

    f_pvs = [pvalue_star(pv) for pv in pvs]

    if not show_ns:
        valid_idx = [i for i, f_pv in enumerate(f_pvs) if f_pv != 'ns']
        pairs = [pairs[i] for i in valid_idx]
        f_pvs = [f_pvs[i] for i in valid_idx]

    # Add annotations
    if len(pairs) > 0:
        annotator = Annotator(pairs=pairs, data=data, x=x, y=y, hue=hue, **kwargs)
        annotator.verbose = False
        annotator.annotate_custom_annotations(f_pvs)


def concat_datasets(ds, key='end', unit='sec'):
    dfs = []
    for d in ds:
        if key == 'end':
            try:
                df = d.endpoint_data
            except:
                df = d.read(key='end', file='endpoint_h5')
        elif key == 'step':
            try:
                df = d.step_data
            except:
                df = d.read(key='step')
        df['DatasetID'] = d.id
        df['GroupID'] = d.group_id
        dfs.append(df)
    df0 = pd.concat(dfs)
    if key == 'step':
        df0.reset_index(level='Step', drop=False, inplace=True)
        dts = np.unique([d.config['dt'] for d in ds])
        if len(dts) == 1:
            dt = dts[0]
            dic = {'sec': 1, 'min': 60, 'hour': 60 * 60, 'day': 24 * 60 * 60}
            df0['Step'] *= dt / dic[unit]
    return df0


def conf_ax_3d(vars, target, ax=None, fig=None, lims=None, title=None, maxN=5, labelpad=30, tickpad=10):
    if fig is None and ax is None:
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure(figsize=(15, 10))
        ax = Axes3D(fig, azim=115, elev=15)

    ax.xaxis.set_major_locator(ticker.MaxNLocator(maxN))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(maxN))
    ax.zaxis.set_major_locator(ticker.MaxNLocator(maxN))
    ax.xaxis.set_tick_params(pad=tickpad)
    ax.yaxis.set_tick_params(pad=tickpad)
    ax.zaxis.set_tick_params(pad=tickpad)

    ax.set_xlabel(vars[0], labelpad=labelpad)
    ax.set_ylabel(vars[1], labelpad=labelpad)
    ax.set_zlabel(target, labelpad=labelpad)
    if lims is not None:
        ax.set_xlim(lims[0])
        ax.set_ylim(lims[1])
        ax.set_zlim(lims[2])

    if title is not None:
        ax.set_suptitle(title, fontsize=20)

    return fig, ax


def modelConfTable(mID, save_to=None, save_as=None, columns=['Parameter', 'Symbol', 'Value', 'Unit'], rows=None,
                   figsize=(14, 11), **kwargs):
    from lib.aux.combining import render_mpl_table
    from lib.conf.base.dtypes import par
    from lib.conf.base.init_pars import init_pars
    from lib.conf.stored.conf import loadConf
    m = loadConf(mID, "Model")
    if rows is None:
        rows = ['physics', 'body'] + [k for k, v in m.brain.modules.items() if v]

    rowDicts = []
    for k in rows:
        try:
            rowDicts.append(m[k])
        except:
            rowDicts.append(m.brain[f'{k}_params'])
    rowColors0 = ['lightskyblue', 'lightsteelblue', 'lightcoral', 'indianred', 'lightsalmon', '#a55af4', 'palegreen',
                  'plum', 'pink'][:len(rows)]
    Nrows = {rowLab: 0 for rowLab in rows}

    def register(vs, rowColor):
        data.append(vs)
        rowColors.append(rowColor)
        Nrows[vs[0]] += 1

    rowColors = [None]
    data = []

    dvalid = dNl.AttrDict.from_nested_dicts({'interference': {
        'square': ['crawler_phi_range', 'attenuation', 'attenuation_max'],
        'phasic': ['max_attenuation_phase', 'attenuation', 'attenuation_max'],
        'default': ['attenuation']
    },
        'turner': {
            'neural': ['base_activation', 'activation_range', 'n', 'tau'],
            'constant': ['initial_amp'],
            'sinusoidal': ['initial_amp', 'initial_freq']
        },
        'crawler': {
            'realistic': ['initial_freq', 'max_scaled_vel', 'max_vel_phase', 'stride_dst_mean', 'stride_dst_std'],
            'constant': ['initial_amp']
        },
        'physics': ['ang_damping', 'torque_coef', 'body_spring_k', 'bend_correction_coef'],
        'body': ['initial_length', 'Nsegs'],
        'olfactor': ['decay_coef'],
    })

    for l, dd, rowColor in zip(rows, rowDicts, rowColors0):
        d0 = init_pars().get(l, None)
        if l in ['physics', 'body', 'olfactor']:
            rowValid = dvalid[l]
        elif l == 'interference':
            rowValid = dvalid[l][dd.mode]
        elif l == 'turner':
            rowValid = dvalid[l][dd.mode]
        elif l == 'crawler':
            rowValid = dvalid[l][dd.waveform]
        elif l == 'intermitter':
            rowValid = [n for n in ['stridechain_dist', 'pause_dist'] if dd[n] is not None and dd[n].name is not None]

        if len(rowValid) == 0:
            Nrows.pop(l, None)
            continue
        for n, vv in d0.items():
            if n not in rowValid:
                continue
            v = dd[n]
            if n in ['stridechain_dist', 'pause_dist']:
                dist_dic={
                    'exponential' : f'Exp(b={v.beta})',
                    'powerlaw' : f'Powerlaw(a={v.alpha})',
                    'levy' : f'Levy(m={v.mu}, s={v.sigma})',
                    'uniform' : f'Uniform()',
                    'lognormal' : f'Lognormal(m={np.round(v.mu, 2)}, s={np.round(v.sigma, 2)})'
                }
                dist_v = dist_dic[v.name]

                if n == 'stridechain_dist':
                    vs1 = [l, 'run length distribution', '$N_{R}$', dist_v, '-']
                    vs2 = [l, 'run length range', '$[N_{R}^{min},N_{R}^{max}]$', v.range, '# $strides$']
                elif n == 'pause_dist':
                    vs1 = [l, 'pause duration distribution', '$t_{P}$', dist_v, '-']
                    vs2 = [l, 'pause duration range', '$[t_{P}^{min},t_{P}^{max}]$', v.range, '$sec$']
                register(vs1, rowColor)
                register(vs2, rowColor)
            else:
                p = par(n, **vv)

                if n == 'initial_length':
                    v *= 1000
                elif n == 'suppression_mode':
                    if v == 'both':
                        v = '$I_{T}$ & $\omega$'
                    elif v == 'amplitude':
                        v = fr'$\omega$'
                    elif v == 'oscillation':
                        v = '$I_{T}$'

                else:
                    try:
                        v = np.round(v, 2)
                    except:
                        pass
                vs = [l, p[n]['label'], p[n]['symbol'], v, p[n]['unit']]
                register(vs, rowColor)

    cumNrows = dict(zip(list(Nrows.keys()), np.cumsum(list(Nrows.values())).astype(int)))
    df = pd.DataFrame(data, columns=['field'] + columns)
    df.set_index(['field'], inplace=True)

    ax, fig, mpl = render_mpl_table(df, colWidths=[0.35, 0.1, 0.25, 0.15], cellLoc='center', rowLoc='center',
                                    figsize=figsize, adjust_kws={'left': 0.2, 'right': 0.95},
                                    row_colors=rowColors, return_table=True, **kwargs)
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    for k, cell in mpl._cells.items():
        if k[1] == -1:
            cell._text._text = ''
            cell._linewidth = 0

    for rowLab, idx in cumNrows.items():
        try:
            cell = mpl._cells[(idx - Nrows[rowLab] + 1, -1)]
            cell._text._text = rowLab.upper()
        except:
            pass
    if save_to is not None:
        os.makedirs(save_to, exist_ok=True)
        if save_as is None:
            save_as = mID
        filename = f'{save_to}/{save_as}.pdf'
        fig.savefig(filename, dpi=300)
    plt.close()
    return fig


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
    from lib.conf.base.init_pars import init_pars
    d0 = init_pars().get(module, None)
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


def test_model(mID=None, m=None, dur=2 / 3, dt=1 / 16, Nids=1, min_turn_amp=20, d=None, fig=None, axs=None, **kwargs):
    from lib.anal.plotting import annotated_strideplot, annotated_turnplot
    if d is None:
        from lib.eval.eval_aux import sim_model
        d = sim_model(mID=mID, m=m, dur=dur, dt=dt, Nids=Nids, enrichment=False)
    s, e, c = d.step_data, d.endpoint_data, d.config

    Nticks = int(dur * 60 / dt)
    trange = np.arange(0, Nticks * dt, dt)
    ss = s.xs(c.agent_ids[0], level='AgentID').loc[:Nticks]

    pars, labs = getPar(['v', 'c_CT', 'Act_tur', 'fov', 'b'], to_return=['d', 'symbol'])

    Nrows = len(pars)
    P = BasePlot(name=f'{mID}_test', **kwargs)
    P.build(Nrows, 1, figsize=(25, 5 * Nrows), sharex=True, fig=fig, axs=axs)
    a_v = ss[getPar('v')].values
    a_fov = ss[getPar('fov')].values
    annotated_strideplot(a_v, dt, ax=P.axs[0])
    annotated_strideplot(a_v, dt, a2plot=ss[pars[1]].values, ax=P.axs[1], ylim=(0, 1), show_extrema=False)

    annotated_turnplot(a_fov, dt, a2plot=ss[pars[2]].values, ax=P.axs[2], min_amp=min_turn_amp)
    annotated_turnplot(a_fov, dt, ax=P.axs[3], min_amp=min_turn_amp)
    annotated_turnplot(a_fov, dt, a2plot=ss[pars[4]].values, ax=P.axs[4], min_amp=min_turn_amp)

    for i in range(Nrows):
        P.conf_ax(i, xlim=(0, trange[-1] + 10 * dt), ylab=labs[i], xlab='time (sec)',
                  xvis=True if i == Nrows - 1 else False)
    P.adjust((0.1, 0.95), (0.15, 0.95), 0.01, 0.05)
    P.fig.align_ylabels(P.axs[:])
    return P.get()


# def add_letters(fig, axs, dx=-0.05, dy=0.005):
#     letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
#     for i, ax in enumerate(axs):
#         X = ax.get_position().x0 + dx
#         Y = ax.get_position().y1 + dy
#         fig.text(X, Y, letters[i], size=30, weight='bold')
