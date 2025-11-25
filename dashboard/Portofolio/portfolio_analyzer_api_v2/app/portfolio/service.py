from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from datetime import date, datetime, timedelta
import math
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from .models import (
    PortfolioAnalyzeRequest, RecommendationTask, Evidence, SchoolContext, StudentProfile, TestPolicy,
    TaskTemplate, TestPlanRequest, TestPlanResponse, EligibilityCheckRequest, EligibilityCheckResponse
)
from .constants import (
    ROLE_WEIGHT, AWARD_WEIGHT, FACTOR_WEIGHT, LENS_LIST, SPIKE_MIN_SHARE, LENS_MIN_SCORE, 
    MIN_PLAYBOOKS, THEME_LEXICON, SAT_TARGET_DELTA, ACT_TARGET_DELTA
)

# Load .env file - try multiple locations
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '..', '.env'),  # Project root
    os.path.join(os.getcwd(), '.env'),  # Current working directory
    '.env'  # Relative path
]
for env_path in env_paths:
    abs_path = os.path.abspath(env_path)
    if os.path.exists(abs_path):
        load_dotenv(dotenv_path=abs_path)
        break
else:
    # Fallback: try to find .env file
    load_dotenv()

_openai_api_key = os.getenv("OPENAI_API_KEY")
if _openai_api_key:
    # Remove quotes if present
    _openai_api_key = _openai_api_key.strip().strip('"').strip("'")
client = OpenAI(api_key=_openai_api_key) if _openai_api_key else None

def _load_playbooks() -> List[dict]:
    """Load playbooks from JSON file"""
    playbooks_path = os.path.join(os.path.dirname(__file__), "playbooks.json")
    try:
        with open(playbooks_path, 'r') as f:
            return json.load(f)
    except:
        return []

def _log1p(x: float | int | None) -> float:
    return math.log1p(x or 0)

def _weeks_between(start: Optional[date], end: Optional[date]) -> int:
    if not start:
        return 1
    e = end or date.today()
    days = max(1, (e - start).days)
    return max(1, math.ceil(days / 7))

def _major_match(theme_tags: List[str], intended_major: Optional[str]) -> int:
    if not intended_major or not theme_tags:
        return 0
    im = intended_major.lower()
    for t in theme_tags:
        if t.lower() in im or any(t.lower() in " ".join(v) for v in THEME_LEXICON.values()):
            return 1
    return 0

def compute_impact(ev: Evidence, intended_major: Optional[str]) -> float:
    """Compute raw impact score per spec: 0.28×role + 0.18×log1p(people) + 0.38×log1p(hours) + 0.16×award"""
    weeks_active = _weeks_between(ev.start_date, ev.end_date)
    award_weight_max = 0.0
    for a in ev.awards:
        lvl = str(a.get("level","none")).lower()
        award_weight_max = max(award_weight_max, AWARD_WEIGHT.get(lvl, 0.0))
    
    # Calculate hours_total: use hours_total if provided, else hours_per_week × weeks_active
    hours_total = ev.hours_total if ev.hours_total is not None else (ev.hours_per_week or 0) * weeks_active

    impact_raw = (
        0.28 * ROLE_WEIGHT[ev.role_level] +
        0.18 * _log1p(ev.people_impacted) +
        0.38 * _log1p(hours_total) +
        0.16 * award_weight_max
    )
    return impact_raw

def normalize_impacts(impacts: Dict[str, float]) -> Dict[str, float]:
    """Normalize impacts to 0-10. If max == min, assign 5.0 to all items."""
    if not impacts:
        return {}
    vals = list(impacts.values())
    mn, mx = min(vals), max(vals)
    out = {}
    if abs(mx - mn) < 1e-9:
        # If max == min: assign 5.0 to all items
        for k in impacts:
            out[k] = 5.0
    else:
        for k, v in impacts.items():
            out[k] = 10.0 * (v - mn) / (mx - mn)
    return out

def lens_scores(portfolio: List[Evidence], impacts_norm: Dict[str, float]) -> Dict[str, float]:
    sums: Dict[str, float] = {k: 0.0 for k in LENS_LIST}
    for ev in portfolio:
        sums[ev.lens] += impacts_norm.get(ev.id, 0.0)
    max_sum = max(sums.values()) if sums else 1.0
    if max_sum <= 0: max_sum = 1.0
    scores = {k: (v / max_sum) * 10.0 for k, v in sums.items()}
    return scores

