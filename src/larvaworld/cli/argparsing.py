from typing import List
from argparse import ArgumentParser

from larvaworld.lib import reg, aux, sim



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

#
# def build_ParsArg(name, k=None, h='', dtype=float, v=None, vs=None, **kwargs):
#     if k is None:
#         k = name
#     d = {
#         'key': name,
#         'short': k,
#         'help': h,
#     }
#     if dtype == bool:
#         d['action'] = 'store_true' if not v else 'store_false'
#     elif dtype == List[str]:
#         d['type'] = str
#         d['nargs'] = '+'
#         if vs is not None:
#             d['choices'] = vs
#     elif dtype == List[int]:
#         d['type'] = int
#         d['nargs'] = '+'
#         if vs is not None:
#             d['choices'] = vs
#     else:
#         d['type'] = dtype
#         if vs is not None:
#             d['choices'] = vs
#         if v is not None:
#             d['default'] = v
#             d['nargs'] = '?'
#     return d


# def parser_dict(d0):
#     p = aux.AttrDict()
#     for n, v in d0.items():
#         if 'v' in v.keys() or 'k' in v.keys() or 'h' in v.keys():
#             entry = build_ParsArg(n, **v)
#             p[n] = ParsArg(**entry)
#         else:
#             p[n] = parser_dict(v)
#
#     return p.flatten()


class Parser:
    """
    Create an argument parser for a group of arguments (normally from a dict).
    """

    def __init__(self, name):
        self.name = name
        # d0=reg.par.PI[name]
        self.parsargs = self.parser_dict(reg.par.PI[name])

    def add(self, parser=None):
        if parser is None:
            parser = ArgumentParser()
        for k, v in self.parsargs.items():
            parser = v.add(parser)
        return parser

    def get(self, input):
        dic = aux.AttrDict({k: v.get(input) for k, v in self.parsargs.items()})
        return dic.unflatten()

    def parser_dict(self, d0):
        p = aux.AttrDict()
        for n, v in d0.items():
            if 'v' in v.keys() or 'k' in v.keys() or 'h' in v.keys():
                entry = self.build_ParsArg(n, **v)
                p[n] = ParsArg(**entry)
            else:
                p[n] = self.parser_dict(v)

        return p.flatten()

    def build_ParsArg(self, name, k=None, h='', dtype=float, v=None, vs=None, **kwargs):
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


def update_exp_conf(type, N=None, mIDs=None):
    '''
    Loads the configuration of an experiment based on its ID.
    Modifies the included larvagroups
    Args:
        type: The experiment type
        N: Overwrite the number of agents per larva group
        mIDs: Overwrite the larva models used in the experiment.If not None a larva group per model ID will be simulated.

    Returns:
        The experiment's configuration
    '''
    conf = reg.stored.getExp(type)
    conf.experiment = type

    if mIDs is not None:
        Nm = len(mIDs)
        gConfs = list(conf.larva_groups.values())
        if len(conf.larva_groups) != Nm:
            gConfs = [gConfs[0]] * Nm
            for gConf, col in zip(gConfs, aux.N_colors(Nm)):
                gConf.default_color = col
        conf.larva_groups = aux.AttrDict({mID: {} for mID in mIDs})
        for mID, gConf in zip(mIDs, gConfs):
            conf.larva_groups[mID] = gConf
            conf.larva_groups[mID].model = reg.stored.getModel(mID)

    if N is not None:
        for gID, gConf in conf.larva_groups.items():
            gConf.distribution.N = N

    return conf

