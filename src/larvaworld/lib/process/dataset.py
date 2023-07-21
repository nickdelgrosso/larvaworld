import os
import shutil
import numpy as np
import pandas as pd
import warnings

import param

from larvaworld.lib import reg, aux


class BaseLarvaDataset:

    @staticmethod
    def initGeo(to_Geo=False,**kwargs):
        if to_Geo:
            try:
                from larvaworld.lib.process.larva_trajectory_collection import LarvaTrajectoryCollection
                return LarvaTrajectoryCollection(**kwargs)
            except :
                pass
            # from larvaworld.lib.process.dataset import LarvaDataset
        return LarvaDataset(**kwargs)





    def __init__(self, dir=None, config=None, refID=None,load_data=True,step=None, end=None,agents=None, **kwargs):
        '''
        Dataset class that stores a single experiment, real or simulated.
        Metadata and configuration parameters are stored in the 'config' dictionary.
        This can be provided as an argument, retrieved from a stored experiment or generated for a new experiment.

        The default pipeline goes as follows :
        The dataset needs the config file to be initialized. If it is not provided as an argument there are two ways to retrieve it.
        First if "dir" is an existing directory of a stored dataset the config file will be loaded from the default location
        within the dataset's file structure, specifically from a "conf.txt" in the "data" directory under the root "dir".
        As it is not handy to provide an absolute directory as an argument, the root "dir" locations of a number of stored "reference" datasets
        are stored in a file and loaded as a dictionary where the keys are unique "refID" strings holding the root "dir" value.

        Accessing the reference path dictionary is extremely easy through the "reg.stored" registry class with the following methods :
        -   getRefDir(id) returns the "root" directory stored in the "larvaworld/lib/reg/confDicts/Ref.txt" under the unique id
        -   getRef(id=None, dir=None) returns the config dictionary stored at the "root" directory. Accepts either the "dir" path or the "refID" id
        -   loadRef(id) first retrieves the config dictionary and then initializes the dataset.
            By setting load_data=True there is an attempt to load the data from the disc if found at the provided root directory.
            This last method can be accessed directly via "reg.loadRef(id)"

        In the case that none of the above attempts yielded a config dictionary, a novel one is generated using any additional keyword arguments are provided.
        This is the default way that a new dataset is initialized. The data content is set after initialization via the "set_data(step, end)"
        method with which we provide the both the step-wise timeseries and the endpoint single-per-agent measurements

        Endpoint measurements are loaded always as a pd.Dataframe 'endpoint_data' with 'AgentID' indexing

        The timeseries data though can be initialized and processed in two ways :
        -   in the default mode  a pd.Dataframe 'step_data' with a 2-level index : 'Step' for the timestep index and 'AgentID' for the agent unique ID.
            Data is stored as a single HDF5 file or as nested dictionaries. The core file is 'data.h5' with keys like 'step' for timeseries and 'end' for endpoint metrics.
        -   in the trajectory mode a "movingpandas.TrajectoryCollection" is adjusted to the needs of the larva-tracking data format via the
            "lib.process.LarvaTrajectoryCollection" class

        Args:
            dir: Path to stored data. Ignored if 'config' is provided. Defaults to None for no storage to disc
            load_data: Whether to load stored data
            config: The metadata dictionary. Defaults to None for attempting to load it from disc or generate a new.
            **kwargs: Any arguments to store in a novel configuration dictionary
        '''

        if config is None:
            config = reg.getRef(dir=dir, id=refID)
            if config is None:
                config = self.generate_config(dir=dir, refID=refID, **kwargs)

        c = self.config = config
        if c.dir is not None:
            os.makedirs(c.dir, exist_ok=True)
            os.makedirs(self.data_dir, exist_ok=True)
        self.__dict__.update(c)
        self.epoch_dict = aux.AttrDict({'pause': None, 'run': None})
        self.larva_dicts = {}
        self.h5_kdic = aux.h5_kdic(c.point, c.Npoints, c.Ncontour)
        if load_data:
            self.load()
        elif step is not None or end is not None:
            self.set_data(step=step, end=end, agents=agents)



    def set_data(self, step=None, end=None,**kwargs):
        pass

    def generate_config(self, **kwargs):
        c0 = aux.AttrDict({'id': 'unnamed',
                           'group_id': None,
                           'refID': None,
                           'dir': None,
                           'fr': None,
                           'dt': None,
                           'Npoints': 3,
                           'Ncontour': 0,
                           'u' : 'm',
                           'x': 'x',
                           'y': 'y',
                           'sample': None,
                           'color': None,
                           'metric_definition': None,
                           'env_params': {},
                           'larva_groups': {},
                           'source_xy': {},
                           'life_history': None,
                           })

        c0.update(kwargs)
        if c0.dt is not None :
            c0.fr=1/c0.dt
        if c0.fr is not None :
            c0.dt=1/c0.fr
        if c0.metric_definition is None:
            c0.metric_definition = reg.get_null('metric_definition')

        points = aux.nam.midline(c0.Npoints, type='point')

        try:
            c0.point = points[c0.metric_definition.spatial.point_idx - 1]
        except:
            c0.point = 'centroid'

        if len(c0.larva_groups) == 1:
            c0.group_id, gConf = list(c0.larva_groups.items())[0]
            c0.color = gConf['default_color']
            c0.sample = gConf['sample']
            c0.model = gConf['model']
            c0.life_history = gConf['life_history']

        reg.vprint(f'Generated new conf {c0.id}', 1)
        return c0

    @property
    def data_dir(self):
        return f'{self.config.dir}/data'

    @property
    def plot_dir(self):
        return f'{self.config.dir}/plots'

    def save_config(self, refID=None):
        c = self.config
        if refID is not None:
            c.refID = refID
        if c.refID is not None:
            reg.conf.Ref.setID(c.refID, c.dir)
            reg.vprint(f'Saved reference dataset under : {c.refID}', 1)
        for k, v in c.items():
            if isinstance(v, np.ndarray):
                c[k] = v.tolist()
        aux.save_dict(c, f'{self.data_dir}/conf.txt')

    @property
    def Nangles(self):
        return np.clip(self.config.Npoints - 2, a_min=0, a_max=None)

    @property
    def points(self):
        return aux.nam.midline(self.config.Npoints, type='point')

    @property
    def contour(self):
        return aux.nam.contour(self.config.Ncontour)

    def delete(self):
        shutil.rmtree(self.config.dir)
        reg.vprint(f'Dataset {self.id} deleted',2)

    def set_id(self, id, save=True):
        self.id = id
        self.config.id = id
        if save:
            self.save_config()

    def set_endpoint_data(self,end):
        self.endpoint_data = end.sort_index()
        self.agent_ids = self.endpoint_data.index.values
        self.config.agent_ids = self.agent_ids
        self.config.N = len(self.agent_ids)

    def load(self, **kwargs):
        pass

