from dataclasses import asdict

from dto.item import ItemDto


class FilterPostproc:
    def filterDuplicates(self, start_item: ItemDto, reco_items: list, parameters):
        # doesn't work with imageurl, has to be changed to teaserimage
        for parameter in parameters:
            all_param_items = []
            nn_items = []
            for item in reco_items:
                if (
                    asdict(item)[parameter] not in asdict(start_item)[parameter]
                    and asdict(item)[parameter] not in all_param_items
                ):
                    all_param_items.append(asdict(item)[parameter])
                    nn_items.append(item)
        return nn_items

    def filterDuplicateImage(df, item):
        pass
