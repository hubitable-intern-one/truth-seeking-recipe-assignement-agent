import sys
import os
sys.path.append(os.getcwd())
from models.recipe_context import EvidenceQuery, Evidence
import json
import traceback

sample_json = """
[
    {
        "query": "test query",
        "evidence_items": [
            {
                "notes": "some notes",
                "source_link": "http://example.com",
                "link_status": true,
                "contains_notes_in_content": true
            }
        ]
    }
]
"""

try:
    data = json.loads(sample_json)
    queries = [EvidenceQuery(**item) for item in data]
    print("Validation Successful")
    # print(queries)
except Exception as e:
    print("Validation Failed")
    print(e)
    traceback.print_exc()
