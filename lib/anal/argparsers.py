import copy
from argparse import ArgumentParser

from lib.registry.pars import preg
from lib.aux import dictsNlists as dNl, colsNstr as cNs
from lib.registry import reg


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
        self.parsargs = preg.parser_dict.parser_dict[name]

    def add(self, parser=None):
        if parser is None:
            parser = ArgumentParser()
        for k, v in self.parsargs.items():
            parser = v.add(parser)
        return parser

    def get(self, input):
        dic = {k: v.get(input) for k, v in self.parsargs.items()}
        d = preg.init_dict.get_null(name=self.name, **dic)
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
        return dNl.NestDict({k: v.get(input) for k, v in self.parsers.items()})


def adjust_sim(exp, conf_type, sim):
    if exp is not None and conf_type is not None:
        # from lib.conf.stored.conf import next_idx
        if sim.duration is None:
            try:
                exp_conf = preg.conftype_dict.loadConf(id=exp, conftype=conf_type)
                sim.duration = exp_conf.sim_params.duration
            except:
                sim.duration = 3.0
        if sim.sim_ID is None:
            sim.sim_ID = f'{exp}_{reg.next_idx(id=exp, conftype=conf_type)}'
        if sim.path is None:
            if conf_type == 'Exp':
                sim.path = f'single_runs/{exp}'
            elif conf_type == 'Ga':
                sim.path = f'ga_runs/{exp}'
            elif conf_type == 'Batch':
                sim.path = f'batch_runs/{exp}'
            elif conf_type == 'Eval':
                sim.path = f'eval_runs/{exp}'
        return sim


def update_exp_conf(exp, d=None, N=None, models=None, arena=None, conf_type='Exp', **kwargs):
    if conf_type == 'Batch':
        exp_conf = preg.loadConf(conftype=conf_type, id=exp)
        batch_id = d['batch_setup']['batch_id']
        if batch_id is None:
            idx = reg.next_idx(id=exp, conftype='Batch')
            batch_id = f'{exp}_{idx}'

        exp_conf.exp = update_exp_conf(exp_conf.exp, d, N, models)
        exp_conf.batch_id = batch_id
        exp_conf.batch_type = exp

        exp_conf.update(**kwargs)
        return exp_conf

    try:
        exp_conf = preg.expandConf(id=exp, conftype=conf_type)
    except:
        exp_conf = preg.expandConf(id=exp, conftype='Exp')

    if arena is not None:
        exp_conf.env_params.arena = arena
    if d is None:
        d = {'sim_params': preg.init_dict.get_null('sim_params')}

    exp_conf.sim_params = adjust_sim(exp=exp, conf_type=conf_type, sim=dNl.NestDict(d['sim_params']))
    if models is not None:
        if conf_type in ['Exp', 'Eval']:
            exp_conf = update_exp_models(exp_conf, models)
    if N is not None:
        if conf_type == 'Exp':
            for gID, gConf in exp_conf.larva_groups.items():
                gConf.distribution.N = N
    exp_conf.update(**kwargs)
    return exp_conf


def update_exp_models(exp_conf, models, N=None):
    larva_groups = {}
    Nmodels = len(models)
    colors = cNs.N_colors(Nmodels)
    gConf0 = list(exp_conf.larva_groups.values())[0]
    if isinstance(models, dict):
        for i, ((gID, m), col) in enumerate(zip(models.items(), colors)):
            gConf = dNl.NestDict(copy.deepcopy(gConf0))
            gConf.default_color = col
            gConf.model = m
            larva_groups[gID] = gConf
    elif isinstance(models, list):
        for i, (m, col) in enumerate(zip(models, colors)):
            # print(i,m,col)
            gConf = dNl.NestDict(copy.deepcopy(gConf0))
            gConf.default_color = col
            if isinstance(m, dict):
                gConf.model = m
                larva_groups[f'LarvaGroup{i}'] = gConf
            elif m in preg.storedConf('Model'):
                gConf.model = preg.expandConf(id=m, conftype='Model')
                larva_groups[m] = gConf
            elif m in preg.storedConf('Brain'):
                gConf.model = preg.expandConf(id=m, conftype='Brain')
                larva_groups[m] = gConf
            else:
                raise ValueError(f'{m} larva-model or brain-model does not exist!')
    if N is not None:
        for gID, gConf in larva_groups.items():
            gConf.distribution.N = N
    exp_conf.larva_groups = larva_groups
    return exp_conf