def coverage_index(lens_scores_map: Dict[str, float]) -> float:
    total = sum(lens_scores_map.values())
    if total <= 0: return 0.0
    ps = [v/total for v in lens_scores_map.values()]
    H = 0.0
    for p in ps:
        if p > 0:
            H -= p * math.log(p)
    return H / math.log(len(lens_scores_map))

def detect_spike(portfolio: List[Evidence], impacts_norm: Dict[str, float]) -> Tuple[Optional[str], float]:
    theme_impact: Dict[str, float] = {}
    for ev in portfolio:
        if not ev.theme_tags: 
            continue
        imp = impacts_norm.get(ev.id, 0.0)
        top_tag = ev.theme_tags[0].lower()
        theme_impact[top_tag] = theme_impact.get(top_tag, 0.0) + imp
    total = sum(theme_impact.values())
    if total <= 0:
        return None, 0.0
    top_theme = max(theme_impact.items(), key=lambda kv: kv[1])
    share = top_theme[1] / total
    if share >= SPIKE_MIN_SHARE:
        return top_theme[0], share
    return None, share

def _gpa_norm(gpa: Optional[float]) -> float:
    if gpa is None: return 0.0
    lo, hi = 2.5, 4.0
    g = min(max(gpa, lo), hi)
    return (g - lo) / (hi - lo)

def _tests_norm(profile: Optional[StudentProfile], mid50: Optional[dict]) -> float:
    """Tests score: 0 at p25, 0.5 at p50, 1.0 at p75 (interpolate piecewise)"""
    if not profile or not mid50:
        return 0.0
    # Check SAT
    if profile.tests.sat and profile.tests.sat.score and mid50.get("sat_composite"):
        lo, md, hi = mid50["sat_composite"][0], mid50["sat_composite"][1], mid50["sat_composite"][-1]
        s = profile.tests.sat.score
        if s <= lo: return 0.0
        if s >= hi: return 1.0
        if s == md: return 0.5
        if s < md: return (s - lo) / (md - lo) * 0.5
        return 0.5 + (s - md) / (hi - md) * 0.5
    # Check ACT
    if profile.tests.act and profile.tests.act.score and mid50.get("act_composite"):
        lo, md, hi = mid50["act_composite"][0], mid50["act_composite"][1], mid50["act_composite"][-1]
        s = profile.tests.act.score
        if s <= lo: return 0.0
        if s >= hi: return 1.0
        if s == md: return 0.5
        if s < md: return (s - lo) / (md - lo) * 0.5
        return 0.5 + (s - md) / (hi - md) * 0.5
    return 0.0

def alignment_for_school(ctx: Optional[SchoolContext], prof: Optional[StudentProfile], lens_s: Dict[str, float]) -> float:
    if not ctx or not prof:
        return 0.0
    gpa = _gpa_norm(prof.gpa_unweighted)
    rigor_count = 0
    for subj, grade in prof.grades_by_subject.items():
        g = str(grade).upper()
        if g in {"A*", "A", "HL", "HLA"}:
            rigor_count += 1
    rigor = min(1.0, rigor_count / 6.0)
    tests = _tests_norm(prof, ctx.mid50_scores or {})
    essay = ((lens_s.get("Creativity", 0.0) + lens_s.get("Growth", 0.0)) / 20.0)
    ecs = ((lens_s.get("Leadership", 0.0) + lens_s.get("Community", 0.0)) / 20.0)
    recs = 1.0 if (ctx.recommenders_required or 0) <= 1 else 0.5
    interest = 0.0

    dims = {"gpa": gpa, "rigor": rigor, "test_scores": tests, "essay": essay, "ec": ecs, "recommendations": recs, "interest": interest}
    weights = ctx.factor_importance or {}
    num = den = 0.0
    for k, v in dims.items():
        w = FACTOR_WEIGHT.get(weights.get(k, "considered"), 0.3)
        num += w * v
        den += w
    return (num / den) if den > 0 else 0.0

