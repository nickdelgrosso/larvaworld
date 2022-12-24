import numpy as np

from lib.model.modules.locomotor import DefaultLocomotor
from lib.aux import dictsNlists as dNl
from lib import reg


class Brain:
    def __init__(self, agent=None, dt=None):
        self.agent = agent

        self.sensor_dict = dNl.NestDict({
            'olfactor': {'func': self.sense_odors, 'A': 0.0, 'mem': 'memory'},
            'toucher': {'func': self.sense_food, 'A': 0.0, 'mem': 'touch_memory'},
            'thermosensor': {'func': self.sense_thermo, 'A': 0.0, 'mem': None},
            'windsensor': {'func': self.sense_wind, 'A': 0.0, 'mem': None}
        })

        if dt is None:
            dt = self.agent.model.dt
        self.dt = dt

    def sense_odors(self, pos=None):
        if self.agent is None:
            return {}
        if pos is None:
            pos = self.agent.olfactor_pos

        cons = {}
        for id, layer in self.agent.model.odor_layers.items():
            v = layer.get_value(pos)
            cons[id] = v + np.random.normal(scale=v * self.olfactor.noise)
        return cons

    def sense_food(self,**kwargs):
        a = self.agent
        if a is None:
            return {}
        sensors = a.get_sensors()
        return {s: int(a.detect_food(a.get_sensor_position(s))[0] is not None) for s in sensors}

    def sense_wind(self,**kwargs):
        if self.agent is None:
            v = 0.0
        else:
            w = self.agent.model.windscape
            if w is None:
                v = 0.0
            else:
                v = w.get_value(self.agent)
        return {'windsensor': v}

    def sense_thermo(self, pos=None):
        a = self.agent
        if a is None:
            return {'cool': 0, 'warm': 0}
        if pos is None:
            pos = a.pos
        ad = a.model.arena_dims
        pos_adj = [(pos[0] + (ad[0] * 0.5)) / ad[0], (pos[1] + (ad[1] * 0.5)) / ad[1]]
        try:
            cons = a.model.thermo_layers.get_thermo_value(pos_adj)
        except AttributeError:
            return {'cool': 0, 'warm': 0}
        return cons

    def sense(self, reward=False, **kwargs):
        for k in self.sensor_dict.keys():
            sensor = getattr(self, k)
            if sensor:
                mem = self.sensor_dict[k]['mem']
                if mem is not None:
                    sensor_memory = getattr(self, mem)
                    if sensor_memory:
                        dx = sensor.get_dX()
                        sensor.gain = sensor_memory.step(dx, reward, brain=self)

                func = self.sensor_dict[k]['func']
                self.sensor_dict[k]['A'] = sensor.step(func(**kwargs), brain=self)

    @ property
    def A_in(self):
        return np.sum([v['A'] for v in self.sensor_dict.values()])


class DefaultBrain(Brain):
    def __init__(self, conf, agent=None, dt=None, **kwargs):
        super().__init__(agent=agent, dt=dt)
        self.locomotor = DefaultLocomotor(dt=self.dt, conf=conf, **kwargs)
        # reg.Dic.MD.init_brain(conf, self)

    # def init_brain(self, conf, B):
        D = reg.model.dict.model.m
        for k in ['olfactor', 'toucher', 'windsensor', 'thermosensor']:
            if conf.modules[k]:
                m = conf[f'{k}_params']
                if k == 'windsensor':
                    m.gain_dict = {'windsensor': 1.0}
                mode = 'default'
                kws = {kw: getattr(self, kw) for kw in D[k].kwargs.keys()}
                M = D[k].mode[mode].class_func(**m, **kws)
                if k == 'toucher':
                    M.init_sensors(brain=self)


            else:
                M = None
            setattr(self, k, M)
        self.touch_memory = None
        self.memory = None
        if conf.modules['memory']:
            mm = conf['memory_params']
            mode = mm['modality']
            kws = {kw: getattr(self, kw) for kw in D['memory'].kwargs.keys()}
            if mode == 'olfaction' and self.olfactor:
                mm.gain = self.olfactor.gain
                self.memory = D['memory'].mode[mode].class_func(**mm, **kws)
            elif mode == 'touch' and self.toucher:
                mm.gain = self.toucher.gain
                self.touch_memory = D['memory'].mode[mode].class_func(**mm, **kws)
        # return B



    def step(self, pos=(0.0, 0.0), reward=False, **kwargs):
        self.sense(pos=pos, reward=reward)

        length = self.agent.real_length if self.agent is not None else 1
        return self.locomotor.step(A_in=self.A_in, length=length)
