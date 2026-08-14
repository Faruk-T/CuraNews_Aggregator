"""spaCy NLP and algorithmic curation — Issues #14/#15+."""

from curanews.nlp.entities import ExtractedEntity
from curanews.nlp.spacy_pipe import SpacyModelUnavailableError, SpacyPipe, SpacyPipeResult, get_spacy_pipe
from curanews.nlp.topics import match_topic_keywords

__all__ = [
    "ExtractedEntity",
    "SpacyModelUnavailableError",
    "SpacyPipe",
    "SpacyPipeResult",
    "get_spacy_pipe",
    "match_topic_keywords",
]


def __getattr__(name: str):
    if name in {"tag_article", "tag_article_id"}:
        from curanews.nlp import tagging

        return getattr(tagging, name)
    if name in {"CurationEngine", "ScoredArticle", "jaccard", "freshness_score"}:
        from curanews.nlp import curation

        return getattr(curation, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
