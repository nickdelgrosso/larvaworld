import numpy as np


from lib.aux import dictsNlists as dNl
from lib.registry import reg
I=reg.Dic.DEF



def lgs(models, ids=None, **kwargs):
    from lib.aux.colsNstr import N_colors
    if ids is None:
        ids = models
    N = len(models)
    cols = N_colors(N)
    lgs = {}
    for m, c, id in zip(models, cols, ids):
        lg0 = lg(id, c=c, m=m, **kwargs)
        lgs.update(lg0)
    return lgs


def lg(group='Larva', m='explorer', **kwargs):


    return reg.lg(id=group, mID=m, **kwargs)






def exp(env_name, l={}, exp_name=None, en=False, sim={}, c=[], as_entry=False, **kwargs):

    ct = reg.Dic.CT.dict.Exp
    kw = {'kwdic': {'sim_params': sim},
        'larva_groups': l,
        'env_params': env_name,
        'collections': ['pose'] + c,
    }

    if en:
        kw['enrichment'] = I.enr_dict(proc=['angular', 'spatial', 'dispersion', 'tortuosity'],
                                         bouts=['stride', 'pause', 'turn'])
    kw.update(kwargs)

    if not as_entry:
        return ct.gConf(**kw)
    else:
        if exp_name is None:
            exp_name = env_name
        return ct.entry(id=exp_name, **kw)


def chem_exp(name, c=['olfactor'], dur=5.0, **kwargs):
    return exp(name, sim={'duration': dur}, c=c,
               enrichment=I.enr_dict(proc=['spatial', 'angular', 'source'], bouts=['stride', 'pause', 'turn'],
                                        fits=False), **kwargs)


def food_exp(name, c=['feeder'], dur=10.0, en=True, **kwargs):
    return exp(name, sim={'duration': dur}, c=c, en=en, **kwargs)


def game_exp(name, c=[], dur=20.0, **kwargs):
    return exp(name, sim={'duration': dur}, c=c, **kwargs)


def deb_exp(name, c=['feeder', 'gut'], dur=5.0, enrichment=None, **kwargs):
    if enrichment is None :
        enrichment = I.enr_dict(proc=['spatial'])
    return exp(name, sim={'duration': dur}, c=c, enrichment=enrichment, **kwargs)


def simple_exp(name, dur=10.0, en=True, **kwargs):
    return exp(name, sim={'duration': dur}, en=en, **kwargs)


def anemo_exp(name, dur=5.0, c=['wind'], en=False, **kwargs):
    return exp(name, sim={'duration': dur}, c=c, en=en, enrichment=I.enr_dict(proc=['spatial', 'angular', 'wind']), **kwargs)


def thermo_exp(name, dur=10.0, c=['thermo'], en=False, enrichment=None, **kwargs):
    return exp(name, sim={'duration': dur}, c=c, en=en, enrichment=enrichment, **kwargs)


def chemanemo_exp(name, dur=5.0, c=['olfactor', 'wind'], en=False,
                  enrichment=I.enr_dict(proc=['spatial', 'angular', 'source', 'wind'],
                                           bouts=['stride', 'pause', 'turn'],
                                           fits=False), **kwargs):
    return exp(name, sim={'duration': dur}, c=c, en=en, enrichment=enrichment, **kwargs)


def pref_exp(name, dur=5.0, c=[], enrichment=I.enr_dict(proc=['PI']), **kwargs):
    return exp(name, sim={'duration': dur}, c=c, enrichment=enrichment, **kwargs)


