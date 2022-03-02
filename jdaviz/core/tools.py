import os

from echo import delay_callback

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool
from glue_jupyter.bqplot.common.tools import (HomeTool, BqplotPanZoomMode,
                                              BqplotPanZoomXMode, BqplotPanZoomYMode,
                                              BqplotRectangleMode, BqplotCircleMode,
                                              BqplotEllipseMode, BqplotXRangeMode,
                                              BqplotYRangeMode, BqplotSelectionTool,
                                              INTERACT_COLOR)
from bqplot.interacts import BrushSelector, BrushIntervalSelector

__all__ = []

ICON_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'icons')


# Override icons for built-in tools from glue-jupyter
HomeTool.icon = os.path.join(ICON_DIR, 'home.svg')
BqplotPanZoomMode.icon = os.path.join(ICON_DIR, 'pan.svg')
BqplotPanZoomXMode.icon = os.path.join(ICON_DIR, 'pan_x.svg')
BqplotPanZoomYMode.icon = os.path.join(ICON_DIR, 'pan_y.svg')
BqplotRectangleMode.icon = os.path.join(ICON_DIR, 'select_xy.svg')
BqplotCircleMode.icon = os.path.join(ICON_DIR, 'select_circle.svg')
BqplotEllipseMode.icon = os.path.join(ICON_DIR, 'select_ellipse.svg')
BqplotXRangeMode.icon = os.path.join(ICON_DIR, 'select_x.svg')
BqplotYRangeMode.icon = os.path.join(ICON_DIR, 'select_y.svg')


class _BaseSelectZoom(BqplotSelectionTool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

    def _new_interact(self):
        raise NotImplementedError(f"_new_interact not implemented by {self.__class__.__name__}")

    def reset(self):
        if hasattr(self, 'interact'):
            self.interact.close()
        self.interact = self._new_interact()
        self.interact.observe(self.on_brushing, "brushing")

    def on_brushing(self, msg):
        if self.interact.brushing:
            # start drawing a box, don't need to do anything
            return

        with delay_callback(self.viewer.state, 'x_min', 'x_max', 'y_min', 'y_max'):
            # implement on_update_zoom to act on the applicable interact Selector
            self.on_update_zoom()

        # reset destroys the current interact and replaces with a new one to avoid having
        # the draggable selection
        self.reset()
        # activate automatically activates the new interact so that another zoom is possible
        # until deselecting the zoom tool
        self.activate()


@viewer_tool
class BoxZoom(_BaseSelectZoom):
    icon = os.path.join(ICON_DIR, 'zoom_box.svg')
    tool_id = 'jdaviz:boxzoom'
    action_text = 'Box zoom'
    tool_tip = 'Zoom to a drawn rectangle'

    def _new_interact(self):
        return BrushSelector(x_scale=self.viewer.scale_x,
                             y_scale=self.viewer.scale_y,
                             color=INTERACT_COLOR)

    def on_update_zoom(self):
        if self.interact.selected_x is None or self.interact.selected_y is None:
            # a valid box was not drawn, perhaps just a click with no drag!
            # let's ignore and reset the tool
            return

        self.viewer.state.x_min, self.viewer.state.x_max = self.interact.selected_x
        self.viewer.state.y_min, self.viewer.state.y_max = self.interact.selected_y


@viewer_tool
class XRangeZoom(_BaseSelectZoom):
    icon = os.path.join(ICON_DIR, 'zoom_xrange.svg')
    tool_id = 'jdaviz:xrangezoom'
    action_text = 'Horizontal zoom'
    tool_tip = 'Zoom to a drawn horizontal region'

    def _new_interact(self):
        return BrushIntervalSelector(scale=self.viewer.scale_x,
                                     color=INTERACT_COLOR)

    def on_update_zoom(self):
        if self.interact.selected is None:
            # a valid region was not drawn, perhaps just a click with no drag!
            # let's ignore and reset the tool
            return

        self.viewer.state.x_min, self.viewer.state.x_max = self.interact.selected


class _BaseSidebarShortcut(Tool):
    plugin_label = None  # define in subclass
    viewer_select_traitlet = 'selected_viewer'

    def activate(self):
        self.viewer.jdaviz_app.state.drawer = True
        tray_item_names = [tray_item['name'] for tray_item in self.viewer.jdaviz_app.state.tray_items]
        index = tray_item_names.index(self.plugin_name)
        if index not in self.viewer.jdaviz_app.state.tray_items_open:
            self.viewer.jdaviz_app.state.tray_items_open = self.viewer.jdaviz_app.state.tray_items_open + [index]
        plugin = self.viewer.jdaviz_app.get_tray_item_from_name(self.plugin_name)
        setattr(plugin, self.viewer_select_traitlet, self.viewer.reference_id)


@viewer_tool
class SidebarShortcutExport(_BaseSidebarShortcut):
    plugin_name = 'g-export-viewer'
    viewer_select_traitlet = 'selected_viewer'

    icon = os.path.join(ICON_DIR, 'save.svg')
    tool_id = 'jdaviz:sidebar_export'
    action_text = 'Export plot'
    tool_tip = 'Open export viewer plugin in sidebar'


@viewer_tool
class SidebarShortcutCompass(_BaseSidebarShortcut):
    plugin_name = 'imviz-compass'
    viewer_select_traitlet = 'selected_viewer'

    icon = os.path.join(ICON_DIR, 'compass.svg')
    tool_id = 'jdaviz:sidebar_compass'
    action_text = 'Compass'
    tool_tip = 'Open compass plugin in sidebar'
