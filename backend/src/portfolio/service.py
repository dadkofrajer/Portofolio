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
    TaskTemplate, TestPlanRequest, TestPlanResponse, EligibilityCheckRequest, EligibilityCheckResponse,
    CriticalImprovementSection, LensImprovementSection, DiversitySpikeSection, AlignmentPriority,
    RegenerateTasksResponse, TestAnalysis
)
from .constants import (
    ROLE_WEIGHT, AWARD_WEIGHT, FACTOR_WEIGHT, LENS_LIST, SPIKE_MIN_SHARE, LENS_MIN_SCORE, 
    MIN_PLAYBOOKS, THEME_LEXICON, SAT_TARGET_DELTA, ACT_TARGET_DELTA
)

# Load .env file - try multiple locations
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),  # Project root
    os.path.join(os.path.dirname(__file__), '..', '..', '.env'),  # Backend root
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

def _generate_structured_recommendations(
    req: PortfolioAnalyzeRequest,
    gaps: List[dict],
    spike_theme: Optional[str],
    spike_share: float,
    lens_scores: Dict[str, float],
    scores: dict,
    impacts_norm: Dict[str, float],
    coverage: float
) -> Tuple[List[CriticalImprovementSection], List[LensImprovementSection], Optional[DiversitySpikeSection], List[AlignmentPriority]]:
    """Generate structured recommendations organized by gaps, lens improvements, diversity/spike, and alignment"""
    track = req.country_tracks[0] if req.country_tracks else "US"
    prof = req.student_profile
    ctx = req.school_context
    
    # Build portfolio context
    portfolio_summary = []
    for ev in req.portfolio[:10]:
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
    
    # Identify lenses that could improve (not in gaps but below 7.0)
    lenses_to_improve = [lens for lens, score in lens_scores.items() 
                        if score >= LENS_MIN_SCORE and score < 7.0]
    
    # Check if diversity/spike needs improvement
    needs_diversity_improvement = coverage < 0.6 or not spike_theme or spike_share < SPIKE_MIN_SHARE
    
    # Build comprehensive prompt for structured generation
    prompt = f"""You are a portfolio coach. Generate structured, specific tasks organized by category.

=== PORTFOLIO CONTEXT ===
{json.dumps(portfolio_summary, indent=2)}

=== LENS SCORES (0-10 scale, target: ≥4.0) ===
{chr(10).join([f"- {lens}: {score:.2f}/10" for lens, score in sorted(lens_scores.items(), key=lambda x: x[1])])}

=== CRITICAL GAPS (need immediate attention) ===
{chr(10).join([f"{i+1}. {gap['type'].upper()} GAP: {gap.get('lens', 'N/A')} - Severity: {gap['severity']:.2f}" for i, gap in enumerate(sorted(gaps, key=lambda x: x.get('severity', 0), reverse=True))])}

=== LENSES THAT COULD IMPROVE (above 4.0 but below 7.0) ===
{chr(10).join([f"- {lens}: {lens_scores[lens]:.2f}/10" for lens in lenses_to_improve]) if lenses_to_improve else "None - all strong lenses are already at 7.0+"}

=== SPIKE & DIVERSITY ANALYSIS ===
- Current spike: {spike_theme if spike_theme else 'NONE DETECTED'}
- Spike share: {spike_share:.1%} (target: ≥35%)
- Coverage index: {coverage:.3f} (target: >0.7)
- Needs improvement: {'YES' if needs_diversity_improvement else 'NO'}

=== ALIGNMENT SCORES ===
{chr(10).join([f"- {school}: {score:.1%}" for school, score in scores.get('alignment', {}).items()])}

=== SCHOOL PRIORITIES ===
{json.dumps(ctx.factor_importance, indent=2) if ctx and ctx.factor_importance else 'Not specified'}

=== STUDENT CONTEXT ===
- Grade: {prof.current_grade if prof else 'N/A'}
- Major: {prof.intended_major if prof else 'N/A'}
- Weekly hours: {req.weekly_hours_cap}h/week
- GPA: {prof.gpa_unweighted if prof and prof.gpa_unweighted else 'N/A'}/4.0

=== TASK GENERATION REQUIREMENTS ===

1. CRITICAL IMPROVEMENTS (for each gap):
   - Generate EXACTLY 3 tasks per gap
   - Tasks must be practical, realistic, and specific to this student's portfolio
   - Reference specific portfolio items when possible
   - Each task should directly address the gap

2. LENS IMPROVEMENTS (for each lens that could improve):
   - Generate EXACTLY 3 tasks per lens
   - Tasks should build on existing strengths in that lens
   - Make tasks specific and actionable

3. DIVERSITY/SPIKE (if needed):
   - Generate 3 tasks if diversity/spike needs improvement
   - Tasks should either deepen existing spike or build diversity

4. ALIGNMENT PRIORITIES:
   - For each school, identify which tasks from above will improve alignment
   - If alignment < 60%: prioritize tasks that address school's very_important factors
   - If alignment ≥ 60%: prioritize tasks that perfect alignment (tweak existing strengths)

=== OUTPUT FORMAT ===
Return JSON with this exact structure:
{{
  "critical_improvements": [
    {{
      "gap_type": "lens",
      "gap_description": "Achievements lens is 0.0/10 (target: ≥4.0)",
      "severity": 1.0,
      "tasks": [
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}},
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}},
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}
      ]
    }}
  ],
  "lens_improvements": [
    {{
      "lens": "Leadership",
      "current_score": 6.72,
      "improvement_opportunity": "Strong but can reach 8.0+ with focused effort",
      "tasks": [
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}},
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}},
        {{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}
      ]
    }}
  ],
  "diversity_spike": {{
    "has_spike": true,
    "spike_theme": "education",
    "spike_share": 0.375,
    "coverage_index": 0.786,
    "needs_improvement": false,
    "tasks": []
  }},
  "alignment_priorities": [
    {{
      "school_name": "Georgia Tech",
      "alignment_score": 0.605,
      "is_high_alignment": true,
      "priority_tasks": ["Task title 1", "Task title 2"],
      "alignment_notes": "High alignment. Focus on tasks that perfect alignment by emphasizing rigor and GPA."
    }}
  ]
}}

IMPORTANT: 
- Generate EXACTLY 3 tasks per gap
- Generate EXACTLY 3 tasks per lens improvement
- Be specific and reference actual portfolio items
- Make tasks practical and realistic
- Priority tasks in alignment_priorities should reference actual task titles from above"""

    if not client or not _openai_api_key:
        # Fallback to rule-based structured recommendations
        return _get_structured_fallback(gaps, lens_scores, lenses_to_improve, spike_theme, spike_share, coverage, scores, track, ctx)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert college admissions portfolio coach. Generate structured, specific tasks organized by gaps, lens improvements, diversity/spike, and alignment priorities. Each gap must have exactly 3 tasks. Each lens improvement must have exactly 3 tasks. Return valid JSON matching the specified structure."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # Parse critical improvements
        critical_improvements = []
        for ci_data in result_json.get("critical_improvements", []):
            tasks = []
            for task_data in ci_data.get("tasks", []):
                try:
                    tasks.append(RecommendationTask(
                        title=task_data.get("title", ""),
                        track=track,
                        estimated_hours=int(task_data.get("estimated_hours", 3)),
                        definition_of_done=task_data.get("definition_of_done", []),
                        micro_coaching=task_data.get("micro_coaching", ""),
                        quick_links=task_data.get("quick_links", [])
                    ))
                except:
                    continue
            if tasks:
                critical_improvements.append(CriticalImprovementSection(
                    gap_type=ci_data.get("gap_type", ""),
                    gap_description=ci_data.get("gap_description", ""),
                    severity=float(ci_data.get("severity", 0)),
                    tasks=tasks[:3]  # Ensure exactly 3
                ))
        
        # Parse lens improvements
        lens_improvements = []
        for li_data in result_json.get("lens_improvements", []):
            tasks = []
            for task_data in li_data.get("tasks", []):
                try:
                    tasks.append(RecommendationTask(
                        title=task_data.get("title", ""),
                        track=track,
                        estimated_hours=int(task_data.get("estimated_hours", 3)),
                        definition_of_done=task_data.get("definition_of_done", []),
                        micro_coaching=task_data.get("micro_coaching", ""),
                        quick_links=task_data.get("quick_links", [])
                    ))
                except:
                    continue
            if tasks:
                lens_improvements.append(LensImprovementSection(
                    lens=li_data.get("lens", ""),
                    current_score=float(li_data.get("current_score", 0)),
                    improvement_opportunity=li_data.get("improvement_opportunity", ""),
                    tasks=tasks[:3]  # Ensure exactly 3
                ))
        
        # Parse diversity/spike
        ds_data = result_json.get("diversity_spike", {})
        diversity_spike = None
        if ds_data:
            ds_tasks = []
            for task_data in ds_data.get("tasks", []):
                try:
                    ds_tasks.append(RecommendationTask(
                        title=task_data.get("title", ""),
                        track=track,
                        estimated_hours=int(task_data.get("estimated_hours", 3)),
                        definition_of_done=task_data.get("definition_of_done", []),
                        micro_coaching=task_data.get("micro_coaching", ""),
                        quick_links=task_data.get("quick_links", [])
                    ))
                except:
                    continue
            diversity_spike = DiversitySpikeSection(
                has_spike=ds_data.get("has_spike", False),
                spike_theme=ds_data.get("spike_theme"),
                spike_share=ds_data.get("spike_share"),
                coverage_index=float(ds_data.get("coverage_index", 0)),
                needs_improvement=ds_data.get("needs_improvement", False),
                tasks=ds_tasks[:3] if ds_tasks else []
            )
        
        # Parse alignment priorities
        alignment_priorities = []
        for ap_data in result_json.get("alignment_priorities", []):
            alignment_priorities.append(AlignmentPriority(
                school_name=ap_data.get("school_name", ""),
                alignment_score=float(ap_data.get("alignment_score", 0)),
                is_high_alignment=ap_data.get("is_high_alignment", False),
                priority_tasks=ap_data.get("priority_tasks", []),
                alignment_notes=ap_data.get("alignment_notes", "")
            ))
        
        return critical_improvements, lens_improvements, diversity_spike, alignment_priorities
        
    except Exception as e:
        import logging
        logging.warning(f"GPT structured recommendations failed: {e}. Using fallback.")
        return _get_structured_fallback(gaps, lens_scores, lenses_to_improve, spike_theme, spike_share, coverage, scores, track, ctx)