def game_groups(dim=0.1, N=10, x=0.4, y=0.0, mode='king'):
    x = np.round(x * dim, 3)
    y = np.round(y * dim, 3)
    if mode == 'king':
        l = {**lg('Left', N=N, p=(-x, y), m='gamer-5x', c='darkblue', o=I.oG(id='Left_odor')),
             **lg('Right', N=N, p=(+x, y), m='gamer-5x', c='darkred', o=I.oG(id='Right_odor'))}
    elif mode == 'flag':
        l = {**lg('Left', N=N, p=(-x, y), m='gamer', c='darkblue'),
             **lg('Right', N=N, p=(+x, y), m='gamer', c='darkred')}
    elif mode == 'catch_me':
        l = {**lg('Left', N=1, p=(-0.01, 0.0), m='follower-L', c='darkblue', o=I.oD(id='Left_odor')),
             **lg('Right', N=1, p=(+0.01, 0.0), m='follower-R', c='darkred', o=I.oD(id='Right_odor'))}
    return l

def lgs_x4(N=5):
    return lgs(models=['RE_NEU_PHI_DEF_max_forager', 'RE_NEU_PHI_DEF_max_feeder', 'RE_NEU_PHI_DEF_nav', 'RE_NEU_PHI_DEF'],
                                                       ids=['forager', 'Orco', 'navigator', 'explorer'], N=N)

def GTRvsS(**kwargs):
    return reg.Dic.GT.dict.LarvaGroup.RvsS_groups(**kwargs)

