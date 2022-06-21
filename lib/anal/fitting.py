import os
import warnings
import numpy as np
from scipy.stats import levy, norm, uniform, rv_discrete, ks_2samp
from scipy.special import erf

from lib.aux import naming as nam
#from lib.aux.dictsNlists import AttrDict, save_dict, NestDict
import lib.aux.dictsNlists as dNl
from lib.conf.pars.pars import ParDict


def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

def get_logNpow(x, xmax, xmid, overlap=0, discrete=False):
    r = len(x[x < xmid]) / len(x)
    m, s = get_lognormal(x[x < xmid + overlap * (xmax - xmid)])
    a = get_powerlaw_alpha(x[x >= xmid], xmid, xmax, discrete=discrete)
    return m, s, a, r


def get_powerlaw_alpha(dur, dur0=None, dur1=None, discrete=False):
    from lib.aux.stdout import suppress_stdout_stderr
    if dur0 is None :
        dur0=np.min(dur)
    if dur1 is None :
        dur1=np.max(dur)
    with suppress_stdout_stderr():
        from powerlaw import Fit
        return Fit(dur, xmin=dur0, xmax=dur1, discrete=discrete).power_law.alpha


def get_lognormal(dur):
    d = np.log(dur)
    return np.mean(d), np.std(d)

def get_exp_beta(x, xmin=None) :
    if xmin is None :
        xmin=np.min(x)
    return len(x) / np.sum(x - xmin)

def compute_density(x, xmin, xmax, Nbins=64):
    log_range = np.linspace(np.log2(xmin), np.log2(xmax), Nbins)
    bins = np.unique((2 * 2 ** (log_range)) / 2)
    x_filt = x[x >= xmin]
    x_filt = x_filt[x_filt <= xmax]
    cdf = np.ones(len(bins))
    pdf = np.zeros(len(bins) - 1)
    for i in range(len(bins)):
        cdf[i] = 1 - np.mean(x_filt < bins[i])
        if i >= 1:
            pdf[i - 1] = -(cdf[i] - cdf[i - 1]) / (bins[i] - bins[i - 1])
    bins1 = 0.5 * (bins[:-1] + bins[1:])
    return bins, bins1, pdf, cdf


def KS(a1, a2):
    return np.max(np.abs(a1 - a2))


def MSE(a1, a2, scaled=False):
    if scaled:
        s1 = sum(a1)
        s2 = sum(a2)
    else:
        s1, s2 = 1, 1
    return np.sum((a1 / s1 - a2 / s2) ** 2) / a1.shape[0]

def KS2(a1, a2):
    if len(a1)==0 or len(a2)==0 :
        return np.nan
    else :
        return ks_2samp(a1, a2)[0]


def logNpow_switch(x, xmax, u2, du2, c2cum, c2, discrete=False, fit_by='cdf'):
    from lib.conf.pars.pars import ParDict
    xmids = u2[1:-int(len(u2) / 3)][::2]
    overlaps = np.linspace(0, 1, 6)
    temp = np.ones([len(xmids), len(overlaps)])
    for i, xmid in enumerate(xmids):
        for j, ov in enumerate(overlaps):
            mm, ss, aa, r = get_logNpow(x, xmax, xmid, discrete=discrete, overlap=ov)
            lp_cdf = 1 - ParDict.dist_dict['logNpow']['cdf'](u2, mm, ss, aa, xmid, r)
            lp_pdf = ParDict.dist_dict['logNpow']['pdf'](du2, mm, ss, aa, xmid, r)
            if fit_by == 'cdf':
                temp[i, j] = MSE(c2cum, lp_cdf)
            elif fit_by == 'pdf':
                temp[i, j] = MSE(c2, lp_pdf)

    if all(np.isnan(temp.flatten())):
        return np.nan, np.nan
    else:
        ii, jj = np.unravel_index(np.nanargmin(temp), temp.shape)
        return xmids[ii], overlaps[jj]


