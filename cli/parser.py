from typing import List
from argparse import ArgumentParser


from lib import reg, aux, sim
from cli.conf_aux import update_exp_conf


class ParsArg:
    """
    Create a single parser argument
    This is a class used to populate a parser with arguments and get their values.
    """

    def __init__(self, short, key, **kwargs):
        self.key = key
        self.args = [f'-{short}', f'--{key}']
        self.kwargs = kwargs

    def add(self, p):
        p.add_argument(*self.args, **self.kwargs)
        return p

    def get(self, input):
        return getattr(input, self.key)


def build_ParsArg(name, k=None, h='', dtype=float, v=None, vs=None):
    if k is None:
        k = name
    d = {
        'key': name,
        'short': k,
        'help': h,
    }
    if dtype == bool:
        d['action'] = 'store_true' if not v else 'store_false'
    elif dtype == List[str]:
        d['type'] = str
        d['nargs'] = '+'
        if vs is not None:
            d['choices'] = vs
    elif dtype == List[int]:
        d['type'] = int
        d['nargs'] = '+'
        if vs is not None:
            d['choices'] = vs
    else:
        d['type'] = dtype
        if vs is not None:
            d['choices'] = vs
        if v is not None:
            d['default'] = v
            d['nargs'] = '?'
    return {name: d}


def par_dict(d0):
    if d0 is None:
        return None

    def par(name, dtype=float, v=None, vs=None, h='', k=None, **kwargs):
        return build_ParsArg(name, k, h, dtype, v, vs)

    d = {}
    for n, v in d0.items():
        if 'v' in v.keys() or 'k' in v.keys() or 'h' in v.keys():
            entry = par(n, **v)
        else:
            entry = {n: {'dtype': dict, 'content': par_dict(d0=v)}}
        d.update(entry)
    return d


def parser_dict(name):
    dic = par_dict(reg.par.PI[name])
    try:
        parsargs = {k: ParsArg(**v) for k, v in dic.items()}
    except:
        parsargs = {}
        for k, v in dic.items():
            for kk, vv in v['content'].items():
                parsargs[kk] = ParsArg(**vv)
    return aux.AttrDict(parsargs)


class Parser:
    """
    Create an argument parser for a group of arguments (normally from a dict).
    """

    def __init__(self, name):
        self.name = name
        self.parsargs = parser_dict(name)
        # self.parsargs = reg.parsers.parser_dict[name]

    def add(self, parser=None):
        if parser is None:
            parser = ArgumentParser()
        for k, v in self.parsargs.items():
            parser = v.add(parser)
        return parser

    def get(self, input):
        dic = {k: v.get(input) for k, v in self.parsargs.items()}
        d = reg.get_null(name=self.name, **dic)
        return d


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
        return aux.AttrDict({k: v.get(input) for k, v in self.parsers.items()})


def run_template(sim_mode, args, d):
    kws={'id' : args.id}
    if sim_mode == 'Replay':
        run = sim.ReplayRun(**d['Replay'], **kws)
        run.run()
    elif sim_mode == 'Batch':
        conf = reg.loadConf(conftype='Batch', id=args.experiment)
        conf.batch_type = args.experiment
        conf.exp = update_exp_conf(conf.exp, sim_params=d['sim_params'], N=args.Nagents, mIDs=args.models)

        exec = sim.Exec(mode='batch', conf=conf, run_externally=False, **kws)
        exec.run()
    elif sim_mode == 'Exp':
        # conf = reg.expandConf(id=args.experiment, conftype='Exp')
        # conf.experiment = args.experiment
        # conf.sim_params = aux.AttrDict(d['sim_params'])
        # if conf.sim_params.duration is None:
        #     conf.sim_params.duration =reg.loadConf(id=args.experiment, conftype='Exp').sim_params.duration
        # if args.models is not None:
        #     conf = update_exp_models(conf, args.models)
        # if args.Nagents is not None:
        #     for gID, gConf in conf.larva_groups.items():
        #         gConf.distribution.N = args.Nagents


        conf = update_exp_conf(exp=args.experiment, sim_params=d['sim_params'], N=args.Nagents, mIDs=args.models)
        run = sim.ExpRun(parameters=conf,
                     screen_kws={'vis_kwargs': d['visualization']}, **kws)
        ds = run.simulate()
        if args.analysis:
            run.analyze(show=args.show)

    elif sim_mode == 'Ga':
        conf = reg.expandConf(id=args.experiment, conftype='Ga')
        conf.experiment = args.experiment
        conf.offline=args.offline
        conf.show_screen=args.show_screen
        conf.sim_params = aux.AttrDict(d['sim_params'])
        # conf = update_exp_conf(exp=args.experiment, d=d, offline=args.offline, show_screen=args.show_screen,conf_type='Ga')
        conf.ga_select_kws = d['ga_select_kws']

        if args.base_model is not None:
            conf.ga_build_kws.base_model = args.base_model
        if args.bestConfID is not None:
            conf.ga_build_kws.bestConfID = args.bestConfID
        GA = sim.GAlauncher(parameters=conf, **kws)
        best_genome = GA.simulate()
    elif sim_mode == 'Eval':
        evrun = sim.EvalRun(**d.Eval, show=args.show_screen, **kws)
        evrun.simulate()
        evrun.plot_results()
        evrun.plot_models()


def get_parser(sim_mode, parser=None):
    dic = aux.AttrDict({
        'Batch': [['sim_params'], ['e', 'N', 'ms']],
        'Eval': [['Eval'], ['hide']],
        'Exp': [['sim_params', 'visualization'], ['e', 'N', 'ms', 'a']],
        'Ga': [['sim_params', 'ga_select_kws'], ['e', 'mID0', 'mID1', 'offline', 'hide']],
        'Replay': [['Replay'], []]
    })
    mks, ks = dic[sim_mode]

    MP = MultiParser(mks)
    p = MP.add(parser)
    p.add_argument('-id', '--id', type=str, help='The simulation ID. If not provided a default is generated')
    for k in ks:
        if k == 'e':
            p.add_argument('experiment', choices=reg.storedConf(sim_mode), help='The experiment mode')
        elif k == 'N':
            p.add_argument('-N', '--Nagents', type=int, help='The number of simulated larvae in each larva group')
        elif k == 'ms':
            p.add_argument('-ms', '--models', type=str, nargs='+',
                           help='The larva models to use for creating the simulation larva groups')
        elif k == 'mID0':
            p.add_argument('-mID0', '--base_model', choices=reg.storedConf('Model'),
                           help='The model configuration to optimize')
        elif k == 'mID1':
            p.add_argument('-mID1', '--bestConfID', type=str,
                           help='The model configuration ID to store the best genome')
        elif k == 'a':
            p.add_argument('-a', '--analysis', action="store_true", help='Whether to exec analysis')
            p.add_argument('-show', '--show', action="store_true", help='Whether to show the analysis plots')
        elif k == 'offline':
            p.add_argument('-offline', '--offline', action="store_true",
                           help='Whether to exec a full LarvaworldSim environment')
        elif k == 'hide':
            p.add_argument('-hide', '--show_screen', action="store_false",
                           help='Whether to render the screen visualization')

    return MP, p

