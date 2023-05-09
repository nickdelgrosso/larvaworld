import pandas as pd
import panel as pn
import numpy as np
import holoviews as hv

pn.extension()

from larvaworld.lib import reg, aux
from larvaworld.lib.process.dataset import LarvaDatasetCollection


class TrackViewer(LarvaDatasetCollection):

    def __init__(self, size=600, **kwargs):
        super().__init__(**kwargs)
        self.size = size

        self.xy_data = self.get_xy()
        self.dsp_mean = self.get_mean_dispersal()

        x, y = self.arena_dims
        self.image_kws = {
            'title': f'Trajectory viewer',
            'xlim': (-x / 2, x / 2),
            'ylim': (-y / 2, y / 2),
            'width': self.size,
            'height': self.size,
            'xlabel': 'X (m)',
            'ylabel': 'Y (m)',
        }
        self.app = self.get_app()

    def get_xydata_valid(self, valid_gIDs, i, dispersal_on):
        mode = 'origin' if dispersal_on else 'default'
        d = dict(zip(self.labels, self.xy_data[mode]))
        return {gID: d[gID].loc[:i].groupby('AgentID') for gID in valid_gIDs}

    def get_mean_dispersal(self):
        # d = dict(zip(self.labels,tv.xy_data['origin']))
        # {gID : d[gID].loc[:i].groupby('AgentID') for gID in valid_gIDs}
        ddic = {}
        for id, gd in zip(self.labels, self.xy_data['origin']):

            tt = gd.groupby('Step')
            dii = {}
            for i, ttt in tt:
                temp = ttt ** 2
                temp2 = temp.sum(axis=1) ** 0.5
                dii[i] = temp2.mean()
            ddic[id] = dii

        return ddic

    def get_xy(self):
        xy_data = aux.AttrDict({'default': [], 'origin': []})
        for d in self.datasets:
            xy = d.load_traj()
            xy_grouped = xy.groupby('AgentID')
            xy0s = xy_grouped.first()
            xy_origin = pd.concat([g - xy0s.loc[id] for id, g in xy_grouped]).sort_index()
            xy_data.default.append(xy)
            xy_data.origin.append(xy_origin)
        return xy_data

    def get_app(self):

        cb_IDs = pn.widgets.CheckBoxGroup(value=self.labels, options=self.labels)
        cb_vis = pn.widgets.CheckBoxGroup(value=['Positions', 'Disperal circle'],
                                          options=['Positions', 'IDs', 'Tracks', 'Disperal circle'])
        cb_rnd_col = pn.widgets.Checkbox(name='Random colors', value=False, disabled=True)
        cb_dispersal = pn.widgets.Checkbox(name='Align tracks to origin', value=True)

        slider_kws = {
            'width': self.size,
            'start': 0,
            'end': self.Nticks - 1,
            'interval': int(1000 * self.dt),
            'value': 0,
            'loop_policy': 'loop',

        }
        time_slider = pn.widgets.Player(**slider_kws)

        @pn.depends(i=time_slider, valid_gIDs=cb_IDs, dispersal_on=cb_dispersal, vis_ops=cb_vis, rnd_cols=cb_rnd_col)
        def get_image(valid_gIDs, i, dispersal_on, vis_ops, rnd_cols):
            pos_on = 'Positions' in vis_ops
            ids_on = 'IDs' in vis_ops
            paths_on = 'Tracks' in vis_ops
            circle_on = 'Disperal circle' in vis_ops
            dic = self.get_xydata_valid(valid_gIDs, i, dispersal_on)
            # for gID, data in dic.items()

            goverlay = None
            for gID, data in dic.items():
                track_kws = {
                    'color': None if rnd_cols else self.color_palette[gID],
                }
                _points = data.last()

                points = hv.Points(_points, label=gID).opts(line_width=4, **track_kws)
                overlay = points
                r = ((_points ** 2).sum(axis=1) ** 0.5).mean()
                circle2 = hv.Ellipse(0, 0, r).opts(line_width=6, **track_kws)
                overlay *= circle2
                if ids_on:
                    labels = hv.Labels(_points.reset_index(), ['x', 'y']).opts(text_font_size='8pt', xoffset=0.015,
                                                                               visible=ids_on)
                    overlay *= labels
                if paths_on:
                    _paths = [xyi for id, xyi in data]
                    paths = hv.Path(_paths).opts(**track_kws)
                    overlay *= paths
                goverlay = overlay if goverlay is None else goverlay * overlay

            goverlay.opts(
                hv.opts.Points(size=5, visible=pos_on),
                # hv.opts.Labels(text_font_size='8pt', xoffset=0.015,visible=ids_on),
            )

            if circle_on:
                for gID, data in self.dsp_mean.items():
                    r = data[i]

                    track_kws = {
                        'color': None if rnd_cols else self.color_palette[gID],
                    }
                    circle = hv.Ellipse(0, 0, r).opts(line_width=4, **track_kws)
                    goverlay *= circle

            goverlay.opts(responsive=False, **self.image_kws)

            return goverlay

        img_dmap = hv.DynamicMap(get_image)
        app = pn.Row(img_dmap, pn.Column(
            pn.Row(
                pn.Column('Datasets', cb_IDs, sizing_mode='stretch_width'),
                pn.Column('Visibility', cb_vis, sizing_mode='stretch_width'),
                pn.Column('Settings', cb_rnd_col, cb_dispersal, sizing_mode='stretch_width'),
                width=self.size),
            pn.Row(pn.Column('Tick', time_slider))
        ))
        return app

