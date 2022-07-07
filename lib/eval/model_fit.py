import copy
import os

import numpy as np
import pandas as pd
import param


from lib.aux import dictsNlists as dNl

from lib.model.body.controller import PhysicsController

from lib.registry.pars import preg


class Calibration:
    def __init__(self, refID, turner_mode='neural', physics_keys=None, absolute=True, shorts=None):
        self.refID = refID
        self.refDataset = d = preg.loadRef(refID)
        d.load(contour=False)
        s, e, c = d.step_data, d.endpoint_data, d.config
        if shorts is None:
            shorts = ['b', 'fov', 'foa', 'tur_t', 'tur_fou']
        self.shorts = shorts
        self.target = {sh: d.get_chunk_par(chunk='pause', short=sh, min_dur=3, mode='distro') for sh in self.shorts}
        self.N = self.target[self.shorts[0]].shape[0]
        self.dt = c.dt


        if physics_keys is None:
            physics_keys = []
        if turner_mode == 'neural':
            turner_keys = ['base_activation', 'n', 'tau']
        elif turner_mode == 'sinusoidal':
            turner_keys = ['initial_amp', 'initial_freq']
        elif turner_mode == 'constant':
            turner_keys = ['initial_amp']

        self.mkeys = dNl.NestDict({
            'turner': turner_keys,
            'physics': physics_keys,
            'all' : physics_keys+turner_keys
        })

        self.D = preg.larva_conf_dict2
        self.mdicts = dNl.NestDict({
            'turner': self.D.dict.model.m['turner'].mode[turner_mode].args,
            'physics': self.D.dict.model.m['physics'].args
        })
        self.mconfs = dNl.NestDict({
            'turner': None,
            'physics': None
        })

        init, bounds=[],[]
        for k in self.mkeys.turner :
            p=self.mdicts.turner[k]
            init.append(p.v)
            bounds.append(p.lim)
        for k in self.mkeys.physics :
            p=self.mdicts.physics[k]
            init.append(p.v)
            bounds.append(p.lim)
        self.init=np.array(init)
        self.bounds=bounds

        self.Tfunc=self.D.dict.model.m['turner'].mode[turner_mode].class_func
        self.turner_mode = turner_mode
        self.absolute = absolute

        self.best = None
        self.KS_dic = None

    # def build_modelConf(self, new_id=None, **kwargs):
    #     if new_id is None:
    #         new_id = f'fitted_{self.turner_mode}_turner'
    #     m = self.refDataset.average_modelConf(new_id=new_id, **self.best, **kwargs)
    #     return {new_id: m}

    # def plot_turner_distros(self, sim, fig=None, axs=None, in_deg=False, **kwargs):
    #     Nps = len(self.shorts)
    #     P = BasePlot(name='turner_distros', **kwargs)
    #     P.build(Ncols=Nps, fig=fig, axs=axs, figsize=(5 * Nps, 5), sharey=True)
    #     for i, sh in enumerate(self.shorts):
    #         p, lab = preg.getPar(sh, to_return=['d', 'lab'])
    #         vs = self.target[sh]
    #         if in_deg:
    #             vs = np.rad2deg(vs)
    #         lim = np.nanquantile(vs, 0.99)
    #         bins = np.linspace(-lim, lim, 100)
    #
    #         ws = np.ones_like(vs) / float(len(vs))
    #         P.axs[i].hist(vs, weights=ws, label='experiment', bins=bins, color='red', alpha=0.5)
    #
    #         vs0 = sim[sh]
    #         if in_deg:
    #             vs0 = np.rad2deg(vs0)
    #         ws0 = np.ones_like(vs0) / float(len(vs0))
    #         P.axs[i].hist(vs0, weights=ws0, label='model', bins=bins, color='blue', alpha=0.5)
    #         P.conf_ax(i, ylab='probability' if i == 0 else None, xlab=lab,
    #                   xMaxN=4, yMaxN=4, leg_loc='upper left' if i == 0 else None)
    #     P.adjust(LR=(0.1, 0.95), BT=(0.15, 0.95), W=0.01, H=0.1)
    #     return P.get()

    def sim_turner(self, N=2000):
        from lib.aux.ang_aux import wrap_angle_to_0
        T = self.Tfunc(**self.mconfs.turner, dt=self.dt)
        PH = PhysicsController(**self.mconfs.physics)
        simFOV = np.zeros(N) * np.nan
        simB = np.zeros(N) * np.nan
        b = 0
        fov = 0
        for i in range(N):
            ang = T.step(0)
            fov = PH.compute_ang_vel(torque=PH.torque_coef * ang,v=fov, b=b,
                                           c=PH.ang_damping, k=PH.body_spring_k, dt=T.dt)
            b = wrap_angle_to_0(b + fov * self.dt)
            simFOV[i] = fov
            simB[i] = b

        simB = np.rad2deg(simB)
        simFOV = np.rad2deg(simFOV)
        simFOA = np.diff(simFOV, prepend=[0]) / self.dt

        if 'tur_t' in self.shorts or 'tur_fou' in self.shorts:
            from lib.process.aux import detect_turns, process_epochs

            Lturns, Rturns = detect_turns(pd.Series(simFOV), self.dt)
            Ldurs, Lamps, Lmaxs = process_epochs(simFOV, Lturns, self.dt, return_idx=False)
            Rdurs, Ramps, Rmaxs = process_epochs(simFOV, Rturns, self.dt, return_idx=False)
            Tamps = np.concatenate([Lamps, Ramps])
            Tdurs = np.concatenate([Ldurs, Rdurs])

            sim = {'b': simB, 'fov': simFOV, 'foa': simFOA, 'tur_t': Tdurs, 'tur_fou': Tamps}

        else:
            sim = {'b': simB, 'fov': simFOV, 'foa': simFOA}
        return sim

    def eval_turner(self, sim):
        from scipy.stats import ks_2samp

        if not self.absolute:
            Ks_dic = {sh: np.round(ks_2samp(self.target[sh], sim[sh])[0], 3) for sh in self.shorts}
        else:
            Ks_dic = {sh: np.round(ks_2samp(np.abs(self.target[sh]), np.abs(sim[sh]))[0], 3) for sh in self.shorts}
        err = np.sum(list(Ks_dic.values()))
        return err, Ks_dic

    def retrieve_modules(self, q, Ndec=None):
        if Ndec is not None:
            q=[np.round(q0,Ndec) for q0 in q]
        dic = dNl.NestDict({k:q0 for k,q0 in zip(self.mkeys.all, q)})


        for k,mdict in self.mdicts.items() :
            kwargs= {kk : dic[kk] for kk in self.mkeys[k]}
            self.mconfs[k]=self.D.conf(mdict=mdict,**kwargs)
        # return mconfs

    def optimize_turner(self, q=None, return_sim=False, N=2000):
        self.retrieve_modules(q)
        sim = self.sim_turner(N=N)
        if return_sim:
            return sim
        else:
            err, Ks_dic = self.eval_turner(sim)
            # print(err)
            return err

    def run(self, method='Nelder-Mead', **kwargs):
        from scipy.optimize import minimize

        # print(f'Calibrating parameters {list(self.space_dict.keys())}')
        # bnds = [(dic['min'], dic['max']) for k, dic in self.space_dict.items()]
        # init = np.array([dic['initial_value'] for k, dic in self.space_dict.items()])

        # print(bnds)
        # print(self.init)
        # print(self.bounds)
        # raise
        res = minimize(self.optimize_turner, self.init, method=method, bounds=self.bounds, **kwargs)
        self.best, self.KS_dic = self.eval_best(q=res.x)
        # self.best, self.KS_dic = self.plot_turner(q=res.x)
    #
    def eval_best(self,q):
        self.retrieve_modules(q, Ndec=2)
        sim = self.sim_turner(N=self.N)
        err, Ks_dic = self.eval_turner(sim)
        best = self.mconfs
        return best, Ks_dic


