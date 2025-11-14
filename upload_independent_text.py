import json
import re

import datetime
from pathlib import Path


from op_server_uploader.text import upload_text
from op_server_uploader.instance import upload_instance, upload_add_search_segmentation, upload_translation_instance
from BoSegmenter.botok_tokenizer import get_segments, get_segment_spans
from milvus_segment_generator.segment import segment_text


def preprocess_text(text):
    text = re.sub(r"〔.+〕", "", text)
    text = re.sub(r"\{D.+?\}", "", text)
    if text.endswith("༄"):
        text = text[:-1]
    text = text.replace("\n", "")
    return text

def prepare_instance(text):
    text_segments = get_segments(text)
    segmentation = get_segment_spans(text_segments)
    instance = {
        'metadata': {
            "type": "critical",
            "source": "openpecha.org",
            "colophon": "Sample colophon text",
            "incipit_title": {
                "en": "Opening words",
                "bo": "དབུ་ཚིག"
                }
            },
        'annotation': segmentation,
        'content': text
    }
    return instance

def prepare_search_segmentation(base_text, lang):
    segmentation, segmented_text = segment_text(base_text, lang)
    search_seg_ann = {
        'type': 'search_segmentation',
        'annotation': segmentation
    }
    return search_seg_ann



def upload_independent_text(text_dir):
    openpecha_server_ids = {}
    base_text = (text_dir / "base.txt").read_text(encoding='utf-8')
    base_text = preprocess_text(base_text)

    text_meta_data = json.load(open(text_dir / "meta.json", "r"))
    text_meta_data['date'] = datetime.datetime.now().strftime("%Y-%m-%d")
    op_text_id = upload_text(text_meta_data)
    print("Text uploaded successfully")
    op_instance = prepare_instance(base_text)
    op_instance_id = upload_instance(op_text_id, op_instance)
    print("Instance uploaded successfully")
    op_search_seg_ann = prepare_search_segmentation(base_text, 'bo')
    op_search_seg_ann_id = upload_add_search_segmentation(op_instance_id, op_search_seg_ann)
    print("Search segmentation uploaded successfully")
    openpecha_server_ids['text_id'] = op_text_id
    openpecha_server_ids['instance_id'] = op_instance_id
    openpecha_server_ids['search_seg_ann_id'] = op_search_seg_ann_id
    print("Independent text uploaded successfully")
    return openpecha_server_ids


if __name__ == "__main__":
    text_dirs = list(Path("data/independent_text").iterdir())
    text_dirs.sort()
    independent_text_list = []
    for text_dir in text_dirs:
        independent_text_ids = upload_independent_text(text_dir)
        independent_text_list.append(independent_text_ids)
    with open('./data/independent_text_list.json', 'w') as f:
        json.dump(independent_text_list, f)