def fit_bouts(c, aux_dic=None,chunk_dicts=None,  s=None, e=None, dataset=None,id=None, store=False):
    from lib.model.modules.intermitter import get_EEB_poly1d
    if id is None:
        id = c.id

    if aux_dic is None :
        if chunk_dicts is not None :
            from lib.aux.dictsNlists import chunk_dicts_to_aux_dict
            aux_dic=chunk_dicts_to_aux_dict(chunk_dicts,c)
        else :
            for k in ['run_count', 'run_dur', 'pause_dur']:
                if dataset is not None:
                    aux_dic[k]=dataset.get_par(k).values
                elif s is not None:
                    aux_dic[k] = s[k].dropna().values
                else :
                    aux_dic[k] = None


    dic, best = {}, {}
    for k, v in aux_dic.items():
        # print(k,v.shape)
        if k=='stridechain_length':
            k='run_count'
        discr = True if k == 'run_count' else False
        if v is not None and v.shape[0]>0 :
            dic[k] = fit_bout_distros(np.abs(v), dataset_id=id, bout=k, combine=False, discrete=discr)
            best[k] = dic[k]['best'][k]['best']
        else:
            dic[k] = None
            best[k] = None

    c.bout_distros = dNl.NestDict(best)

    dic = dNl.NestDict(dic)
    if store:
        path=c.dir_dict.pooled_epochs
        os.makedirs(path, exist_ok=True)
        dNl.save_dict(dic, f'{path}/{id}.txt', use_pickle=True)
        print('Pooled group bouts saved')
    # return dic

    try:
        c.intermitter = {
            nam.freq('crawl'): e[nam.freq(nam.scal(nam.vel('')))].mean(),
            nam.freq('feed'): e[nam.freq('feed')].mean() if nam.freq('feed') in e.columns else 2.0,
            'dt': c.dt,
            'crawl_bouts': True,
            'feed_bouts': True,
            'stridechain_dist': c.bout_distros.run_count,
            'pause_dist': c.bout_distros.pause_dur,
            'run_dist': c.bout_distros.run_dur,
            'feeder_reoccurence_rate': None,
        }
        c['EEB_poly1d'] = get_EEB_poly1d(**c.intermitter).c.tolist()
    except :
        pass
    return dic


