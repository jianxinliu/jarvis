"""Excel 分析相关的数据模型."""

from typing import Optional

from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    """规则条件模型."""

    field: str = Field(..., description="字段名（如：ctr, 收入）")
    operator: str = Field(..., description="操作符（如：>, <, >=, <=, ==, !=）")
    value: float = Field(..., description="比较值")
    priority: int = Field(0, description="优先级（数字越小优先级越高，默认0）")


class RuleGroup(BaseModel):
    """规则组模型（原子化的逻辑单元）."""

    conditions: list[RuleCondition] = Field(..., description="条件列表")
    logic: str = Field("or", description="组内逻辑关系：and 或 or")
    priority: int = Field(0, description="优先级（数字越小优先级越高，默认0）")


class FilterRule(BaseModel):
    """筛选规则模型（支持原子化逻辑关系）."""

    groups: list[RuleGroup] = Field(..., description="规则组列表")
    logic: str = Field("or", description="组间逻辑关系：and 或 or")


class ExcelAnalysisRequest(BaseModel):
    """Excel 分析请求模型."""

    rule: FilterRule = Field(..., description="筛选规则")
    days: int = Field(7, ge=1, le=30, description="查看近几日的均值，默认7天")


class LinkData(BaseModel):
    """链接数据模型."""

    link: str = Field(..., description="链接")
    ctr: Optional[float] = Field(None, description="CTR 均值")
    revenue: Optional[float] = Field(None, description="收入均值")
    data: dict = Field(default_factory=dict, description="其他数据")
    matched_groups: list[int] = Field(default_factory=list, description="满足的规则组索引列表")
    matched_rules: list[str] = Field(default_factory=list, description="满足的规则描述列表")


class ExcelAnalysisResponse(BaseModel):
    """Excel 分析响应模型."""

    total_rows: int = Field(..., description="总行数")
    matched_count: int = Field(..., description="符合规则的数量")
    links: list[LinkData] = Field(..., description="符合规则的链接列表")
    columns: list[str] = Field(..., description="Excel 列名")
    rule_fields: list[str] = Field(default_factory=list, description="规则中使用的字段列表")

