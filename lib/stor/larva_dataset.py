import itertools
import os.path
import shutil
import numpy as np
import pandas as pd
import warnings
import copy

import lib.aux.dictsNlists as dNl
import lib.aux.naming as nam

from lib.registry.pars import preg


class LarvaDataset:
    def __init__(self, dir, load_data=True, **kwargs):
        self.define_paths(dir)
        self.retrieve_conf(**kwargs)
        self.larva_tables = {}
        self.larva_dicts = {}
        self.configure_body()
        self.define_linear_metrics()
        if load_data:
            try:
                self.load()
            except:
                print('Data not found. Load them manually.')

    def retrieve_conf(self, id='unnamed', fr=16, Npoints=None, Ncontour=0, metric_definition=None, env_params={},
                      larva_groups={},
                      source_xy={}, **kwargs):
        # try:
        if os.path.exists(self.dir_dict.conf):
            config = dNl.load_dict(self.dir_dict.conf, use_pickle=False)

        else:
            if metric_definition is None:
                metric_definition = preg.get_null('metric_definition')
            group_ids = list(larva_groups.keys())
            samples = dNl.unique_list([larva_groups[k]['sample'] for k in group_ids])
            if len(group_ids) == 1:
                group_id = group_ids[0]
                color = larva_groups[group_id]['default_color']
                sample = larva_groups[group_id]['sample']
                life_history = larva_groups[group_id]['life_history']
            else:
                group_id = None
                color = None
                sample = samples[0] if len(samples) == 1 else None
                life_history = None

            if Npoints is None:
                try:
                    # FIXME This only takes the first configuration into account
                    Npoints = list(larva_groups.values())[0]['model']['body']['Nsegs'] + 1
                except:
                    Npoints = 3

            config = {'id': id,
                      'group_id': group_id,
                      'group_ids': group_ids,
                      'refID': None,
                      'dir': self.dir,
                      'dir_dict': self.dir_dict,
                      'aux_dir': self.dir_dict.aux_h5,
                      'parent_plot_dir': f'{self.dir}/plots',
                      'fr': fr,
                      'dt': 1 / fr,
                      'Npoints': Npoints,
                      'Ncontour': Ncontour,
                      'sample': sample,
                      'color': color,
                      'metric_definition': {
                          'spatial': {
                              'hardcoded': metric_definition['spatial'],
                              'fitted': None,
                          },
                          'angular': {
                              'hardcoded': metric_definition['angular'],
                              'fitted': None
                          }
                      },
                      'env_params': env_params,
                      'larva_groups': larva_groups,
                      'source_xy': source_xy,
                      'life_history': life_history,

                      }
        self.config = dNl.NestDict(config)
        self.config.dir_dict = self.dir_dict
        self.__dict__.update(self.config)

    def set_data(self, step=None, end=None, food=None):
        if step is not None:
            step.sort_index(level=['Step', 'AgentID'], inplace=True)
            self.step_data = step
            self.agent_ids = step.index.unique('AgentID').values
            self.num_ticks = step.index.unique('Step').size
        if end is not None:
            end.sort_index(inplace=True)
            self.endpoint_data = end
        if food is not None:
            self.food_endpoint_data = food
        self.update_config()

    def drop_pars(self, groups=None, is_last=True, show_output=True, **kwargs):
        if groups is None:
            groups = {n: False for n in
                      ['midline', 'contour', 'stride', 'non_stride', 'stridechain', 'pause', 'Lturn', 'Rturn', 'turn',
                       'unused']}
        if self.step_data is None:
            self.load()
        s = self.step_data
        pars = []
        if groups['midline']:
            pars += dNl.flatten_list(self.points_xy)
        if groups['contour']:
            pars += dNl.flatten_list(self.contour_xy)
        for c in ['stride', 'non_stride', 'stridechain', 'pause', 'Lturn', 'Rturn', 'turn']:
            if groups[c]:
                pars += [nam.start(c), nam.stop(c), nam.id(c), nam.dur(c), nam.length(c), nam.dst(c),
                         nam.straight_dst(c), nam.scal(nam.dst(c)), nam.scal(nam.straight_dst(c)), nam.orient(c)]
        if groups['unused']:
            pars += self.get_unused_pars()
        pars = dNl.unique_list(pars)
        s.drop(columns=[p for p in pars if p in s.columns], inplace=True)
        self.set_data(step=s)
        if is_last:
            self.save()
            self.load()
        if show_output:
            print(f'{len(pars)} parameters dropped. {len(s.columns)} remain.')

    def get_unused_pars(self):
        vels = [nam.vel(''), nam.scal(nam.vel(''))]
        lin = [nam.dst(''), nam.vel(''), nam.acc('')]
        lins = lin + nam.scal(lin) + nam.cum([nam.dst(''), nam.scal(nam.dst(''))]) + nam.max(vels) + nam.min(vels)
        beh = ['stride', nam.chain('stride'), 'pause', 'turn', 'Lturn', 'Rturn']
        behs = nam.start(beh) + nam.stop(beh) + nam.id(beh) + nam.dur(beh) + nam.length(beh)
        str = [nam.dst('stride'), nam.straight_dst('stride'), nam.orient('stride'), 'dispersion']
        strs = str + nam.scal(str)
        var = ['spinelength', 'ang_color', 'lin_color', 'state']
        vpars = lins + self.ang_pars + self.xy_pars + behs + strs + var
        pars = [p for p in self.step_data.columns.values if p not in vpars]
        return pars

    def read(self, key='step', file='data_h5'):
        return pd.read_hdf(self.dir_dict[file], key)

    def load(self, step=True, end=True, food=False,
             h5_ks=['contour', 'midline', 'epochs', 'base_spatial', 'angular', 'dspNtor']):
        D = self.dir_dict
        store = pd.HDFStore(D.data_h5)

        if step:
            s = store['step']
            for h5_k in h5_ks:
                try:
                    temp = pd.HDFStore(D[h5_k])
                    s = s.join(temp[h5_k])
                    temp.close()
                except:
                    pass
            s.sort_index(level=['Step', 'AgentID'], inplace=True)
            self.agent_ids = s.index.unique('AgentID').values
            self.num_ticks = s.index.unique('Step').size
            self.step_data = s
        if end:
            try:
                endpoint = pd.HDFStore(D.endpoint_h5)
                self.endpoint_data = endpoint['end']
                self.endpoint_data.sort_index(inplace=True)
                endpoint.close()
            except:
                self.endpoint_data = store['end']
        if food:
            self.food_endpoint_data = store['food']
            self.food_endpoint_data.sort_index(inplace=True)
        store.close()

    def save_vel_definition(self, component_vels=True, add_reference=True):
        from lib.process.calibration import comp_stride_variation, comp_segmentation
        warnings.filterwarnings('ignore')
        store = pd.HDFStore(self.dir_dict.vel_definition)
        res_v = comp_stride_variation(self, component_vels=component_vels)
        for k, v in res_v.items():
            store[k] = v

        res_fov = comp_segmentation(self)
        for k, v in res_fov.items():
            store[k] = v

        store.close()
        self.define_linear_metrics()
        self.save_config(add_reference=add_reference)
        print(f'Velocity definition dataset stored.')

    def load_vel_definition(self):
        try:
            store = pd.HDFStore(self.dir_dict.vel_definition)
            dic = {k: store[k] for k in store.keys()}
            store.close()
            return dic
        except:
            raise ValueError('Not found')

    def save(self, step=True, end=True, food=False,
             h5_ks=['contour', 'midline', 'epochs', 'base_spatial', 'angular', 'dspNtor'],
             add_reference=False):
        h5_kdic = dNl.NestDict({
            'contour': dNl.flatten_list(self.contour_xy),
            'midline': dNl.flatten_list(self.points_xy),
            'epochs': self.epochs_ps,
            'base_spatial': self.base_spatial_ps,
            'angular': dNl.unique_list(self.angles + self.ang_pars),
            'dspNtor': self.dspNtor_ps,
        })

        D = self.dir_dict
        store = pd.HDFStore(D.data_h5)
        if step:
            stored_ps = []
            s = self.step_data
            for h5_k in h5_ks:
                pps = [p for p in h5_kdic[h5_k] if p in s.columns]
                temp = pd.HDFStore(D[h5_k])
                temp[h5_k] = s[pps]
                temp.close()
                stored_ps += pps

            store['step'] = s.drop(stored_ps, axis=1, errors='ignore')
        if end:
            endpoint = pd.HDFStore(D.endpoint_h5)
            endpoint['end'] = self.endpoint_data
            endpoint.close()
        if food:
            store['food'] = self.food_endpoint_data
        self.save_config(add_reference=add_reference)
        store.close()
        print(f'Dataset {self.id} stored.')

    @property
    def base_spatial_ps(self):
        p = self.point
        pars = [nam.xy(p)[0], nam.xy(p)[1], nam.dst(p), nam.vel(p), nam.acc(p), nam.lin(nam.dst(p)),
                nam.lin(nam.vel(p)), nam.lin(nam.acc(p)),
                nam.cum(nam.dst(p)), nam.cum(nam.lin(nam.dst(p)))]
        spars = nam.scal(pars)
        return pars + spars

    @property
    def epochs_ps(self):
        cs = ['turn', 'Lturn', 'Rturn', 'pause', 'run', 'stride', 'stridechain']
        pars = dNl.flatten_list([[f'{c}_id', f'{c}_start', f'{c}_stop', f'{c}_dur', f'{c}_dst', f'{c}_scaled_dst',
                                  f'{c}_length', f'{c}_amp', f'{c}_vel_max', f'{c}_count'] for c in cs])
        return pars

    @property
    def dspNtor_ps(self):
        tor_ps = [f'tortuosity_{dur}' for dur in [1, 2, 5, 10, 20, 30, 60, 100, 120, 240, 300]]
        dsp_ps = [f'dispersion_{t0}_{t1}' for (t0, t1) in
                  itertools.product([0, 5, 10, 20, 30, 60], [30, 40, 60, 90, 120, 240, 300])]
        pars = tor_ps + dsp_ps + nam.scal(dsp_ps)
        return pars

    def save_larva_dicts(self):
        for k, vs in self.larva_dicts.items():
            os.makedirs(self.dir_dict[k], exist_ok=True)
            for id, dic in vs.items():
                try:
                    dNl.save_dict(dic, f'{self.dir_dict[k]}/{id}.txt', use_pickle=False)
                except:
                    dNl.save_dict(dic, f'{self.dir_dict[k]}/{id}.txt', use_pickle=True)

    def get_larva_dicts(self, env):
        from lib.model.modules.nengobrain import NengoBrain
        deb_dicts = {}
        nengo_dicts = {}
        bout_dicts = {}
        foraging_dicts = {}
        for l in env.get_flies():
            if l.unique_id in self.agent_ids:
                if hasattr(l, 'deb') and l.deb is not None:
                    deb_dicts[l.unique_id] = l.deb.finalize_dict()
                elif isinstance(l.brain, NengoBrain):
                    if l.brain.dict is not None:
                        nengo_dicts[l.unique_id] = l.brain.dict
                if l.brain.locomotor.intermitter is not None:
                    bout_dicts[l.unique_id] = l.brain.locomotor.intermitter.build_dict()
                if len(env.foodtypes) > 0:
                    foraging_dicts[l.unique_id] = l.finalize_foraging_dict()
                self.config.foodtypes = env.foodtypes
        self.larva_dicts = {'deb': deb_dicts, 'nengo': nengo_dicts, 'bout_dicts': bout_dicts,
                            'foraging': foraging_dicts}

    def get_larva_tables(self, env):
        if env.table_collector is not None:
            for name, table in env.table_collector.tables.items():
                df = pd.DataFrame(table)
                if 'unique_id' in df.columns:
                    df.rename(columns={'unique_id': 'AgentID'}, inplace=True)
                    N = len(df['AgentID'].unique().tolist())
                    if N > 0:
                        Nrows = int(len(df.index) / N)
                        df['Step'] = np.array([[i] * N for i in range(Nrows)]).flatten()
                        df.set_index(['Step', 'AgentID'], inplace=True)
                        df.sort_index(level=['Step', 'AgentID'], inplace=True)
                        self.larva_tables[name] = df

    def get_larva(self, idx=0, id=None):
        if not hasattr(self, 'step_data'):
            raise ValueError('Step data not loaded.')
        if not hasattr(self, 'endpoint_data'):
            raise ValueError('Endpoint data not loaded.')
        s, e = self.step_data, self.endpoint_data
        if id is None:
            id = self.config.agent_ids[idx]
        ss = s.xs(id, level='AgentID')
        ee = e.loc[id]
        return ss, ee

    def save_larva_tables(self):
        store = pd.HDFStore(self.dir_dict.tables_h5)
        for name, df in self.larva_tables.items():
            store[name] = df
        store.close()

    def save_ExpFitter(self, dic=None):
        dNl.save_dict(dic, self.dir_dict.ExpFitter, use_pickle=False)

    def load_ExpFitter(self):
        try:
            dic = dNl.load_dict(self.dir_dict.ExpFitter, use_pickle=False)
            return dic
        except:
            return None

    def update_config(self):
        self.config.dt = 1 / self.fr
        self.config.dir_dict = self.dir_dict
        if 'agent_ids' not in self.config.keys():
            try:
                ids = self.agent_ids
            except:
                try:
                    ids = self.endpoint_data.index.values
                except:
                    ids = self.read('end', file='endpoint_h5').index.values

            self.config.agent_ids = list(ids)
            self.config.N = len(ids)
        if 't0' not in self.config.keys():
            try:
                self.config.t0 = int(self.step_data.index.unique('Step')[0])
            except:
                self.config.t0 = 0
        if 'Nticks' not in self.config.keys():
            try:
                self.config.Nticks = self.step_data.index.unique('Step').size
            except:
                try:
                    self.config.Nticks = self.endpoint_data['num_ticks'].max()
                except:
                    pass
        if 'duration' not in self.config.keys():
            try:
                self.config.duration = int(self.endpoint_data['cum_dur'].max())
            except:
                self.config.duration = self.config.dt * self.config.Nticks
        if 'quality' not in self.config.keys():
            try:
                df = self.step_data[nam.xy(self.point)[0]].values.flatten()
                valid = np.count_nonzero(~np.isnan(df))
                self.config.quality = np.round(valid / df.shape[0], 2)
            except:
                pass
        if 'aux_pars' not in self.config.keys():
            self.inspect_aux(save=False)

    def save_config(self, add_reference=False, refID=None):
        self.update_config()
        for k, v in self.config.items():
            if isinstance(v, np.ndarray):
                self.config[k] = v.tolist()
        dNl.save_dict(self.config, self.dir_dict.conf, use_pickle=False)
        if add_reference:
            if refID is None:
                refID = f'{self.group_id}.{self.id}'
            self.config.refID = refID
            preg.saveConf(conf=self.config, conftype='Ref', id=refID)

    def save_agents(self, ids=None, pars=None):
        if not hasattr(self, 'step_data'):
            self.load()
        if ids is None:
            ids = self.agent_ids
        if pars is None:
            pars = self.step_data.columns
        path = self.dir_dict.single_tracks
        os.makedirs(path, exist_ok=True)
        for id in ids:
            f = os.path.join(path, f'{id}.csv')
            store = pd.HDFStore(f)
            store['step'] = self.step_data[pars].loc[(slice(None), id), :]
            store['end'] = self.endpoint_data.loc[[id]]
            store.close()
        print('All agent data saved.')

    def load_agent(self, id):
        try:
            f = os.path.join(self.dir_dict.single_tracks, f'{id}.csv')
            store = pd.HDFStore(f)
            s = store['step']
            e = store['end']
            store.close()
            return s, e
        except:
            return None, None

    def load_table(self, name):
        store = pd.HDFStore(self.dir_dict.tables_h5)
        df = store[name]
        store.close()
        return df

    def load_aux(self, type, par=None):
        # print(pd.HDFStore(self.dir_dict['aux_h5']).keys())
        df = self.read(key=f'{type}.{par}', file='aux_h5')
        return df

    def inspect_aux(self, save=True):
        aux_pars = dNl.NestDict({'distro': [], 'dispersion': [], 'other': []})
        distro_ps, dsp_ps, other_ps = [], [], []
        store = pd.HDFStore(self.dir_dict.aux_h5)
        ks = store.keys()
        ks = [k.split('/')[-1] for k in ks]
        for k in ks:
            kks = k.split('.')
            if kks[0].endswith('distro'):
                aux_pars.distro.append(kks[-1])
            elif kks[0].endswith('dispersion'):
                aux_pars.dispersion.append(kks[-1])
            else:
                aux_pars.other.append(kks[-1])
        self.config.aux_pars = aux_pars

        store.close()
        if save:
            self.save_config(add_reference=True, refID=self.config.refID)

    def load_dicts(self, type, ids=None):
        if ids is None:
            ids = self.agent_ids
        ds0 = self.larva_dicts
        if type in ds0 and all([id in ds0[type].keys() for id in ids]):
            ds = [ds0[type][id] for id in ids]
        else:
            files = [f'{id}.txt' for id in ids]
            try:
                ds = dNl.load_dicts(files=files, folder=self.dir_dict[type], use_pickle=False)
            except:
                ds = dNl.load_dicts(files=files, folder=self.dir_dict[type], use_pickle=True)
        return ds

    def get_pars_list(self, p0, s0, draw_Nsegs):
        if p0 is None:
            p0 = self.point
        elif type(p0) == int:
            p0 = 'centroid' if p0 == -1 else self.points[p0]
        dic = {}
        dic['pos_p'] = pos_p = nam.xy(p0) if set(nam.xy(p0)).issubset(s0.columns) else ['x', 'y']
        dic['mid_p'] = mid_p = [xy for xy in self.points_xy if set(xy).issubset(s0.columns)]
        dic['cen_p'] = cen_p = nam.xy('centroid') if set(nam.xy('centroid')).issubset(s0.columns) else []
        dic['con_p'] = con_p = [xy for xy in self.contour_xy if set(xy).issubset(s0.columns)]
        dic['chunk_p'] = chunk_p = [p for p in ['stride_stop', 'stride_id', 'pause_id', 'feed_id'] if p in s0.columns]
        dic['ang_p'] = ang_p = ['bend'] if 'bend' in s0.columns else []

        dic['ors_p'] = ors_p = [p for p in
                                ['front_orientation', 'rear_orientation', 'head_orientation', 'tail_orientation'] if
                                p in s0.columns]
        if draw_Nsegs == len(mid_p) - 1 and set(nam.orient(self.segs)).issubset(s0.columns):
            dic['ors_p'] = ors_p = nam.orient(self.segs)
        pars = dNl.unique_list(cen_p + pos_p + ang_p + ors_p + chunk_p + dNl.flatten_list(mid_p + con_p))

        return dic, pars, p0

    def get_smaller_dataset(self, s0, e0, ids=None, pars=None, time_range=None, dynamic_color=None):
        if ids is None:
            ids = e0.index.values.tolist()
        if type(ids) == list and all([type(i) == int for i in ids]):
            ids = [self.agent_ids[i] for i in ids]
        if dynamic_color is not None and dynamic_color in s0.columns:
            pars.append(dynamic_color)
        else:
            dynamic_color = None
        pars = [p for p in pars if p in s0.columns]
        if time_range is None:
            s = copy.deepcopy(s0.loc[(slice(None), ids), pars])
        else:
            a, b = time_range
            a = int(a / self.dt)
            b = int(b / self.dt)
            s = copy.deepcopy(s0.loc[(slice(a, b), ids), pars])
        e = copy.deepcopy(e0.loc[ids])
        traj_color = s[dynamic_color] if dynamic_color is not None else None
        return s, e, ids, traj_color

    def visualize(self, s0=None, e0=None, vis_kwargs=None, agent_ids=None, save_to=None, time_range=None,
                  draw_Nsegs=None, env_params=None, track_point=None, dynamic_color=None, use_background=False,
                  transposition=None, fix_point=None, fix_segment=None, **kwargs):
        from lib.model.envs._larvaworld_replay import LarvaWorldReplay
        if vis_kwargs is None:
            vis_kwargs = preg.get_null('visualization', mode='video')
        if s0 is None and e0 is None:
            if not hasattr(self, 'step_data'):
                self.load()
            s0, e0 = self.step_data, self.endpoint_data
        dic, pars, track_point = self.get_pars_list(track_point, s0, draw_Nsegs)
        s, e, ids, traj_color = self.get_smaller_dataset(ids=agent_ids, pars=pars, time_range=time_range,
                                                         dynamic_color=dynamic_color, s0=s0, e0=e0)
        if len(ids) == 1:
            n0 = ids[0]
        elif len(ids) == len(self.agent_ids):
            n0 = 'all'
        else:
            n0 = f'{len(ids)}l'

        if env_params is None:
            env_params = self.env_params
        arena_dims = env_params['arena']['arena_dims']

        if transposition is not None:
            from lib.process.spatial import align_trajectories
            s = align_trajectories(s, track_point=track_point, arena_dims=arena_dims, mode=transposition,
                                   config=self.config)
            bg = None
            n1 = 'transposed'
        elif fix_point is not None:
            from lib.process.spatial import fixate_larva
            s, bg = fixate_larva(s, point=fix_point, fix_segment=fix_segment, arena_dims=arena_dims, config=self.config)
            n1 = 'fixed'
        else:
            bg = None
            n1 = 'normal'

        replay_id = f'{n0}_{n1}'
        if vis_kwargs['render']['media_name'] is None:
            vis_kwargs['render']['media_name'] = replay_id
        if save_to is None:
            save_to = self.vis_dir

        base_kws = {
            'vis_kwargs': vis_kwargs,
            'env_params': env_params,
            'id': replay_id,
            'dt': self.dt,
            'Nsteps': len(s.index.unique('Step').values),
            'save_to': save_to,
            'background_motion': bg,
            'use_background': True if bg is not None else False,
            'Box2D': False,
            'traj_color': traj_color,
            # 'space_in_mm': space_in_mm
        }
        replay_env = LarvaWorldReplay(step_data=s, endpoint_data=e, config=self.config, draw_Nsegs=draw_Nsegs,
                                      **dic, **base_kws, **kwargs)

        replay_env.run()
        print('Visualization complete')

    def visualize_single(self, id=0, close_view=True, fix_point=-1, fix_segment=None, save_to=None, time_range=None,
                         draw_Nsegs=None, vis_kwargs=None, **kwargs):
        from lib.model.envs._larvaworld_replay import LarvaWorldReplay
        from lib.process.spatial import fixate_larva
        if type(id) == int:
            id = self.config.agent_ids[id]
        s0, e0 = self.load_agent(id)
        if s0 is None:
            self.save_agents(ids=[id])
            s0, e0 = self.load_agent(id)
        env_params = self.env_params
        if close_view:
            env_params.arena = preg.get_null('arena', arena_dims=(0.01, 0.01))
        if time_range is None:
            s00 = copy.deepcopy(s0)
        else:
            a, b = time_range
            a = int(a / self.dt)
            b = int(b / self.dt)
            s00 = copy.deepcopy(s0.loc[slice(a, b)])
        dic, pars, track_point = self.get_pars_list(fix_point, s00, draw_Nsegs)
        s, bg = fixate_larva(s00, point=fix_point, fix_segment=fix_segment,
                             arena_dims=env_params.arena.arena_dims, config=self.config)
        if save_to is None:
            save_to = self.vis_dir
        replay_id = f'{id}_fixed_at_{fix_point}'
        if vis_kwargs is None:
            vis_kwargs = preg.get_null('visualization', mode='video', video_speed=60, media_name=replay_id)
        base_kws = {
            'vis_kwargs': vis_kwargs,
            'env_params': env_params,
            'id': replay_id,
            'dt': self.dt,
            'Nsteps': len(s.index.unique('Step').values),
            'save_to': save_to,
            'background_motion': bg,
            'use_background': True if bg is not None else False,
            'Box2D': False,
            'traj_color': None,
            # 'space_in_mm': space_in_mm
        }
        replay_env = LarvaWorldReplay(step_data=s, endpoint_data=e0, config=self.config, draw_Nsegs=draw_Nsegs,
                                      **dic, **base_kws, **kwargs)

        replay_env.run()
        print('Visualization complete')

    def configure_body(self):
        N, Nc = self.Npoints, self.Ncontour
        self.points = nam.midline(N, type='point')

        self.Nangles = np.clip(N - 2, a_min=0, a_max=None)
        self.angles = [f'angle{i}' for i in range(self.Nangles)]
        self.Nsegs = np.clip(N - 1, a_min=0, a_max=None)
        self.segs = nam.midline(self.Nsegs, type='seg')

        self.points_xy = nam.xy(self.points)

        self.contour = nam.contour(Nc)
        self.contour_xy = nam.xy(self.contour)

        ang = ['front_orientation', 'rear_orientation', 'head_orientation', 'tail_orientation', 'bend']
        self.ang_pars = ang + nam.unwrap(ang) + nam.vel(ang) + nam.acc(ang) + nam.min(nam.vel(ang)) + nam.max(
            nam.vel(ang))
        self.xy_pars = nam.xy(self.points + self.contour + ['centroid'], flat=True) + nam.xy('')

    def define_paths(self, dir):
        self.dir = dir
        self.data_dir = os.path.join(dir, 'data')
        self.plot_dir = os.path.join(dir, 'plots')
        self.vis_dir = os.path.join(dir, 'visuals')
        self.aux_dir = os.path.join(dir, 'aux')
        self.dir_dict = dNl.NestDict({
            'parent': self.dir,
            'data': self.data_dir,
            'plot': self.plot_dir,
            'vis': self.vis_dir,
            # 'comp_plot': os.path.join(self.plot_dir, 'comparative'),
            'GAoptimization': os.path.join(self.data_dir, 'GAoptimization'),
            'evaluation': os.path.join(self.data_dir, 'evaluation'),
            'foraging': os.path.join(self.data_dir, 'foraging_dicts'),
            'deb': os.path.join(self.data_dir, 'deb_dicts'),
            'nengo': os.path.join(self.data_dir, 'nengo_probes'),
            'single_tracks': os.path.join(self.data_dir, 'single_tracks'),
            'bout_dicts': os.path.join(self.data_dir, 'bout_dicts'),
            'model_tables': os.path.join(self.plot_dir, 'model_tables'),
            'model_summaries': os.path.join(self.plot_dir, 'model_summaries'),
            'pooled_epochs': os.path.join(self.data_dir, 'pooled_epochs'),
            'cycle_curves': os.path.join(self.data_dir, 'cycle_curves.txt'),
            'chunk_dicts': os.path.join(self.data_dir, 'chunk_dicts'),
            'tables_h5': os.path.join(self.data_dir, 'tables.h5'),
            'sim': os.path.join(self.data_dir, 'sim_conf.txt'),
            'ExpFitter': os.path.join(self.data_dir, 'ExpFitter.txt'),
            'fit': os.path.join(self.data_dir, 'dataset_fit.csv'),
            'conf': os.path.join(self.data_dir, 'dataset_conf.csv'),
            'data_h5': os.path.join(self.data_dir, 'data.h5'),
            'endpoint_h5': os.path.join(self.data_dir, 'endpoint.h5'),
            'derived_h5': os.path.join(self.data_dir, 'derived.h5'),
            'midline': os.path.join(self.data_dir, 'midline.h5'),
            'contour': os.path.join(self.data_dir, 'contour.h5'),
            'epochs': os.path.join(self.data_dir, 'epochs.h5'),
            'base_spatial': os.path.join(self.data_dir, 'base_spatial.h5'),
            'angular': os.path.join(self.data_dir, 'angular.h5'),
            'dspNtor': os.path.join(self.data_dir, 'dspNtor.h5'),
            'aux_h5': os.path.join(self.data_dir, 'aux.h5'),
            'vel_definition': os.path.join(self.data_dir, 'vel_definition.h5'),
        })
        for k in ['parent', 'data']:
            os.makedirs(self.dir_dict[k], exist_ok=True)

    def define_linear_metrics(self):
        sp_conf = self.config.metric_definition.spatial
        if sp_conf.fitted is None:
            point_idx = sp_conf.hardcoded.point_idx
            use_component_vel = sp_conf.hardcoded.use_component_vel
        else:
            point_idx = sp_conf.fitted.point_idx
            use_component_vel = sp_conf.fitted.use_component_vel

        try:
            self.config.point = self.points[point_idx - 1]
        except:
            self.config.point = 'centroid'
        self.point = self.config.point
        self.distance = nam.dst(self.point)
        self.velocity = nam.vel(self.point)
        self.acceleration = nam.acc(self.point)
        if use_component_vel:
            self.velocity = nam.lin(self.velocity)
            self.acceleration = nam.lin(self.acceleration)

    def enrich(self, metric_definition=None, preprocessing={}, processing={}, bout_annotation=True,
               to_drop={}, recompute=False, mode='minimal', show_output=False, is_last=True, annotation={},
               add_reference=False, **kwargs):
        c = self.config
        md = metric_definition
        if md is None:
            md = c.metric_definition
        else:
            c.metric_definition.angular.hardcoded.update(**md['angular'])
            c.metric_definition.spatial.hardcoded.update(**md['spatial'])
            self.define_linear_metrics()

        from lib.process.basic import preprocess, process
        warnings.filterwarnings('ignore')
        s, e = self.step_data, self.endpoint_data
        cc = {
            's': s,
            'e': e,
            'c': c,
            'show_output': show_output,
            'recompute': recompute,
            'mode': mode,
            'is_last': False,
        }
        preprocess(**preprocessing, **cc, **kwargs)
        process(processing=processing, **cc, **kwargs, **md['dispersion'], **md['tortuosity'])
        if bout_annotation and any([annotation[kk] for kk in ['stride', 'pause', 'turn']]):
            from lib.process import aux, patch
            self.chunk_dicts = aux.comp_chunk_dicts(s, e, c, **kwargs)
            self.store_chunk_dicts(self.chunk_dicts)
            aux.turn_mode_annotation(e, self.chunk_dicts)
            patch.comp_patch(s, e, c)
            if annotation['on_food']:
                from lib.process import patch
                patch.comp_on_food(s, e, c)
            if annotation['interference']:
                self.cycle_curves = aux.compute_interference(s=s, e=e, c=c, chunk_dicts=self.chunk_dicts, **kwargs)
                self.pooled_epochs = self.compute_pooled_epochs(chunk_dicts=self.chunk_dicts)
                self.store_pooled_epochs(self.pooled_epochs)

        self.drop_pars(**to_drop, **cc)
        if is_last:
            self.save(add_reference=add_reference)
        return self

    def compute_pooled_epochs(self, chunk_dicts=None):
        from lib.anal.fitting import fit_bouts
        s, e, c = self.step_data, self.endpoint_data, self.config
        if chunk_dicts is None:
            try:
                chunk_dicts = self.chunk_dicts
            except:
                chunk_dicts = self.load_chunk_dicts()
        if chunk_dicts is not None:
            self.pooled_epochs = fit_bouts(c=c, chunk_dicts=chunk_dicts, s=s, e=e, id=c.id)
            # if store:
            #     path = c.dir_dict.pooled_epochs
            #     os.makedirs(path, exist_ok=True)
            #     dNl.save_dict(self.pooled_epochs, f'{path}/{self.id}.txt', use_pickle=True)
            #     print('Pooled group bouts saved')
            return self.pooled_epochs
        else:
            return None

    def get_traj_aligned(self, mode='origin'):
        try:
            return self.read(key=f'traj_aligned2{mode}', file='aux_h5')
        except:
            return None

    def get_par(self, par, key=None):
        def get_end_par(par):
            try:
                return self.read(key='end', file='endpoint_h5')[par]
            except:
                try:
                    return self.endpoint_data[par]
                except:
                    return None

        def get_step_par(par):
            try:
                return self.read(key='step')[par]
            except:
                try:
                    return self.step_data[par]
                except:
                    return None

        if key in ['distro', 'dispersion']:
            try:
                return self.read(key=f'{key}.{par}', file='aux_h5')
            except:
                return self.get_par(par, key='step')

        if key == 'end':
            return get_end_par(par)
        elif key == 'step':
            return get_step_par(par)
        else:
            e = get_end_par(par)
            if e is not None:
                return e
            else:
                s = get_step_par(par)
                if s is not None:
                    return s
                else:
                    try:
                        return self.read(key=f'distro.{par}', file='aux_h5')
                    except:
                        return None

    def delete(self, show_output=True):
        shutil.rmtree(self.dir)
        if show_output:
            print(f'Dataset {self.id} deleted')

    def set_id(self, id, save=True):
        self.id = id
        self.config.id = id
        if save:
            self.save_config()

    def load_pooled_epochs(self, id=None):
        if id is None:
            id = self.id
        path = os.path.join(self.dir_dict.pooled_epochs, f'{id}.txt')
        return dNl.load_dict(path, use_pickle=True)
        # try:
        #     dic = dNl.load_dict(path, use_pickle=True)
        #     print(f'Pooled epochs loaded for dataset {id}')
        #     return dic
        # except:
        #     try:
        #         dic = self.compute_pooled_epochs()
        #         return dic
        #     except:
        #         print(f'Pooled epochs not found for dataset {id}')
        #         return None

    def load_chunk_dicts(self, id=None):
        if id is None:
            id = self.id
        path = os.path.join(self.dir_dict.chunk_dicts, f'{id}.txt')
        return dNl.load_dict(path, use_pickle=True)

    def store_chunk_dicts(self, chunk_dicts, id=None):
        if id is None:
            id = self.id
        path = self.dir_dict.chunk_dicts
        os.makedirs(path, exist_ok=True)
        filepath = f'{path}/{id}.txt'
        dNl.save_dict(chunk_dicts, filepath, use_pickle=True)
        print('Individual larva bouts saved')

    def store_pooled_epochs(self, pooled_epochs, id=None):
        if id is None:
            id = self.id
        path = self.dir_dict.pooled_epochs
        os.makedirs(path, exist_ok=True)
        filepath = f'{path}/{id}.txt'
        dNl.save_dict(pooled_epochs, filepath, use_pickle=True)
        print('Pooled group bouts saved')

    def load_cycle_curves(self):
        try:
            return dNl.load_dict(self.dir_dict.cycle_curves, use_pickle=True)
        except:
            pass

    def get_chunks(self, chunk, shorts, min_dur=0, max_dur=np.inf, idx=None):
        min_ticks = int(min_dur / self.config.dt)
        pars = preg.getPar(shorts)
        ss = self.step_data[pars]

        dic = self.load_chunk_dicts()
        chunks = []
        if idx is None:
            ids = self.agent_ids
        elif type(idx) == int:
            ids = [self.agent_ids[idx]]
        elif type(idx) == list:
            ids = [self.agent_ids[idxx] for idxx in idx]
        for id in ids:
            sss = ss.xs(id, level='AgentID')
            p01s = dic[id][chunk]
            p_ticks = np.diff(p01s).flatten()
            vp01s = p01s[p_ticks > min_ticks]
            Nvps = vp01s.shape[0]
            if Nvps > 0:
                for i in range(Nvps):
                    vp0, vp1 = vp01s[i, :]
                    entry = {'id': id, 'chunk': sss.loc[vp0:vp1]}
                    chunks.append(entry)
        return chunks

    def get_chunk_par(self, chunk, short=None, par=None, min_dur=0, mode='distro'):
        if par is None:
            par = preg.getPar(short)

        dic0 = self.load_chunk_dicts()
        dics = [dic0[id] for id in self.agent_ids]
        sss = [self.step_data[par].xs(id, level='AgentID') for id in self.agent_ids]

        if mode == 'distro':
            chunk_idx = f'{chunk}_idx'
            chunk_dur = f'{chunk}_dur'
            vs = []
            for ss, dic in zip(sss, dics):
                if min_dur == 0:
                    idx = dic[chunk_idx]
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
                vs.append(ss.loc[idx].values)
            vs = np.concatenate(vs)
            return vs
        elif mode == 'extrema':
            cc0s, cc1s, cc01s = [], [], []
            for ss, dic in zip(sss, dics):
                epochs = dic[chunk]
                # for id in self.agent_ids:
                #     ss = self.step_data[par].xs(id, level='AgentID')
                #     dic = dic0[id]
                if min_dur != 0:
                    chunk_dur = f'{chunk}_dur'
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

    def existing(self, key='end', return_shorts=False):
        if key == 'end':
            e = self.endpoint_data if hasattr(self, 'endpoint_data') else self.read(key='end', file='endpoint_h5')
            pars = e.columns.values.tolist()
        elif key == 'step':
            s = self.step_data if hasattr(self, 'step_data') else self.read(key='step')
            pars = s.columns.values.tolist()
        elif key in ['distro', 'dispersion']:
            self.inspect_aux(save=False)
            pars = self.config.aux_pars[key]
        if not return_shorts:
            return sorted(pars)
        else:
            shorts = preg.getPar(d=pars, to_return='k')
            return sorted(shorts)

    def sample_modelConf(self, N, mID, sample_ks=None):
        from lib.aux.sim_aux import sample_group
        from lib.aux.sim_aux import generate_larvae
        m = preg.loadConf(id=mID, conftype='Model')
        # m = loadConf(mID, 'Model')
        if sample_ks is None:
            modF = dNl.flatten_dict(m)
            sample_ks = [p for p in modF if modF[p] == 'sample']
        RefPars = dNl.load_dict(preg.path_dict["ParRef"], use_pickle=False)
        invRefPars = {v: k for k, v in RefPars.items()}
        sample_ps = [invRefPars[p] for p in sample_ks]
        sample_dict = sample_group(e=self.read(key='end', file='endpoint_h5'), N=N, sample_ps=sample_ps) if len(
            sample_ps) > 0 else {}
        all_pars = generate_larvae(N, sample_dict, m, RefPars)
        return all_pars

    def store_model_graphs(self, mIDs):
        # from lib.registry.pars import preg
        from lib.aux.combining import combine_pdfs
        G = preg.graph_dict.dict
        # from lib.plot.grid import model_summary
        f1 = self.dir_dict.model_tables
        f2 = self.dir_dict.model_summaries
        os.makedirs(f1, exist_ok=True)
        os.makedirs(f2, exist_ok=True)
        for mID in mIDs:
            # _ = G['model table'](mID, save_to=f1)
            try:
                _ = G['model table'](mID, save_to=f1)
            except:
                print('TABLE FAIL', mID)
            try:
                _ = G['model summary'](refDataset=self, mID=mID, Nids=10, save_to=f2)
            except:
                print('SUMMARY FAIL', mID)

        combine_pdfs(file_dir=f1, save_as="___ALL_MODEL_CONFIGURATIONS___.pdf", deep=False)
        combine_pdfs(file_dir=f2, save_as="___ALL_MODEL_SUMMARIES___.pdf", deep=False)

    def eval_model_graphs(self, mIDs, dIDs=None,id=None, N=10, enrichment=True, offline=False, dur=None, **kwargs):
        if id is None:
            id = f'{len(mIDs)}mIDs'
        if dIDs is None:
            dIDs = mIDs
        from lib.eval.evaluation import EvalRun
        evrun = EvalRun(refID=self.config.refID, id=id, modelIDs=mIDs, dataset_ids=dIDs, N=N,
                        save_to=self.dir_dict.evaluation,
                        bout_annotation=True, enrichment=enrichment, show=False, offline=offline, **kwargs)
        #
        evrun.run(video=False, dur=dur)
        evrun.eval()
        # evrun.plot_models()
        evrun.plot_results()
        return evrun

    def modelConf_analysis(self, avgVSvar=False, mods3=False):
        warnings.filterwarnings('ignore')
        if 'modelConfs' not in self.config.keys():
            self.config.modelConfs = dNl.NestDict({'average': {}, 'variable': {}, 'individual': {}, '3modules': {}})
        M = preg.larva_conf_dict
        if avgVSvar:
            entries_avg, mIDs_avg = M.adapt_6mIDs(refID=self.config.refID, e=self.endpoint_data, c=self.config)
            self.config.modelConfs.average = entries_avg
            self.save_config(add_reference=True)
            self.store_model_graphs(mIDs=mIDs_avg)
            self.eval_model_graphs(mIDs=mIDs_avg, norm_modes=['raw', 'minmax'], id='6mIDs_avg', N=10)
            preg.graph_dict.dict['mpl'](data=M.diff_df(mIDs=mIDs_avg), font_size=18, save_to=self.dir_dict.model_tables,
                                        name='avg_mIDs_diffs')

            entries_var, mIDs_var = M.add_var_mIDs(refID=self.config.refID, e=self.endpoint_data, c=self.config,
                                                   mID0s=mIDs_avg)
            self.config.modelConfs.variable = entries_var
            self.save_config(add_reference=True)
            self.eval_model_graphs(mIDs=mIDs_var, norm_modes=['raw', 'minmax'], id='6mIDs_var', N=10)
            self.eval_model_graphs(mIDs=mIDs_avg[:3] + mIDs_var[:3], norm_modes=['raw', 'minmax'], id='3mIDs_avgVSvar1',
                                   N=10)
            self.eval_model_graphs(mIDs=mIDs_avg[3:] + mIDs_var[3:], norm_modes=['raw', 'minmax'], id='3mIDs_avgVSvar2',
                                   N=10)
        if mods3:
            entries_3m, mIDs_3m = M.adapt_3modules(refID=self.config.refID, e=self.endpoint_data, c=self.config)
            self.config.modelConfs['3modules'] = entries_3m
            self.save_config(add_reference=True)
            self.store_model_graphs(mIDs=mIDs_3m)
            # self.eval_model_graphs(mIDs=mIDs_avg, norm_modes=['raw', 'minmax'], id='6mIDs_avg', N=10)
            preg.graph_dict.dict['mpl'](data=M.diff_df(mIDs=mIDs_3m), font_size=18, save_to=self.dir_dict.model_tables,
                                        name='3fitted_modules_diffs')

            dIDs = ['NEU', 'SIN', 'CON']
            for Cmod in ['RE', 'SQ', 'GAU', 'CON']:
                for Ifmod in ['PHI', 'SQ', 'DEF']:
                    mIDs = [f'{Cmod}_{Tmod}_{Ifmod}_DEF_fit' for Tmod in dIDs]
                    id=f'Tmod_variable_Cmod_{Cmod}_Ifmod_{Ifmod}'
                    d.eval_model_graphs(mIDs=mIDs, dIDs=dIDs, norm_modes=['raw', 'minmax'],id=id, N=10)