def run_template(sim_mode, args, kw_dicts):
    '''
    Generates the simulation configuration and launches it
    Args:
        sim_mode: The simulation mode
        args: Parsed arguments
        kw_dicts: Parsed argument dicts

    Returns:
        -nothing-
    '''
    kws=aux.AttrDict({'id' : args.id, **kw_dicts['sim_params']})
    if sim_mode == 'Replay':
        conf =kw_dicts['Replay']
        run = sim.ReplayRun(parameters=conf, **kws)
        run.run()
    elif sim_mode == 'Batch':
        kws.mode='batch'
        kws.run_externally=False
        kws.conf = reg.stored.get(conftype='Batch', id=args.experiment)
        kws.conf.batch_type = args.experiment
        kws.conf.exp = update_exp_conf(kws.conf.exp, N=args.Nagents, mIDs=args.models)
        if kws.duration is not None:
            kws.duration = kws.conf.exp.duration
        exec = sim.Exec(**kws)
        exec.run()
    elif sim_mode == 'Exp':
        conf = update_exp_conf(args.experiment, N=args.Nagents, mIDs=args.models)
        if kws.duration is None:
            kws.duration = conf.sim_params.duration
        kws.screen_kws = {'vis_kwargs': kw_dicts['visualization']}

        run = sim.ExpRun(parameters=conf, **kws)
        ds = run.simulate()
        if args.analysis:
            run.analyze(show=args.show)

    elif sim_mode == 'Ga':
        conf = reg.stored.expand(id=args.experiment, conftype='Ga')
        kws.experiment = args.experiment
        if kws.duration is None:
            kws.duration = conf.sim_params.duration
        conf.ga_build_kws.ga_select_kws = kw_dicts['ga_select_kws']
        temp=kw_dicts['ga_space_kws']
        if temp.base_model is not None:
            conf.ga_build_kws.ga_space_kws.base_model = temp.base_model

        if temp.bestConfID is not None:
            conf.ga_build_kws.ga_space_kws.bestConfID = temp.bestConfID
        conf.ga_build_kws.ga_space_kws.init_mode = temp.init_mode
        temp1 = kw_dicts['ga_eval_kws']
        if temp1.fitness_target_refID is not None:
            conf.ga_build_kws.ga_eval_kws.fitness_target_refID = temp1.fitness_target_refID

        GA = sim.GAlauncher(parameters=conf, **kws)
        best_genome = GA.simulate()
    elif sim_mode == 'Eval':
        conf =kw_dicts.Eval
        evrun = sim.EvalRun(parameters=conf, **kws)
        evrun.simulate()
        evrun.plot_results()
        evrun.plot_models()


def get_parser(sim_mode, parser=None):
    '''
    Prepares a dedicated parser for each simulation mode and adds it to the main parser
    Args:
        sim_mode: The simulation mode
        parser: Main parser

    Returns:
        MPs : Dictionary of dedicated parsers for each simulation mode
    '''
    dic = aux.AttrDict({
        'Batch': [[], ['e', 'N', 'ms']],
        'Eval': [['Eval'], []],
        'Exp': [['visualization'], ['e', 'N', 'ms', 'a']],
        'Ga': [['ga_select_kws', 'ga_space_kws', 'ga_eval_kws'], ['e']],
        'Replay': [['Replay'], []]
    })
    mks, ks = dic[sim_mode]
    mks.append('sim_params')
    MP = MultiParser(mks)
    p = MP.add(parser)
    p.add_argument('-id', '--id', type=str, help='The simulation ID. If not provided a default is generated')
    # p.add_argument('-no_store', '--store_data', action="store_false", help='Whether to store the simulation data or not')
    for k in ks:
        if k == 'e':
            p.add_argument('experiment', choices=reg.stored.confIDs(sim_mode), help='The experiment mode')
        # elif k == 't':
        #     p.add_argument('-t', '--duration', type=float, help='The duration of the simulation in minutes')
        # elif k == 'Box2D':
        #     p.add_argument('-Box2D', '--Box2D', action="store_true", help='Whether to use the Box2D physics engine or not')
        elif k == 'N':
            p.add_argument('-N', '--Nagents', type=int, help='The number of simulated larvae in each larva group')
        elif k == 'ms':
            p.add_argument('-ms', '--models', type=str, nargs='+',
                           help='The larva models to use for creating the simulation larva groups')
        # elif k == 'mID0':
        #     p.add_argument('-mID0', '--base_model', choices=reg.storedConf('Model'),
        #                    help='The model configuration to optimize')
        # elif k == 'mID1':
        #     p.add_argument('-mID1', '--bestConfID', type=str,
        #                    help='The model configuration ID to store the best genome')
        elif k == 'a':
            p.add_argument('-a', '--analysis', action="store_true", help='Whether to exec analysis')
            p.add_argument('-show', '--show', action="store_true", help='Whether to show the analysis plots')
        # elif k == 'offline':
        #     p.add_argument('-offline', '--offline', action="store_true",
        #                    help='Whether to exec a full LarvaworldSim environment')
        # elif k == 'hide':
        #     p.add_argument('-hide', '--show_display', action="store_false",
        #                    help='Whether to render the screen visualization')

    return MP

