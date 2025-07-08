import os
import json
from paddleocr import DocImgOrientationClassification
SAVE_JSON = "./output"

model = DocImgOrientationClassification(model_dir="/opt/data/private/hyl/code/InStruct/model/ocr_model/PP-LCNet_x1_0_doc_ori/")
output = model.predict("合同r.jpg",  batch_size=1)
for res in output:
    res.save_to_json(SAVE_JSON)

for filename in os.listdir(SAVE_JSON):
    json_path = os.path.join(SAVE_JSON, filename)
    with open(json_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)
    os.remove(json_path)

label_names = ocr_data["label_names"]
print(label_names[0])