def _get_structured_fallback(
    gaps: List[dict],
    lens_scores: Dict[str, float],
    lenses_to_improve: List[str],
    spike_theme: Optional[str],
    spike_share: float,
    coverage: float,
    scores: dict,
    track: str,
    ctx: Optional[SchoolContext]
) -> Tuple[List[CriticalImprovementSection], List[LensImprovementSection], Optional[DiversitySpikeSection], List[AlignmentPriority]]:
    """Fallback structured recommendations if GPT fails"""
    critical_improvements = []
    lens_improvements = []
    
    # Generate critical improvements for gaps
    for gap in sorted(gaps, key=lambda x: x.get('severity', 0), reverse=True):
        if gap.get("type") == "lens":
            lens = gap.get("lens")
            score = lens_scores.get(lens, 0)
            tasks = []
            if lens == "Achievements":
                tasks = [
                    RecommendationTask(
                        title="Enter 2 competitions aligned with your theme",
                        track=track, estimated_hours=15,
                        definition_of_done=["Research competitions", "Submit projects", "Document results"],
                        micro_coaching=f"Your {lens} lens is {score:.2f}/10. Competitions will boost recognition.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title="Apply for awards and recognition programs",
                        track=track, estimated_hours=10,
                        definition_of_done=["Identify programs", "Prepare applications", "Submit"],
                        micro_coaching=f"External recognition strengthens your {lens} lens.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title="Document and showcase your achievements",
                        track=track, estimated_hours=6,
                        definition_of_done=["Create achievement portfolio", "Add certificates", "Update descriptions"],
                        micro_coaching=f"Proper documentation makes your {lens} lens visible.",
                        quick_links=[]
                    )
                ]
            elif lens == "Growth":
                tasks = [
                    RecommendationTask(
                        title="Document your learning journey with milestones",
                        track=track, estimated_hours=10,
                        definition_of_done=["Create timeline", "Add artifacts", "Reflect on growth"],
                        micro_coaching=f"Your {lens} lens is {score:.2f}/10. Documenting growth shows development.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title="Take on a challenging new skill or project",
                        track=track, estimated_hours=12,
                        definition_of_done=["Choose challenge", "Set goals", "Track progress"],
                        micro_coaching=f"New challenges demonstrate {lens}.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title="Create reflective essays on your development",
                        track=track, estimated_hours=8,
                        definition_of_done=["Write reflections", "Add to portfolio", "Update descriptions"],
                        micro_coaching=f"Reflection showcases {lens} journey.",
                        quick_links=[]
                    )
                ]
            else:
                # Generic tasks for other lens gaps
                tasks = [
                    RecommendationTask(
                        title=f"Strengthen {lens} lens: Build focused activity",
                        track=track, estimated_hours=12,
                        definition_of_done=["Plan activity", "Execute", "Document"],
                        micro_coaching=f"Your {lens} lens is {score:.2f}/10. Focused effort will improve it.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title=f"Add artifacts to {lens} activities",
                        track=track, estimated_hours=8,
                        definition_of_done=["Collect artifacts", "Upload", "Update descriptions"],
                        micro_coaching=f"Artifacts strengthen {lens} evidence.",
                        quick_links=[]
                    ),
                    RecommendationTask(
                        title=f"Deepen {lens} engagement",
                        track=track, estimated_hours=10,
                        definition_of_done=["Increase involvement", "Take leadership", "Document impact"],
                        micro_coaching=f"Increased engagement boosts {lens}.",
                        quick_links=[]
                    )
                ]
            
            if tasks:
                critical_improvements.append(CriticalImprovementSection(
                    gap_type="lens",
                    gap_description=f"{lens} lens is {score:.2f}/10 (target: ≥4.0)",
                    severity=gap.get("severity", 0),
                    tasks=tasks[:3]
                ))
    
    # Generate lens improvements
    for lens in lenses_to_improve:
        score = lens_scores.get(lens, 0)
        tasks = [
            RecommendationTask(
                title=f"Enhance {lens} lens: Build on existing strengths",
                track=track, estimated_hours=10,
                definition_of_done=["Identify strengths", "Plan enhancement", "Execute"],
                micro_coaching=f"Your {lens} lens is {score:.2f}/10. Building on strengths can reach 8.0+.",
                quick_links=[]
            ),
            RecommendationTask(
                title=f"Add depth to {lens} activities",
                track=track, estimated_hours=8,
                definition_of_done=["Deepen engagement", "Add complexity", "Document"],
                micro_coaching=f"Depth improves {lens} impact.",
                quick_links=[]
            ),
            RecommendationTask(
                title=f"Showcase {lens} achievements",
                track=track, estimated_hours=6,
                definition_of_done=["Update descriptions", "Add artifacts", "Highlight impact"],
                micro_coaching=f"Better presentation strengthens {lens}.",
                quick_links=[]
            )
        ]
        lens_improvements.append(LensImprovementSection(
            lens=lens,
            current_score=score,
            improvement_opportunity=f"Strong at {score:.2f}/10, can reach 8.0+ with focused effort",
            tasks=tasks[:3]
        ))
    
    # Diversity/spike
    needs_improvement = coverage < 0.6 or not spike_theme or spike_share < SPIKE_MIN_SHARE
    diversity_spike = DiversitySpikeSection(
        has_spike=spike_theme is not None,
        spike_theme=spike_theme,
        spike_share=spike_share,
        coverage_index=coverage,
        needs_improvement=needs_improvement,
        tasks=[] if not needs_improvement else [
            RecommendationTask(
                title="Build or deepen your spike theme",
                track=track, estimated_hours=15,
                definition_of_done=["Choose theme", "Plan activities", "Execute"],
                micro_coaching="A strong spike (≥35% concentration) improves narrative.",
                quick_links=[]
            )
        ]
    )
    
    # Alignment priorities
    alignment_priorities = []
    for school, align_score in scores.get("alignment", {}).items():
        is_high = align_score >= 0.6
        priority_tasks = []
        if is_high:
            priority_tasks = ["Focus on perfecting alignment", "Tweak existing strengths"]
        else:
            priority_tasks = ["Address critical gaps", "Build missing strengths"]
        
        alignment_priorities.append(AlignmentPriority(
            school_name=school,
            alignment_score=align_score,
            is_high_alignment=is_high,
            priority_tasks=priority_tasks,
            alignment_notes=f"Alignment is {'high' if is_high else 'low'}. {'Focus on perfecting' if is_high else 'Prioritize tasks that address school priorities'}."
        ))
    
    return critical_improvements, lens_improvements, diversity_spike, alignment_priorities

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
    
    # Generate structured recommendations (3 tasks per section)
    critical_improvements, lens_improvements, diversity_spike, alignment_priorities = _generate_structured_recommendations(
        req, gaps, spike_theme, spike_share, lens_s, scores, impacts_norm, coverage
    )
    
    # Analyze standardized tests for each school
    standardized_tests = analyze_standardized_tests(req, prof)

    return {
        "scores": scores,
        "gaps": gaps,
        "critical_improvements": [ci.model_dump() for ci in critical_improvements],
        "lens_improvements": [li.model_dump() for li in lens_improvements],
        "diversity_spike": diversity_spike.model_dump() if diversity_spike else None,
        "alignment_priorities": [ap.model_dump() for ap in alignment_priorities],
        "standardized_tests": [ta.model_dump() for ta in standardized_tests]
    }

