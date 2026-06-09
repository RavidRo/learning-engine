## Purpose

Define the Updates page layout behavior for summary statistics, feed width, responsive presentation, and unchanged update interactions.

## Requirements

### Requirement: Updates summary appears above feed content
The Updates page SHALL present update summary statistics above the update feed content when updates data is available.

#### Scenario: Updates data is loaded
- **WHEN** the Updates page has an updates payload
- **THEN** the updates found, sources checked, and interests with updates statistics appear above the feed, source error callouts, update groups, and empty state content

### Requirement: Updates feed uses available panel width
The Updates page SHALL allow feed content to use the available panel width below the summary statistics.

#### Scenario: Update groups are displayed
- **WHEN** the Updates page displays grouped updates
- **THEN** the update groups are not constrained by a persistent left statistics column

### Requirement: Updates layout remains responsive
The Updates page SHALL keep summary statistics readable and non-overlapping across desktop, tablet, and mobile viewport widths.

#### Scenario: Narrow viewport displays summary statistics
- **WHEN** the Updates page is viewed on a narrow viewport
- **THEN** the summary statistics wrap or stack without overlapping header controls, feed content, or each other

### Requirement: Updates behavior is unchanged
The Updates page SHALL preserve existing update refresh, filtering window, error callout, empty state, and grouping behavior.

#### Scenario: User refreshes updates
- **WHEN** the user changes the update window or refreshes updates
- **THEN** the page uses the same update collection behavior and displays the same categories of results and errors as before the layout change
