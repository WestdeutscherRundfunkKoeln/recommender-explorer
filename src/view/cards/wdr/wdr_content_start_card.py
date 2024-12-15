import panel as pn
import logging
from dto.wdr_content_item import WDRContentItemDto
from view.cards.wdr.wdr_content_card import WDRContentCard

logger = logging.getLogger(__name__)

class WDRContentStartCard(WDRContentCard):

    def draw(self, content_dto: WDRContentItemDto, nr, model, model_config, modal_viewer):
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

        pn.extension(raw_css=[stylesheet_image])

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

        truncated_description = pn.pane.Markdown(f"""
        ***
        ##### {content_dto.title}
        {" ".join(content_dto.longDescription.split(" ")[:500])}...
        """)

        config = {"headerControls": {"maximize": "remove", "collapse": "remove", "minimize":"remove", "smallify":"remove"}}

        float_panel = pn.layout.FloatPanel(
            pn.Column(
                teaserimage,
                super().draw(content_dto, pn.Card()),
                truncated_description
            ),
            #truncated_description,
            sizing_mode="stretch_width",
            width=330,
            height=330,
            config=config,
            visible=False,
            contained=True,
            styles={"position": "absolute", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)",
                    "z-index": "1000"},)

        float_panel_container = pn.bind(lambda visible: float_panel if visible else None, float_panel.param.visible)

        #def toggle_float_panel(event):
            #float_panel.visible = not float_panel.visible

        def toggle_float_panel(event):
            if float_panel.visible:
                float_panel.css_classes = ["float-panel"]
            else:
                float_panel.css_classes = ["float-panel", "visible"]
            float_panel.visible = not float_panel.visible


        button.on_click(toggle_float_panel)

        child_objects = [
            teaserimage,
            pn.pane.Markdown(f""" ### Modell: {model} """),
            button,
        ]

        card = pn.Card(
            styles={ 'background': self.config[model_config][content_dto.provenance][model]['start_color'], 'overflow': 'auto' },
            margin=5,
            height=self.card_height,
            hide_header=True
        )

        card.objects = child_objects

        card = super().draw(content_dto, card, button)

        return pn.Column(card, float_panel_container)
