"""Framework-visible symbols that Vulture cannot infer statically."""

from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.models import (
    CollectedUpdate,
    CollectionError,
    SourceInterest,
    Update,
    UpdatesResponse,
)

CollectedUpdate.matched_keywords
SourceInterest.interest_id
SourceInterest.interest_name
SourceInterest.source_id
SourceInterest.source_label
Update.source_interest
CollectionError.interest_id
CollectionError.interest_name
CollectionError.source_id
CollectionError.source_label
UpdatesResponse.sources_checked
UpdatesResponse.since

# I want to keep for my own satisfaction
Timeframe.from_point
Timeframe.starting_at
Timeframe.around
Timeframe.overlaps
Timeframe.shift
