import os

import numpy as np
import param

import larvaworld
from larvaworld.lib import reg, aux, util

CONFTYPES = ['Ref', 'Model', 'ModelGroup', 'Env', 'Exp', 'ExpGroup', 'Essay', 'Batch', 'Ga', 'Tracker',
                          'Group', 'Trial', 'Life', 'Body', 'Tree', 'Source']

GROUPTYPES = ['LarvaGroup', 'SourceGroup', 'epoch']

Path = aux.AttrDict({k : f'{reg.CONF_DIR}/{k}.txt' for k in CONFTYPES})

def build_ConfTypeSubkeys():
    d0 = {k: {} for k in CONFTYPES}
    d1 = {
        'Batch': {'exp': 'Exp'},
        'Ga': {'env_params': 'Env'},
        'Exp': {'env_params': 'Env',
                'trials': 'Trial',
                'larva_groups': 'Model',
                }
    }
    d0.update(d1)
    return aux.AttrDict(d0)

CONFTYPE_SUBKEYS = build_ConfTypeSubkeys()


def build_GroupTypeSubkeys():
    d0 = {k: {} for k in GROUPTYPES}
    d1 = {
        'LarvaGroup': {'Model'},
        # 'Ga': {'env_params': 'Env'},
        # 'Exp': {'env_params': 'Env',
        #         'trials': 'Trial',
        #         'larva_groups': 'Model',
        #         }
    }
    d0.update(d1)
    return aux.AttrDict(d0)

GROUPTYPE_SUBKEYS = build_GroupTypeSubkeys()


CONFTREE = aux.AttrDict({k : aux.load_dict(Path[k]) for k in CONFTYPES})

def build_conf_tree_expanded():
    c0 = aux.AttrDict({k : aux.load_dict(Path[k]) for k in CONFTYPES})
    sk = CONFTYPE_SUBKEYS
    for confType0 in c0.keys():
        if confType0 in sk.keys():
            pairs = sk[confType0]
            for id, conf in c0[confType0].items():
                for subID, confType in pairs.items():


                    if subID in conf.keys():
                        if isinstance(conf[subID], str) and conf[subID] in c0[confType].keys():
                            conf[subID]=c0[confType][conf[subID]]
                        elif (subID, confType) == ('larva_groups', 'Model'):
                            for gID, gConf in conf[subID].items():
                                mID=gConf.model
                                if mID in c0['Model'].keys():
                                    gConf.model=c0['Model'][mID]
                                else:
                                    # print(f'{mID} not found')
                                    pass
                                    # raise
    return c0

CONFTREE_EXPANDED = build_conf_tree_expanded()


class BaseType:
    def __init__(self, k):
        self.k = k
        if k in reg.par.PI.keys():
            self.dict0 = reg.par.PI[k]
            self.mdict = util.init2mdict(self.dict0)
            self.ks = util.get_ks(self.mdict)
        else:
            self.dict0 = None
            self.mdict = None
            self.ks = None


    def gConf_kws(self, dic):
        kws0 = {}
        for k, kws in dic.items():
            m0 = self.mdict[k]
            kws0[k] = self.gConf(m0, **kws)
        return aux.AttrDict(kws0)

    def gConf(self, m0=None, kwdic=None, **kwargs):
        if m0 is None:
            if self.mdict is None:
                return None
            else:
                m0 = self.mdict
        if kwdic is not None:
            kws0 = self.gConf_kws(kwdic)
            kwargs.update(kws0)

        return aux.AttrDict(util.gConf(m0, **kwargs))

    def entry(self, id, **kwargs):
        return aux.AttrDict({id: self.gConf(**kwargs)})



def lgs(mIDs, ids=None, cs=None,**kwargs):

    if ids is None:
        ids = mIDs
    N = len(mIDs)
    if cs is None :
        cs = aux.N_colors(N)
    return aux.AttrDict(aux.merge_dicts([lg(id, c=c, mID=mID, **kwargs) for mID, c, id in zip(mIDs, cs, ids)]))


def lg(id=None, c='black', N=1, mode='uniform', sh='circle', loc=(0.0, 0.0), ors=(0.0, 360.0),
       s=(0.0, 0.0), mID='explorer',age=0.0, epochs={},  o=None,sample = None, expand=False, **kwargs):

    if mID is not None :
        m = mID if not expand else stored.getModel(mID)
        if id is None:
            id=mID
    else :
        m=None
    if id is None:
        id='LarvaGroup'

    if type(s) == float:
        s = (s, s)
    kws = {'kwdic': {
        'distribution': {'N': N, 'scale': s, 'orientation_range': ors, 'loc': loc, 'shape': sh, 'mode': mode},
        'life_history': {'age': age,'epochs': epochs}
    },
           'default_color': c, 'model': m,'sample':sample,  **kwargs}
    if o is not None:
        kws['odor'] = o

    return stored.group.LarvaGroup.entry(id=id, **kws)

