
import math
import random
import numpy as np
from numpy import ndarray
from shapely import geometry, ops
from typing import Optional, List

import larvaworld
from larvaworld.lib import aux
from larvaworld.lib.aux import nam




def LvsRtoggle(side):
    if side == 'Left':
        return 'Right'
    elif side == 'Right':
        return 'Left'
    else:
        raise ValueError(f'Argument {side} is neither Left nor Right')


def inside_polygon(points, tank_polygon):
    return all([tank_polygon.contains(geometry.Point(x, y)) for x, y in points])




def rearrange_contour(ps0):
    ps_plus = [p for p in ps0 if p[1] >= 0]
    ps_plus.sort(key=lambda x: x[0], reverse=True)
    ps_minus = [p for p in ps0 if p[1] < 0]
    ps_minus.sort(key=lambda x: x[0], reverse=False)
    return ps_plus + ps_minus

def get_tank_polygon(c, k=0.97, return_polygon=True):
    X, Y = c.env_params.arena.dims
    shape = c.env_params.arena.shape
    if shape == 'circular':
        # This is a circle_to_polygon shape from the function
        tank_shape = aux.circle_to_polygon(60, X / 2)
    elif shape == 'rectangular':
        # This is a rectangular shape
        tank_shape = np.array([(-X / 2, -Y / 2),
                               (-X / 2, Y / 2),
                               (X / 2, Y / 2),
                               (X / 2, -Y / 2)])
    if return_polygon:
        return geometry.Polygon(tank_shape * k)
    else:
        # tank_shape=np.insert(tank_shape,-1,tank_shape[0,:])
        return tank_shape




def position_head_in_tank(hr0, ho0, l0, fov0,fov1, ang_vel, lin_vel, dt, tank, sf=1, go_err =0, turn_err =0):
    hf0 = hr0 + np.array([math.cos(ho0), math.sin(ho0)]) * l0
    def get_hf0(ang_vel):
        d_or = ang_vel * dt
        return aux.rotate_point_around_point(origin=hr0, point=hf0, radians=-d_or)


    def fov(ang_vel, turn_err =0):
        dv=8*np.pi / 90
        idx=0
        while not inside_polygon([get_hf0(ang_vel)], tank):
            if idx == 0:
                dv *= np.sign(ang_vel)
            ang_vel -= dv
            if ang_vel < fov0:
                ang_vel = fov0
                dv = np.abs(dv)
            elif ang_vel > fov1:
                ang_vel = fov1
                dv -= np.abs(dv)
            idx += 1
            if np.isnan(ang_vel) or idx > 100:
                turn_err += 1
                ang_vel = 0
                break
        return ang_vel, turn_err

    ang_vel, turn_err=fov(ang_vel, turn_err=turn_err)

    ho1 = ho0 + ang_vel * dt
    k = np.array([math.cos(ho1), math.sin(ho1)])
    hf01 = get_hf0(ang_vel)
    coef = dt * sf * k

    def get_hf1(lin_vel):
        return hf01 + coef * lin_vel
    def lv(lin_vel,go_err=0):
        dv = 0.00011
        idx = 0
        while not inside_polygon([get_hf1(lin_vel)], tank):
            idx += 1
            lin_vel -= dv
            if np.isnan(lin_vel) or idx > 100:
                go_err += 1
                lin_vel =0
                break
            if lin_vel < 0:
                lin_vel = 0
                break
        return lin_vel, go_err

    lin_vel, go_err=lv(lin_vel, go_err=go_err)
    d = lin_vel * dt
    hp1 = hr0 + k * (d * sf + l0 / 2)
    return d, ang_vel, lin_vel, hp1, ho1, turn_err, go_err


class Collision(Exception):

    def __init__(self, object1, object2):
        self.object1 = object1
        self.object2 = object2





def generate_seg_shapes(Nsegs: int, points:ndarray, seg_ratio: Optional[ndarray] = None,
                 centered: bool = True, closed: bool = False) -> ndarray:
    """
    Segments a body into equal-length or given-length segments via vertical lines.

    Args:
    - Nsegs: Number of segments to divide the body into.
    - points: Array with shape (M,2) representing the contour of the body to be segmented.
    - seg_ratio: List of N floats specifying the ratio of the length of each segment to the length of the body.
                Defaults to None, in which case equal-length segments will be generated.
    - centered: If True, centers the segments around the origin. Defaults to True.
    - closed: If True, the last point of each segment is connected to the first point. Defaults to False.

    Returns:
    - ps: Numpy array with shape (Nsegs,L,2), where L is the number of vertices of each segment.
          The first segment in the list is the front-most segment.
    """

    # If segment ratio is not provided, generate equal-length segments
    if seg_ratio is None:
        seg_ratio = np.array([1 / Nsegs] * Nsegs)

    # Create a polygon from the given body contour
    p = geometry.Polygon(points)
    # Get maximum y value of contour
    y0 = np.max(p.exterior.coords.xy[1])

    # Segment body via vertical lines
    ps = [p]
    for cum_r in np.cumsum(seg_ratio):
        l = geometry.LineString([(1 - cum_r, y0), (1 - cum_r, -y0)])
        new_ps = []
        for p in ps:
            new_ps += list(ops.split(p, l).geoms)
        ps = new_ps

    # Sort segments so that front segments come first
    ps.sort(key=lambda x: x.exterior.xy[0], reverse=True)

    # Transform to 2D array of coords
    ps = [p.exterior.coords.xy for p in ps]
    ps = [np.array([[x, y] for x, y in zip(xs, ys)]) for xs, ys in ps]

    # Center segments around 0,0
    if centered:
        for i, (r, cum_r) in enumerate(zip(seg_ratio, np.cumsum(seg_ratio))):
            ps[i] -= [(1 - cum_r) + r / 2, 0]

    # Put front point at the start of segment vertices. Drop duplicate rows
    for i in range(len(ps)):
        if i == 0:
            ind = np.argmax(ps[i][:, 0])
            ps[i] = np.flip(np.roll(ps[i], -ind - 1, axis=0), axis=0)
        else:
            ps[i] = np.flip(np.roll(ps[i], 1, axis=0), axis=0)
        _, idx = np.unique(ps[i], axis=0, return_index=True)
        ps[i] = ps[i][np.sort(idx)]
        if closed:
            ps[i] = np.concatenate([ps[i], [ps[i][0]]])
    return np.array(ps)