class LarvaDataset(BaseLarvaDataset):
    def __init__(self, **kwargs):
        '''
        This is the default dataset class. Timeseries are stored as a pd.Dataframe 'step_data' with a 2-level index : 'Step' for the timestep index and 'AgentID' for the agent unique ID.
        Data is stored as a single HDF5 file or as nested dictionaries. The core file is 'data.h5' with keys like 'step' for timeseries and 'end' for endpoint metrics.
        To lesser the burdain of loading and saving all timeseries parameters as columns in a single pd.Dataframe, the most common parameters have been split in a set of groupings,
         available via keys that access specific entries of the "data.h5". The keys of "self.h5_kdic" dictionary store the parameters that every "h5key" keeps :
        -   'contour': The contour xy coordinates,
        -   'midline': The midline xy coordinates,
        -   'epochs': The behavioral epoch detection and annotation,
        -   'base_spatial': The most basic spatial parameters,
        -   'angular': The angular parameters,
        -   'dspNtor':  Dispersal and tortuosity,

        All parameters not included in any of these groups stays with the original "step" key that is always saved and loaded
        '''
        super().__init__(**kwargs)






    def set_data(self, step=None, end=None, agents=None):
        c=self.config
        if step is not None:
            assert step.index.names == ['Step', 'AgentID']
            s = step.sort_index(level=['Step', 'AgentID'])
            self.Nticks = s.index.unique('Step').size
            c.t0 = int(s.index.unique('Step')[0])
            c.Nticks = self.Nticks
            if 'duration' not in c.keys():
                c.duration = c.dt * c.Nticks
            if 'quality' not in c.keys():
                try:
                    df = s[aux.nam.xy(c.point)[0]].values.flatten()
                    valid = np.count_nonzero(~np.isnan(df))
                    c.quality = np.round(valid / df.shape[0], 2)
                except:
                    pass

            self.step_data = s

        if end is not None:
            self.set_endpoint_data(end)

        if agents is not None :
            self.larva_dicts = aux.get_larva_dicts(agents, validIDs=self.agent_ids)


    def _load_step(self, h5_ks=None):
        s = self.read('step')
        if h5_ks is None :
            h5_ks=list(self.h5_kdic.keys())
        for h5_k in h5_ks:
            ss = self.read(h5_k)
            if ss is not None :
                ps = aux.nonexisting_cols(ss.columns.values,s)
                if len(ps) > 0:
                    s = s.join(ss[ps])
        return s


    def load(self, step=True, h5_ks=None):
        s = self._load_step(h5_ks=h5_ks) if step else None
        e = self.read('end')
        self.set_data(step=s, end=e)


    def _save_step(self, s):
        s = s.loc[:, ~s.columns.duplicated()]
        stored_ps = []
        for h5_k,ps in self.h5_kdic.items():
            pps = aux.unique_list(aux.existing_cols(ps,s))
            if len(pps) > 0:
                self.store(s[pps], h5_k)
                stored_ps += pps

        self.store(s.drop(stored_ps, axis=1, errors='ignore'), 'step')

    def save(self, refID=None):
        if hasattr(self, 'step_data'):
            self._save_step(s=self.step_data)
        if hasattr(self, 'endpoint_data'):
            self.store(self.endpoint_data, 'end')
        self.save_config(refID=refID)
        reg.vprint(f'***** Dataset {self.id} stored.-----', 1)

    def store(self, df, key, file='data'):
        path=f'{self.data_dir}/{file}.h5'
        if not isinstance(df, pd.DataFrame):
            pd.DataFrame(df).to_hdf(path, key)
        else :
            df.to_hdf(path, key)


    def read(self, key, file='data'):
        path=f'{self.data_dir}/{file}.h5'
        try :
            return pd.read_hdf(path, key)
        except:
            return None




    def load_traj(self, mode='default'):
        key=f'traj.{mode}'
        df = self.read(key)
        if df is None :
            if mode=='default':
                df = self._load_step(h5_ks=[])[['x', 'y']]
            elif mode in ['origin', 'center']:
                s = self._load_step(h5_ks=['contour', 'midline'])
                df=reg.funcs.preprocessing["transposition"](s, c=self.config, replace=False, transposition=mode)[['x', 'y']]
            else :
                raise ValueError('Not implemented')
            self.store(df,key)
        return df



    def load_dicts(self, type, ids=None):
        if ids is None:
            ids = self.agent_ids
        ds0 = self.larva_dicts
        if type in ds0 and all([id in ds0[type].keys() for id in ids]):
            ds = [ds0[type][id] for id in ids]
        else:
            ds= aux.loadSoloDics(agent_ids=ids, path=f'{self.data_dir}/individuals/{type}.txt')
        return ds

    def visualize(self,parameters={}, **kwargs):
        from larvaworld.lib.sim.dataset_replay import ReplayRun
        kwargs['dataset'] = self
        rep = ReplayRun(parameters=parameters, **kwargs)
        rep.run()








    @property
    def data_path(self):
        return f'{self.data_dir}/data.h5'



    def _enrich(self,pre_kws={}, proc_keys=[],anot_keys=[], is_last=True,**kwargs):
        cc = {
            'd': self,
            's': self.step_data,
            'e': self.endpoint_data,
            'c': self.config,
            **kwargs
        }

        warnings.filterwarnings('ignore')
        for k, v in pre_kws.items():
            if v:
                ccc=cc
                ccc[k]=v
                reg.funcs.preprocessing[k](**ccc)
        for k in proc_keys:
            reg.funcs.processing[k](**cc)
        for k in anot_keys:
            reg.funcs.annotating[k](**cc)

        if is_last:
            self.save()
        return self


    def enrich(self, metric_definition=None, preprocessing={}, processing={},annotation={},**kwargs):
        proc_keys=[k for k, v in processing.items() if v]
        anot_keys=[k for k, v in annotation.items() if v]
        # if metric_definition is not None :
        #     self.config.metric_definition.update(metric_definition)
        #     for k in proc_keys :
        #         if k in metric_definition.keys():
        #             kwargs.update(metric_definition[k])
        return self._enrich(pre_kws=preprocessing,proc_keys=proc_keys,
                            anot_keys=anot_keys,**kwargs)






    def get_par(self, par=None, k=None, key='step'):
        if par is None and k is not None:
            par=reg.getPar(k)

        if key == 'end':
            if not hasattr(self, 'endpoint_data'):
                self.load(step=False)
            df=self.endpoint_data

        elif key == 'step':
            if not hasattr(self, 'step_data'):
                self.load()
            df=self.step_data
        else :
            raise

        if par in df.columns :
            return df[par]
        else :
            return reg.par.get(k=k, d=self, compute=True)






    def get_chunk_par(self, chunk, k=None, par=None, min_dur=0, mode='distro'):
        chunk_idx = f'{chunk}_idx'
        chunk_dur = f'{chunk}_dur'
        if par is None:
            par = reg.getPar(k)
            
        dic0 = aux.AttrDict(self.read('chunk_dicts'))

        dics = [dic0[id] for id in self.agent_ids]
        sss = [self.step_data[par].xs(id, level='AgentID') for id in self.agent_ids]

        if mode == 'distro':

            vs = []
            for ss, dic in zip(sss, dics):
                if min_dur == 0:
                    idx = dic[chunk_idx]+self.t0
                else:
                    epochs = dic[chunk][dic[chunk_dur] >= min_dur]
                    Nepochs = epochs.shape[0]
                    if Nepochs == 0:
                        idx = []
                    elif Nepochs == 1:
                        idx = np.arange(epochs[0][0], epochs[0][1] + 1, 1)
                    else:
                        slices = [np.arange(r0, r1 + 1, 1) for r0, r1 in epochs]
                        idx = np.concatenate(slices)
                vs.append(ss.loc[idx].dropna().values)
            vs = np.concatenate(vs)
            return vs
        elif mode == 'extrema':
            cc0s, cc1s, cc01s = [], [], []
            for ss, dic in zip(sss, dics):
                epochs = dic[chunk]
                if min_dur != 0:
                    epochs = epochs[dic[chunk_dur] >= min_dur]
                Nepochs = epochs.shape[0]
                if Nepochs > 0:
                    c0s = ss.loc[epochs[:, 0]].values
                    c1s = ss.loc[epochs[:, 1]].values
                    cc0s.append(c0s)
                    cc1s.append(c1s)
            cc0s = np.concatenate(cc0s)
            cc1s = np.concatenate(cc1s)
            cc01s = cc1s - cc0s
            return cc0s, cc1s, cc01s




    @property
    def data(self):
        s=self.step_data if hasattr(self, 'step_data') else None
        e=self.endpoint_data if hasattr(self, 'endpoint_data') else None
        return s, e, self.config