# def GTRvsS2(N=1, age=72.0, q=1.0, h_starved=0.0, sample='exploration.150controls', substrate_type='standard',pref='',
#                 navigator=False, expand=False, **kwargs):
#     if age==0.0 :
#         epochs={}
#     else :
#         if h_starved==0:
#             eps={
#                 0 : {'start': 0.0, 'stop' : age, 'substate':{'type': substrate_type, 'quality': q}}
#             }
#         else :
#             eps = {
#                 0: {'start': 0.0, 'stop': age-h_starved, 'substate': {'type': substrate_type, 'quality': q}},
#                 1: {'start': age-h_starved, 'stop': age, 'substate': {'type': substrate_type, 'quality': 0}},
#             }
#         epochs={}
#         for id,kws in eps.items():
#             epochs.update(stored.group.epoch.entry(id=id, **kws))
#
#
#
#
#     kws0 = {
#         'kwdic': {
#             'distribution': {'N': N, 'scale': (0.005, 0.005)},
#             'life_history': {'age': age,
#                              'epochs': epochs,
#                              },
#         'odor':{}
#         },
#         'sample': sample,
#     }
#
#     mcols = ['blue', 'red']
#     mID0s = ['rover', 'sitter']
#     lgs = {}
#     for mID0, mcol in zip(mID0s, mcols):
#         id=f'{pref}{mID0.capitalize()}'
#
#
#
#         if navigator :
#             mID0=f'navigator_{mID0}'
#         if expand:
#             mID0=stored.getModel(mID0)
#
#
#
#         kws = {
#             'default_color': mcol,
#             'model': mID0,
#             **kws0
#         }
#
#         lgs.update(stored.group.LarvaGroup.entry(id, **kws))
#     return aux.AttrDict(lgs)





def next_idx(id, conftype='Exp'):
    f = f'{reg.CONF_DIR}/SimIdx.txt'
    if not os.path.isfile(f):
        d = aux.AttrDict({k: {} for k in ['Exp', 'Batch', 'Essay', 'Eval', 'Ga']})
    else:
        d = aux.load_dict(f)

    if not conftype in d.keys():
        d[conftype] = {}
    if not id in d[conftype].keys():
        d[conftype][id] = 0
    d[conftype][id] += 1
    aux.save_dict(d, f)
    return d[conftype][id]



