import logging
from datetime import datetime, timezone

import panel as pn
from dto.wdr_content_item import WDRContentItemDto
from view.RecoExplorerApp import RecoExplorerApp

logger = logging.getLogger(__name__)


class WDRContentDraftCard:
    CARD_HEIGHT = 600

    def __init__(
        self, config, reco_explorer_app_instance: RecoExplorerApp | None = None
    ):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance

    def draw(
        self, content_dto: WDRContentItemDto, nr, model, model_config, modal_viewer
    ):
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

        teaserimage = pn.pane.HTML("""
                     <div class="img_wrapper">
                         <img class="blurred_background" src="https://www1.wdr.de/resources/img/wdr/logo/wdr_logo.svg">
                         <img class="teaser_image" src="https://www1.wdr.de/resources/img/wdr/logo/wdr_logo.svg">
                     </div>
                     """)

        teaserimage.stylesheets = [stylesheet_image]
        teaserimage.margin = (0, 0, 0, 0)

        child_objects: list[pn.viewable.Viewable] = [
            teaserimage,
            pn.pane.Markdown(f""" ### Modell: {model} """),
            pn.pane.Markdown(f"""
                   #### DRAFT
                   **Datentyp:** Beitrag 📰 
                   **Datum:** {datetime.now(tz=timezone.utc)}
            """),
            pn.pane.Markdown(f"""
            ***
            ##### DRAFT
            {" ".join(content_dto.description.split(" ")[:500]).strip()}{"..." if len(content_dto.description) > 500 else ""}
            """),
        ]


        return pn.Column(
            pn.Card(
                styles={
                    "background": self.config[model_config][content_dto.provenance][
                        model
                    ]["start_color"],
                    "overflow": "auto",
                },
                margin=5,
                height=self.CARD_HEIGHT,
                hide_header=True,
                objects=child_objects,
            )
        )