if __name__ == '__main__':
    from lib.registry.pars import preg
    from lib.aux import dictsNlists as dNl
    import pandas as pd

    refID = 'None.150controls'
    # refID='None.Sims2019_controls'
    h5_ks = ['contour', 'midline', 'epochs', 'base_spatial', 'angular', 'dspNtor']
    h5_ks = ['epochs', 'angular', 'dspNtor']
    # h5_ks = []

    d = preg.loadRef(refID)
    d.load(h5_ks=h5_ks)
    # entries_3m = d.config.modelConfs['3modules']

    dIDs = ['NEU', 'SIN', 'CON']
    for Cmod in ['RE', 'SQ', 'GAU', 'CON']:
        for Ifmod in ['PHI', 'SQ', 'DEF']:
            mIDs = [f'{Cmod}_{Tmod}_{Ifmod}_DEF_fit' for Tmod in dIDs]
            id = f'Tmod_variable_Cmod_{Cmod}_Ifmod_{Ifmod}'
            d.eval_model_graphs(mIDs=mIDs, dIDs=dIDs, norm_modes=['raw', 'minmax'], id=id, N=5)
    # for mID,m in entries_3m.items():
    #     print(mID, m)
    # d.store_model_graphs(mIDs=mIDs_3m)
    # d.modelConf_analysis(mods3=True)