class StoredConfRegistry :
    def __init__(self):
        self.group=aux.AttrDict({k: BaseType(k=k) for k in GROUPTYPES})
        self.conf=aux.AttrDict({k: BaseType(k=k) for k in CONFTYPES})

    def ConfPath(self, conftype):
        return Path[conftype]

    def get_dict(self, conftype):
        path=self.ConfPath(conftype)
        return aux.load_dict(path)

    def set_dict(self, conftype, d):
        path = self.ConfPath(conftype)
        aux.save_dict(d, path)

    def resetDict(self,conftype, init=False):
        dd = reg.funcs.stored_confs[conftype]()

        if os.path.isfile(self.ConfPath(conftype)):
            if init:
                return
            else:
                d = self.get_dict(conftype)
        else:
            d = {}

        N0, N1 = len(d), len(dd)

        d.update(dd)

        Ncur = len(d)
        Nnew = Ncur - N0
        Nup = N1 - Nnew
        self.set_dict(conftype, d)
        reg.vprint(f'{conftype}  configurations : {Nnew} added , {Nup} updated,{Ncur} now existing', 1)

    def resetConfs(self, conftypes=None, **kwargs):
        if conftypes is None:
            conftypes = CONFTYPES

        for conftype in conftypes:
            self.resetDict(conftype, **kwargs)

    def confIDs(self, conftype):
        d=self.get_dict(conftype)
        return sorted(list(d.keys()))

    @ property
    def RefIDs(self):
        return self.confIDs('Ref')

    @property
    def ModelIDs(self):
        return self.confIDs('Model')

    def get(self, conftype, id):
        d=self.get_dict(conftype)
        if id in d.keys():
            return aux.AttrDict(d[id])
        else:
            reg.vprint(f'{conftype} Configuration {id} does not exist', 1)
            raise ValueError()

    def set(self, conftype, id, conf, mode='overwrite'):
        d=self.get_dict(conftype)
        if id in d.keys() and mode == 'update':
            d[id] = d[id].update_nestdict(conf.flatten())
        else:
            d[id] = aux.AttrDict(conf)
        self.set_dict(conftype, d)
        reg.vprint(f'{conftype} Configuration saved under the id : {id}', 1)

    def delete(self, conftype, id=None):
        if id is not None:
            d=self.get_dict(conftype)
            if id in d.keys():
                d.pop(id, None)
                self.set_dict(conftype, d)
                reg.vprint(f'Deleted {conftype} configuration under the id : {id}', 1)

    def expand(self, conftype, id=None, conf=None):
        if conf is None:
            if id in self.confIDs(conftype):

                conf = self.get(conftype, id)
            else:
                return None
        subks = CONFTYPE_SUBKEYS[conftype]
        if len(subks) > 0:
            for subID, subk in subks.items():
                ids = self.confIDs(subk)
                if subID == 'larva_groups' and subk == 'Model':
                    for k, v in conf['larva_groups'].items():
                        if v.model in ids:
                            v.model = self.get(subk, id=v.model)
                else:
                    if conf[subID] in ids:
                        conf[subID] = self.get(subk, id=conf[subID])

        return conf


    def getExp(self, id, expand=True):
        if expand :
            return self.expand(conftype='Exp', id=id)
        else :
            return self.get(conftype='Exp', id=id)

    def getModel(self, id):
        return self.get(conftype='Model', id=id)

    def getEnv(self, id):
        return self.get(conftype='Env', id=id)

    def setModel(self, id, conf):
        return self.set(conftype='Model', id=id, conf=conf)

    def getGroup(self, id):
        return self.get(conftype='Group', id=id)

    def getRefDir(self, id):
        d = self.get_dict('Ref')
        if id in d.keys():
            return d[id]
        else:
            reg.vprint(f'Reference dataset with ID {id} does not exist. Returning None', 1)
            return None

    def getRef(self, id=None, dir=None):
        if dir is None:
            dir=self.getRefDir(id)
        if dir is not None:
            path = f'{dir}/data/conf.txt'
            if os.path.isfile(path):
                c = aux.load_dict(path)
                if 'id' in c.keys():
                    reg.vprint(f'Loaded existing conf {c.id}', 1)
                    return c
        return None

    def loadRef(self, id, load=False, **kwargs):
        c=self.getRef(id)
        if c is not None:
            d = larvaworld.LarvaDataset(config=c, load_data=False)
            if not load:
                reg.vprint(f'Loaded stored reference configuration : {id}')
                return d
            else:
                d.load(**kwargs)
                reg.vprint(f'Loaded stored reference dataset : {id}')
                return d

        else:
            return None


    def setRefID(self, id, dir=None):
        if dir is not None:
            d = self.get_dict('Ref')
            d[id] = dir
            self.set_dict('Ref', d)



    def retrieve_dataset(self,dataset=None, refID=None, dir=None):
        if dataset is None:
            if refID is not None:
                dataset = self.loadRef(refID)
            elif dir is not None:
                dataset = larvaworld.LarvaDataset(dir=f'{reg.DATA_DIR}/{dir}', load_data=False)
            else:
                raise ValueError('Unable to load dataset. Either refID or storage path must be provided. ')
        return dataset

    def imitation_exp(self, refID, model='explorer', **kwargs):
        c = self.getRef(refID)

        kws = {
            'id': 'ImitationGroup',
            'expand': True,
            'sample': refID,
            'model': model,
            'default_color': 'blue',
            'distribution': {'N': c.N},
            'imitation': True,

        }


        exp_conf = reg.get_null('Exp', sim_params=reg.get_null('sim_params', dt=c.dt, duration=c.duration),
                                env_params=c.env_params, larva_groups=full_lg(**kws),experiment='imitation',
                                trials={}, enrichment=reg.par.base_enrich())
        exp_conf.update(**kwargs)
        return exp_conf


stored=StoredConfRegistry()



class ConfSelector(param.Selector):
    """Select among stored configurations of a given conftype by ID"""
    def __init__(self, conftype,default=None,  **kwargs):
        kws={
            'default' : default,
            'objects' : stored.confIDs(conftype),
            'doc' : f'The {conftype} configuration ID',
            **kwargs
        }
        if default is None :
            kws['empty_default']=True
            kws['allow_None']=True
        super().__init__(**kws)



