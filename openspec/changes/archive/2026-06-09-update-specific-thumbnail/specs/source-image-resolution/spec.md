## MODIFIED Requirements

### Requirement: Manual source images take precedence
#### Scenario: Update thumbnail uses update image before source image
- **WHEN** a collected update includes a non-empty update-specific image URL and its source also has a manual or automatically resolved image URL
- **THEN** the Updates page renders the update-specific image as the update thumbnail

#### Scenario: Update thumbnail falls back to source image
- **WHEN** a collected update has no non-empty update-specific image URL and its source has a manual or automatically resolved image URL
- **THEN** the Updates page renders the source image as the update thumbnail

#### Scenario: Update thumbnail falls back to source initial
- **WHEN** a collected update has no non-empty update-specific image URL and no source image URL
- **THEN** the Updates page renders the existing source-label fallback initial
