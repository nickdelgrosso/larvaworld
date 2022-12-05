from lib.gui.tabs.tab import GuiTab
from lib.gui.aux import buttons as gui_but, functions as gui_fun, elements as gui_el


class EnvTab(GuiTab):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.canvas_size=(800,800)
        self.S, self.L, self.B = 'Source', 'Larva', 'Border'
        self.Su, self.Sg = f'{self.S.lower()}_units', f'{self.S.lower()}_groups'
        # self.Lu, self.Lg=f'{self.L.lower()}_units', f'{self.L.lower()}_groups'
        self.Bg = f'{self.B.lower()}_list'

    def update(self, w, c, conf, id=None):
        for n in [self.Bg, 'arena', 'odorscape', 'windscape']:
            c[n].update(w, conf[n] if n in conf.keys() else {})
        for n in [self.Sg, self.Su, 'food_grid']:
            c[n].update(w, conf['food_params'][n])

    def get(self, w, v, c, as_entry=False):
        return {
            'food_params': {n: c[n].get_dict(v, w) for n in [self.Sg, self.Su, 'food_grid']},
            **{n: c[n].get_dict(v, w) for n in [self.Bg, 'arena', 'odorscape', 'windscape']},
        }

    def build(self):
        s2 = gui_el.PadTable(self.Sg, dict_name='SourceGroup', index='Group ID',col_widths=[10, 3, 8, 7, 6],
                      heading_dict={'N': 'distribution.N', 'color': 'default_color', 'odor': 'odor.odor_id',
                                    'amount': 'amount'})
        s3 = gui_el.PadTable(self.Su, dict_name='source', index='ID', col_widths=[10, 8, 8, 8],
                      heading_dict={'color': 'default_color', 'odor': 'odor.odor_id', 'amount': 'amount'})
        s4 = gui_el.PadTable(self.Bg, dict_name='border_list', index='ID', col_widths=[10, 8, 19],
                      heading_dict={'color': 'default_color', 'points': 'points'})
        s5 = gui_el.PadDict('arena', header_width=23, after_header=[gui_but.GraphButton('Button_Burn', 'RESET_ARENA',
                                                                         tooltip='Reset to the initial arena. All drawn items will be erased.'),
                                                             gui_but.GraphButton('Globe_Active', 'NEW_ARENA',
                                                                         tooltip='Create a new arena.All drawn items will be erased.')])
        s6 = gui_el.PadDict('food_grid', header_width=26, toggle=True)
        s7 = gui_el.PadDict('odorscape', header_width=36)
        s8 = gui_el.PadDict('windscape', header_width=36,
                     subconfs={
                         'puffs': {'heading_dict': {'duration': 'duration', 'interval': 'interval', 'speed': 'speed'}}})
        c = {}
        for s in [s2, s3, s4, s5, s6, s7, s8]:
            c.update(s.get_subdicts())
        l1 = [c[n].get_layout(as_pane=True)[0] for n in [self.Sg, self.Su, 'food_grid']]
        c2 = gui_el.PadDict(self.S, content=l1, header_width=34, dict_name=self.S.lower())
        c.update(c2.get_subdicts())
        sl1 = gui_el.SelectionList(tab=self, buttons=['save', 'delete', 'tree', 'conf_tree'], disp=self.name, width=35,root_key='env_conf',)
        l = gui_fun.gui_cols([[sl1, s7, s8, s4], [c2]], x_fracs=[0.25, 0.25], as_pane=True, pad=(10, 10))
        self.layout = l
        return l, c, {}, {}

if __name__ == "__main__":
    from lib.gui.tabs.gui import LarvaworldGui
    # larvaworld_gui = LarvaworldGui()
    larvaworld_gui = LarvaworldGui(tabs=['env'])
    larvaworld_gui.run()
