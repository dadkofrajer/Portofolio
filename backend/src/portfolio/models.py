from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, AnyUrl
from datetime import date

Lens = Literal["Curiosity","Growth","Community","Creativity","Leadership","Achievements"]
RoleLevel = Literal["Member","Core","Lead","Founder"]
EvidenceType = Literal["Club","Competition","Research","Startup","Work","Volunteering","Project","Certificate","Award"]
Track = Literal["US","UK","EU"]
TestUse = Literal["required","recommended","considered_if_submitted","not_considered"]
Platform = Literal["Common App","UCAS","Coalition","School Portal"]
TestPrepStatus = Literal["none","studying","taken"]
Criticality = Literal["low","medium","high"]

class TestScore(BaseModel):
    score: Optional[int] = None
    date: Optional[str] = None  # ISO date
    planned_date: Optional[str] = None  # ISO date
    prep_status: TestPrepStatus = "none"

class StudentTests(BaseModel):
    sat: Optional[TestScore] = None
    act: Optional[TestScore] = None
    ielts: Optional[TestScore] = None
    toefl: Optional[TestScore] = None

class StudentProfile(BaseModel):
    student_id: str = Field(..., description="External UUID/ID")
    current_grade: str = Field(..., description="e.g., 'Year 13', '12'")
    weekly_hours_cap: int = Field(..., ge=2, le=25)
    intended_major: Optional[str] = Field(None, description="e.g., 'Computer Science'")
    curriculum: Optional[str] = Field(None, description="A-Levels/IB/AP/Maturita/Other")
    gpa_unweighted: Optional[float] = Field(None, ge=0, le=4.0)
    gpa_weighted: Optional[float] = Field(None, ge=0, le=5.0)
    grades_by_subject: dict[str, str] = Field(default_factory=dict, description="subject → predicted/actual grade")
    tests: StudentTests = Field(default_factory=StudentTests)
    constraints: list[str] = Field(default_factory=list, description="e.g., ['Varsity Tue/Thu 17–20', 'Part-time job Sat']")

class Evidence(BaseModel):
    id: str = Field(..., description="Stable identifier")
    title: str = Field(..., min_length=2, max_length=120)
    lens: Lens = Field(..., description="Category: Curiosity, Growth, Community, Creativity, Leadership, Achievements")
    type: EvidenceType = Field(..., description="Club, Competition, Research, Startup, Work, Volunteering, Project, Certificate, Award")
    area_of_activity: Optional[str] = Field(None, description="e.g., 'Volleyball', 'football', 'CS'")
    role_level: RoleLevel = Field(..., description="Member, Core, Lead, Founder")
    theme_tags: list[str] = Field(default_factory=list)
    start_date: Optional[date] = None
    end_date: Optional[date] = None  # null/ongoing
    hours_total: Optional[int] = Field(None, ge=0, le=5000)
    hours_per_week: Optional[float] = Field(None, ge=0, le=60)
    team_size: Optional[int] = Field(None, ge=1, le=10000)
    people_impacted: Optional[int] = Field(None, ge=0, le=1000000)
    awards: list[dict] = Field(default_factory=list, description="List of {level: school|regional|national|international}")
    artifact_links: list[AnyUrl] = Field(default_factory=list)
    description_raw: Optional[str] = Field(None, max_length=2000)

class ApplicationRound(BaseModel):
    round: Literal["EA","ED","RD","Regular","Rolling","Other"]
    closing_date: Optional[str] = None
    notification_date: Optional[str] = None
    binding: bool = False

class TestPolicy(BaseModel):
    admission_use: TestUse
    latest_submission_date: Optional[str] = None
    used_for: list[Literal["admission","placement"]] = []

class GPAProfile(BaseModel):
    avg_hs_gpa: Optional[float] = None
    submitted_gpa_pct: Optional[int] = None
    gpa_buckets_pct: dict[str, int] = {}

class SchoolContext(BaseModel):
    name: str
    cds_year: Optional[str] = None
    cds_url: Optional[str] = None
    application_platform: Optional[Platform] = None
    application_rounds: list[ApplicationRound] = []
    application_fee_usd: Optional[int] = None
    fee_waivers_available: Optional[bool] = None
    test_policy: Optional[TestPolicy] = None
    percent_submitting_scores: Optional[dict[str, int]] = None
    mid50_scores: Optional[dict[str, list[int]]] = None
    gpa_profile: Optional[GPAProfile] = None
    factor_importance: Optional[dict[str, Literal["very_important","important","considered","not_considered"]]] = None
    recommenders_required: Optional[int] = None
    supplemental_essays: Optional[list[str]] = None
    required_subjects: list[str] = []

class PortfolioAnalyzeRequest(BaseModel):
    country_tracks: list[Track]
    schools: list[str]
    deadlines: dict[str, str]
    weekly_hours_cap: int = Field(8, ge=2, le=25)
    school_context: Optional[SchoolContext] = None
    student_profile: Optional[StudentProfile] = None
    portfolio: list[Evidence] = []

class RecommendationTask(BaseModel):
    title: str
    track: Track
    estimated_hours: int
    definition_of_done: list[str]
    micro_coaching: str
    quick_links: list[str] = []

class TaskTemplate(BaseModel):
    id: str
    title: str
    track: Track
    duration_hours: int = Field(..., ge=1)
    buffer_days: int = Field(0, ge=0)
    deps: list[str] = Field(default_factory=list)
    criticality: Criticality
    deadline: Optional[str] = Field(None, description="ISO date - nearest relevant school deadline")
    dod: list[str] = Field(default_factory=list, description="Definition of done")

class PortfolioAnalyzeResponse(BaseModel):
    scores: dict
    gaps: list[dict]
    recommendations: list[RecommendationTask]
    tasks: list[TaskTemplate]

class TestPlanRequest(BaseModel):
    student_profile: StudentProfile
    school_context: SchoolContext
    weekly_hours_cap: int = Field(..., ge=2, le=25)

class TestPlanResponse(BaseModel):
    decision: Literal["PLAN", "SEND", "SKIP", "OPTIONAL"]
    rationale: str
    tasks: Optional[list[TaskTemplate]] = None

class EligibilityCheckRequest(BaseModel):
    student_profile: StudentProfile
    school_context: SchoolContext

class EligibilityCheckResponse(BaseModel):
    eligible: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
