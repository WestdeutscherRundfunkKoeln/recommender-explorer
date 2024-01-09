def getTopN(N, category_list):
    category_items = {}
    for items in category_list:
        for item in items:
            if item in category_items:
                category_items[item] += 1
            else:
                category_items[item] = 1

    top_category_idxs = sorted(category_items.items(), key=lambda x: x[1], reverse=True)
    top_categories = [key for key, value in top_category_idxs[0:N]]
    top_categories = sorted(top_categories)
    return top_categories