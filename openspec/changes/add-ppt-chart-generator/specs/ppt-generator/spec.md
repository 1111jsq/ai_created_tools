## ADDED Requirements

### Requirement: Natural Language Data Parsing
The system SHALL parse natural language text to extract structured data and determine the appropriate chart type.

#### Scenario: Parse simple sales data
- **WHEN** input text is "Sales in Q1 were 100, Q2 were 150"
- **THEN** extract categories ["Q1", "Q2"] and series data [100, 150]
- **AND** recommend "BAR" or "LINE" chart type

### Requirement: PPTX Generation
The system SHALL generate a `.pptx` file containing the requested charts based on the structured data.

#### Scenario: Generate bar chart presentation
- **WHEN** structured data specifies a Bar Chart with categories and values
- **THEN** create a valid `.pptx` file
- **AND** the slide contains a bar chart reflecting the data


