import numpy as np
import pandas as pd


from lib.aux import dictsNlists as dNl
from lib import reg










def grid_search_dict(space_dict):
    import pypet
    dic={}
    for p, args in space_dict.items() :
        if args['values'] is not None :
            dic[p]=args['values']
        else :
            r0,r1=args['range']
            vs = np.linspace(r0, r1, args['Ngrid'])
            # print(type(r0), type(vs[0]))
            # raise
            if type(r0) == int and type(r1) == int:
                vs = vs.astype(int)
            dic[p] = vs.tolist()
    return pypet.cartesian_product(dic)


def get_space_from_file(space_filepath=None, params=None, space_pd=None, returned_params=None, flag=None,
                        flag_range=[0, +np.inf], ranges=None,
                        par4ranges=None, additional_params=None, additional_values=None):
    if space_pd is None:
        space_pd = pd.read_csv(space_filepath, index_col=0)
    if params is None:
        params = space_pd.columns.values.tolist()
    if returned_params is None:
        returned_params = params
    if ((ranges is not None) and (par4ranges is not None)):
        for p, r in zip(par4ranges, ranges):
            space_pd = space_pd[(space_pd[p] >= r[0]) & (space_pd[p] <= r[1])].copy(deep=True)
            print('Ranges found. Selecting combinations within range')
    if flag:
        r0, r1 = flag_range
        space_pd = space_pd[space_pd[flag].dropna() > r0].copy(deep=True)
        space_pd = space_pd[space_pd[flag].dropna() < r1].copy(deep=True)
        print(f'Using {flag} to select suitable parameter combinations')

    values = [space_pd[p].values.tolist() for p in params]
    values = [[float(b) for b in a] for a in values]
    if additional_params is not None and additional_values is not None:
        for p, vs in zip(additional_params, additional_values):
            Nspace = len(values[0])
            Nv = len(vs)
            values = [a * Nv for a in values] + dNl.flatten_list([[v] * Nspace for v in vs])
            returned_params += [p]

    space = dict(zip(returned_params, values))
    return space





def delete_traj(batch_type, traj_name):
    import h5py
    filename = f'{reg.Path["BATCH"]}/{batch_type}/{batch_type}.hdf5'
    with h5py.File(filename, 'r+') as f:
        del f[traj_name]


