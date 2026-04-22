from typing import TypedDict, Optional


class ProspectDict(TypedDict, total=False):
    podcast_name: str
    host_name: str
    rss_url: str
    domain: str
    cadence_days: Optional[float]
    recent_episode_topic: str
    episode_count: int
    categories: dict
    last_publish_time: int
    work_email: Optional[str]
    title: Optional[str]
    company_name: Optional[str]
    company_size: Optional[int]
    industry: Optional[str]
    enrichment_status: str
    score: int
    status: str
    disqualify_reason: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    language: Optional[str]
    qualification_status: Optional[str]
    episode_details: Optional[list]      # list of episode dicts (title, description, guest_name, published)
    podcast_profile: Optional[str]       # LLM-extracted podcast niche, format, guests, patterns
    company_profile: Optional[str]       # LLM-extracted company product, market, content signals
    production_signals: Optional[str]    # LLM-observed video, remote guests, tools, quality signals
    has_video: Optional[bool]             # True if video signals detected in RSS feed
    phone_number: Optional[str]
    call_context: Optional[str]            # JSON string of AI-generated call briefing
