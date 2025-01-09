import logging

import panel as pn

from dto.wdr_content_item import WDRContentItemDto
from view.cards.wdr.wdr_content_card import WDRContentCard
from view.cards.cards_utils import create_click_handler
from view.cards.cards_utils import append_custom_css_for_insert_id_button
from view.cards.cards_utils import insert_id_button

logger = logging.getLogger(__name__)


class WDRContentRecoCard(WDRContentCard):
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

        button = pn.widgets.Button(name="Details öffnen", button_type="primary", width_policy="fit")

        truncated_description = pn.Card(
            pn.pane.Markdown(f"""
        ***
        ##### {content_dto.title}
        {" ".join(content_dto.longDescription.split(" ")[:500])}...
        """,
                             styles={
                                 'background': self.config[model_config][content_dto.provenance][model][
                                     "reco_color"], }))

        teaserimage_card = pn.Card(
            teaserimage,
            styles={
                'background': self.config[model_config][content_dto.provenance][model]["reco_color"],
            },
        )

        config = {
            "headerControls": {"maximize": "remove", "collapse": "remove", "minimize": "remove", "smallify": "remove"}}

        float_panel = pn.layout.FloatPanel(
            pn.Column(
                teaserimage_card,
                super().draw(content_dto, pn.Card(
                    styles={'background': self.config[model_config][content_dto.provenance][model]["reco_color"]})),
                truncated_description
            ),
            sizing_mode="stretch_width",
            min_width=450,
            max_width=700,
            height=330,
            config=config,
            visible=False,
            styles={"background": self.config[model_config][content_dto.provenance][model]["reco_color"],
                    "position": "absolute", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)",
                    "z-index": "1000"}, )

        float_panel_container = pn.bind(lambda visible: float_panel if visible else None, float_panel.param.visible)

        def toggle_float_panel(event):
            float_panel.visible = not float_panel.visible

        button.on_click(toggle_float_panel)

        child_objects = [
            teaserimage,
            pn.pane.Markdown(f""" ### Score: {str(round(content_dto.dist, 2))}"""),
            #button,
        ]

        card = pn.Card(
            styles={
                "background": self.config[model_config][content_dto.provenance][model][
                    "reco_color"
                ],
                "overflow": "auto",
            },
            margin=5,
            height=self.card_height,
            hide_header=True,
        )

        card.objects = child_objects

        append_custom_css_for_insert_id_button(
            self.config, model_config, content_dto, model
        )
        click_handler = create_click_handler(
            content_dto.externalid,
            self.reco_explorer_app_instance.config_based_nav_controls,
        )
        insert_id_button_widget = insert_id_button(click_handler)

        card = super().draw(content_dto, card, insert_id_button_widget, button)

        return pn.Column(card, float_panel_container)
