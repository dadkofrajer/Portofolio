import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_shape():
    payload = {
      "country_tracks": ["US"],
      "schools": ["Georgia Tech"],
      "deadlines": {"Georgia Tech": "2026-01-04"},
      "weekly_hours_cap": 8,
      "student_profile": {"gpa_unweighted": 3.8, "intended_major": "Computer Science"},
      "portfolio": [
        {"id":"e1","title":"Robotics team lead","lens":"Leadership","type":"Club","role_level":"Lead","hours_per_week":4,"people_impacted":30,"theme_tags":["Robotics"]},
        {"id":"e2","title":"ML wildfire classifier","lens":"Curiosity","type":"Project","role_level":"Founder","hours_total":80,"theme_tags":["AI"]}
      ]
    }
    res = client.post("/portfolio/analyze", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert set(data.keys()) == {"scores","gaps","recommendations","tasks"}
    assert "lens_scores" in data["scores"]
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["tasks"], list)