def fit_bout_distros(x0, xmin=None, xmax=None, discrete=False, xmid=np.nan, overlap=0.0, Nbins=64, print_fits=False,
                     dataset_id='dataset', bout='pause', combine=True, fit_by='pdf', eval_func_id='KS2'):
    from lib.conf.pars.pars import ParDict
    from lib.aux.stdout import suppress_stdout
    eval_func_dic={
        'MSE':MSE,
        'KS':KS,
        'KS2':KS2,
    }
    eval_func=eval_func_dic[eval_func_id]

    if xmin is None :
        xmin=np.nanmin(x0)
    if xmax is None :
        xmax=np.nanmax(x0)
    with suppress_stdout(True):
        warnings.filterwarnings('ignore')
        x = x0[x0 >= xmin]
        x = x[x <= xmax]

        u2, du2, c2, c2cum = compute_density(x, xmin, xmax, Nbins=Nbins)
        values = [u2, du2, c2, c2cum]

        a2 = 1 + len(x) / np.sum(np.log(x / xmin))
        a = get_powerlaw_alpha(x, xmin, xmax, discrete=discrete)
        p_cdf = 1 - ParDict.dist_dict['powerlaw']['cdf'](u2, xmin, a)
        p_pdf = ParDict.dist_dict['powerlaw']['pdf'](du2, xmin, a)

        b = get_exp_beta(x, xmin)
        e_cdf = 1 - ParDict.dist_dict['exponential']['cdf'](u2, xmin, b)
        e_pdf = ParDict.dist_dict['exponential']['pdf'](du2, xmin, b)

        m, s = get_lognormal(x)
        l_cdf = 1 - ParDict.dist_dict['lognormal']['cdf'](u2, m, s)
        l_pdf = ParDict.dist_dict['lognormal']['pdf'](du2, m, s)

        m_lev, s_lev = levy.fit(x)
        lev_cdf = 1 - ParDict.dist_dict['levy']['cdf'](u2, m_lev, s_lev)
        lev_pdf = ParDict.dist_dict['levy']['pdf'](du2, m_lev, s_lev)

        m_nor, s_nor = norm.fit(x)
        nor_cdf = 1 - ParDict.dist_dict['normal']['cdf'](u2, m_nor, s_nor)
        nor_pdf = ParDict.dist_dict['normal']['pdf'](du2, m_nor, s_nor)

        uni_cdf = 1 - ParDict.dist_dict['uniform']['cdf'](u2, xmin, xmin + xmax)
        uni_pdf = ParDict.dist_dict['uniform']['pdf'](du2, xmin, xmin + xmax)

        if np.isnan(xmid) and combine:
            xmid, overlap = logNpow_switch(x, xmax, u2, du2, c2cum, c2, discrete, fit_by)

        if not np.isnan(xmid):
            mm, ss, aa, r = get_logNpow(x, xmax, xmid, discrete=discrete, overlap=overlap)
            lp_cdf = 1 - ParDict.dist_dict['logNpow']['cdf'](u2, mm, ss, aa, xmid, r)
            lp_pdf = ParDict.dist_dict['logNpow']['pdf'](du2, mm, ss, aa, xmid, r)
        else:
            mm, ss, aa, r = np.nan, np.nan, np.nan, np.nan
            lp_cdf, lp_pdf = None, None

        if fit_by == 'cdf':
            KS_pow = eval_func(c2cum, p_cdf)
            KS_exp = eval_func(c2cum, e_cdf)
            KS_logn = eval_func(c2cum, l_cdf)
            KS_lognNpow = eval_func(c2cum, lp_cdf) if lp_cdf is not None else np.nan
            KS_lev = eval_func(c2cum, lev_cdf)
            KS_norm = eval_func(c2cum, nor_cdf)
            KS_uni = eval_func(c2cum, uni_cdf)
        elif fit_by == 'pdf':
            KS_pow = eval_func(c2, p_pdf)
            KS_exp = eval_func(c2, e_pdf)
            KS_logn = eval_func(c2, l_pdf)
            KS_lognNpow = eval_func(c2, lp_pdf) if lp_pdf is not None else np.nan
            KS_lev = eval_func(c2, lev_pdf)
            KS_norm = eval_func(c2, nor_pdf)
            KS_uni = eval_func(c2, uni_pdf)

        Ks = np.array([KS_pow, KS_exp, KS_logn, KS_lognNpow, KS_lev, KS_norm, KS_uni])
        idx_Kmax = np.nanargmin(Ks)

        res = np.round(
            [a, KS_pow, b, KS_exp, m, s, KS_logn, mm, ss, aa, xmid, r, overlap, KS_lognNpow, m_lev, s_lev, KS_lev,
             m_nor, s_nor, KS_norm, KS_uni, xmin, xmax], 5)
        pdfs = [p_pdf, e_pdf, l_pdf, lp_pdf, lev_pdf, nor_pdf, uni_pdf]
        cdfs = [p_cdf, e_cdf, l_cdf, lp_cdf, lev_cdf, nor_cdf, uni_cdf]
    p = bout

    names = [f'alpha_{p}', f'KS_pow_{p}',
             f'beta_{p}', f'KS_exp_{p}',
             f'mu_log_{p}', f'sigma_log_{p}', f'KS_log_{p}',
             f'mu_logNpow_{p}', f'sigma_logNpow_{p}', f'alpha_logNpow_{p}', f'switch_logNpow_{p}', f'ratio_logNpow_{p}',
             f'overlap_logNpow_{p}', f'KS_logNpow_{p}',
             f'mu_levy_{p}', f'sigma_levy_{p}', f'KS_levy_{p}',
             f'mu_norm_{p}', f'sigma_norm_{p}', f'KS_norm_{p}',
             f'KS_uni_{p}',
             f'min_{p}', f'max_{p}']
    res_dict = dict(zip(names, res))

    names2 = ['alpha', 'KS_pow',
              'beta', 'KS_exp',
              'mu_log', 'sigma_log', 'KS_log',
              'mu_logNpow', 'sigma_logNpow', 'alpha_logNpow', 'switch_logNpow', 'ratio_logNpow',
              'overlap_logNpow', 'KS_logNpow',
              f'mu_levy', f'sigma_levy', f'KS_levy',
              f'mu_norm', f'sigma_norm', f'KS_norm',
              f'KS_uni',
              'xmin', 'xmax']
    res_dict2 = dict(zip(names2, res))
    best = {bout: {'best': get_best_distro(p, res_dict, idx_Kmax=idx_Kmax),
                   'fits': res_dict2}}

    if print_fits:
        print()
        print(f'-----{dataset_id}-{bout}----------')
        print(f'initial range : {np.min(x0)} - {np.max(x0)}, Nbouts : {len(x0)}')
        print(f'accepted range : {xmin} - {xmax}, Nbouts : {len(x)}')
        print("powerlaw exponent MLE:", a2)
        print("powerlaw exponent powerlaw package:", a)
        print("exponential exponent MLE:", b)
        print("lognormal mean,std:", m, s)
        print("lognormal-powerlaw mean,std, alpha, switch, ratio, overlap :", mm, ss, aa, xmid, r, overlap)
        print("levy loc,scale:", m_lev, s_lev)
        print("normal loc,scale:", m_nor, s_nor)
        print('MSE pow', KS_pow)
        print('MSE exp', KS_exp)
        print('MSE logn', KS_logn)
        print('MSE lognNpow', KS_lognNpow)
        print('MSE levy', KS_lev)
        print('MSE normal', KS_norm)
        print('MSE uniform', KS_uni)

        print()
        print(f'---{dataset_id}-{bout}-distro')
        print(best)
        print()

    dic = {
        'values': values, 'pdfs': pdfs, 'cdfs': cdfs, 'Ks': Ks, 'idx_Kmax': idx_Kmax, 'res': res, 'res_dict': res_dict,
        'best': best
    }
    return dic


