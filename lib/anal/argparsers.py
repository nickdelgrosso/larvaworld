import copy
from argparse import ArgumentParser

from lib.aux.colsNstr import N_colors
import lib.aux.dictsNlists as dNl
from lib.conf.pars.pars import ParDict
from lib.conf.base.dtypes import null_dict

# 
class Parser:
    """
    Create an argument parser for a group of arguments (normally from a dict).
    """

    # def __init__(self, name):
    #     self.name = name
    #     d0 = ParDict.init_dict[name]
    #     try :
    #         self.parsargs =build_ParsDict2(d0)
    #     except :
    #         self.parsargs = build_ParsDict(d0)

    def __init__(self, name):
        self.name = name
        self.parsargs =ParDict.parser_dict[name]


    def add(self, parser=None):
        if parser is None:
            parser = ArgumentParser()
        for k, v in self.parsargs.items():
            parser = v.add(parser)
        return parser

    def get(self, input):
        dic = {k: v.get(input) for k, v in self.parsargs.items()}
        # print(dic)
        return null_dict(self.name, **dic)


class MultiParser:
    """
    Combine multiple parsers under a single multi-parser
    """

    def __init__(self, names):
        self.parsers = {n: Parser(n) for n in names}

    def add(self, parser=None):
        if parser is None:
            parser = ArgumentParser()
        for k, v in self.parsers.items():
            parser = v.add(parser)
        return parser

    def get(self, input):
        return dNl.NestDict({k: v.get(input) for k, v in self.parsers.items()})

def update_exp_conf(exp, d=None, N=None, models=None, arena=None, conf_type='Exp', **kwargs):
    from lib.conf.stored.conf import expandConf
    from lib.conf.pars.opt_par import SimParConf
    try :
        exp_conf = expandConf(exp, conf_type)
    except :
        exp_conf = expandConf(exp, conf_type='Exp')
    if arena is not None :
        exp_conf.env_params.arena = arena
    if d is None:
        d = {'sim_params': null_dict('sim_params')}
    exp_conf.sim_params = SimParConf(exp=exp, conf_type=conf_type, **d['sim_params']).dict
    if models is not None:
        if conf_type in ['Exp', 'Eval'] :
            exp_conf = update_exp_models(exp_conf, models)
    if N is not None:
        if conf_type == 'Exp':
            for gID, gConf in exp_conf.larva_groups.items():
                gConf.distribution.N = N
    exp_conf.update(**kwargs)
    return exp_conf


def update_exp_models(exp_conf, models, N=None):
    from lib.conf.stored.conf import expandConf, kConfDict
    larva_groups = {}
    Nmodels = len(models)
    colors = N_colors(Nmodels)
    gConf0 = list(exp_conf.larva_groups.values())[0]
    if isinstance(models, dict):
        for i, ((gID, m), col) in enumerate(zip(models.items(), colors)):
            gConf = dNl.NestDict(copy.deepcopy(gConf0))
            gConf.default_color = col
            gConf.model = m
            larva_groups[gID] = gConf
    elif isinstance(models, list):
        for i, (m, col) in enumerate(zip(models, colors)):
            gConf = dNl.NestDict(copy.deepcopy(gConf0))
            gConf.default_color = col
            if isinstance(m, dict):
                gConf.model = m
                larva_groups[f'LarvaGroup{i}'] = gConf
            elif m in kConfDict('Model'):
                gConf.model = expandConf(m, 'Model')
                larva_groups[m] = gConf
            elif m in kConfDict('Brain'):
                gConf.model = expandConf(m, 'Brain')
                larva_groups[m] = gConf
            else:
                raise ValueError(f'{m} larva-model or brain-model does not exist!')
    if N is not None:
        for gID, gConf in larva_groups.items():
            gConf.distribution.N = N
    exp_conf.larva_groups = larva_groups
    return exp_conf


if __name__ == '__main__':
    conf = update_exp_conf(exp='chemorbit', d=None, N=None, models=None, arena=None, conf_type='Eval')

    print(conf.sim_params)

    # raise