import copy

import PySimpleGUI as sg

from lib.aux.dtype_dicts import opt_pars_dict, space_pars_dict
from lib.conf import exp_types
from lib.conf.batch_conf import test_batch
from lib.gui.gui_lib import CollapsibleDict, button_kwargs, Collapsible, text_kwargs, buttonM_kwargs, named_list_layout, \
    gui_table, save_gui_conf, delete_gui_conf
from lib.gui.simulation_tab import get_sim_conf, update_sim
from lib.sim.single_run import generate_config, next_idx
from lib.conf.conf import loadConfDict, loadConf


def init_batch(batch, collapsibles={}):
    # collapsibles['METHODS'] = CollapsibleDict('METHODS', True,
    #                                                dict=batch['methods'], type_dict=method_pars_dict)

    # collapsibles['SPACE_SEARCH'] = CollapsibleDict('SPACE_SEARCH', True,
    #                                                dict=batch['space_search'], type_dict=space_pars_dict)
    collapsibles['OPTIMIZATION'] = CollapsibleDict('OPTIMIZATION', True,
                                                   dict=batch['optimization'], type_dict=opt_pars_dict,
                                                   toggle=True, disabled=True)
    batch_layout = [
        # collapsibles['SPACE_SEARCH'].get_section(),
        collapsibles['OPTIMIZATION'].get_section(),
    ]
    collapsibles['BATCH'] = Collapsible('BATCH', True, batch_layout)
    return collapsibles['BATCH'].get_section()


def update_batch(batch, window, collapsibles, space_search):

    collapsibles['OPTIMIZATION'].update(window, batch['optimization'])
    space_search = batch['space_search']
    return space_search


def get_batch(window, values, collapsibles, space_search):
    batch = {}
    batch['optimization'] = collapsibles['OPTIMIZATION'].get_dict(values, window)
    batch['space_search'] = space_search
    batch['exp'] = values['EXP']
    return copy.deepcopy(batch)


def build_batch_tab(collapsibles):
    batch_results={}
    batch = copy.deepcopy(test_batch)
    space_search = batch['space_search']
    l_exp = [sg.Col([
        named_list_layout(text='Batch:', key='BATCH_CONF', choices=list(loadConfDict('Batch').keys())),
        [sg.Button('Load', key='LOAD_BATCH', **button_kwargs),
         sg.Button('Save', key='SAVE_BATCH', **button_kwargs),
         sg.Button('Delete', key='DELETE_BATCH', **button_kwargs),
         sg.Button('Run', key='RUN_BATCH', **button_kwargs)]
    ])]
    batch_conf = [[sg.Text('Batch id:', **text_kwargs), sg.In('unnamed_batch_0', key='batch_id', **text_kwargs)],
                  [sg.Text('Path:', **text_kwargs), sg.In('unnamed_batch', key='batch_path', **text_kwargs)],
                  # [sg.Text('Duration (min):', **text_kwargs), sg.In(3, key='batch_dur', **text_kwargs)],
                  # [sg.Text('Timestep (sec):', **text_kwargs), sg.In(0.1, key='dt', **text_kwargs)],
                  # collapsibles['OUTPUT'].get_section()
                  ]

    collapsibles['BATCH_CONFIGURATION'] = Collapsible('BATCH_CONFIGURATION', True, batch_conf)
    l_conf = collapsibles['BATCH_CONFIGURATION'].get_section()
    l_opt = init_batch(batch, collapsibles)
    l_batch = [[sg.Col([l_exp,l_conf,[sg.Button('SPACE_SEARCH', **buttonM_kwargs)], l_opt])]]
    return l_batch, collapsibles, space_search, batch_results


def set_space_table(space_search):
    N = len(space_search['pars'])
    t0 = []
    for i in range(N):
        d = {}
        for k, v in space_search.items():
            d[k] = v[i]
        t0.append(d)

    t1 = gui_table(t0, space_pars_dict, title='space search')
    dic = {}
    for k in list(space_pars_dict.keys()):
        dic[k] = [l[k] for l in t1]
        # if k == 'ranges':
        #     dic[k] = np.array(dic[k])
    return dic


def eval_batch(event, values, window, collapsibles, dicts):
    space_search = dicts['space_search']
    if event == 'LOAD_BATCH':
        if values['BATCH_CONF'] != '':
            batch=values['BATCH_CONF']
            window.Element('batch_id').Update(value=f'{batch}_{next_idx(batch, type="batch")}')
            window.Element('batch_path').Update(value=batch)
            conf = loadConf(batch, 'Batch')
            space_search = update_batch(conf, window, collapsibles, space_search)

            window.Element('EXP').Update(value=conf['exp'])
            exp_id = conf['exp']
            source_units, border_list, larva_groups, source_groups = update_sim(window, exp_id, collapsibles)
            dicts['source_units'] = source_units
            dicts['border_list'] = border_list
            dicts['larva_groups'] = larva_groups
            dicts['source_groups'] = source_groups



    elif event == 'SAVE_BATCH':
        batch = get_batch(window, values, collapsibles, space_search)
        save_gui_conf(window, batch, 'Batch')


    elif event == 'DELETE_BATCH':
        delete_gui_conf(window, values, 'Batch')


    elif event == 'RUN_BATCH':
        if values['BATCH_CONF'] != '' and values['EXP'] != '':
            from lib.sim.batch_lib import prepare_batch, batch_run
            batch = get_batch(window, values, collapsibles, space_search)
            batch_id = str(values['batch_id'])
            batch_path = str(values['batch_path'])
            sim_params = get_sim_conf(window, values)
            life_params = collapsibles['LIFE'].get_dict(values, window)
            sim_config = generate_config(exp=batch["exp"], sim_params=sim_params, life_params=life_params)
            batch_kwargs = prepare_batch(batch, batch_id, sim_config)
            df, plots=batch_run(**batch_kwargs)
            dicts['batch_results']['df'] = df
            dicts['batch_results']['plots'] = plots

    elif event == 'SPACE_SEARCH':
        space_search = set_space_table(space_search)

    dicts['space_search'] = space_search

    return dicts
