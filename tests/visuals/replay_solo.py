from lib.conf.base.dtypes import null_dict
from lib.conf.stored.conf import loadRef

refID = 'exploration.dish_0'
d = loadRef(refID)
d.visualize_single(id=5, close_view=True, fix_point=6, fix_segment=-1, save_to='./media',
                         draw_Nsegs=None)