def analyze_gaps(portfolio: List[Evidence], lens_s: Dict[str, float], spike: Tuple[Optional[str], float], 
                 ctx: Optional[SchoolContext], prof: Optional[StudentProfile], impacts_norm: Dict[str, float]) -> List[dict]:
    """Comprehensive gap analysis per spec"""
    gaps: List[dict] = []
    
    # Lens gap: if lens_score < 4.0
    for lens, score in lens_s.items():
        if score < LENS_MIN_SCORE:
            severity = (LENS_MIN_SCORE - score) / LENS_MIN_SCORE
            gaps.append({"type":"lens","lens":lens,"severity": round(severity, 2)})
    
    # Spike gap: if no spike
    theme, share = spike
    if not theme:
        gaps.append({"type":"spike","severity":1.0})
    
    # Recommenders gap
    if ctx and (ctx.recommenders_required or 0) > 1:
        gaps.append({"type":"recs","severity":0.5,"required":ctx.recommenders_required})
    
    # Artifacts gap: if < 50% of items have ≥ 1 artifact_link
    if portfolio:
        items_with_artifacts = sum(1 for ev in portfolio if ev.artifact_links and len(ev.artifact_links) >= 1)
        coverage = items_with_artifacts / len(portfolio)
        if coverage < 0.5:
            severity = (0.5 - coverage) / 0.5
            gaps.append({"type":"artifacts","severity": round(severity, 2)})
    
    # Duration gap: if median weeks_active < 8
    if portfolio:
        weeks_list = [_weeks_between(ev.start_date, ev.end_date) for ev in portfolio]
        if weeks_list:
            weeks_list.sort()
            median_weeks = weeks_list[len(weeks_list) // 2]
            if median_weeks < 8:
                severity = (8 - median_weeks) / 8
                gaps.append({"type":"duration","severity": round(severity, 2)})
    
    # Major alignment gap: if share of major-aligned impact < 0.3
    if prof and prof.intended_major and portfolio:
        total_impact = sum(impacts_norm.values())
        if total_impact > 0:
            major_aligned_impact = 0.0
            for ev in portfolio:
                if _major_match(ev.theme_tags, prof.intended_major):
                    major_aligned_impact += impacts_norm.get(ev.id, 0.0)
            share = major_aligned_impact / total_impact
            if share < 0.3:
                severity = (0.3 - share) / 0.3
                gaps.append({"type":"alignment","severity": round(severity, 2)})
    
    return gaps

def _playbook_matches(playbook: dict, gaps: List[dict], lens_scores: Dict[str, float], 
                      spike_theme: Optional[str], portfolio: List[Evidence], 
                      intended_major: Optional[str]) -> bool:
    """Check if a playbook's applies_if conditions match current state"""
    applies_if = playbook.get("applies_if", {})
    if not applies_if:
        return False
    
    # Check lens condition
    if "lens" in applies_if:
        lens = applies_if["lens"]
        if lens not in lens_scores or lens_scores[lens] >= LENS_MIN_SCORE:
            return False
    
    # Check theme condition
    if "theme" in applies_if:
        theme = applies_if["theme"].lower()
        if not spike_theme or spike_theme.lower() != theme:
            # Also check if any evidence has this theme
            has_theme = any(theme in [t.lower() for t in ev.theme_tags] for ev in portfolio)
            if not has_theme:
                return False
    
    # Check min_weeks condition
    if "min_weeks" in applies_if:
        min_weeks = applies_if["min_weeks"]
        # Check if we have enough runway (simplified - would need deadline info)
        pass  # Would need deadline context
    
    return True

def _generate_gpt_recommendations(
    req: PortfolioAnalyzeRequest,
    gaps: List[dict],
    spike_theme: Optional[str],
    spike_share: float,
    lens_scores: Dict[str, float],
    scores: dict,
    impacts_norm: Dict[str, float]
) -> List[RecommendationTask]:
    """Generate personalized recommendations using GPT API"""
    track = req.country_tracks[0] if req.country_tracks else "US"
    prof = req.student_profile
    ctx = req.school_context
    
    # Build context for GPT
    portfolio_summary = []
    for ev in req.portfolio[:10]:  # Limit to top 10 for context
        impact = impacts_norm.get(ev.id, 0.0)
        portfolio_summary.append({
            "title": ev.title,
            "lens": ev.lens,
            "type": ev.type,
            "role_level": ev.role_level,
            "theme_tags": ev.theme_tags,
            "area_of_activity": ev.area_of_activity,
            "impact_score": round(impact, 2)
        })
    
    # Analyze metrics to provide clear guidance
    weak_lenses = [lens for lens, score in lens_scores.items() if score < LENS_MIN_SCORE]
    strong_lenses = [lens for lens, score in lens_scores.items() if score >= 7.0]
    lens_gaps = [g for g in gaps if g.get("type") == "lens"]
    artifacts_gap = next((g for g in gaps if g.get("type") == "artifacts"), None)
    duration_gap = next((g for g in gaps if g.get("type") == "duration"), None)
    alignment_gap = next((g for g in gaps if g.get("type") == "alignment"), None)
    
    # Calculate alignment breakdown if available
    alignment_score = scores.get('alignment', {}).get(ctx.name if ctx else '', 0) if ctx else 0
    
    # Identify portfolio items that need strengthening
    weak_items = [ev for ev in req.portfolio if impacts_norm.get(ev.id, 0) < 5.0]
    strong_items = [ev for ev in req.portfolio if impacts_norm.get(ev.id, 0) >= 7.0]
    
    # Build metric-driven prompt
    prompt = f"""You are a portfolio coach. The system has calculated specific metrics showing exactly what needs improvement. Generate tasks that DIRECTLY address these calculated gaps.

=== CALCULATED METRICS ANALYSIS ===

LENS SCORES (0-10 scale, target: ≥4.0):
{chr(10).join([f"- {lens}: {score:.2f}/10 {'⚠️ BELOW TARGET' if score < LENS_MIN_SCORE else '✓ Strong'}" for lens, score in sorted(lens_scores.items(), key=lambda x: x[1])])}

CRITICAL GAPS REQUIRING ACTION:
{chr(10).join([f"1. {gap['type'].upper()} GAP: {gap.get('lens', gap.get('severity', 'N/A'))} - Severity: {gap['severity']:.2f}" for gap in sorted(gaps, key=lambda x: x.get('severity', 0), reverse=True)[:5]])}

SPIKE ANALYSIS:
- Current spike: {spike_theme if spike_theme else 'NONE DETECTED'}
- Spike share: {spike_share:.1%} ({spike_share:.3f}) {'⚠️ NEEDS BUILDING' if not spike_theme or spike_share < SPIKE_MIN_SHARE else '✓ Strong'}
- Target: ≥35% concentration in one theme

COVERAGE INDEX: {scores.get('coverage', 0):.3f} (target: >0.7, max: 1.0)
- {'⚠️ Too concentrated in few lenses' if scores.get('coverage', 0) < 0.6 else '✓ Good diversity'}

ALIGNMENT WITH {ctx.name if ctx else 'SCHOOL'}:
- Overall alignment: {alignment_score:.1%} {'⚠️ Needs improvement' if alignment_score < 0.6 else '✓ Good'}
- School priorities: {json.dumps(ctx.factor_importance, indent=2) if ctx and ctx.factor_importance else 'Not specified'}

=== PORTFOLIO ITEMS NEEDING ATTENTION ===

Weak Items (impact < 5.0, need strengthening):
{chr(10).join([f"- {ev.title} ({ev.lens} lens, impact: {impacts_norm.get(ev.id, 0):.2f}): Needs {'artifacts' if not ev.artifact_links else 'more impact'}" for ev in weak_items[:5]])}

Strong Items (can leverage):
{chr(10).join([f"- {ev.title} ({ev.lens} lens, impact: {impacts_norm.get(ev.id, 0):.2f})" for ev in strong_items[:3]])}

=== STUDENT CONTEXT ===
- Grade: {prof.current_grade if prof else 'N/A'}, Major: {prof.intended_major if prof else 'N/A'}
- Weekly hours available: {req.weekly_hours_cap}h/week
- GPA: {prof.gpa_unweighted if prof and prof.gpa_unweighted else 'N/A'}/4.0

=== TASK GENERATION INSTRUCTIONS ===

Generate 6-8 SPECIFIC tasks that DIRECTLY address the calculated metrics above. For EACH task:

1. REFERENCE THE SPECIFIC METRIC: "Your {weak_lenses[0]} lens score is {lens_scores.get(weak_lenses[0] if weak_lenses else '', 0):.2f}/10. To reach 4.0+, you need..."

2. ADDRESS THE HIGHEST SEVERITY GAPS FIRST:
   - If lens gap exists: Create task to build that specific lens (e.g., "Leadership lens is 2.5/10 → organize event")
   - If spike missing: Create task to deepen existing theme or build new one
   - If artifacts gap: Create task to add artifacts to specific weak items
   - If duration gap: Create task to extend or deepen existing activities

3. USE SCHOOL PRIORITIES: Weight tasks by factor_importance:
   - very_important factors → High priority tasks
   - important factors → Medium priority tasks
   - considered factors → Lower priority

4. LEVERAGE STRONG ITEMS: Reference strong items and suggest building on them

5. BE SPECIFIC: Don't say "improve portfolio" - say "Add 3 artifacts to your ML wildfire project (currently impact 4.2) to boost Curiosity lens from 3.9 to 5.0+"

6. MAKE IT ACTIONABLE: Each task should have clear, measurable steps that directly improve the calculated metric

EXAMPLE GOOD TASK:
{{
  "title": "Strengthen Achievements lens: Enter 2 competitions aligned with your AI/ML theme",
  "estimated_hours": 15,
  "definition_of_done": [
    "Research and identify 2 ML/AI competitions with deadlines in next 8 weeks",
    "Submit your wildfire prediction project to Kaggle competitions",
    "Enter a hackathon focused on climate tech (leverages your existing project)",
    "Document competition results and add to portfolio with artifacts"
  ],
  "micro_coaching": "Your Achievements lens is 0.0/10. Your ML project is strong (impact 8.5) but needs recognition. Competitions will boost this lens to 4.0+ and align with your AI spike theme.",
  "quick_links": []
}}

BAD TASK (too generic):
{{
  "title": "Improve portfolio",
  "estimated_hours": 10,
  "definition_of_done": ["Work on activities", "Add more items"],
  "micro_coaching": "Make your portfolio better"
}}

=== REQUIRED OUTPUT ===
Return JSON: {{"recommendations": [{{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}, ...]}}

Each task MUST:
- Reference specific calculated metrics (lens scores, gaps, alignment)
- Address the highest severity gaps first
- Be personalized to their actual portfolio items
- Have measurable outcomes that will improve the metrics"""

    # Check if OpenAI client is available
    if not client or not _openai_api_key:
        # Fallback to rule-based if API key not configured
        return _get_fallback_recommendations(track, gaps, spike_theme, ctx)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" for better quality
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert college admissions portfolio coach. You MUST generate tasks that directly address calculated metrics (lens scores, gaps, alignment). Each task must reference specific metrics and show how it will improve them. Return a JSON object with a 'recommendations' key containing an array of RecommendationTask objects. Each task must have: title (string), estimated_hours (integer), definition_of_done (array of 3-5 specific steps), micro_coaching (string explaining which metric this improves), quick_links (array, can be empty)."
                },
                {
                    "role": "user",
                    "content": prompt + "\n\nReturn your response as: {\"recommendations\": [{\"title\": \"...\", \"estimated_hours\": 10, \"definition_of_done\": [...], \"micro_coaching\": \"...\", \"quick_links\": []}, ...]}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower temperature for more focused, metric-driven responses
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # Handle both {"recommendations": [...]} and [...] formats
        if "recommendations" in result_json:
            recs_data = result_json["recommendations"]
        elif isinstance(result_json, list):
            recs_data = result_json
        else:
            recs_data = []
        
        # Validate and convert to RecommendationTask objects
        recommendations = []
        for rec_data in recs_data[:MIN_PLAYBOOKS + 2]:  # Get a few extra in case some are invalid
            try:
                rec = RecommendationTask(
                    title=rec_data.get("title", ""),
                    track=track,
                    estimated_hours=int(rec_data.get("estimated_hours", 3)),
                    definition_of_done=rec_data.get("definition_of_done", []),
                    micro_coaching=rec_data.get("micro_coaching", ""),
                    quick_links=rec_data.get("quick_links", [])
                )
                recommendations.append(rec)
            except Exception as e:
                # Skip invalid recommendations
                continue
        
        # Ensure we have at least MIN_PLAYBOOKS
        if len(recommendations) < MIN_PLAYBOOKS:
            # Fallback to generic tasks
            recommendations.extend(_get_fallback_recommendations(track, gaps, spike_theme, ctx))
        
        return recommendations[:MIN_PLAYBOOKS]
        
    except Exception as e:
        # Log error for debugging
        import logging
        logging.warning(f"GPT API call failed: {e}. Using fallback recommendations.")
        # Fallback to rule-based recommendations if GPT fails
        return _get_fallback_recommendations(track, gaps, spike_theme, ctx)

def _get_fallback_recommendations(track: str, gaps: List[dict], spike_theme: Optional[str], ctx: Optional[SchoolContext]) -> List[RecommendationTask]:
    """Fallback rule-based recommendations if GPT fails"""
    recs = []
    
    if not spike_theme:
        recs.append(RecommendationTask(
            title="Spike: build & publish 1 project",
            track=track, estimated_hours=20,
            definition_of_done=["Choose theme", "Baseline build", "Experiment log (3 variants)", "README + 2-min demo video"],
            micro_coaching="Depth beats breadth; one strong theme improves narrative and supplements.",
            quick_links=[]
        ))
    
    lens_gaps = [g for g in gaps if g.get("type") == "lens"]
    lens_gaps.sort(key=lambda x: x.get("severity", 0), reverse=True)
    
    for gap in lens_gaps[:2]:
        lens = gap.get("lens")
        if lens == "Leadership":
            recs.append(RecommendationTask(
                title="Leadership escalation: organize a themed workshop",
                track=track, estimated_hours=12,
                definition_of_done=["Book room", "Confirm 2 speakers", "Run event", "Collect attendance + quotes", "Publish summary post"],
                micro_coaching="Small, real events demonstrate initiative and impact within weeks.",
                quick_links=[]
            ))
        elif lens == "Community":
            recs.append(RecommendationTask(
                title="Community partnership: launch a service initiative",
                track=track, estimated_hours=10,
                definition_of_done=["Identify need", "Partner with organization", "Run 3 sessions", "Document impact"],
                micro_coaching="Community engagement shows empathy and real-world application.",
                quick_links=[]
            ))
    
    if any(g.get("type") == "artifacts" for g in gaps):
        recs.append(RecommendationTask(
            title="Evidence hardening: convert at least 2 activities into strong artifacts",
            track=track, estimated_hours=6,
            definition_of_done=["Add metrics to descriptions", "Upload 2 artifacts/links per item", "Rewrite bullets with strong verbs"],
            micro_coaching="Review your top activities and make outcomes measurable; add links.",
            quick_links=[]
        ))
    
    while len(recs) < MIN_PLAYBOOKS:
        recs.append(RecommendationTask(
            title="Portfolio polish sprint",
            track=track, estimated_hours=3,
            definition_of_done=["Fix grammar in 2 items", "Standardize titles", "Ensure dates + hours filled"],
            micro_coaching="Tighten presentation for quick wins.",
            quick_links=[]
        ))
    
    return recs[:MIN_PLAYBOOKS]

def synthesize_recommendations(req: PortfolioAnalyzeRequest, gaps: List[dict], spike_theme: Optional[str],
                               lens_scores: Dict[str, float], scores: dict, impacts_norm: Dict[str, float]) -> List[RecommendationTask]:
    """Synthesize personalized recommendations using GPT API"""
    spike_share = scores.get("spike", {}).get("share", 0.0) if isinstance(scores.get("spike"), dict) else 0.0
    return _generate_gpt_recommendations(req, gaps, spike_theme, spike_share, lens_scores, scores, impacts_norm)

def to_task_templates(recs: List[RecommendationTask], req: PortfolioAnalyzeRequest) -> List[TaskTemplate]:
    """Convert recommendations to TaskTemplate objects"""
    deadlines = list(req.deadlines.values())
    nearest_deadline = min(deadlines) if deadlines else None
    track = req.country_tracks[0] if req.country_tracks else "US"
    tasks = []
    for i, r in enumerate(recs):
        # Determine criticality based on title/content
        criticality = "high" if "spike" in r.title.lower() or "leadership" in r.title.lower() else "medium"
        tasks.append(TaskTemplate(
            id=f"task_{i}",
            title=r.title,
            track=track,
            duration_hours=r.estimated_hours,
            buffer_days=2,
            deps=[],
            criticality=criticality,
            deadline=nearest_deadline,
            dod=r.definition_of_done
        ))
    return tasks

def analyze_portfolio(req: PortfolioAnalyzeRequest) -> dict:
    prof = req.student_profile
    impacts_raw: Dict[str, float] = {}
    for ev in req.portfolio:
        impacts_raw[ev.id] = compute_impact(ev, prof.intended_major if prof else None)
    impacts_norm = normalize_impacts(impacts_raw) if impacts_raw else {}
    lens_s = lens_scores(req.portfolio, impacts_norm) if impacts_norm else {k:0.0 for k in LENS_LIST}
    coverage = coverage_index(lens_s) if sum(lens_s.values())>0 else 0.0
    spike_theme, spike_share = detect_spike(req.portfolio, impacts_norm)

    align_map: Dict[str, float] = {}
    for s in req.schools:
        align_map[s] = alignment_for_school(req.school_context, prof, lens_s) if req.school_context and prof else 0.0

    scores = {
        "impact_total": round(sum(impacts_norm.values()), 2),
        "lens_scores": {k: round(v,2) for k,v in lens_s.items()},
        "coverage": round(coverage, 3),
        "spike": ({"theme": spike_theme, "share": round(spike_share,3)} if spike_theme else None),
        "alignment": {k: round(v,3) for k,v in align_map.items()}
    }

    gaps = analyze_gaps(req.portfolio, lens_s, (spike_theme, spike_share), req.school_context, prof, impacts_norm)
    recs = synthesize_recommendations(req, gaps, spike_theme, lens_s, scores, impacts_norm)
    tasks = to_task_templates(recs, req)

    return {
        "scores": scores,
        "gaps": gaps,
        "recommendations": [r.model_dump() for r in recs],
        "tasks": [t.model_dump() for t in tasks]
    }

def plan_tests(req: TestPlanRequest) -> TestPlanResponse:
    """Test planning logic per spec section 5"""
    profile = req.student_profile
    ctx = req.school_context
    policy = ctx.test_policy
    
    if not policy:
        return TestPlanResponse(decision="SKIP", rationale="No test policy specified")
    
    # Decision logic
    if policy.admission_use == "not_considered":
        return TestPlanResponse(decision="SKIP", rationale="Tests not considered by this school")
    
    if policy.admission_use == "required":
        # Must plan if required
        return _create_test_plan(profile, ctx, req.weekly_hours_cap, "required")
    
    # Optional/considered_if_submitted/recommended
    # Check if baseline >= p50
    mid50 = ctx.mid50_scores or {}
    baseline_sat = profile.tests.sat.score if profile.tests.sat and profile.tests.sat.score else None
    baseline_act = profile.tests.act.score if profile.tests.act and profile.tests.act.score else None
    
    # Determine which test to use
    test_type = None
    baseline = None
    p50 = None
    
    if baseline_sat and mid50.get("sat_composite"):
        test_type = "SAT"
        baseline = baseline_sat
        p50 = mid50["sat_composite"][1] if len(mid50["sat_composite"]) > 1 else mid50["sat_composite"][0]
    elif baseline_act and mid50.get("act_composite"):
        test_type = "ACT"
        baseline = baseline_act
        p50 = mid50["act_composite"][1] if len(mid50["act_composite"]) > 1 else mid50["act_composite"][0]
    
    if baseline and p50 and baseline >= p50:
        return TestPlanResponse(decision="SEND", rationale=f"Baseline {test_type} score {baseline} meets or exceeds p50 ({p50})")
    
    # Check runway and hours
    latest_date_str = policy.latest_submission_date if policy else None
    if not latest_date_str and ctx.application_rounds:
        latest_date_str = ctx.application_rounds[0].closing_date
    
    if latest_date_str:
        try:
            # Handle ISO date strings (YYYY-MM-DD)
            if 'T' in latest_date_str:
                latest_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00')).date()
            else:
                latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
            runway_weeks = max(0, (latest_date - date.today()).days // 7)
        except Exception:
            runway_weeks = 0
    else:
        runway_weeks = 0
    
    if runway_weeks >= 8 and req.weekly_hours_cap >= 3:
        return _create_test_plan(profile, ctx, req.weekly_hours_cap, "optional")
    else:
        return TestPlanResponse(
            decision="SKIP",
            rationale=f"Insufficient runway ({runway_weeks} weeks) or hours ({req.weekly_hours_cap}/week). Reallocate to essays/rigor."
        )

def _create_test_plan(profile: StudentProfile, ctx: SchoolContext, weekly_hours: int, reason: str) -> TestPlanResponse:
    """Create test preparation plan"""
    mid50 = ctx.mid50_scores or {}
    test_type = None
    baseline = None
    p50 = None
    target_delta = None
    
    if mid50.get("sat_composite"):
        test_type = "SAT"
        baseline = profile.tests.sat.score if profile.tests.sat and profile.tests.sat.score else None
        p50 = mid50["sat_composite"][1] if len(mid50["sat_composite"]) > 1 else mid50["sat_composite"][0]
        target_delta = SAT_TARGET_DELTA
    elif mid50.get("act_composite"):
        test_type = "ACT"
        baseline = profile.tests.act.score if profile.tests.act and profile.tests.act.score else None
        p50 = mid50["act_composite"][1] if len(mid50["act_composite"]) > 1 else mid50["act_composite"][0]
        target_delta = ACT_TARGET_DELTA
    
    if not test_type or not p50:
        return TestPlanResponse(decision="OPTIONAL", rationale="No test scores or mid50 data available")
    
    target_score = p50
    if baseline:
        target_score = min(baseline + target_delta, p50)
    
    # Estimate hours needed (rough: 1 hour per point for SAT, 2 hours per point for ACT)
    hours_needed = target_delta * (1 if test_type == "SAT" else 2)
    hours_needed = max(20, min(hours_needed, 60))  # Cap between 20-60 hours
    
    policy = ctx.test_policy
    latest_date_str = policy.latest_submission_date if policy else None
    if not latest_date_str and ctx.application_rounds:
        latest_date_str = ctx.application_rounds[0].closing_date
    
    tasks = [
        TaskTemplate(
            id="test_prep_1",
            title=f"{test_type} Prep: Diagnostic & Study Plan",
            track="US",
            duration_hours=4,
            buffer_days=0,
            deps=[],
            criticality="high" if reason == "required" else "medium",
            deadline=latest_date_str,
            dod=["Take diagnostic test", "Identify weak areas", "Create 8-week study schedule"]
        ),
        TaskTemplate(
            id="test_prep_2",
            title=f"{test_type} Prep: Practice Tests & Review",
            track="US",
            duration_hours=hours_needed - 4,
            buffer_days=0,
            deps=["test_prep_1"],
            criticality="high" if reason == "required" else "medium",
            deadline=latest_date_str,
            dod=[f"Complete {hours_needed // 3} practice tests", "Review mistakes", f"Target score: {target_score}"]
        )
    ]
    
    rationale = f"{test_type} {reason}. Target: {target_score} (current: {baseline or 'none'}, p50: {p50}). Estimated {hours_needed}h prep."
    return TestPlanResponse(decision="PLAN", rationale=rationale, tasks=tasks)

def check_eligibility(req: EligibilityCheckRequest) -> EligibilityCheckResponse:
    """Rule-based eligibility screen per spec"""
    profile = req.student_profile
    ctx = req.school_context
    warnings = []
    errors = []
    
    # Check GPA if available
    if ctx.gpa_profile and ctx.gpa_profile.avg_hs_gpa:
        if profile.gpa_unweighted and profile.gpa_unweighted < 2.5:
            warnings.append(f"GPA {profile.gpa_unweighted} is below typical threshold (2.5)")
    
    # Check required subjects
    if ctx.required_subjects:
        missing = []
        for req_subj in ctx.required_subjects:
            if req_subj not in profile.grades_by_subject:
                missing.append(req_subj)
        if missing:
            errors.append(f"Missing required subjects: {', '.join(missing)}")
    
    # Check test requirements
    if ctx.test_policy and ctx.test_policy.admission_use == "required":
        has_sat = profile.tests.sat and profile.tests.sat.score
        has_act = profile.tests.act and profile.tests.act.score
        if not has_sat and not has_act:
            errors.append("Test scores required but none submitted")
    
    # Check minimum test scores if mid50 available
    if ctx.mid50_scores:
        mid50 = ctx.mid50_scores
        if mid50.get("sat_composite") and profile.tests.sat and profile.tests.sat.score:
            p25 = mid50["sat_composite"][0]
            if profile.tests.sat.score < p25 - 100:  # Allow some buffer
                warnings.append(f"SAT score {profile.tests.sat.score} is significantly below p25 ({p25})")
        if mid50.get("act_composite") and profile.tests.act and profile.tests.act.score:
            p25 = mid50["act_composite"][0]
            if profile.tests.act.score < p25 - 2:
                warnings.append(f"ACT score {profile.tests.act.score} is significantly below p25 ({p25})")
    
    eligible = len(errors) == 0
    return EligibilityCheckResponse(eligible=eligible, warnings=warnings, errors=errors)