from larvaworld.lib.model import Life, Food, FoodGrid, ThermoScape, WindScape, DiffusionValueLayer, Border, ArenaConf





class LarvaGroup(aux.NestedConf):
    model = ConfSelector('Model')
    # model = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.ModelIDs, doc='The model configuration ID')
    default_color = param.Color('black', doc='The default color of the group')
    odor = aux.ClassAttr(aux.Odor, doc='The odor of the agent')
    distribution = aux.ClassAttr(aux.Larva_Distro,doc='The spatial distribution of the group agents')
    life_history = aux.ClassAttr(Life, doc='The life history of the group agents')
    sample = ConfSelector('Ref')
    # sample = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.RefIDs, doc='The ID of a reference dataset to sample from')
    imitation = param.Boolean(default=False, doc='Whether to imitate the reference dataset.')



    def __init__(self,id=None,**kwargs):
        super().__init__(**kwargs)
        if id is None:
            if self.model is not None :
                id = self.model
            else :
                id = 'LarvaGroup'
        self.id=id


    def entry(self, expand=False, as_entry=True):
        conf = self.nestedConf
        if expand and conf.model is not None:
            conf.model = stored.getModel(conf.model)
        if as_entry :
            return aux.AttrDict({self.id: conf})
        else:
            return conf

    def __call__(self, parameter_dict={}):
        Nids=self.distribution.N
        if self.model is not None:
            m=stored.getModel(self.model)
        else :
            m=None
        kws={
            'm' : m,
            'refID' : self.sample,
            'parameter_dict' : parameter_dict,
            'Nids' : Nids,
        }

        if not self.imitation:
            ps, ors = aux.generate_xyNor_distro(self.distribution)
            ids = [f'{self.id}_{i}' for i in range(Nids)]
            all_pars, refID = util.sampleRef(**kws)
        else:
            ids, ps, ors, all_pars = util.imitateRef(**kws)
        confs = []
        for id, p, o, pars in zip(ids, ps, ors, all_pars):
            conf = {
                'pos': p,
                'orientation': o,
                'default_color': self.default_color,
                'unique_id': id,
                'group': self.id,
                'odor': self.odor,
                'life_history': self.life_history,
                **pars
            }
            confs.append(conf)
        return confs



class ExpConf(aux.NestedConf):
    env_params = ConfSelector('Env')
    # env_params = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Env'), doc='The environment configuration ID')
    trials = ConfSelector('Trial',default='default')
    # trials = param.Selector(default='default', objects=stored.confIDs('Trial'), doc='The trial configuration ID')
    collections = param.ListSelector(default=['pose'],objects=reg.output_keys, doc='The data to collect as output')
    larva_groups = aux.ClassDict(item_type=LarvaGroup, doc='The larva groups')
    sim_params = aux.ClassAttr(aux.SimConf,doc='The simulation configuration')
    enrichment = aux.ClassAttr(aux.EnrichConf, doc='The post-simulation processing')
    experiment = ConfSelector('Exp')
    # experiment = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Exp'), doc='The experiment configuration ID')



    def __init__(self,id=None,**kwargs):
        super().__init__(**kwargs)



# class ReplayConf(aux.NestedConf):
#     refID = ConfSelector('Env')
#     dir = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Env'), doc='The environment configuration ID')
#     overlap_mode = ConfSelector('Trial',default='default')
#     close_view = param.Selector(default='default', objects=stored.confIDs('Trial'), doc='The trial configuration ID')
#     fix_segment = param.ListSelector(default=['pose'],objects=reg.output_keys, doc='The data to collect as output')
#     fix_point = aux.ClassDict(item_type=LarvaGroup, doc='The larva groups')
#     draw_Nsegs = aux.ClassAttr(aux.SimConf,doc='The simulation configuration')
#     track_point = aux.ClassAttr(aux.EnrichConf, doc='The post-simulation processing')
#     time_range = ConfSelector('Exp')
#     dynamic_color = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Exp'), doc='The experiment configuration ID')
#     agent_ids = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Exp'), doc='The experiment configuration ID')
#     transposition = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Exp'), doc='The experiment configuration ID')
#     env_params = param.Selector(default=None,empty_default=True,allow_None=True, objects=stored.confIDs('Exp'), doc='The experiment configuration ID')







def full_lg(id=None, expand=False,as_entry=True,**conf):
    try :
        lg=LarvaGroup(id=id,**conf)
        return lg.entry(expand=expand, as_entry=as_entry)
    except :
        raise

