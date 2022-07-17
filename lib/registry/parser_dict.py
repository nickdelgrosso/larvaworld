import time
from typing import List
import lib.aux.dictsNlists as dNl
# from lib.conf.stored.conf import loadConfDict

from lib.registry.pars import preg
# t0 = time.time()
# d=preg.conftype_dict.storedConf('Exp')
# t1 = time.time()
# d=preg.conftype_dict.storedConf('Exp')
# t2 = time.time()
# d=preg.conftype_dict.storedConf('Exp')
# t3 = time.time()
# from lib.conf.stored.conf import kConfDict
# d=kConfDict('Exp')
# t4 = time.time()
# d=kConfDict('Exp')
# t5 = time.time()
# d=kConfDict('Exp')
# t6 = time.time()
# print(t3-t2)
# print(t2-t1)
# print(t1-t0)
# print(t4-t3)
# print(t5-t4)
# print(t6-t5)
# raise
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


def build_ParsArg(name, k=None, h='', dtype=float, v=None, vs=None, **kwargs):
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


def get_ParsDict(d0):
    dic = {}
    for n, ndic in d0.items():
        entry = build_ParsArg(name=n, **ndic)
        dic.update(entry)
    return dic


def build_ParsDict(dic):
    return {k: ParsArg(**v) for k, v in dic.items()}
    # return parsargs


def get_ParsDict2(d0):
    def par(name, dtype=float, v=None, vs=None, h='', k=None, **kwargs):
        return build_ParsArg(name, k, h, dtype, v, vs)

    def par_dict(d0, **kwargs):
        if d0 is None:
            return None
        d = {}
        for n, v in d0.items():
            if 'v' in v.keys() or 'k' in v.keys() or 'h' in v.keys():
                entry = par(n, **v, **kwargs)
            else:
                entry = {n: {'dtype': dict, 'content': par_dict(d0=v, **kwargs)}}
            d.update(entry)
        return d

    dic = par_dict(d0=d0)
    return dic


def build_ParsDict2(dic):
    try:
        parsargs = {k: ParsArg(**v) for k, v in dic.items()}
    except:
        parsargs = {}
        for k, v in dic.items():
            for kk, vv in v['content'].items():
                parsargs[kk] = ParsArg(**vv)
    return parsargs


class ParserDict:
    def __init__(self, init_dict=None, load=True,
                 names=['sim_params', 'batch_setup', 'eval_conf', 'visualization', 'ga_select_kws', 'replay']):
        self.dict_path = preg.path_dict['ParserDict']
        if not load:
            self.predict = self.build_predict(names, init_dict)
            dNl.save_dict(self.predict, self.dict_path)
        else:
            self.predict = dNl.load_dict(self.dict_path)
        self.dict = self.build_parser_dict(self.predict)

    def build_predict(self, names, init_dict=None):
        if init_dict is None:
            from lib.registry import init_pars
            init_dict = init_pars.init_dict.dict
        # self.init_dict = init_dict
        pred = dNl.NestDict()
        for name in names:
            d0 = init_dict[name]
            try:
                pred[name] = get_ParsDict2(d0)
            except:
                pred[name] = get_ParsDict(d0)
        return pred

    def build_parser_dict(self, predict):
        d = dNl.NestDict()
        for name, dic in predict.items():
            try:
                d[name] = build_ParsDict2(dic)
            except:
                d[name] = build_ParsDict(dic)
        return d



parser_dict = ParserDict()