class LarvaDatasetCollection :
    def __init__(self,labels=None, add_samples=False,config=None,**kwargs):
        datasets = self.get_datasets(**kwargs)

        for d in datasets:
            assert isinstance(d, BaseLarvaDataset)
        if labels is None:
            labels = [d.id for d in datasets]

        if add_samples:
            targetIDs = aux.unique_list([d.config['sample'] for d in datasets])
            targets = [reg.loadRef(id) for id in targetIDs if id in reg.conf.Ref.confIDs]
            datasets += targets
            if labels is not None:
                labels += targetIDs
        self.config = config
        self.datasets = datasets
        self.labels = labels
        self.Ndatasets = len(datasets)
        self.colors = self.get_colors()
        assert self.Ndatasets == len(self.labels)

        self.group_ids = aux.unique_list([d.config['group_id'] for d in self.datasets])
        self.Ngroups = len(self.group_ids)
        self.set_dir()

    def set_dir(self):
        if self.config and 'dir' in self.config :
            self.dir=self.config.dir
        elif self.Ndatasets>1 and self.Ngroups==1:
            dir0=aux.unique_list([os.path.dirname(os.path.abspath(d.dir)) for d in self.datasets])
            if len(dir0)==1:
                self.dir=dir0[0]
                self.plot_dir=f'{self.dir}/group_plots'


    def plot(self, gID,**kwargs):
        return reg.graphs.run_group(gID,datasets=self.datasets,save_to=self.plot_dir,**kwargs)


    def get_datasets(self, datasets=None, refIDs=None, dirs=None, group_id=None):
        if datasets :
            pass
        elif refIDs:
            datasets= [reg.loadRef(refID) for refID in refIDs]
        elif dirs :
            datasets= [LarvaDataset(dir=f'{reg.DATA_DIR}/{dir}', load_data=False) for dir in dirs]
        elif group_id :
            datasets = reg.conf.Ref.loadRefGroup(group_id, to_return='list')
        return datasets

    def get_colors(self):
        colors=[]
        for d in self.datasets :
            color=d.config['color']
            while color is None or color in colors :
                color=aux.random_colors(1)[0]
            colors.append(color)
        return colors

    @property
    def data_dict(self):
        return dict(zip(self.labels, self.datasets))

    @property
    def data_palette(self):
        return zip(self.labels, self.datasets, self.colors)

    @property
    def data_palette_with_N(self):
        return zip(self.labels_with_N, self.datasets, self.colors)

    @property
    def color_palette(self):
        return dict(zip(self.labels, self.colors))

    @property
    def Nticks(self):
        Nticks_list = [d.config.Nticks for d in self.datasets]
        return int(np.max(aux.unique_list(Nticks_list)))

    @property
    def N(self):
        N_list = [d.config.N for d in self.datasets]
        return int(np.max(aux.unique_list(N_list)))

    @property
    def labels_with_N(self):
        return [f'{l} (N={d.config.N})' for l,d in self.data_dict.items()]

    @property
    def fr(self):
        fr_list = [d.fr for d in self.datasets]
        return np.max(aux.unique_list(fr_list))

    @property
    def dt(self):
        dt_list = aux.unique_list([d.dt for d in self.datasets])
        return np.max(dt_list)

    @property
    def duration(self):
        return int(self.Nticks * self.dt)

    @property
    def tlim(self):
        return 0, self.duration

    def trange(self, unit='min'):
        if unit == 'min':
            T = 60
        elif unit == 'sec':
            T = 1
        t0, t1 = self.tlim
        x = np.linspace(t0 / T, t1 / T, self.Nticks)
        return x

    @property
    def arena_dims(self):
        dims=np.array([d.env_params.arena.dims for d in self.datasets])
        if self.Ndatasets>1:
            dims=np.max(dims, axis=0)
        else :
            dims=dims[0]
        return tuple(dims)

    @property
    def arena_geometry(self):
        geos = aux.unique_list([d.env_params.arena.geometry for d in self.datasets])
        if len(geos) ==1:
            return geos[0]
        else:
            return None

    def concat_data(self, key):
        return aux.concat_datasets(dict(zip(self.labels, self.datasets)), key=key)

    @ classmethod
    def from_agentpy_output(cls, output=None, agents=None,to_Geo=False):
        config0 = aux.AttrDict(output.parameters['constants'])
        ds = []
        for gID, df in output.variables.items():
            assert 'sample_id' not in df.index.names
            step, end = convert_group_output_to_dataset(df, config0['collectors'])
            config = config0.get_copy()
            gConf = config0.larva_groups[gID]
            kws = {
                'larva_groups': {gID: gConf},
                # 'df': df,
                'group_id': config0.id,
                'id': gID,
                'refID': None,
                # 'refID': f'{config0.id}/{gID}',
                'dir': f'{config0.dir}/data/{gID}',
                'color': gConf.default_color,
                # 'sample': gConf.sample,
                # 'life_history': gConf.life_history,
                # 'model': gConf.model,

            }
            config.update(**kws)
            d=BaseLarvaDataset.initGeo(to_Geo=to_Geo,config=config,load_data=False,step=step,end=end,agents=agents)

            ds.append(d)

        return cls(datasets=ds, config=config0)

    @classmethod
    def from_agentpy_logs(cls, logs, Ngen, p):
        ds = []
        for gID, gLog in logs.items():
            df=df_from_log(gLog)
            assert 'sample_id' not in df.index.names
            step, end = convert_group_output_to_dataset(df, p['collectors'])
            config = p.get_copy()
            # config.id=gID

            kws = {
                # 'larva_groups': {gID: gConf},
                # 'df': df,
                'group_id': p.id,
                'id': f'{Ngen}_{gID}',
                'refID': None,
                # 'refID': f'{config0.id}/{gID}',
                'dir': f'{p.dir}/{Ngen}/{gID}',
                'color': None,
                # 'sample': gConf.sample,
                # 'life_history': gConf.life_history,
                # 'model': gConf.model,

            }
            config.update(**kws)
            d = BaseLarvaDataset.initGeo(config=config, load_data=False, step=step, end=end)

            ds.append(d)

        return ds

