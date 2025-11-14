import json

import datetime
from pathlib import Path


from op_server_uploader.text import upload_text
from op_server_uploader.instance import upload_instance, upload_add_search_segmentation, upload_translation_instance


PRAYER_CATEGORY_ID = "A6uBwcy0ZvFj1GfRWThAn"

def get_recitation_text(prayer_path):
    text = json.loads(prayer_path.read_text(encoding='utf-8'))
    return text

def get_text(text, lang):
    text_content = ''
    char_walker = 0
    segment_ann = []
    for segment in text['text']:
        cur_segment = segment[lang]
        text_content += cur_segment
        segment_ann.append({
            'span': {
                'start': char_walker,
                'end': char_walker + len(cur_segment)
            }
        })
        char_walker += len(cur_segment)
    return text_content, segment_ann

def get_target_annotation(src_segment_ann):
    annotations = []
    for ann_index, ann in enumerate(src_segment_ann):
        annotations.append({
            'span': {
                'start': ann['span']['start'],
                'end': ann['span']['end']
            },
            'index': ann_index,
        })
    return annotations

def get_alignment_annotation(translation_segment_ann):
    annotations = []
    for ann_index, ann in enumerate(translation_segment_ann):
        annotations.append({
            'span': {
                'start': ann['span']['start'],
                'end': ann['span']['end']
            },
            'index': ann_index,
            'alignment_index': [ann_index]
        })
    return annotations

def prepare_translation_instance(src_text_id, src_instance_id, src_segment_ann, trans_lang, text):

    translation_text, translation_segment_ann = get_text(text, trans_lang)
    translation_instance = {
        "language": trans_lang,
        "content": translation_text,
        "title": text['title'][trans_lang],
        "source": text['source'][trans_lang]['link'],
        "author": {
            "person_bdrc_id": "P4954"
        },
        "segmentation": translation_segment_ann,
        "target_annotation": get_target_annotation(src_segment_ann),
        "alignment_annotation": get_alignment_annotation(translation_segment_ann),
        "copyright": text['source'][trans_lang]['copyright'],
        "license": text['source'][trans_lang]['license']
        }
    return translation_instance

def prepare_text(text, type_, lang):
    op_text = {
        "type": type_,
        "title": {
            "bo": text["title"][lang],
        },
        "language": lang,
        "contributions": [
            {
            "person_bdrc_id": "P4954",
            "role": "author"
            }
        ],
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "bdrc": "",
        "category_id": PRAYER_CATEGORY_ID,
        "copyright": text['source'][lang]['copyright'],
        "license": text['source'][lang]['license'],
    }

    return op_text

def prepare_instance(text, language):
    bo_text, bo_segment_ann = get_text(text, 'bo')
    
    instance= {
        'metadata': {
        "type": "critical",
        "source": text['source'][language]['link'],
        "colophon": "Sample colophon text",
        "incipit_title": {
            "en": "Opening words",
            "bo": "དབུ་ཚིག"
          }
        },
        'annotation': bo_segment_ann,
        'content': bo_text
    }
    return instance

def prepare_search_segmentation(segment_ann):
    search_seg_ann = {
        'type': 'search_segmentation',
        'annotation': segment_ann
    }
    return search_seg_ann

def upload_recitation_text(prayer_path):
    recitation_text_ids = {
        'bo': {},
        'en': {},
        'lzh': {}
    }
    recitation_text = get_recitation_text(prayer_path)

    bo_text = prepare_text(recitation_text, 'root', 'bo')
    bo_text_id = upload_text(bo_text)

    bo_instance = prepare_instance(recitation_text, language="bo")
    bo_instance_id = upload_instance(bo_text_id, bo_instance)
    bo_search_seg_ann = prepare_search_segmentation(bo_instance['annotation'])
    bo_search_seg_ann_id = upload_add_search_segmentation(bo_instance_id, bo_search_seg_ann)
    recitation_text_ids['bo']['text_id'] = bo_text_id
    recitation_text_ids['bo']['instance_id'] = bo_instance_id
    recitation_text_ids['bo']['search_seg_ann_id'] = bo_search_seg_ann_id
    print("BO instance and search segmentation uploaded successfully")

    en_instance = prepare_translation_instance(bo_text_id, bo_instance_id, bo_instance['annotation'], 'en', recitation_text)
    en_text_id, en_instance_id = upload_translation_instance(bo_instance_id, en_instance)
    en_search_seg_ann = prepare_search_segmentation(en_instance['segmentation'])
    en_search_seg_ann_id = upload_add_search_segmentation(en_instance_id, en_search_seg_ann)
    recitation_text_ids['en']['text_id'] = en_text_id
    recitation_text_ids['en']['instance_id'] = en_instance_id
    recitation_text_ids['en']['search_seg_ann_id'] = en_search_seg_ann_id
    print("EN instance and search segmentation uploaded successfully")

    zh_instance = prepare_translation_instance(bo_text_id, bo_instance_id, bo_instance['annotation'], 'lzh', recitation_text)
    zh_text_id, zh_instance_id = upload_translation_instance(bo_instance_id, zh_instance)
    zh_search_seg_ann = prepare_search_segmentation(zh_instance['segmentation'])
    zh_search_seg_ann_id = upload_add_search_segmentation(zh_instance_id, zh_search_seg_ann)
    recitation_text_ids['lzh']['text_id'] = zh_text_id
    recitation_text_ids['lzh']['instance_id'] = zh_instance_id
    recitation_text_ids['lzh']['search_seg_ann_id'] = zh_search_seg_ann_id
    print("ZH instance and search segmentation uploaded successfully")
    print("Recitation text uploaded successfully")
    return recitation_text_ids

if __name__ == "__main__":
    
    recitation_text_list = []
    prayer_text_paths = list(Path("data/prayers").iterdir())
    prayer_text_paths.sort()

    for prayer_text_path in prayer_text_paths:
        recitation_text_ids = upload_recitation_text(prayer_text_path)
        recitation_text_list.append(recitation_text_ids)

    with open('./data/recitation_text_list.json', 'w') as f:
        json.dump(recitation_text_list, f)