import json

subgenre_luts = {}
thematic_luts = {}
show_luts = {}

with open('audiothek_content_dev_latest.json', encoding='utf-8') as f:
    for line in f:

        c = json.loads(line)
        prim_id = c['id']

        #
        # subgenre lut
        #
        if 1:
            subgenre_ids = c['subgenreCategories']
            subgenre_tits = c['subgenreCategoriesTitle']
            for idx, x in enumerate(subgenre_ids):
                key = subgenre_ids[idx]
                val = subgenre_tits[idx]
                subgenre_luts[key] = val

                out = json.dumps(subgenre_luts, indent=4, ensure_ascii=False).encode('utf8')
                with open('audiothek_subgenre_lut_2024_06_24.json', 'w', encoding='utf-8') as fp:
                    #print(out, file=fp)
                    fp.write(out.decode())


        # 
        # thematics lut
        #
        if 1:
            thematic_ids = c['thematicCategories']
            thematic_tits = c['thematicCategoriesTitle']

            for idx, x in enumerate(thematic_ids):
                key = thematic_ids[idx]
                val = thematic_tits[idx]
                thematic_luts[key] = val

            out = json.dumps(thematic_luts, indent=4, ensure_ascii=False).encode('utf8')
            with open('audiothek_thematic_lut_2024_06_24.json', 'w', encoding='utf-8') as fp:
                #print(out, file=fp)
                fp.write(out.decode())
