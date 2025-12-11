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
    latest_revenue: Optional[float] = Field(None, description="最新一条数据的收入")
    data: dict = Field(default_factory=dict, description="其他数据")
    matched_groups: list[int] = Field(default_factory=list, description="满足的规则组索引列表")
    matched_rules: list[str] = Field(default_factory=list, description="满足的规则描述列表")
    is_latest_data_match: bool = Field(False, description="是否由最新数据满足规则（而非均值）")


class ExcelAnalysisResponse(BaseModel):
    """Excel 分析响应模型."""

    total_rows: int = Field(..., description="总行数")
    matched_count: int = Field(..., description="符合规则的数量")
    links: list[LinkData] = Field(..., description="符合规则的链接列表")
    columns: list[str] = Field(..., description="Excel 列名")
    rule_fields: list[str] = Field(default_factory=list, description="规则中使用的字段列表")
    record_id: Optional[int] = Field(None, description="保存到数据库后的记录ID")
    no_yesterday_links: list[str] = Field(default_factory=list, description="昨天无数据的链接列表")
    offline_links: list[str] = Field(default_factory=list, description="下线的链接列表（昨天和今天都无数据）")


class AnalysisRecordSummary(BaseModel):
    """分析记录摘要模型."""

    id: int
    file_name: str
    total_rows: int
    matched_count: int
    days: int
    created_at: str


class LinkHistoryItem(BaseModel):
    """链接历史项模型."""

    id: int
    analysis_record_id: int
    link: str
    ctr: Optional[float] = None
    revenue: Optional[float] = None
    latest_revenue: Optional[float] = None
    data: dict = Field(default_factory=dict)
    matched_groups: list[int] = Field(default_factory=list)
    matched_rules: list[str] = Field(default_factory=list)
    created_at: str
    file_name: str  # 关联的分析记录文件名


class LinkChangeTrend(BaseModel):
    """链接变化趋势模型."""

    link: str
    records: list[LinkHistoryItem] = Field(..., description="历史记录列表，按时间排序")
    ctr_changes: list[Optional[float]] = Field(..., description="CTR 变化序列")
    revenue_changes: list[Optional[float]] = Field(..., description="收入变化序列")
    first_seen: str = Field(..., description="首次出现时间")
    last_seen: str = Field(..., description="最后出现时间")
    appearance_count: int = Field(..., description="出现次数")

