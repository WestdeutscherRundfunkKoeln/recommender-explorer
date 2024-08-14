import logging
from typing import Callable, Any

import panel as pn
import view.ui_constants as c
from dto.wdr_content_item import WDRContentItemDto
from view.cards.wdr.wdr_content_card import WDRContentCard
from view.util.view_utils import get_first_widget_by_accessor_function

logger = logging.getLogger(__name__)


class WDRContentRecoCard(WDRContentCard):
    CARD_HEIGHT = 600
    IMAGE_HEIGHT = 200

    def _create_click_handler(self, external_id) -> Callable[[Any], None]:
        """
        Create a click handler function that sets the value of a target widget
        to the external_id. Uses view utils function to get widget by accessor name.

        :param external_id: The external ID.
        :return: The click handler function.
        """
        def click_handler(event):
            target_widget = get_first_widget_by_accessor_function(self.reco_explorer_app_instance.config_based_nav_controls, "get_item_by_crid")
            if target_widget:
                target_widget.value = external_id

        return click_handler

    def _insert_id_button(self, click_handler) -> pn.widgets.Button:
        """
        Creates and returns a Button widget and assigns the
        specified click_handler function to its on_click event.

        :param click_handler: The function to be called when the button is clicked.
        :return: A Button widget with the assigned click_handler function for the on_click event.
        """
        insert_id_button = pn.widgets.Button(name=c.INSERT_ID_BUTTON_LABEL)
        insert_id_button.on_click(click_handler)
        return insert_id_button

    def _append_custom_css_for_insert_id_button(self, model_config, content_dto, model):
        """
        Appends custom CSS for the "insert id button" on the recommended item card. Colors depends on
        the start item and reco items card color from the config.

        :param model_config: The configuration for the model.
        :param content_dto: The data transfer object for the content.
        :param model: The model to append the custom CSS for.

        :return: None
        """
        css = f"""
            .bk.bk-btn.bk-btn-default {{
                background-color: {self.config[model_config][content_dto.provenance][model]["start_color"]} !important;
                font-weight: bolder;
            }}
            .bk.bk-btn.bk-btn-default:hover {{
                border-color: {self.config[model_config][content_dto.provenance][model]["reco_color"]} !important;
            }}
            """
        pn.extension(raw_css=[css])

    def draw(self, content_dto: WDRContentItemDto, nr, model, model_config, modal_func):
        stylesheet_image = """
                                 .img_wrapper {
                                     position: relative;
                                     width: 100%;
                                     height: 200px; 
                                 }

                                 img {
                                     display:block;
                                     width: 100%; 
                                     height: 100%;

                                     position: absolute;
                                     top: 0;
                                     left: 0;
                                 }

                                 .teaser_image{
                                     object-fit: contain;
                                     backdrop-filter: blur(10px);
                                 }

                                 .blurred_background {
                                     object-fit: fill;
                                 }

                                 .duration_label {
                                     position: absolute; 
                                     right:0px; 
                                     top:0px; 

                                     background-color: 
                                     rgba(0,0,0,0.4); 

                                     padding-left: 4px; 
                                     padding-right: 4px;
                                 }

                                 .duration_label span{
                                     color: #ffff; 
                                     font-weight: 500; 
                                     font-size: 12px;
                                 }
                             """

        teaserimage = pn.pane.HTML(f"""
                             <div class="img_wrapper">
                                 <img class="blurred_background" src={content_dto.teaserimage}>
                                 <img class="teaser_image" src={content_dto.teaserimage}>
                                 <div class="duration_label">
                                     <span>{(content_dto.duration / 60):.0f} Min.</span>
                                 </div>
                             </div>
                             """)

        teaserimage.stylesheets = [stylesheet_image]
        teaserimage.margin = (0, 0, 0, 0)

        child_objects = [
            teaserimage,
            pn.pane.Markdown(f""" ### Score: {str(round(content_dto.dist, 2))}"""),
        ]

        card = pn.Card(
            styles={
                "background": self.config[model_config][content_dto.provenance][model][
                    "reco_color"
                ],
                "overflow": "auto",
            },
            margin=5,
            height=self.CARD_HEIGHT,
            hide_header=True,
        )

        card.objects = child_objects

        self._append_custom_css_for_insert_id_button(model_config, content_dto, model)
        click_handler = self._create_click_handler(content_dto.externalid)
        insert_id_button = self._insert_id_button(click_handler)

        return super().draw(content_dto, card, insert_id_button)
