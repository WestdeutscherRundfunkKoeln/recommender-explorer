from typing import Any

from bokeh.models.formatters import PrintfTickFormatter
import panel as pn
from view.widgets.widget import UIWidget

from view import ui_constants as c


class SliderWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.FloatSlider:
        slider = pn.widgets.FloatSlider(
            name=config.get(c.SLIDER_NAME_KEY, "Wert"),
            format=PrintfTickFormatter(
                format=f"%.2f {config.get(c.SLIDER_UNIT_KEY, '')}"
            ),
            start=config.get(c.SLIDER_START_KEY, 0),
            end=config.get(c.SLIDER_END_KEY, 1),
            step=config.get(c.SLIDER_STEP_KEY, 0.01),
            value=config.get(c.SLIDER_START_KEY, 0),
        )
        slider.params = {
            "label": config.get(c.SLIDER_LABEL_KEY, "relativerangefilter_duration"),
            "reset_to": config.get(c.SLIDER_START_KEY, 0),
        }

        duration_filter_watcher = slider.param.watch(
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
            "value",
            onlychanged=True,
        )

        self.controller_instance.register(
            "reco_filter",
            slider,
            duration_filter_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )
        return slider