def convert_group_output_to_dataset(df, collectors):


    df.index.set_names(['AgentID', 'Step'], inplace=True)
    df = df.reorder_levels(order=['Step', 'AgentID'], axis=0)
    df.sort_index(level=['Step', 'AgentID'], inplace=True)

    end = df[collectors['end']].xs(df.index.get_level_values('Step').max(), level='Step')
    step = df[collectors['step']]

    return step, end


def df_from_log(gLog):
    g= {}
    Ng=0
    for id, log in gLog.items():
        N=len(log['t'])
        Ng+=N
        # Add object id/key to object log
        log['obj_id'] = [id] * N

        # Add object log to aggregate log
        for k, v in log.items():
            Nv=len(v)
            if k not in g:
                g[k] = []
            # while len(g[k]) < (Ng-Nv):
            #     g[k].append(None)
            # g[k][-len(v):] = v
            g[k].extend(v)
            # print(id, k, len(g[k]), len(v))
    # for k, v in g.items():
    #     print(k,len(v))
    df = pd.DataFrame(g)
    return df.set_index(['obj_id', 't'])
        # return ddf
# class RefDataset(aux.NestedConf):
#     refID = reg.conf.Ref.confID_selector()
#     # refID = aux.OptionalSelector(objects=[], doc='The reference dataset ID')
#     dataset_dir = param.Foldername(default=None,
#                            label='directory of reference dataset',
#                            doc='The path to the stored dataset relative to Root/data. Alternative to providing refID')
#
#     conf = param.ClassSelector(default=None, class_=aux.AttrDict,
#                                label='reference dataset config', doc='The stored reference dataset config')
#     refDataset = param.ClassSelector(default=None, class_=BaseLarvaDataset,
#                                   label='reference dataset', doc='The stored reference dataset')
#
#     """Select a reference dataset by ID"""
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.update_dir()
#         self.update_conf()
#
#
#
#     @param.depends('refID', watch=True)
#     def update_dir(self):
#         self.dataset_dir = reg.conf.Ref.getRefDir(self.refID)
#
#
#
#     @param.depends('dataset_dir', watch=True)
#     def update_conf(self, **kwargs):
#         if self.dataset_dir is not None:
#
#             path = f'{self.dataset_dir}/data/conf.txt'
#             if os.path.isfile(path):
#                 c = aux.load_dict(path)
#                 if 'id' in c.keys():
#                     reg.vprint(f'Loaded existing conf {c.id}', 1)
#                     self.conf = c
#         self.update_dataset(**kwargs)
#
#     def update_dataset(self, **kwargs):
#         if self.conf is not None:
#             self.refDataset = LarvaDataset(config=self.conf, **kwargs)
#         elif self.dataset_dir is not None:
#             self.refDataset = LarvaDataset(dir=f'{reg.DATA_DIR}/{self.dataset_dir}', **kwargs)

# def prepare_dataset(config,step,end,to_Geo=False,agents=None):
#     if not to_Geo :
#         # from larvaworld.lib.process.dataset import LarvaDataset
#         d = LarvaDataset(config=config)
#     else:
#         from larvaworld.lib.process.larva_trajectory_collection import LarvaTrajectoryCollection
#         d = LarvaTrajectoryCollection(config=config)
#     d.set_data(step=step, end=end)
#     if agents and not to_Geo:
#         d.larva_dicts = aux.get_larva_dicts(agents, validIDs=d.agent_ids)
#
#
#     return d

