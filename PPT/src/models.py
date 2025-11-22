from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from pptx.dml.color import RGBColor

class ChartType(str, Enum):
    BAR = "BAR"
    LINE = "LINE"
    PIE = "PIE"
    SCATTER = "SCATTER"

class SeriesData(BaseModel):
    name: str = Field(description="Name of the data series")
    values: List[float] = Field(description="List of numerical values corresponding to categories")

class ChartData(BaseModel):
    title: str = Field(description="Title of the chart")
    categories: List[str] = Field(description="Labels for the x-axis or categories")
    series: List[SeriesData] = Field(description="One or more data series")
    x_axis_label: Optional[str] = Field(default=None, description="Label for X axis")
    y_axis_label: Optional[str] = Field(default=None, description="Label for Y axis")

class PresentationRequest(BaseModel):
    slide_title: str = Field(description="Title for the presentation slide")
    summary: str = Field(description="Brief summary or insight from the data")
    chart_type: ChartType = Field(description="Recommended chart type")
    data: ChartData = Field(description="Structured data for the chart")

class ThemeStyle(BaseModel):
    name: str
    bg_color: RGBColor
    text_color: RGBColor
    card_color: RGBColor
    accent_colors: List[RGBColor]
    title_font: str = "Arial Black"
    body_font: str = "Arial"

    class Config:
        arbitrary_types_allowed = True
