import panel as pn
import logging
from dto.pa_service_content_item import PaServiceContentItemDto
from view.cards.paservice_cards.pa_service_content_card import PaServiceContentCard

logger = logging.getLogger(__name__)

class PaServiceContentStartCard(PaServiceContentCard):

    CARD_HEIGHT = 600
    def __init__(self, config):
        super().__init__(config)

    def draw(self, content_dto: PaServiceContentItemDto, nr, model, model_config, modal_viewer):
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
                         <img class="blurred_background" src={content_dto.teaserImageUrl}>
                         <img class="teaser_image" src={content_dto.teaserImageUrl}>
                         <div class="duration_label">
                             <span>{(content_dto.duration / 60):.0f} Min.</span>
                         </div>
                     </div>
                     """)

        teaserimage.stylesheets = [stylesheet_image]
        teaserimage.margin = (0, 0, 0, 0)

        child_objects = [
            teaserimage,
            pn.pane.Markdown(f""" ### Modell: {model} """)
        ]

        card = pn.Card(
            styles={ 'background': self.config[model_config][content_dto.provenance][model]['start_color'], 'overflow': 'auto' },
            margin=5,
            height=self.CARD_HEIGHT,
            hide_header=True
        )

        card.objects = child_objects

        return super().draw(content_dto, card)