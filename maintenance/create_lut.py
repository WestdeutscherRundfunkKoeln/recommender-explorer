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
        if 0:
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
        if 0: 
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


            
        # 
        # show-core-id lut
        #
        if 1:

            show_core_id = c.get('showCoreId', False)

            if show_core_id:
                curr_episode_nr = c.get('episodeNumber', 10000)
                curr_season_nr = c.get('seasonNumber', 10000)

                if not show_luts.get(show_core_id):
                    show_luts[show_core_id] = {}
                    show_luts[show_core_id] = {'episode': prim_id }

                if curr_season_nr <= show_luts[show_core_id].get('season_nr', 10000):
                    if curr_episode_nr < show_luts[show_core_id].get('episode_nr', 10000):
                        # new low of season and episode
                        show_luts[show_core_id] = {'episode': prim_id, 'season_nr': curr_season_nr, 'episode_nr': curr_episode_nr}
                        #show_luts[show_core_id] = {'episode': prim_id }

                transposed = []
                for idx, val in show_luts.items():
                    item = {
                        'id': idx,
                        'episode': val.get('episode'),
                        'season': val.get('season_nr', 0),
                        'episode_nr': val.get('episode_nr', 0)
                    }
                    transposed.append(item)


    # write out
    out = json.dumps(transposed, indent=4, ensure_ascii=False).encode('utf8')
    with open('audiothek_show_lut_2024_06_27.json', 'w', encoding='utf-8') as fp:
        fp.write(out.decode())