def generate_seg_positions(Nsegs, pos, orientation, length,seg_ratio=None) :
    x,y=pos
    if seg_ratio is None:
        seg_ratio = np.array([1 / Nsegs] * Nsegs)
    ls_x = np.cos(orientation) * length * seg_ratio
    ls_y = np.sin(orientation) * length / Nsegs
    return [[x + (-i + (Nsegs - 1) / 2) * ls_x[i],
                      y + (-i + (Nsegs - 1) / 2) * ls_y] for i in range(Nsegs)]



def generate_segs_offline(N, pos, orientation, length, shape='drosophila_larva', seg_ratio=None, color=None,
                 mode='default'):
    if seg_ratio is None:
        seg_ratio = np.array([1 / N] * N)

    seg_positions =generate_seg_positions(N, pos, orientation, length,seg_ratio)
    from larvaworld.lib.reg.stored.miscellaneous import body_shapes
    base_seg_vertices = generate_seg_shapes(N, seg_ratio=seg_ratio, points=body_shapes[shape])
    if color is None:
        color = [0.0, 0.0, 0.0]
    seg_colors = [np.array((0, 255, 0))] + [color] * (N - 2) + [np.array((255, 0, 0))] if N > 5 else [color] * N
    if mode == 'default':
        from larvaworld.lib.model.agents.segmented_body import generate_segs
        return generate_segs(N, seg_positions, orientation, base_seg_vertices, seg_colors, seg_ratio, length)




def set_contour(segs, Ncontour=22):
    vertices = [np.array(seg.vertices) for seg in segs]
    l_side = aux.flatten_list([v[:int(len(v) / 2)] for v in vertices])
    r_side = aux.flatten_list([np.flip(v[int(len(v) / 2):], axis=0) for v in vertices])
    r_side.reverse()
    total_contour = l_side + r_side
    if len(total_contour) > Ncontour:
        random.seed(1)
        contour = [total_contour[i] for i in sorted(random.sample(range(len(total_contour)), Ncontour))]
    else:
        contour = total_contour
    return contour

def sense_food(pos, sources=None, grid=None, radius=None):

    if grid:
        cell = grid.get_grid_cell(pos)
        if grid.get_cell_value(cell) > 0:
            return cell
    elif sources and radius is not None:
        valid = sources.select(aux.eudi5x(np.array(sources.pos), pos) <= radius)
        valid.select(valid.amount > 0)

        if len(valid) > 0:
            return random.choice(valid)
    return None


def get_larva_dicts(ls):
    deb_dicts = {}
    nengo_dicts = {}
    bout_dicts = {}
    for id, l in ls.items():
        if hasattr(l, 'deb') and l.deb is not None:
            deb_dicts[id] = l.deb.finalize_dict()
        try :
            from larvaworld.lib.model.modules.nengobrain import NengoBrain
            if isinstance(l.brain, NengoBrain):
                if l.brain.dict is not None:
                    nengo_dicts[id] = l.brain.dict
        except :
            pass
        if l.brain.locomotor.intermitter is not None:
            bout_dicts[id] = l.brain.locomotor.intermitter.build_dict()

    dic0 = aux.AttrDict({'deb': deb_dicts,
                         'nengo': nengo_dicts, 'bouts': bout_dicts,
                         })

    dic = aux.AttrDict({k: v for k, v in dic0.items() if len(v) > 0})
    return dic

def get_step_slice(s,e,dt, pars, t0=0, t1=40, track_t0_min=0, track_t1_min=0):
    s0, s1 = int(t0 / dt), int(t1 / dt)
    trange = np.arange(s0, s1, 1)
    tmin = track_t0_min + t0
    tmax = t1 - track_t1_min
    valid_ids = e[(e['t0'] <= tmin) & (e['t1'] >= tmax)].index
    return s.loc[(trange, valid_ids), pars]

def index_unique(df, level='Step', ascending=True, as_array=False):
    """
    Get the unique values of a level of a pandas Multiindex

    Args:
    - df: pd.DataFrame - The dataframe.
    - level: str - The level to index.
    - ascending: bool - Whether to sort the data in ascending order or not.
    - as_array: bool - Whether to return the result as an array or not.
    """

    a = df.index.get_level_values(level).sort_values(ascending=ascending).drop_duplicates()
    if as_array:
        return a.values
    else:
        return a

def existing_cols(cols,df) :
    return [col for col in cols if col in df.columns.values]

def nonexisting_cols(cols,df) :
    return [col for col in cols if col not in df.columns.values]

def cols_exist(cols,df) :
    return set(cols).issubset(df.columns.values)