def analyze_standardized_tests(req: PortfolioAnalyzeRequest, prof: Optional[StudentProfile]) -> List[TestAnalysis]:
    """Analyze standardized test scores for each school and provide recommendations"""
    if not prof or not req.school_context:
        return []
    
    ctx = req.school_context
    policy = ctx.test_policy
    mid50 = ctx.mid50_scores or {}
    
    if not policy:
        return []
    
    test_analyses = []
    track = req.country_tracks[0] if req.country_tracks else "US"
    
    # Get student's test scores
    sat_score = prof.tests.sat.score if prof.tests.sat and prof.tests.sat.score else None
    act_score = prof.tests.act.score if prof.tests.act and prof.tests.act.score else None
    
    # Determine which test to analyze (prefer SAT if both available)
    test_type = None
    current_score = None
    test_mid50 = None
    
    if sat_score and mid50.get("sat_composite"):
        test_type = "SAT"
        current_score = sat_score
        test_mid50 = mid50["sat_composite"]
    elif act_score and mid50.get("act_composite"):
        test_type = "ACT"
        current_score = act_score
        test_mid50 = mid50["act_composite"]
    
    # If no test taken and not required, skip analysis
    if not current_score and policy.admission_use != "required":
        return []
    
    # Calculate competitiveness if score exists
    competitiveness = None
    if current_score and test_mid50 and len(test_mid50) >= 3:
        p25, p50, p75 = test_mid50[0], test_mid50[1], test_mid50[-1]
        if current_score >= p75:
            competitiveness = "highly_competitive"
        elif current_score >= p50:
            competitiveness = "competitive"
        elif current_score >= p25:
            competitiveness = "below_competitive"
        else:
            competitiveness = "not_competitive"
    
    # Determine recommendation based on policy and score
    recommendation = "submit"
    rationale = ""
    tasks = []
    
    if policy.admission_use == "not_considered":
        recommendation = "submit"  # Doesn't matter, but default to submit
        rationale = "Tests are not considered by this school. Submit if you have scores, but they won't impact admission."
    
    elif policy.admission_use == "required":
        if not current_score:
            # Not taken - need to take it
            recommendation = "reschedule"
            rationale = f"Tests are required but you haven't taken {test_type or 'SAT/ACT'} yet. You must take and submit scores."
            tasks = _create_test_prep_tasks(test_type or "SAT", ctx, req.weekly_hours_cap, track)
        elif competitiveness == "not_competitive" or (current_score and test_mid50 and current_score < test_mid50[0] - 50):
            # Score is very low - check if there's time to improve
            latest_date_str = policy.latest_submission_date
            if not latest_date_str and ctx.application_rounds:
                latest_date_str = ctx.application_rounds[0].closing_date
            
            if latest_date_str:
                try:
                    if 'T' in latest_date_str:
                        latest_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00')).date()
                    else:
                        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
                    runway_weeks = max(0, (latest_date - date.today()).days // 7)
                except:
                    runway_weeks = 0
            else:
                runway_weeks = 0
            
            if runway_weeks >= 8 and req.weekly_hours_cap >= 3:
                # Can improve - reschedule
                recommendation = "reschedule"
                p25 = test_mid50[0] if test_mid50 else 0
                rationale = f"Your {test_type} score of {current_score} is below p25 ({p25}). Tests are required. You have {runway_weeks} weeks to improve - reschedule and prepare."
                tasks = _create_test_prep_tasks(test_type, ctx, req.weekly_hours_cap, track)
            else:
                # No time to improve - worst case: leave school out
                recommendation = "leave_school_out"
                rationale = f"Your {test_type} score of {current_score} is below competitive range and tests are required. Insufficient time ({runway_weeks} weeks) to improve. Consider removing this school from your list."
        else:
            # Score is acceptable - submit
            recommendation = "submit"
            comp_text = competitiveness.replace("_", " ").title() if competitiveness else "acceptable"
            rationale = f"Your {test_type} score of {current_score} is {comp_text} (p25: {test_mid50[0] if test_mid50 else 'N/A'}, p50: {test_mid50[1] if test_mid50 and len(test_mid50) > 1 else 'N/A'}, p75: {test_mid50[-1] if test_mid50 else 'N/A'}). Tests are required - submit your score."
    
    elif policy.admission_use in ["recommended", "considered_if_submitted"]:
        if not current_score:
            # Optional - can take or skip
            recommendation = "reschedule"
            rationale = f"Tests are {policy.admission_use.replace('_', ' ')}. You haven't taken {test_type or 'SAT/ACT'} yet. Consider taking it to strengthen your application."
            tasks = _create_test_prep_tasks(test_type or "SAT", ctx, req.weekly_hours_cap, track)
        elif competitiveness in ["not_competitive"] or (current_score and test_mid50 and current_score < test_mid50[0] - 20):
            # Score is low - don't submit if optional
            recommendation = "dont_submit"
            p25 = test_mid50[0] if test_mid50 else 0
            rationale = f"Your {test_type} score of {current_score} is significantly below p25 ({p25}). Since tests are optional, don't submit this score as it may hurt your application."
        elif competitiveness == "below_competitive" or (current_score and test_mid50 and len(test_mid50) > 1 and current_score < test_mid50[1]):
            # Score is below p50 - check if there's time to retake
            # Use application deadline if it gives more time than test submission deadline
            app_deadline_str = None
            if ctx.application_rounds:
                app_deadline_str = ctx.application_rounds[0].closing_date
            
            test_deadline_str = policy.latest_submission_date
            
            # Choose the deadline that gives more runway (later date)
            latest_date_str = None
            if app_deadline_str and test_deadline_str:
                try:
                    app_date = datetime.strptime(app_deadline_str, '%Y-%m-%d').date() if 'T' not in app_deadline_str else datetime.fromisoformat(app_deadline_str.replace('Z', '+00:00')).date()
                    test_date = datetime.strptime(test_deadline_str, '%Y-%m-%d').date() if 'T' not in test_deadline_str else datetime.fromisoformat(test_deadline_str.replace('Z', '+00:00')).date()
                    latest_date_str = app_deadline_str if app_date > test_date else test_deadline_str
                except:
                    latest_date_str = app_deadline_str or test_deadline_str
            else:
                latest_date_str = app_deadline_str or test_deadline_str
            
            runway_weeks = 0
            if latest_date_str:
                try:
                    if 'T' in latest_date_str:
                        latest_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00')).date()
                    else:
                        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
                    runway_weeks = max(0, (latest_date - date.today()).days // 7)
                except:
                    runway_weeks = 0
            
            p25 = test_mid50[0] if test_mid50 else 0
            p50 = test_mid50[1] if test_mid50 and len(test_mid50) > 1 else 0
            
            if runway_weeks >= 8 and req.weekly_hours_cap >= 3:
                # There's time to retake - suggest retaking
                recommendation = "reschedule"
                rationale = f"Your {test_type} score of {current_score} is below the median (p50: {p50}). Since tests are optional and you have {runway_weeks} weeks, consider retaking the test to strengthen your application. Target: {p50}+ to significantly improve your competitiveness."
                tasks = _create_test_retake_tasks(test_type, ctx, req.weekly_hours_cap, track, current_score, p50)
            else:
                # No time to retake - can submit but won't help much
                recommendation = "submit"
                rationale = f"Your {test_type} score of {current_score} is in the p25-p50 range ({p25}-{p50}). Since tests are optional, you can submit but it won't significantly strengthen your application. Insufficient time ({runway_weeks} weeks) to retake."
        else:
            # Score is good - submit
            recommendation = "submit"
            comp_text = competitiveness.replace("_", " ").title() if competitiveness else "good"
            rationale = f"Your {test_type} score of {current_score} is {comp_text}. Since tests are {policy.admission_use.replace('_', ' ')}, submit your score to strengthen your application."
    
    # Create test analysis for this school
    test_analysis = TestAnalysis(
        school_name=ctx.name,
        test_policy=policy.admission_use,
        test_type=test_type,
        current_score=current_score,
        mid50_scores=test_mid50,
        competitiveness=competitiveness,
        recommendation=recommendation,
        rationale=rationale,
        tasks=tasks
    )
    
    return [test_analysis]

def _create_test_retake_tasks(test_type: str, ctx: SchoolContext, weekly_hours: int, track: str, current_score: int, target_score: int) -> List[RecommendationTask]:
    """Create test retake preparation tasks"""
    policy = ctx.test_policy
    
    latest_date_str = policy.latest_submission_date if policy else None
    if not latest_date_str and ctx.application_rounds:
        latest_date_str = ctx.application_rounds[0].closing_date
    
    # Calculate score improvement needed
    score_delta = max(0, target_score - current_score)
    
    tasks = [
        RecommendationTask(
            title=f"Register for {test_type} Retake",
            track=track,
            estimated_hours=2,
            definition_of_done=[
                f"Research {test_type} retake dates",
                f"Register for {test_type} retake exam",
                f"Schedule retake before {latest_date_str or 'application deadline'}",
                f"Set target score: {target_score}+ (current: {current_score})"
            ],
            micro_coaching=f"Retaking {test_type} gives you a chance to improve from {current_score} to {target_score}+, which will significantly strengthen your application.",
            quick_links=[
                "https://www.collegeboard.org" if test_type == "SAT" else "https://www.act.org"
            ]
        ),
        RecommendationTask(
            title=f"{test_type} Retake: Focused Study Plan",
            track=track,
            estimated_hours=8,
            definition_of_done=[
                "Analyze previous test performance",
                "Identify specific weak areas to improve",
                "Create focused 6-8 week study plan",
                f"Set improvement goal: +{score_delta} points to reach {target_score}+"
            ],
            micro_coaching=f"Focus on improving your weakest sections. A {score_delta}-point improvement will move you from {current_score} to {target_score}+, making you more competitive.",
            quick_links=[]
        ),
        RecommendationTask(
            title=f"{test_type} Retake: Practice & Review",
            track=track,
            estimated_hours=18,
            definition_of_done=[
                "Complete 3-4 full practice tests",
                "Review mistakes from previous test",
                "Focus on weak areas identified",
                f"Practice until consistently scoring {target_score}+ on practice tests"
            ],
            micro_coaching=f"Consistent practice is key. Aim to score {target_score}+ on practice tests before your retake to ensure improvement.",
            quick_links=[]
        )
    ]
    
    return tasks

def _create_test_prep_tasks(test_type: str, ctx: SchoolContext, weekly_hours: int, track: str) -> List[RecommendationTask]:
    """Create test preparation tasks"""
    policy = ctx.test_policy
    mid50 = ctx.mid50_scores or {}
    
    # Get target score
    target_score = None
    if test_type == "SAT" and mid50.get("sat_composite"):
        target_score = mid50["sat_composite"][1] if len(mid50["sat_composite"]) > 1 else mid50["sat_composite"][0]
    elif test_type == "ACT" and mid50.get("act_composite"):
        target_score = mid50["act_composite"][1] if len(mid50["act_composite"]) > 1 else mid50["act_composite"][0]
    
    latest_date_str = policy.latest_submission_date if policy else None
    if not latest_date_str and ctx.application_rounds:
        latest_date_str = ctx.application_rounds[0].closing_date
    
    tasks = [
        RecommendationTask(
            title=f"Register for {test_type}",
            track=track,
            estimated_hours=2,
            definition_of_done=[
                f"Research {test_type} test dates",
                f"Register for {test_type} exam",
                f"Schedule test date before {latest_date_str or 'application deadline'}"
            ],
            micro_coaching=f"Register for {test_type} to meet school requirements. Target score: {target_score if target_score else 'competitive range'}.",
            quick_links=[
                "https://www.collegeboard.org" if test_type == "SAT" else "https://www.act.org"
            ]
        ),
        RecommendationTask(
            title=f"{test_type} Diagnostic Test & Study Plan",
            track=track,
            estimated_hours=6,
            definition_of_done=[
                f"Take {test_type} diagnostic test",
                "Identify weak areas",
                "Create 6-8 week study schedule",
                f"Set target score: {target_score if target_score else 'competitive range'}"
            ],
            micro_coaching=f"Diagnostic test will help identify areas to focus on. Aim for {target_score if target_score else 'competitive'} score.",
            quick_links=[]
        ),
        RecommendationTask(
            title=f"{test_type} Practice Tests & Review",
            track=track,
            estimated_hours=20,
            definition_of_done=[
                "Complete 3-4 full practice tests",
                "Review mistakes and weak areas",
                "Focus on improving lowest-scoring sections",
                f"Target score: {target_score if target_score else 'competitive range'}"
            ],
            micro_coaching=f"Regular practice tests are essential for improvement. Focus on consistent practice to reach {target_score if target_score else 'competitive'} score.",
            quick_links=[]
        )
    ]
    
    return tasks

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

def regenerate_tasks_for_section(
    req: PortfolioAnalyzeRequest,
    section_type: str,
    section_identifier: Optional[str],
    exclude_task_titles: List[str]
) -> RegenerateTasksResponse:
    """Regenerate alternative tasks for a specific section"""
    prof = req.student_profile
    impacts_raw: Dict[str, float] = {}
    for ev in req.portfolio:
        impacts_raw[ev.id] = compute_impact(ev, prof.intended_major if prof else None)
    impacts_norm = normalize_impacts(impacts_raw) if impacts_raw else {}
    lens_s = lens_scores(req.portfolio, impacts_norm) if impacts_norm else {k:0.0 for k in LENS_LIST}
    coverage = coverage_index(lens_s) if sum(lens_s.values())>0 else 0.0
    spike_theme, spike_share = detect_spike(req.portfolio, impacts_norm)
    
    gaps = analyze_gaps(req.portfolio, lens_s, (spike_theme, spike_share), req.school_context, prof, impacts_norm)
    
    track = req.country_tracks[0] if req.country_tracks else "US"
    
    # Build portfolio context
    portfolio_summary = []
    for ev in req.portfolio[:10]:
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
    
    # Generate alternative tasks based on section type
    if section_type == "critical_improvements":
        # Find the specific gap
        target_gap = None
        if section_identifier:
            for gap in gaps:
                if gap.get("type") == "lens" and gap.get("lens") == section_identifier:
                    target_gap = gap
                    break
                elif gap.get("type") == section_identifier:
                    target_gap = gap
                    break
        else:
            # Use the highest severity gap
            target_gap = max(gaps, key=lambda x: x.get('severity', 0)) if gaps else None
        
        if not target_gap:
            raise ValueError(f"No gap found for identifier: {section_identifier}")
        
        tasks = _generate_alternative_tasks_for_gap(
            req, target_gap, lens_s, impacts_norm, portfolio_summary, track, exclude_task_titles
        )
        return RegenerateTasksResponse(
            section_type=section_type,
            section_identifier=section_identifier or target_gap.get("lens") or target_gap.get("type"),
            tasks=tasks
        )
    
    elif section_type == "lens_improvements":
        if not section_identifier:
            raise ValueError("section_identifier required for lens_improvements")
        
        lens_score = lens_s.get(section_identifier, 0)
        if lens_score < LENS_MIN_SCORE:
            raise ValueError(f"Lens {section_identifier} is below minimum (has a gap, use critical_improvements instead)")
        
        tasks = _generate_alternative_tasks_for_lens(
            req, section_identifier, lens_score, impacts_norm, portfolio_summary, track, exclude_task_titles
        )
        return RegenerateTasksResponse(
            section_type=section_type,
            section_identifier=section_identifier,
            tasks=tasks
        )
    
    elif section_type == "diversity_spike":
        tasks = _generate_alternative_tasks_for_diversity_spike(
            req, spike_theme, spike_share, coverage, impacts_norm, portfolio_summary, track, exclude_task_titles
        )
        return RegenerateTasksResponse(
            section_type=section_type,
            section_identifier=None,
            tasks=tasks
        )
    
    else:
        raise ValueError(f"Unknown section_type: {section_type}")

def _generate_alternative_tasks_for_gap(
    req: PortfolioAnalyzeRequest,
    gap: dict,
    lens_scores: Dict[str, float],
    impacts_norm: Dict[str, float],
    portfolio_summary: List[dict],
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Generate 3 alternative tasks for a specific gap"""
    gap_type = gap.get("type")
    lens = gap.get("lens")
    severity = gap.get("severity", 0)
    score = lens_scores.get(lens, 0) if lens else 0
    
    prompt = f"""Generate EXACTLY 3 ALTERNATIVE tasks for this gap. These must be DIFFERENT from the previous suggestions.

=== GAP INFORMATION ===
Type: {gap_type}
Lens: {lens or 'N/A'}
Current Score: {score:.2f}/10 (target: ≥4.0)
Severity: {severity:.2f}

=== PORTFOLIO CONTEXT ===
{json.dumps(portfolio_summary, indent=2)}

=== EXCLUDE THESE TASK TITLES (do not suggest similar tasks) ===
{chr(10).join([f"- {title}" for title in exclude_titles])}

=== STUDENT CONTEXT ===
- Grade: {req.student_profile.current_grade if req.student_profile else 'N/A'}
- Major: {req.student_profile.intended_major if req.student_profile else 'N/A'}
- Weekly hours: {req.weekly_hours_cap}h/week

=== REQUIREMENTS ===
1. Generate EXACTLY 3 tasks
2. Tasks must be DIFFERENT from excluded titles
3. Tasks must be practical, realistic, and specific to this student
4. Each task should directly address the gap
5. Be creative and suggest alternative approaches

Return JSON: {{"tasks": [{{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}, ...]}}"""

    if not client or not _openai_api_key:
        # Fallback
        return _get_fallback_alternative_tasks_for_gap(gap, lens_scores, track, exclude_titles)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert portfolio coach. Generate exactly 3 ALTERNATIVE tasks that are different from previous suggestions. Be creative and suggest different approaches."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7  # Higher temperature for more variety
        )
        
        result_json = json.loads(response.choices[0].message.content)
        tasks_data = result_json.get("tasks", [])
        
        tasks = []
        for task_data in tasks_data[:3]:
            try:
                # Check if title is too similar to excluded ones
                title = task_data.get("title", "")
                if any(excluded.lower() in title.lower() or title.lower() in excluded.lower() 
                       for excluded in exclude_titles):
                    continue
                
                tasks.append(RecommendationTask(
                    title=title,
                    track=track,
                    estimated_hours=int(task_data.get("estimated_hours", 3)),
                    definition_of_done=task_data.get("definition_of_done", []),
                    micro_coaching=task_data.get("micro_coaching", ""),
                    quick_links=task_data.get("quick_links", [])
                ))
            except:
                continue
        
        # Ensure we have 3 tasks
        while len(tasks) < 3:
            tasks.extend(_get_fallback_alternative_tasks_for_gap(gap, lens_scores, track, exclude_titles))
        
        return tasks[:3]
        
    except Exception as e:
        import logging
        logging.warning(f"GPT alternative tasks failed: {e}. Using fallback.")
        return _get_fallback_alternative_tasks_for_gap(gap, lens_scores, track, exclude_titles)

def _generate_alternative_tasks_for_lens(
    req: PortfolioAnalyzeRequest,
    lens: str,
    current_score: float,
    impacts_norm: Dict[str, float],
    portfolio_summary: List[dict],
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Generate 3 alternative tasks for lens improvement"""
    prompt = f"""Generate EXACTLY 3 ALTERNATIVE tasks to improve the {lens} lens. These must be DIFFERENT from previous suggestions.

=== LENS INFORMATION ===
Lens: {lens}
Current Score: {current_score:.2f}/10 (target: reach 8.0+)

=== PORTFOLIO CONTEXT ===
{json.dumps(portfolio_summary, indent=2)}

=== EXCLUDE THESE TASK TITLES ===
{chr(10).join([f"- {title}" for title in exclude_titles])}

=== REQUIREMENTS ===
1. Generate EXACTLY 3 tasks
2. Tasks must be DIFFERENT from excluded titles
3. Build on existing strengths in {lens}
4. Be creative with alternative approaches

Return JSON: {{"tasks": [{{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}, ...]}}"""

    if not client or not _openai_api_key:
        return _get_fallback_alternative_tasks_for_lens(lens, current_score, track, exclude_titles)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Generate exactly 3 ALTERNATIVE tasks for lens improvement. Be creative and suggest different approaches."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result_json = json.loads(response.choices[0].message.content)
        tasks_data = result_json.get("tasks", [])
        
        tasks = []
        for task_data in tasks_data[:3]:
            try:
                title = task_data.get("title", "")
                if any(excluded.lower() in title.lower() or title.lower() in excluded.lower() 
                       for excluded in exclude_titles):
                    continue
                
                tasks.append(RecommendationTask(
                    title=title,
                    track=track,
                    estimated_hours=int(task_data.get("estimated_hours", 3)),
                    definition_of_done=task_data.get("definition_of_done", []),
                    micro_coaching=task_data.get("micro_coaching", ""),
                    quick_links=task_data.get("quick_links", [])
                ))
            except:
                continue
        
        while len(tasks) < 3:
            tasks.extend(_get_fallback_alternative_tasks_for_lens(lens, current_score, track, exclude_titles))
        
        return tasks[:3]
        
    except Exception as e:
        import logging
        logging.warning(f"GPT alternative lens tasks failed: {e}. Using fallback.")
        return _get_fallback_alternative_tasks_for_lens(lens, current_score, track, exclude_titles)

def _generate_alternative_tasks_for_diversity_spike(
    req: PortfolioAnalyzeRequest,
    spike_theme: Optional[str],
    spike_share: float,
    coverage: float,
    impacts_norm: Dict[str, float],
    portfolio_summary: List[dict],
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Generate 3 alternative tasks for diversity/spike improvement"""
    prompt = f"""Generate EXACTLY 3 ALTERNATIVE tasks to improve diversity/spike. These must be DIFFERENT from previous suggestions.

=== DIVERSITY/SPIKE STATUS ===
Has Spike: {spike_theme is not None}
Spike Theme: {spike_theme or 'None'}
Spike Share: {spike_share:.1%} (target: ≥35%)
Coverage Index: {coverage:.3f} (target: >0.7)

=== PORTFOLIO CONTEXT ===
{json.dumps(portfolio_summary, indent=2)}

=== EXCLUDE THESE TASK TITLES ===
{chr(10).join([f"- {title}" for title in exclude_titles])}

=== REQUIREMENTS ===
1. Generate EXACTLY 3 tasks
2. Tasks must be DIFFERENT from excluded titles
3. Focus on either building spike or improving diversity
4. Be creative with alternative approaches

Return JSON: {{"tasks": [{{"title": "...", "estimated_hours": N, "definition_of_done": [...], "micro_coaching": "...", "quick_links": []}}, ...]}}"""

    if not client or not _openai_api_key:
        return _get_fallback_alternative_tasks_for_diversity_spike(spike_theme, spike_share, coverage, track, exclude_titles)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Generate exactly 3 ALTERNATIVE tasks for diversity/spike improvement. Be creative."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result_json = json.loads(response.choices[0].message.content)
        tasks_data = result_json.get("tasks", [])
        
        tasks = []
        for task_data in tasks_data[:3]:
            try:
                title = task_data.get("title", "")
                if any(excluded.lower() in title.lower() or title.lower() in excluded.lower() 
                       for excluded in exclude_titles):
                    continue
                
                tasks.append(RecommendationTask(
                    title=title,
                    track=track,
                    estimated_hours=int(task_data.get("estimated_hours", 3)),
                    definition_of_done=task_data.get("definition_of_done", []),
                    micro_coaching=task_data.get("micro_coaching", ""),
                    quick_links=task_data.get("quick_links", [])
                ))
            except:
                continue
        
        while len(tasks) < 3:
            tasks.extend(_get_fallback_alternative_tasks_for_diversity_spike(spike_theme, spike_share, coverage, track, exclude_titles))
        
        return tasks[:3]
        
    except Exception as e:
        import logging
        logging.warning(f"GPT alternative diversity tasks failed: {e}. Using fallback.")
        return _get_fallback_alternative_tasks_for_diversity_spike(spike_theme, spike_share, coverage, track, exclude_titles)

def _get_fallback_alternative_tasks_for_gap(
    gap: dict,
    lens_scores: Dict[str, float],
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Fallback alternative tasks for gap"""
    gap_type = gap.get("type")
    lens = gap.get("lens")
    score = lens_scores.get(lens, 0) if lens else 0
    
    alternatives = []
    if gap_type == "lens" and lens:
        if lens == "Achievements":
            alternatives = [
                ("Submit to academic journals or conferences", 20),
                ("Create a public showcase of your work", 12),
                ("Mentor others and document the impact", 15)
            ]
        elif lens == "Growth":
            alternatives = [
                ("Take on a challenging certification program", 25),
                ("Start a learning journal documenting progress", 8),
                ("Join a study group or learning community", 10)
            ]
        else:
            alternatives = [
                (f"Explore new {lens.lower()} opportunities", 12),
                (f"Document your {lens.lower()} journey", 8),
                (f"Deepen your {lens.lower()} engagement", 15)
            ]
    
    tasks = []
    for title, hours in alternatives:
        if not any(excluded.lower() in title.lower() for excluded in exclude_titles):
            tasks.append(RecommendationTask(
                title=title,
                track=track,
                estimated_hours=hours,
                definition_of_done=["Plan", "Execute", "Document"],
                micro_coaching=f"Alternative approach to improve {lens or gap_type} from {score:.2f}/10.",
                quick_links=[]
            ))
        if len(tasks) >= 3:
            break
    
    return tasks[:3]

def _get_fallback_alternative_tasks_for_lens(
    lens: str,
    current_score: float,
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Fallback alternative tasks for lens improvement"""
    alternatives = [
        (f"Alternative approach to enhance {lens}", 12),
        (f"Creative way to build {lens} strength", 10),
        (f"Different strategy for {lens} improvement", 15)
    ]
    
    tasks = []
    for title, hours in alternatives:
        if not any(excluded.lower() in title.lower() for excluded in exclude_titles):
            tasks.append(RecommendationTask(
                title=title,
                track=track,
                estimated_hours=hours,
                definition_of_done=["Plan", "Execute", "Document"],
                micro_coaching=f"Alternative approach to improve {lens} from {current_score:.2f}/10 to 8.0+.",
                quick_links=[]
            ))
        if len(tasks) >= 3:
            break
    
    return tasks[:3]

def _get_fallback_alternative_tasks_for_diversity_spike(
    spike_theme: Optional[str],
    spike_share: float,
    coverage: float,
    track: str,
    exclude_titles: List[str]
) -> List[RecommendationTask]:
    """Fallback alternative tasks for diversity/spike"""
    alternatives = [
        ("Alternative approach to build spike", 15),
        ("Different strategy for diversity", 12),
        ("Creative way to improve portfolio balance", 10)
    ]
    
    tasks = []
    for title, hours in alternatives:
        if not any(excluded.lower() in title.lower() for excluded in exclude_titles):
            tasks.append(RecommendationTask(
                title=title,
                track=track,
                estimated_hours=hours,
                definition_of_done=["Plan", "Execute", "Document"],
                micro_coaching=f"Alternative approach to {'build spike' if not spike_theme else 'improve diversity'}.",
                quick_links=[]
            ))
        if len(tasks) >= 3:
            break
    
    return tasks[:3]

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
