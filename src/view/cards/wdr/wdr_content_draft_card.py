import logging
from typing import cast

import panel as pn
from dto.wdr_content_item import WDRContentItemDto
from view.RecoExplorerApp import RecoExplorerApp


logger = logging.getLogger(__name__)


class WDRContentDraftCard:
    CARD_HEIGHT = 600
    type_icon = {
        "beitrag": "📰",
        "audio": "🔊",
        "video": "🎥",
    }

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
                   #### {content_dto.title}
                   **Datentyp:** {content_dto.type.title()} {self.type_icon.get(content_dto.type, "")} 
                   **Datum:** {content_dto.availableFrom}
                   **Strukturpfad:** {content_dto.structurePath}
                   **External ID:** {content_dto.externalid}
                   **Themen:** {', '.join(set(content_dto.thematicCategories))}
                   **Keywords:** {', '.join(set(content_dto.keywords))}
                   **Sophora ID:** [{content_dto.sophoraid}](https://{content_dto.domain}{content_dto.structurePath}/{content_dto.sophoraid}.html)
            """),
            pn.pane.Markdown(f"""
            ***
            ##### {content_dto.title}
            {" ".join(content_dto.longDescription.split(" ")[:500])}...
            """),
        ]

        return pn.Card(
            styles={
                "background": self.config[model_config][content_dto.provenance][model][
                    "start_color"
                ],
                "overflow": "auto",
            },
            margin=5,
            height=self.CARD_HEIGHT,
            hide_header=True,
            objects=child_objects,
        )