def get_best_distro(bout, f, idx_Kmax=None):
    k = bout
    r = (f[f'min_{k}'], f[f'max_{k}'])
    if idx_Kmax is None:
        idx_Kmax = np.argmin([f[f'KS_{d}_{k}'] for d in ['pow', 'exp', 'log', 'logNpow', 'levy', 'norm', 'uni']])
    if idx_Kmax == 0:
        distro = {'range': r,
                  'name': 'powerlaw',
                  'alpha': f[f'alpha_{k}']}
    elif idx_Kmax == 1:
        distro = {'range': r,
                  'name': 'exponential',
                  'beta': f[f'beta_{k}']}
    elif idx_Kmax == 2:
        distro = {'range': r,
                  'name': 'lognormal',
                  'mu': f[f'mu_log_{k}'],
                  'sigma': f[f'sigma_log_{k}']}
    elif idx_Kmax == 3:
        n = 'logNpow'
        distro = {'range': r,
                  'name': n,
                  'mu': f[f'mu_{n}_{k}'],
                  'sigma': f[f'sigma_{n}_{k}'],
                  'alpha': f[f'alpha_{n}_{k}'],
                  'switch': f[f'switch_{n}_{k}'],
                  'ratio': f[f'ratio_{n}_{k}'],
                  'overlap': f[f'overlap_{n}_{k}'],
                  }
    elif idx_Kmax == 4:
        distro = {'range': r,
                  'name': 'levy',
                  'mu': f[f'mu_levy_{k}'],
                  'sigma': f[f'sigma_levy_{k}']}
    elif idx_Kmax == 5:
        distro = {'range': r,
                  'name': 'normal',
                  'mu': f[f'mu_norm_{k}'],
                  'sigma': f[f'sigma_norm_{k}']}
    elif idx_Kmax == 6:
        distro = {'range': r,
                  'name': 'uniform'}
    return distro


def pvalue_star(pv):
    a = {1e-4: "****", 1e-3: "***",
         1e-2: "**", 0.05: "*", 1: "ns"}
    for k, v in a.items():
        if pv < k:
            return v
    return "ns"

#
# def fit2d_matrix(x, N):
#     degrees = [(i, j) for i in range(N) for j in range(N)]  # list of monomials x**i * y**j to use
#     matrix = np.stack([np.prod(x ** d, axis=1) for d in degrees], axis=-1)  # stack monomials like columns
#     return matrix
#
# def fit2d_coeff(df, vars, target,N=3, show=True):
#     x = df[vars].values
#     z = df[target].values
#     matrix = fit2d_matrix(x, N)
#     coeff = np.linalg.lstsq(matrix, z, rcond=None)[0]  # lstsq returns some additional info we ignore
#     fit = np.dot(matrix, coeff)
#     if show:
#         from lib.plot.dataplot import plot_3d, plot_surface
#         import matplotlib.pyplot as plt
#         plot_3d(df, vars=vars, target=target, show=show, surface=True)
#         plt.plot(fit, color='red', label='fitted')
#         plt.plot(z, color='green', label='original')
#         plt.legend()
#         plt.show()
#     return coeff
#
#
# def fit2d_predict(coeff, ranges,  Ngrid=100, target=None,vars=None,  show=True):
#     (r00, r01), (r10, r11) = ranges
#     y0 = np.linspace(r00, r01, Ngrid)
#     y1 = np.linspace(r10, r11, Ngrid)
#     yy0, yy1 = np.meshgrid(y0, y1)
#     yy0f, yy1f = np.array(yy0).flatten(), np.array(yy1).flatten()
#     x = np.stack((yy0f, yy1f), axis=-1)
#     N = int(np.sqrt(len(coeff)))
#     matrix = fit2d_matrix(x, N)
#     predict = np.dot(matrix, coeff)
#     if show:
#         import matplotlib.pyplot as plt
#         from lib.plot.dataplot import plot_3d, plot_surface
#         z0 = predict.reshape(yy0.shape)
#         fig3 = plot_surface(yy0, yy1, z0, vars=vars, target=target, show=show)

