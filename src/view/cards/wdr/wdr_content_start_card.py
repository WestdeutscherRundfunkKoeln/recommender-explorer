import panel as pn
import logging
from dto.wdr_content_item import WDRContentItemDto
from view.cards.wdr.wdr_content_card import WDRContentCard

logger = logging.getLogger(__name__)


class WDRContentStartCard(WDRContentCard):

    def draw(self, content_dto: WDRContentItemDto, nr, model, model_config, modal_viewer):
        def create_float_panel():
            teaserimage_card = pn.Card(
                teaserimage,
                styles={
                    'background': self.config[model_config][content_dto.provenance][model]["reco_color"],
                },
            )

            float_panel = pn.layout.FloatPanel(
                pn.Column(
                    teaserimage_card,
                    super(WDRContentStartCard, self).draw(content_dto, pn.Card(
                        styles={'background': self.config[model_config][content_dto.provenance][model]["reco_color"]})),
                    truncated_description
                ),
                config={"headerControls": {"maximize": "remove", "collapse": "remove",
                                           "minimize": "remove", "smallify": "remove",},
                        "panelSize": "800 1100",
                        "position": "center 10 -500"
                        },
                styles={ "panelSize": "900 1100",
                        "z-index": "1000",
                        "background": self.config[model_config][content_dto.provenance][model]['start_color']},
            )

            return float_panel

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
                         
                         .relative-container {
                             position: relative;
                             display: inline-block;
                         }
                         
                         .float-panel {
                             position: absolute;
                             top: 50%;
                             left: 50%;
                             transform: translate(-50%, -50%);
                             z-index: 1000;
                             display: none;
                         }   
                         
                         .float-panel.visible {
                              display: block;
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

        pn.extension(raw_css=[stylesheet_image])

        button = pn.widgets.Button(name="Details öffnen", button_type="primary", width_policy="fit")

        panel_container = pn.Column()

        def toggle_float_panel(event):
            panel_container.clear()  # Clear the entire container (remove panel)
            panel_container.append(create_float_panel())  # Add the new panel

        button.on_click(toggle_float_panel)
        truncated_description = pn.Card(
            pn.pane.Markdown(f"""
        ***
        ##### {content_dto.title}
        {" ".join(content_dto.longDescription.split(" ")[:500])}...
        """,
                             styles={
                                 'background': self.config[model_config][content_dto.provenance][model]["reco_color"], }
                             ))
        child_objects = [
            teaserimage,
            pn.pane.Markdown(f""" ### Modell: {model} """)
        ]

        card = pn.Card(
            styles={'background': self.config[model_config][content_dto.provenance][model]['start_color'],
                    'overflow': 'auto'},
            margin=5,
            height=self.card_height,
            hide_header=True
        )

        card.objects = child_objects

        card = super().draw(content_dto, card, button)

        return pn.Column(card, panel_container)