#
def epar(e, k=None, par=None, average=True):
    if par is None:
        D = preg.dict
        par = D[k].d
    vs = e[par]
    if average:
        return np.round(vs.median(), 2)
    else:
        return vs


def adapt_crawler(ee, mode='realistic', average=True):
    # print(ee.columns.values[:40])
    # raise
    # D = preg.larva_conf_dict
    mdict=preg.larva_conf_dict.dict2.model.m['crawler'].mode[mode].args
    conf0 = dNl.NestDict({'mode':mode})
    for d, p in mdict.items():
        print(d,p.codename)
        if isinstance(p, param.Parameterized):
            conf0[d] = epar(ee, par=p.codename, average=average)
        else:
            raise

    return conf0


def adapt_intermitter(c, e, **kwargs):
    intermitter = preg.get_null('intermitter')
    intermitter.stridechain_dist = c.bout_distros.run_count
    try:
        ll1, ll2 = intermitter.stridechain_dist.range
        intermitter.stridechain_dist.range = (int(ll1), int(ll2))
    except:
        pass

    intermitter.run_dist = c.bout_distros.run_dur
    try:
        ll1, ll2 = intermitter.run_dist.range
        intermitter.run_dist.range = (np.round(ll1, 2), np.round(ll2, 2))
    except:
        pass
    intermitter.pause_dist = c.bout_distros.pause_dur
    try:
        ll1, ll2 = intermitter.pause_dist.range
        intermitter.pause_dist.range = (np.round(ll1, 2), np.round(ll2, 2))
    except:
        pass
    intermitter.crawl_freq = epar(e, 'fsv', average=True)
    return intermitter


def optimize_mID_turnerNinterference(mID0,  refID, mID1=None, **kwargs) :
    if mID1 is None :
        mID1=mID0
    from lib.anal.argparsers import adjust_sim
    from lib.ga.util.ga_launcher import GAlauncher
    conf = preg.expandConf(id='realism', conftype='Ga')
    conf.show_screen = False
    conf.ga_select_kws.Pmutation = 0.3
    conf.ga_select_kws.Cmutation = 0.3
    conf.ga_select_kws.Ngenerations = 10
    conf.ga_select_kws.Nagents = 10
    conf.ga_select_kws.Nelit = 2
    conf.ga_build_kws.base_model =mID0
    conf.ga_build_kws.fitness_target_refID =refID
    conf.ga_build_kws.bestConfID = mID1
    conf.sim_params = adjust_sim(exp=conf.experiment, conf_type='Ga', sim=conf.sim_params)
    conf.sim_params.duration = 0.5
    conf.update(kwargs)
    GA = GAlauncher(**conf)
    best_genome = GA.run()
    entry={mID1:best_genome.mConf}
    return entry