def critical_bout(c=0.9, sigma=1, N=1000, tmax=1100, tmin=1) :
    t = 0
    S = 1
    S_prev = 0
    while S > 0:
        p = (sigma * S - c * (S - S_prev)) / N
        p = np.clip(p, 0, 1)
        S_prev = S
        S = np.random.binomial(N, p)
        t += 1
        if t > tmax:
            t = 0
            S = 1
            S_prev = 0
        if S<=0 and t<tmin :
            t = 0
            S = 1
            S_prev = 0
    return t

def exp_bout(beta=0.01, tmax=1100, tmin=1) :
    t = 0
    S = 0
    while S <= 0:
        S = int(np.random.rand() < beta)
        t += 1
        if t > tmax:
            t = 0
            S = 0
        if S>0 and t<tmin :
            t = 0
            S = 0
    return t

class BoutGenerator:
    def __init__(self, name, range, dt, **kwargs):
        from lib.conf.pars.pars import ParDict
        self.name = name
        self.dt = dt
        self.range = range
        self.ddfs = ParDict.dist_dict
        self.xmin, self.xmax = range
        kwargs.update({'xmin': self.xmin, 'xmax': self.xmax})
        self.args = {a: kwargs[a] for a in self.ddfs[self.name]['args']}

        self.dist = self.build(**self.args)

    def sample(self, size=1):
        vs = self.dist.rvs(size=size) * self.dt
        return vs[0] if size == 1 else vs

    def build(self, **kwargs):
        x0, x1 = int(self.xmin / self.dt), int(self.xmax / self.dt)
        xx = np.arange(x0, x1 + 1)
        pmf = self.ddfs[self.name]['pdf'](xx * self.dt, **kwargs)
        mask = ~np.isnan(pmf)
        pmf = pmf[mask]
        xx = xx[mask]
        pmf /= pmf.sum()
        return rv_discrete(values=(xx, pmf))

    def get(self, x, mode):
        func = self.ddfs[self.name][mode]
        return func(x=x, **self.args)


def test_boutGens(mID,refID, **kwargs):
    from lib.conf.stored.conf import loadConf, loadRef
    from lib.plot.epochs import plot_bouts
    from lib.aux.sim_aux import get_sample_bout_distros

    d = loadRef(refID)
    d.load(contour=False)
    s, e, c = d.step_data, d.endpoint_data, d.config
    Npau=s['pause_dur'].dropna().values.shape[0]
    Nrun=s['run_dur'].dropna().values.shape[0]

    dic={}
    m=loadConf(mID, 'Model')
    m=get_sample_bout_distros(m, loadConf(refID, 'Ref'))
    dicM=m.brain.intermitter_params
    for n,n0 in zip(['pause', 'run', 'stridechain'], ['pause_dur', 'run_dur', 'run_count']) :
        N=Npau if n == 'pause' else Nrun
        discr = True if n == 'stridechain' else False
        dt = 1 if n == 'stridechain' else c.dt

        k=f'{n}_dist'
        kk=dicM[k]
        if kk is not None :
            B = BoutGenerator(**kk, dt=dt)
            vs = B.sample(N)
            dic[n0] = fit_bout_distros(vs, dataset_id=mID, bout=n, combine=False, discrete=discr)
    datasets=[{'id' : 'model', 'pooled_epochs': dic, 'color': 'blue'}, {'id' : 'experiment', 'pooled_epochs': d.load_pooled_epochs(), 'color': 'red'}]
    datasets = [dNl.NestDict(dd) for dd in datasets]
    # print(datasets)
    return datasets
    # return plot_bouts(datasets=datasets, plot_fits='none', **kwargs)

