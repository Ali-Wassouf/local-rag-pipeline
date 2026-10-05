from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocFormat, DocStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sha256: str
    title: str
    author: str | None
    format: DocFormat
    original_name: str
    status: DocStatus
    generate_summary: bool
    # Default 0 — only populated with real counts by endpoints that join
    # for them (currently GET /projects/{id}/documents). A document with
    # generate_summary=True can still show summary_count=0 when none of its
    # sections exceeded the summarization threshold (docs/plan.md §8) —
    # these counts are what let the UI tell that apart from "has real
    # summaries" instead of looking identical.
    section_count: int = 0
    summary_count: int = 0
    # True while a summarise-stage job for this document is pending or
    # actively running. Default False — only populated by endpoints that
    # join for it (currently GET /projects/{id}/documents). Lets the UI
    # tell "hasn't finished yet" apart from "genuinely nothing qualified"
    # when summary_count is 0, instead of both looking identical.
    summarizing: bool = False
    # How many sections qualify for summarising, while summarizing=True.
    # summary_count is already the live "done so far" count (each
    # qualifying section's summary is persisted as soon as it's done, not
    # batched at the end — app/ingest/worker.py's _run_summarize), so only
    # the total needs to come from here for "N of M" progress. None before
    # the job has determined it (its very first tick) or once summarizing
    # is False.
    summary_total: int | None = None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    job_id: int | None
    deduped: bool