def GTRvsS(N=1, age=72.0, q=1.0, h_starved=0.0, sample='exploration.150controls', substrate_type='standard', pref='',
           navigator=False, expand=False, **kwargs):
    if age == 0.0:
        epochs = {}
    else:
        if h_starved == 0:
            epochs = {
                0: {'age_range': (0.0, age), 'substrate': {'type': substrate_type, 'quality': q}}
            }
        else:
            epochs = {
                0: {'age_range': (0.0, age - h_starved), 'substrate': {'type': substrate_type, 'quality': q}},
                1: {'age_range': (age - h_starved, age), 'substrate': {'type': substrate_type, 'quality': 0}},
            }
    kws0 = {
        'distribution': {'N': N, 'scale': (0.005, 0.005)},
        'life_history': {'age': age, 'epochs': epochs},
        'sample': sample,
        'expand': expand,
    }

    mcols = ['blue', 'red']
    mID0s = ['rover', 'sitter']
    lgs = {}
    for mID0, mcol in zip(mID0s, mcols):
        id = f'{pref}{mID0.capitalize()}'

        if navigator:
            mID0 = f'navigator_{mID0}'

        kws = {
            'id': id,
            'default_color': mcol,
            'model': mID0,
            **kws0
        }

        lgs.update(full_lg(**kws))
    return aux.AttrDict(lgs)


# def GTRvsS(N=1, age=72.0, q=1.0, h_starved=0.0, sample='exploration.150controls', substrate_type='standard', pref='',
#            navigator=False, expand=False, **kwargs):
#     if age == 0.0:
#         epochs = {}
#     else:
#         if h_starved == 0:
#             eps = {
#                 0: {'start': 0.0, 'stop': age, 'substate': {'type': substrate_type, 'quality': q}}
#             }
#         else:
#             eps = {
#                 0: {'start': 0.0, 'stop': age - h_starved, 'substate': {'type': substrate_type, 'quality': q}},
#                 1: {'start': age - h_starved, 'stop': age, 'substate': {'type': substrate_type, 'quality': 0}},
#             }
#         epochs = {}
#         for id, kws in eps.items():
#             epochs.update(stored.group.epoch.entry(id=id, **kws))
#
#     kws0 = {
#         'distribution': {'N': N, 'scale': (0.005, 0.005)},
#         'life_history': {'age': age, 'epochs': epochs},
#         'sample': sample,
#         'expand': expand,
#     }
#
#     mcols = ['blue', 'red']
#     mID0s = ['rover', 'sitter']
#     lgs = {}
#     for mID0, mcol in zip(mID0s, mcols):
#         id = f'{pref}{mID0.capitalize()}'
#
#         if navigator:
#             mID0 = f'navigator_{mID0}'
#
#         kws = {
#             'id': id,
#             'default_color': mcol,
#             'model': mID0,
#             **kws0
#         }
#
#         lgs.update(full_lg(**kws))
#     return aux.AttrDict(lgs)



class SourceGroup(aux.NestedConf):
    default_color = param.Color('black', doc='The default color of the group')
    odor = aux.ClassAttr(aux.Odor, doc='The odor of the source')
    distribution = aux.ClassAttr(aux.Spatial_Distro,doc='The spatial distribution of the group sources')



    def __init__(self,id=None,**kwargs):
        super().__init__(**kwargs)
        if id is None:
            if self.model is not None :
                id = self.model
            else :
                id = 'SourceGroup'
        self.id=id



class FoodConf(aux.NestedConf):
    source_groups = aux.ClassDict(item_type=SourceGroup,  doc='The groups of odor or food sources available in the arena')
    source_units = aux.ClassDict(item_type=Food,  doc='The individual sources  of odor or food in the arena')
    food_grid = aux.ClassAttr(FoodGrid, default=None, doc='The food grid in the arena')

class EnvConf(aux.NestedConf):
    arena = aux.ClassAttr(ArenaConf, doc='The arena configuration')
    food_params = aux.ClassAttr(FoodConf, doc='The food sources in the arena')
    border_list = aux.ClassDict(item_type=Border, doc='The obstacles in the arena')
    odorscape = aux.ClassAttr(DiffusionValueLayer, default=None, doc='The obstacles in the arena')
    windscape = aux.ClassAttr(WindScape, default=None, doc='The obstacles in the arena')
    thermoscape = aux.ClassAttr(ThermoScape, default=None, doc='The obstacles in the arena')

