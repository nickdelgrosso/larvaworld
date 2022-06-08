from param import Parameterized
from typing import List, Tuple

from lib.conf.base.pars import ParDict, func_dic
import lib.aux.dictsNlists as dNl


def runtime_pars(PF=ParDict.dict):
    return [v.d for k, v in PF.items()]


def getPar(k=None, p=None, d=None, to_return='d', PF=ParDict):
    if k is not None:
        d0=PF.dict
        k0=k
    elif d is not None:
        d0 = PF.ddict
        k0 = d
    elif p is not None:
        d0 = PF.pdict
        k0 = p

    if type(k0) == str:
        par = d0[k0]
        if type(to_return) == list:
            return [getattr(par, i) for i in to_return]
        elif type(to_return) == str:
            return getattr(par, to_return)
    elif type(k0) == list:
        pars = [d0[i] for i in k0]
        if type(to_return) == list:
            return [[getattr(par, i) for par in pars] for i in to_return]
        elif type(to_return) == str:
            return [getattr(par, to_return) for par in pars]


def base_dtype(dtype):
    if dtype in [float, Tuple[float], List[float], List[Tuple[float]]]:
        base_t = float
    elif dtype in [int, Tuple[int], List[int], List[Tuple[int]]]:
        base_t = int
    else:
        base_t = dtype
    return base_t


def init2opt_dict(name):
    from lib.conf.base.init_pars import init_pars
    init_dic = init_pars()[name]
    opt_dict = {}
    for k, v in init_dic.items():
        if 't' not in v.keys():
            v['t'] = float
    for k, v in init_dic.items():
        dtype = v['t']
        dtype0 = base_dtype(dtype)
        func = func_dic[dtype]
        kws = {
            'doc': v['h'],
            'default': v['v'] if 'v' in v.keys() else None,
            'label': v['lab'] if 'lab' in v.keys() else k,

        }
        if dtype0 in [float, int]:
            b0 = v['min'] if 'min' in v.keys() else dtype0(0.0)
            b1 = v['max'] if 'max' in v.keys() else None
            bounds = (b0, b1)
            step = v['dv'] if 'dv' in v.keys() else 0.1
            kws.update({
                'step': step,
                'bounds': bounds,
            })

        opt_dict[k] = func(**kws)
    return opt_dict


class OptParDict(Parameterized):
    def __init__(self, name, **kwargs):
        super().__init__(name=name)
        opt_dict = {name: init2opt_dict(name)}
        for k, v in opt_dict[name].items():
            self.param.add_parameter(k, v)
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @property
    def dict(self):
        dic = self.param.values()
        dic.pop('name', None)
        return dNl.AttrDict.from_nested_dicts(dic)

    @property
    def entry(self):
        return dNl.AttrDict.from_nested_dicts({self.name: self.dict})


class SimParConf(OptParDict):
    def __init__(self, exp=None, conf_type='Exp', sim_ID=None, path=None, duration=None, **kwargs):
        if exp is not None and conf_type is not None:
            from lib.conf.stored.conf import loadConf, next_idx
            if duration is None:
                try:
                    exp_conf = loadConf(exp, conf_type)
                    duration = exp_conf.sim_params.duration
                except:
                    duration = 3.0
            if sim_ID is None:
                sim_ID = f'{exp}_{next_idx(exp, conf_type)}'
            if path is None:
                if conf_type == 'Exp':
                    path = f'single_runs/{exp}'
                elif conf_type == 'Ga':
                    path = f'ga_runs/{exp}'
                elif conf_type == 'Batch':
                    path = f'batch_runs/{exp}'
                elif conf_type == 'Eval':
                    path = f'eval_runs/{exp}'
        super().__init__(name='sim_params', sim_ID=sim_ID, path=path, duration=duration, **kwargs)


if __name__ == '__main__':
    print(getPar(['b', 'fo', 'ro', 'fov', 'Act_tur','x', 'y', 'd', 'v', 'A_tur']))
    pass
    # raise
