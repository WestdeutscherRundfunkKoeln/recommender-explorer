from typing import Any

import panel as pn
from bokeh.models.formatters import PrintfTickFormatter
from view import ui_constants as c
from view.widgets.widget import UIWidget


class SliderWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.Row:

        slider = pn.widgets.FloatSlider(
            name=config.get(c.SLIDER_NAME_KEY, "Wert"),
            format=PrintfTickFormatter(
                format=f"%.2f {config.get(c.SLIDER_UNIT_KEY, '')}"
            ),
            start=config.get(c.SLIDER_START_KEY, 0),
            end=config.get(c.SLIDER_END_KEY, 1),
            step=config.get(c.SLIDER_STEP_KEY, 0.01),
            value=config.get(c.SLIDER_START_KEY, 0),
            width=c.FILTER_WIDTH,
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
            config.get(c.SLIDER_COMPONENT_GROUP_KEY, "reco_filter"),
            slider,
            duration_filter_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )

        slider.is_leaf_widget = True

        slider.reset_identifier = c.RESET_IDENTIFIER_RECO_FILTER

        tooltip = pn.widgets.TooltipIcon(
            value=config.get(c.SLIDER_TOOLTIP_KEY, c.TOOLTIP_FALLBACK)
        )

        if(config.get(c.SLIDER_CUSTOM_KEY)):
            self.change_slider_value(slider)
            slider.param.watch(self.change_slider_value, "value")

        return pn.Row(slider, tooltip)



    def change_slider_value(self, event_or_slider):
        """Change the value of the slider."""
        if isinstance(event_or_slider, pn.widgets.FloatSlider):  # Manual call
            slider = event_or_slider
        else:  # Event-driven call
            slider = event_or_slider.obj

        transformed_value = slider.value * 60
        transformed_format = {"duration": {"gte": transformed_value}}

