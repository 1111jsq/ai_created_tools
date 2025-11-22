## ADDED Requirements

### Requirement: Visual Styles
The system SHALL support multiple visual themes for the generated presentation.

#### Scenario: Generate with Tech theme
- **WHEN** user provides `--style tech`
- **THEN** use dark background, neon accent colors, and modern fonts

#### Scenario: Generate with Light theme
- **WHEN** user provides `--style light`
- **THEN** use white background, standard corporate colors, and clean fonts

#### Scenario: Generate with Retro theme
- **WHEN** user provides `--style retro`
- **THEN** use Solarized color palette and typewriter-style fonts