def Exp_dict() :



    grouped_exp_dict = {
        'exploration': {
            'tethered': simple_exp('focus', dur=30.0, l=lg(m='immobile', N=1, ors=[90.0, 90.0])),
            'focus': simple_exp('focus', l=lg(m='Levy', N=1, ors=[90.0, 90.0])),
            'dish': simple_exp('dish', l=lg(m='loco_default', N=25, s=0.02)),
            'dispersion': simple_exp('arena_200mm', l=lg(m='explorer', N=25)),
            'dispersion_x4': simple_exp('arena_200mm', dur=3.0,
                                        l=lgs(models=['explorer', 'Levy', 'nengo_explorer'],
                                              ids=['CoupledOsc', 'Levy', 'nengo'], N=5)),
        },

        'chemotaxis': {
            'chemotaxis': chem_exp('odor_gradient',
                                   l=lg(m='NEU_Levy_continuous_nav', N=8, p=(-0.04, 0.0), s=(0.005, 0.02),
                                        ors=(-30.0, 30.0))),
            'chemorbit': chem_exp('mid_odor_gaussian', dur=3.0, l=lg(m='RE_NEU_PHI_DEF_nav', N=3)),
            'chemorbit_x3': chem_exp('mid_odor_gaussian', dur=3.0,
                                     l=lgs(models=['RE_NEU_PHI_DEF_nav', 'RL_navigator'],
                                           ids=['CoupledOsc', 'RL'], N=10)),
            'chemorbit_x4': chem_exp('mid_odor_gaussian_square', dur=3.0,l=lgs_x4()),
            'chemotaxis_diffusion': chem_exp('mid_odor_diffusion', dur=10.0, l=lg(m='RE_NEU_PHI_DEF_nav', N=30)),
            'chemotaxis_RL': chem_exp('mid_odor_diffusion', dur=10.0, c=['olfactor', 'memory'],
                                      l=lg(m='RL_navigator', N=10, mode='periphery', s=0.04)),
            'reorientation': chem_exp('mid_odor_diffusion', l=lg(m='immobile', N=200, s=0.05)),
            'food_at_bottom': chem_exp('food_at_bottom', dur=1.0,
                                       l=lgs(models=['Orco_forager', 'forager'],
                                             ids=['Orco', 'control'], N=5, sh='oval', p=(0.0, 0.04), s=(0.04, 0.01)))
        },
        'anemotaxis': {
            'anemotaxis': anemo_exp('windy_arena', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'anemotaxis_bordered': anemo_exp('windy_arena_bordered', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'puff_anemotaxis_bordered': anemo_exp('puff_arena_bordered', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'single_puff': chemanemo_exp('single_puff', dur=2.5, l=lg(m='nengo_explorer', N=20, sample='Puff.Starved')),
            # 'anemotaxis_x2': anemo_exp('windy_arena', dur=2, l=lgs(models=['nengo_explorer', 'explorer'],
            #                                                        ids=['nengo', 'control'], N=10))
        },
        'thermotaxis': {
            'thermotaxis': thermo_exp('thermo_arena', l=lg(m='thermo_navigator', N=10)),

        },

        'odor_preference': {
            'PItest_off': pref_exp('CS_UCS_off_food', dur=3.0, l=lg(N=25, s=(0.005, 0.02), m='RE_NEU_PHI_DEF_nav_x2')),
            'PItest_on': pref_exp('CS_UCS_on_food', l=lg(N=25, s=(0.005, 0.02), m='forager_x2')),
            'PItrain_mini': pref_exp('CS_UCS_on_food_x2', dur=1.0, c=['olfactor', 'memory'],
                                     trials='odor_preference_short', l=lg(N=25, s=(0.005, 0.02), m='RL_forager')),
            'PItrain': pref_exp('CS_UCS_on_food_x2', dur=41.0, c=['olfactor', 'memory'],
                                trials='odor_preference', l=lg(N=25, s=(0.005, 0.02), m='RL_forager')),
            'PItest_off_RL': pref_exp('CS_UCS_off_food', dur=105.0, c=['olfactor', 'memory'],
                                      l=lg(N=25, s=(0.005, 0.02), m='RL_navigator'))},
        'foraging': {
            'patchy_food': food_exp('patchy_food', l=lg(m='forager', N=25)),
            'patch_grid': food_exp('patch_grid', l=lgs_x4()),
            'random_food': food_exp('random_food', c=['feeder', 'toucher'], l=lgs(models=['Orco_forager', 'RL_forager'],
                                                                                  ids=['Orco', 'RL'], N=5,
                                                                                  mode='uniform',
                                                                                  shape='rectangular', s=0.04),
                                    enrichment=I.enr_dict(proc=['spatial'], bouts=[]), en=False),
            'uniform_food': food_exp('uniform_food', l=lg(m='Orco_forager', N=5, s=0.005)),
            'food_grid': food_exp('food_grid', l=lg(m='Orco_forager', N=25)),
            'single_odor_patch': food_exp('single_odor_patch',
                                          l=lgs(models=['Orco_forager', 'forager'],
                                                ids=['Orco', 'control'], N=5, mode='periphery', s=0.01)),
            'single_odor_patch_x4': food_exp('single_odor_patch',l=lgs_x4()),
            'double_patch': food_exp('double_patch', l=GTRvsS(N=5),
                                     c=['toucher', 'feeder', 'olfactor'],
                                     enrichment=I.enr_dict(proc=['spatial', 'angular', 'source'], interference=False,
                                                              on_food=True, fits=False), en=False),
            'tactile_detection': food_exp('single_patch', dur=5.0, c=['toucher'],
                                          l=lg(m='toucher', N=15, mode='periphery', s=0.03), en=False),
            'tactile_detection_x3': food_exp('single_patch', dur=600.0, c=['toucher'],
                                             # l=lgs(models=['toucher', 'toucher_brute'],
                                             l=lgs(models=['RL_toucher_2', 'RL_toucher_0', 'toucher', 'toucher_brute',
                                                           'gRL_toucher_0'],
                                                   # ids=['control', 'brute'], N=10), en=False),
                                                   ids=['RL_3sensors', 'RL_1sensor', 'control', 'brute',
                                                        'RL global best'],
                                                   N=10), en=False),
            'tactile_detection_g': food_exp('single_patch', dur=600.0, c=['toucher'],
                                            l=lgs(models=['RL_toucher_0', 'gRL_toucher_0'],
                                                  ids=['RL state-specific best', 'RL global best'], N=10), en=False),
            'multi_tactile_detection': food_exp('multi_patch', dur=600.0, c=['toucher'],
                                                l=lgs(models=['RL_toucher_2', 'RL_toucher_0', 'toucher'],
                                                      ids=['RL_3sensors', 'RL_1sensor', 'control'], N=4), en=False),
            '4corners': exp('4corners', c=['memory'], l=lg(m='RL_forager', N=10, s=0.04))
        },

        'growth': {'growth': deb_exp('food_grid', dur=24 * 60.0, l=GTRvsS(age=0.0)),
                   'RvsS': deb_exp('food_grid', dur=180.0, l=GTRvsS(age=0.0)),
                   'RvsS_on': deb_exp('food_grid', dur=20.0, l=GTRvsS()),
                   'RvsS_off': deb_exp('arena_200mm', dur=20.0, l=GTRvsS()),
                   'RvsS_on_q75': deb_exp('food_grid', l=GTRvsS(q=0.75)),
                   'RvsS_on_q50': deb_exp('food_grid', l=GTRvsS(q=0.50)),
                   'RvsS_on_q25': deb_exp('food_grid', l=GTRvsS(q=0.25)),
                   'RvsS_on_q15': deb_exp('food_grid', l=GTRvsS(q=0.15)),
                   'RvsS_on_1h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=1.0)),
                   'RvsS_on_2h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=2.0)),
                   'RvsS_on_3h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=3.0)),
                   'RvsS_on_4h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=4.0)),

                   },

        'games': {
            'maze': game_exp('maze', c=['olfactor'],
                             l=lg(N=5, p=(-0.4 * 0.1, 0.0), ors=(-60.0, 60.0), m='RE_NEU_PHI_DEF_nav')),
            'keep_the_flag': game_exp('game', l=game_groups(mode='king')),
            'capture_the_flag': game_exp('game', l=game_groups(mode='flag')),
            'catch_me': game_exp('arena_50mm_diffusion', l=game_groups(mode='catch_me'))
        },

        'zebrafish': {
            'prey_detection': exp('windy_blob_arena', l=lg(m='zebrafish', N=4, s=(0.002, 0.005)),
                                  sim={'Box2D': True, 'duration': 20.0})
        },

        'other': {
            'realistic_imitation': exp('dish', l=lg(m='imitator', N=25), sim={'Box2D': True}, c=['midline', 'contour'])
            # 'imitation': imitation_exp('None.150controls', model='explorer'),
        }
    }
    exp_dict = dNl.merge_dicts(list(grouped_exp_dict.values()))
    return exp_dict
def ExpGroup_dict() :
    grouped_exp_dict = {
        'exploration': {
            'tethered': simple_exp('focus', dur=30.0, l=lg(m='immobile', N=1, ors=[90.0, 90.0])),
            'focus': simple_exp('focus', l=lg(m='Levy', N=1, ors=[90.0, 90.0])),
            'dish': simple_exp('dish', l=lg(m='branch_explorer', N=5, s=0.02)),
            # 'dish_x2': simple_exp('dish', l=lgs(models=['explorer', 'branch_explorer'],
            #                                     ids=['default', 'branch'], N=5)),
            # 'nengo_dish': simple_exp('dish', l=lg(m='nengo_explorer', N=25, s=0.02)),
            'dispersion': simple_exp('arena_200mm', l=lg(m='explorer', N=25)),
            'dispersion_x4': simple_exp('arena_200mm', dur=3.0,
                                        l=lgs(models=['explorer', 'Levy', 'nengo_explorer'],
                                              ids=['CoupledOsc', 'Levy', 'nengo'], N=5)),
        },

        'chemotaxis': {
            'chemotaxis': chem_exp('odor_gradient',
                                   l=lg(m='NEU_Levy_continuous_nav', N=8, p=(-0.04, 0.0), s=(0.005, 0.02),
                                        ors=(-30.0, 30.0))),
            'chemorbit': chem_exp('mid_odor_gaussian', dur=3.0, l=lg(m='RE_NEU_PHI_DEF_nav', N=3)),
            'chemorbit_x3': chem_exp('mid_odor_gaussian', dur=3.0,
                                     l=lgs(models=['RE_NEU_PHI_DEF_nav', 'RL_navigator'],
                                           ids=['CoupledOsc', 'RL'], N=10)),
            'chemotaxis_diffusion': chem_exp('mid_odor_diffusion', dur=10.0, l=lg(m='RE_NEU_PHI_DEF_nav', N=30)),
            'chemotaxis_RL': chem_exp('mid_odor_diffusion', dur=10.0, c=['olfactor', 'memory'],
                                      l=lg(m='RL_navigator', N=10, mode='periphery', s=0.04)),
            'reorientation': chem_exp('mid_odor_diffusion', l=lg(m='immobile', N=200, s=0.05)),
            'food_at_bottom': chem_exp('food_at_bottom', dur=1.0,
                                       l=lgs(models=['Orco_forager', 'forager'],
                                             ids=['Orco', 'control'], N=5, sh='oval', p=(0.0, 0.04), s=(0.04, 0.01)))
        },
        'anemotaxis': {
            'anemotaxis': anemo_exp('windy_arena', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'anemotaxis_bordered': anemo_exp('windy_arena_bordered', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'puff_anemotaxis_bordered': anemo_exp('puff_arena_bordered', dur=0.5, l=lg(m='nengo_explorer', N=4)),
            'single_puff': chemanemo_exp('single_puff', dur=2.5, l=lg(m='nengo_explorer', N=20, sample='Puff.Starved')),
            # 'anemotaxis_x2': anemo_exp('windy_arena', dur=2, l=lgs(models=['nengo_explorer', 'explorer'],
            #                                                        ids=['nengo', 'control'], N=10))
        },
        'thermotaxis': {
            'thermotaxis': thermo_exp('thermo_arena', l=lg(m='thermo_navigator', N=10)),

        },

        'odor_preference': {
            'PItest_off': pref_exp('CS_UCS_off_food', dur=3.0, l=lg(N=25, s=(0.005, 0.02), m='RE_NEU_PHI_DEF_nav_x2')),
            'PItest_on': pref_exp('CS_UCS_on_food', l=lg(N=25, s=(0.005, 0.02), m='forager_x2')),
            'PItrain_mini': pref_exp('CS_UCS_on_food_x2', dur=1.0, c=['olfactor', 'memory'],
                                     trials='odor_preference_short', l=lg(N=25, s=(0.005, 0.02), m='RL_forager')),
            'PItrain': pref_exp('CS_UCS_on_food_x2', dur=41.0, c=['olfactor', 'memory'],
                                trials='odor_preference', l=lg(N=25, s=(0.005, 0.02), m='RL_forager')),
            'PItest_off_RL': pref_exp('CS_UCS_off_food', dur=105.0, c=['olfactor', 'memory'],
                                      l=lg(N=25, s=(0.005, 0.02), m='RL_navigator'))},
        'foraging': {
            'patchy_food': food_exp('patchy_food', l=lg(m='forager', N=25)),
            'patch_grid': food_exp('patch_grid', l=lgs(models=['forager', 'Orco_forager', 'RE_NEU_PHI_DEF_nav', 'RE_NEU_PHI_DEF'],
                                                       ids=['forager', 'Orco', 'navigator', 'explorer'], N=5)),
            'random_food': food_exp('random_food', c=['feeder', 'toucher'], l=lgs(models=['Orco_forager', 'RL_forager'],
                                                                                  ids=['Orco', 'RL'], N=5,
                                                                                  mode='uniform',
                                                                                  shape='rectangular', s=0.04),
                                    enrichment=I.enr_dict(proc=['spatial'], bouts=[]), en=False),
            'uniform_food': food_exp('uniform_food', l=lg(m='Orco_forager', N=5, s=0.005)),
            'food_grid': food_exp('food_grid', l=lg(m='Orco_forager', N=25)),
            'single_odor_patch': food_exp('single_odor_patch',
                                          l=lgs(models=['Orco_forager', 'forager'],
                                                ids=['Orco', 'control'], N=5, mode='periphery', s=0.03)),
            'double_patch': food_exp('double_patch', l=GTRvsS(N=5),
                                     c=['toucher', 'feeder', 'olfactor'],
                                     enrichment=I.enr_dict(proc=['spatial', 'angular', 'source'], interference=False,
                                                              on_food=True, fits=False), en=False),
            'tactile_detection': food_exp('single_patch', dur=5.0, c=['toucher'],
                                          l=lg(m='toucher', N=15, mode='periphery', s=0.03), en=False),
            'tactile_detection_x3': food_exp('single_patch', dur=600.0, c=['toucher'],
                                             # l=lgs(models=['toucher', 'toucher_brute'],
                                             l=lgs(models=['RL_toucher_2', 'RL_toucher_0', 'toucher', 'toucher_brute',
                                                           'gRL_toucher_0'],
                                                   # ids=['control', 'brute'], N=10), en=False),
                                                   ids=['RL_3sensors', 'RL_1sensor', 'control', 'brute',
                                                        'RL global best'],
                                                   N=10), en=False),
            'tactile_detection_g': food_exp('single_patch', dur=600.0, c=['toucher'],
                                            l=lgs(models=['RL_toucher_0', 'gRL_toucher_0'],
                                                  ids=['RL state-specific best', 'RL global best'], N=10), en=False),
            'multi_tactile_detection': food_exp('multi_patch', dur=600.0, c=['toucher'],
                                                l=lgs(models=['RL_toucher_2', 'RL_toucher_0', 'toucher'],
                                                      ids=['RL_3sensors', 'RL_1sensor', 'control'], N=4), en=False),
            '4corners': exp('4corners', c=['memory'], l=lg(m='RL_forager', N=10, s=0.04))
        },

        'growth': {'growth': deb_exp('food_grid', dur=24 * 60.0, l=GTRvsS(age=0.0)),
                   'RvsS': deb_exp('food_grid', dur=180.0, l=GTRvsS(age=0.0)),
                   'RvsS_on': deb_exp('food_grid', dur=20.0, l=GTRvsS()),
                   'RvsS_off': deb_exp('arena_200mm', dur=20.0, l=GTRvsS()),
                   'RvsS_on_q75': deb_exp('food_grid', l=GTRvsS(q=0.75)),
                   'RvsS_on_q50': deb_exp('food_grid', l=GTRvsS(q=0.50)),
                   'RvsS_on_q25': deb_exp('food_grid', l=GTRvsS(q=0.25)),
                   'RvsS_on_q15': deb_exp('food_grid', l=GTRvsS(q=0.15)),
                   'RvsS_on_1h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=1.0)),
                   'RvsS_on_2h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=2.0)),
                   'RvsS_on_3h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=3.0)),
                   'RvsS_on_4h_prestarved': deb_exp('food_grid', l=GTRvsS(h_starved=4.0)),

                   },

        'games': {
            'maze': game_exp('maze', c=['olfactor'],
                             l=lg(N=5, p=(-0.4 * 0.1, 0.0), ors=(-60.0, 60.0), m='RE_NEU_PHI_DEF_nav')),
            'keep_the_flag': game_exp('game', l=game_groups(mode='king')),
            'capture_the_flag': game_exp('game', l=game_groups(mode='flag')),
            'catch_me': game_exp('arena_50mm_diffusion', l=game_groups(mode='catch_me'))
        },

        'zebrafish': {
            'prey_detection': exp('windy_blob_arena', l=lg(m='zebrafish', N=4, s=(0.002, 0.005)),
                                  sim={'Box2D': True, 'duration': 20.0})
        },

        'other': {
            'realistic_imitation': exp('dish', l=lg(m='imitator', N=25), sim={'Box2D': True}, c=['midline', 'contour'])
            # 'imitation': imitation_exp('None.150controls', model='explorer'),
        }
    }
    exp_group_dict = {k: {'simulations': list(v.keys())} for k, v in grouped_exp_dict.items()}
    return exp_group_dict
