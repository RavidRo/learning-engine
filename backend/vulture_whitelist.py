"""Framework-visible symbols that Vulture cannot infer statically."""

from learning_engine.application.responses import CollectionError, UpdatesResponse
from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.updates import SourceInterest, SourceUpdate, Update
from learning_engine.infrastructure.storage import StoredSourceIgnoreKeyword
from learning_engine.presentation.schemas import InterestExportEnvelope

SourceUpdate.matched_keywords
SourceInterest.interest_id
SourceInterest.interest_name
SourceInterest.source_id
SourceInterest.source_label
Update.source_interest
CollectionError.interest_id
CollectionError.interest_name
CollectionError.source_id
CollectionError.source_label
CollectionError.error
UpdatesResponse.sources_checked
UpdatesResponse.since
UpdatesResponse.errors
InterestExportEnvelope.schema_version
InterestExportEnvelope.exported_at

# I want to keep for my own satisfaction
Timeframe.from_point
Timeframe.starting_at
Timeframe.around
Timeframe.overlaps
Timeframe.shift

StoredSourceIgnoreKeyword.keyword_id
