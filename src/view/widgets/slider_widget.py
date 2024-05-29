from typing import Any

from bokeh.models.formatters import PrintfTickFormatter
import panel as pn
from view.widgets.widget import UIWidget

from view import ui_constants


class SliderWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.FloatSlider:
        slider = pn.widgets.FloatSlider(
            name=config.get(ui_constants.SLIDER_LABEL_KEY, "Wert"),
            format=PrintfTickFormatter(
                format=f"%.2f {config.get(ui_constants.SLIDER_UNIT_KEY, '')}"
            ),
            start=config.get(ui_constants.SLIDER_START_KEY, 0),
            end=config.get(ui_constants.SLIDER_END_KEY, 1),
            step=config.get(ui_constants.SLIDER_STEP_KEY, 0.01),
            value=config.get(ui_constants.SLIDER_START_KEY, 0),
        )
        return slider