def run_template(conftype, args, d):
    # MP, p = get_parser(conftype)

    if conftype == 'Rep':
        from lib.sim.replay.replay import ReplayRun
        run = ReplayRun(**d['replay'])
        run.run()
    elif conftype == 'Batch':
        from run.exec_run import Exec
        conf = update_exp_conf(exp=args.experiment, d=d, N=args.Nagents, models=args.models, conf_type='Batch')
        exec = Exec(mode='batch', conf=conf, run_externally=False)
        exec.run()
    elif conftype == 'Exp':
        from lib.sim.single.single_run import SingleRun
        conf = update_exp_conf(exp=args.experiment, d=d, N=args.Nagents, models=args.models, conf_type='Exp')
        run = SingleRun(**conf, vis_kwargs=d['visualization'])
        ds = run.run()

        if args.analysis:
            fig_dict, results = run.analyze(show=args.show)
    elif conftype == 'Ga':
        from lib.sim.ga.ga_launcher import GAlauncher
        conf = update_exp_conf(exp=args.experiment, d=d, offline=args.offline, show_screen=args.show_screen,
                               conf_type='Ga')

        ga_select_kws = d['ga_select_kws']

        if args.base_model is not None:
            conf.ga_build_kws.base_model = args.base_model
        if args.bestConfID is not None:
            conf.ga_build_kws.bestConfID = args.bestConfID

        GA = GAlauncher(**conf)
        best_genome = GA.run()
    elif conftype == 'Eval':
        from lib.sim.eval.evaluation import EvalRun
        evrun = EvalRun(**d.eval_conf)
        evrun.run(video=args.show_screen)
        evrun.eval()
        evrun.plot_results()
        evrun.plot_models()


def get_parser(conftype, parser=None):
    dic = dNl.NestDict({
        'Batch': [['sim_params', 'batch_setup'], ['e', 'N', 'ms']],
        'Eval': [['eval_conf'], ['hide']],
        'Exp': [['sim_params', 'visualization'], ['e', 'N', 'ms', 'a']],
        'Ga': [['sim_params', 'ga_select_kws'], ['e', 'mID0', 'mID1', 'offline', 'hide']],
        'Rep': [['replay'], []]
    })
    mks, ks = dic[conftype]

    MP = MultiParser(mks)
    p = MP.add(parser)
    for k in ks:
        if k == 'e':
            p.add_argument('experiment', choices=reg.CT.dict[conftype].ConfIDs, help='The experiment mode')
        elif k == 'N':
            p.add_argument('-N', '--Nagents', type=int, help='The number of simulated larvae in each larva group')
        elif k == 'ms':
            p.add_argument('-ms', '--models', type=str, nargs='+',
                           help='The larva models to use for creating the simulation larva groups')
        elif k == 'mID0':
            p.add_argument('-mID0', '--base_model', choices=reg.CT.dict['Model'].ConfIDs,
                           help='The model configuration to optimize')
        elif k == 'mID1':
            p.add_argument('-mID1', '--bestConfID', type=str,
                           help='The model configuration ID to store the best genome')
        elif k == 'a':
            p.add_argument('-a', '--analysis', action="store_true", help='Whether to run analysis')
            p.add_argument('-show', '--show', action="store_true", help='Whether to show the analysis plots')
        elif k == 'offline':
            p.add_argument('-offline', '--offline', action="store_true",
                           help='Whether to run a full LarvaworldSim environment')
        elif k == 'hide':
            p.add_argument('-hide', '--show_screen', action="store_false",
                           help='Whether to render the screen visualization')

    return MP, p





if __name__ == '__main__':
    conf = update_exp_conf(exp='chemorbit', d=None, N=None, models=None, arena=None, conf_type='Eval')

    # print(conf.sim_params)

    # raise
