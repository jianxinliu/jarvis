"""Excel 分析相关的 API 路由."""
# mypy: ignore-errors

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.apps.excel.schemas import (
    ExcelAnalysisRequest,
    ExcelAnalysisResponse,
    FilterRule,
    LinkData,
    AnalysisRecordSummary,
    LinkHistoryItem,
    LinkChangeTrend,
)
from app.apps.excel.service import ExcelService
from app.database import get_db
from app.models import ExcelAnalysisRecord, ExcelLinkHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/excel", tags=["excel"])

# Excel 规则配置文件目录
# 使用绝对路径，确保在 Docker 中也能正常工作
RULES_DIR = Path.cwd() / "data" / "excel_rules"
RULES_DIR.mkdir(parents=True, exist_ok=True)


def ensure_latest_revenue_column(db: Session) -> None:
    """
    确保 excel_link_histories 表存在 latest_revenue 列。
    如果不存在则尝试在线添加，避免查询/插入报错。
    """
    try:
        dialect = db.bind.dialect.name if db.bind else "sqlite"
        has_column = False

        if dialect == "sqlite":
            result = db.execute(text("PRAGMA table_info(excel_link_histories);")).fetchall()
            has_column = any(row[1] == "latest_revenue" for row in result)
            if not has_column:
                db.execute(
                    text("ALTER TABLE excel_link_histories ADD COLUMN latest_revenue VARCHAR(50);")
                )
                db.commit()
        else:
            # 兼容其他数据库，尝试查 information_schema
            check_sql = text(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'excel_link_histories' AND column_name = 'latest_revenue'
                """
            )
            res = db.execute(check_sql).fetchone()
            has_column = res is not None
            if not has_column:
                db.execute(
                    text("ALTER TABLE excel_link_histories ADD COLUMN latest_revenue VARCHAR(50);")
                )
                db.commit()
    except Exception as e:
        # 如果失败，不阻塞主流程，但记录日志
        logger.warning(f"检查/添加 latest_revenue 列失败: {e}")


@router.post("/analyze", response_model=ExcelAnalysisResponse)
async def analyze_excel(
    file: UploadFile = File(...),
    rule: str = Form('{"conditions": [], "logic": "or"}'),
    days: int = Form(3),
    save_to_db: bool = Form(False),  # 是否保存到数据库
    db: Session = Depends(get_db),
) -> ExcelAnalysisResponse:
    """
    分析 Excel 文件，根据规则筛选链接.

    Args:
        file: 上传的 Excel 文件
        rule: 筛选规则 JSON 字符串
        days: 查看近几日的均值，默认 3 天

    Returns:
        ExcelAnalysisResponse: 分析结果

    Raises:
        HTTPException: 如果文件格式不正确或处理失败
    """
    try:
        # 确保历史表新增列存在
        ensure_latest_revenue_column(db)

        # 解析规则
        try:
            rule_dict = json.loads(rule) if rule else {}
            filter_rule = FilterRule(**rule_dict)
        except Exception as e:
            logger.error(f"解析规则失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"规则格式错误: {str(e)}",
            )

        # 解析 Excel
        df = ExcelService.parse_excel(file)

        # 检查链接数据状态：昨天无数据、下线链接
        no_yesterday_links, offline_links, df_normal = ExcelService.check_link_data_status(df)

        # 获取最新一天的数据及其收入映射，供结果展示
        df_latest = ExcelService.get_latest_day_data(df_normal)
        latest_revenue_map = ExcelService.build_latest_revenue_map(df_latest)

        # 计算近几日均值（只使用正常数据）
        df_avg = ExcelService.calculate_recent_days_average(df_normal, days=days)

        # 应用筛选规则（基于均值）
        df_filtered, matched_info = ExcelService.apply_filter_rule(df_avg, filter_rule)

        # 转换为链接数据（基于均值）
        # 最新收入映射在均值结果中也需要使用
        links = ExcelService.convert_to_link_data(
            df_filtered,
            matched_info,
            filter_rule,
            is_latest_data_match=False,
            latest_revenue_map=latest_revenue_map,
        )

        # 对最新一天的数据应用筛选规则
        df_latest_filtered, matched_info_latest = ExcelService.apply_filter_rule(
            df_latest, filter_rule
        )

        # 转换为链接数据（基于最新数据）
        links_latest = ExcelService.convert_to_link_data(
            df_latest_filtered,
            matched_info_latest,
            filter_rule,
            is_latest_data_match=True,
            latest_revenue_map=latest_revenue_map,
        )

        # 合并结果：如果链接在最新数据中满足规则但不在均值结果中，添加到结果中
        # 创建均值结果的链接集合
        links_dict = {link.link: link for link in links}

        # 添加最新数据满足但均值不满足的链接
        for link_latest in links_latest:
            if link_latest.link not in links_dict:
                # 标记为最新数据满足
                link_latest.is_latest_data_match = True
                # 在规则描述前添加标记
                if link_latest.matched_rules:
                    link_latest.matched_rules = [
                        f"[最新数据满足] {rule}" for rule in link_latest.matched_rules
                    ]
                links.append(link_latest)
            else:
                # 如果均值也满足，检查是否有最新数据额外满足的规则
                existing_link = links_dict[link_latest.link]
                # 补充最新收入
                if existing_link.latest_revenue is None:
                    existing_link.latest_revenue = link_latest.latest_revenue
                # 合并规则描述（如果最新数据有额外满足的规则）
                if existing_link.matched_rules and link_latest.matched_rules:
                    existing_rules = set(existing_link.matched_rules)
                    latest_rules = set(link_latest.matched_rules)
                    if latest_rules - existing_rules:
                        # 有额外满足的规则，添加标记
                        additional_rules = [
                            f"[最新数据满足] {rule}" for rule in (latest_rules - existing_rules)
                        ]
                        existing_link.matched_rules.extend(additional_rules)

        # 对结果进行排序：按主域名排序，相同域名内按 CTR 降序，如果 CTR 为空则按收入降序
        links.sort(
            key=lambda x: (
                ExcelService.extract_domain(x.link),
                x.ctr if x.ctr is not None else float("-inf"),
                x.revenue if x.revenue is not None else float("-inf"),
            ),
            reverse=False,  # 主域名按字母顺序排序（升序）
        )

        # 获取列名
        columns = ExcelService.get_column_names(df)
        # 增加一个展示列：最新收入
        columns_with_latest = columns[:]
        if "最新收入" not in columns_with_latest:
            columns_with_latest.append("最新收入")

        # 收集所有规则中使用的字段（用于前端显示）
        rule_fields = set()
        for group in filter_rule.groups:
            for condition in group.conditions:
                rule_fields.add(condition.field)
        rule_fields_list = sorted(list(rule_fields))

        response = ExcelAnalysisResponse(
            total_rows=len(df),
            matched_count=len(links),
            links=links,
            columns=columns_with_latest,
            rule_fields=rule_fields_list,
            record_id=None,
            no_yesterday_links=no_yesterday_links,
            offline_links=offline_links,
        )

        # 如果要求保存到数据库，则保存分析结果
        if save_to_db:
            try:
                # 读取文件内容（重置文件指针）
                file_content = None
                if hasattr(file.file, "seek"):
                    try:
                        file.file.seek(0)
                        file_content = file.file.read()
                        file.file.seek(0)  # 再次重置，以防后续使用
                    except Exception as e:
                        logger.warning(f"读取文件内容失败: {e}")
                        # 如果读取失败，继续保存其他数据，但不保存文件内容

                # 创建分析记录
                analysis_record = ExcelAnalysisRecord(
                    file_name=file.filename or "unknown.xlsx",
                    total_rows=len(df),
                    matched_count=len(links),
                    rule=filter_rule.model_dump(),
                    # 保存时带上新增展示列
                    columns=columns_with_latest,
                    rule_fields=rule_fields_list,
                    days=days,
                    file_content=file_content,
                )
                db.add(analysis_record)
                db.flush()  # 获取 record.id

                # 保存链接历史记录
                for link_data in links:
                    link_history = ExcelLinkHistory(
                        analysis_record_id=analysis_record.id,
                        link=link_data.link,
                        ctr=str(link_data.ctr) if link_data.ctr is not None else None,
                        revenue=str(link_data.revenue) if link_data.revenue is not None else None,
                        latest_revenue=str(link_data.latest_revenue)
                        if link_data.latest_revenue is not None
                        else None,
                        data=link_data.data,
                        matched_groups=link_data.matched_groups,
                        matched_rules=link_data.matched_rules,
                    )
                    db.add(link_history)

                db.commit()
                logger.info(f"分析结果已保存到数据库，记录ID: {analysis_record.id}")
                # 设置返回结果中的 record_id
                response.record_id = analysis_record.id  # type: ignore[assignment]
            except Exception as e:
                db.rollback()
                logger.error(f"保存分析结果到数据库失败: {e}", exc_info=True)
                # 不抛出异常，仍然返回分析结果

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"分析 Excel 文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}",
        )


@router.post("/link-details")
async def get_link_details(
    file: Optional[UploadFile] = File(None),
    link: str = Form(...),
    days: int = Form(7),
    record_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    获取链接的详细数据.

    Args:
        file: 上传的 Excel 文件（可选，如果提供 record_id 则不需要）
        link: 链接地址
        days: 查看近几日的均值，默认 7 天（未使用，保留兼容性）
        record_id: 分析记录ID（可选，如果提供则从数据库读取文件）

    Returns:
        JSONResponse: 链接的详细数据
    """
    try:
        # 如果提供了 record_id，从数据库读取文件内容
        if record_id:
            record = (
                db.query(ExcelAnalysisRecord).filter(ExcelAnalysisRecord.id == record_id).first()
            )
            if not record:
                raise ValueError(f"分析记录 {record_id} 不存在")

            if record.file_content is None:  # type: ignore[comparison-overlap]
                raise ValueError("该分析记录没有保存原始文件内容")

            # 从数据库读取的文件内容创建文件对象
            import io

            file_content = io.BytesIO(record.file_content)  # type: ignore

            # 使用 pandas 读取
            df = pd.read_excel(file_content, engine="openpyxl", dtype=str)

            # 尝试将数值列转换为数值类型
            for col in df.columns:
                col_lower = str(col).lower()
                col_str = str(col)
                if "链接" in col_str or "url" in col_lower or "link" in col_lower:
                    continue

                try:
                    if df[col].dtype == "object":
                        converted = pd.to_numeric(df[col], errors="coerce")
                        if len(df) > 0 and converted.notna().sum() / len(df) > 0.5:  # type: ignore[attr-defined]
                            df[col] = converted
                except Exception:
                    pass
        elif file:
            # 重置文件指针（如果可能）
            if hasattr(file.file, "seek"):
                try:
                    file.file.seek(0)
                except Exception:
                    pass

            df = ExcelService.parse_excel(file)
        else:
            raise ValueError("必须提供 file 或 record_id")

        # 查找链接列（使用原始数据，不是均值数据）
        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            raise ValueError("未找到链接列")

        # 筛选出该链接的所有原始数据（不计算均值，显示详细数据）
        link_data = df[df[link_column] == link]

        if len(link_data) == 0:
            raise ValueError(f"未找到链接 {link} 的数据")

        # 转换为字典列表
        data = link_data.to_dict(orient="records")  # type: ignore

        # 处理 NaN 值
        for row in data:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (int, float)):
                    row[key] = float(value)
                else:
                    row[key] = str(value)

        return JSONResponse(
            content={
                "link": link,
                "data": data,
                "total_rows": len(link_data),
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"获取链接详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取链接详情失败: {str(e)}",
        )


@router.post("/rules/save")
async def save_rule(
    name: str = Form(...),
    rule: str = Form(...),
) -> JSONResponse:
    """
    保存筛选规则配置.

    Args:
        name: 规则名称
        rule: 筛选规则 JSON 字符串

    Returns:
        JSONResponse: 保存结果
    """
    try:
        # 验证规则格式
        rule_data = json.loads(rule)
        FilterRule.model_validate(rule_data)

        # 保存到文件
        rule_file = RULES_DIR / f"{name}.json"
        with open(rule_file, "w", encoding="utf-8") as f:
            json.dump(rule_data, f, ensure_ascii=False, indent=2)

        return JSONResponse(
            content={
                "success": True,
                "message": f"规则 '{name}' 保存成功",
                "name": name,
            }
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="规则格式错误",
        )
    except Exception as e:
        logger.error(f"保存规则失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存规则失败: {str(e)}",
        )


@router.get("/rules/list")
async def list_rules() -> JSONResponse:
    """
    获取所有保存的规则列表.

    Returns:
        JSONResponse: 规则列表
    """
    try:
        rules = []
        for rule_file in RULES_DIR.glob("*.json"):
            try:
                with open(rule_file, "r", encoding="utf-8") as f:
                    rule_data = json.load(f)
                    rules.append(
                        {
                            "name": rule_file.stem,
                            "rule": rule_data,
                        }
                    )
            except Exception as e:
                logger.warning(f"读取规则文件 {rule_file} 失败: {e}")

        return JSONResponse(content={"rules": rules})
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取规则列表失败: {str(e)}",
        )


@router.get("/rules/default")
async def get_default_rule() -> JSONResponse:
    """
    获取默认规则配置.

    Returns:
        JSONResponse: 默认规则配置
    """
    try:
        rule_file = RULES_DIR / "default.json"
        if not rule_file.exists():
            return JSONResponse(content={"rule": None})

        with open(rule_file, "r", encoding="utf-8") as f:
            rule_data = json.load(f)

        return JSONResponse(content={"rule": rule_data})
    except Exception as e:
        logger.error(f"获取默认规则失败: {e}", exc_info=True)
        return JSONResponse(content={"rule": None})


@router.get("/rules/{name}")
async def get_rule(name: str) -> JSONResponse:
    """
    获取指定的规则配置.

    Args:
        name: 规则名称

    Returns:
        JSONResponse: 规则配置
    """
    try:
        rule_file = RULES_DIR / f"{name}.json"
        if not rule_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则 '{name}' 不存在",
            )

        with open(rule_file, "r", encoding="utf-8") as f:
            rule_data = json.load(f)

        return JSONResponse(content={"name": name, "rule": rule_data})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取规则失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取规则失败: {str(e)}",
        )


@router.delete("/rules/{name}")
async def delete_rule(name: str) -> JSONResponse:
    """
    删除指定的规则配置.

    Args:
        name: 规则名称

    Returns:
        JSONResponse: 删除结果
    """
    try:
        rule_file = RULES_DIR / f"{name}.json"
        if not rule_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则 '{name}' 不存在",
            )

        rule_file.unlink()

        return JSONResponse(
            content={
                "success": True,
                "message": f"规则 '{name}' 删除成功",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除规则失败: {str(e)}",
        )


@router.post("/preview")
async def preview_excel(
    file: UploadFile = File(...),
    rows: int = Form(10),
) -> JSONResponse:
    """
    预览 Excel 文件（返回前 N 行）.

    Args:
        file: 上传的 Excel 文件
        rows: 返回的行数，默认 10 行

    Returns:
        JSONResponse: 预览数据

    Raises:
        HTTPException: 如果文件格式不正确
    """
    try:
        df = ExcelService.parse_excel(file)

        # 获取前 N 行
        preview_df = df.head(rows)

        # 转换为字典列表
        data = preview_df.to_dict(orient="records")

        # 处理 NaN 值
        for row in data:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (int, float)):
                    row[key] = float(value)

        return JSONResponse(
            content={
                "columns": ExcelService.get_column_names(df),
                "data": data,
                "total_rows": len(df),
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"预览 Excel 文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}",
        )


@router.get("/history/records", response_model=List[AnalysisRecordSummary])
async def get_analysis_records(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[AnalysisRecordSummary]:
    """
    获取历史分析记录列表.

    Args:
        limit: 返回记录数，默认 50
        offset: 偏移量，默认 0
        db: 数据库会话

    Returns:
        List[AnalysisRecordSummary]: 分析记录列表
    """
    try:
        records = (
            db.query(ExcelAnalysisRecord)
            .order_by(ExcelAnalysisRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            AnalysisRecordSummary(
                id=record.id,  # type: ignore[arg-type]
                file_name=record.file_name,
                total_rows=record.total_rows,
                matched_count=record.matched_count,
                days=record.days,
                created_at=record.created_at.isoformat(),
            )  # type: ignore
            for record in records
        ]
    except Exception as e:
        logger.error(f"获取分析记录列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析记录列表失败: {str(e)}",
        )


@router.get("/history/records/{record_id}", response_model=ExcelAnalysisResponse)
async def get_analysis_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
) -> ExcelAnalysisResponse:
    """
    获取指定分析记录的详细信息.

    Args:
        record_id: 分析记录ID
        db: 数据库会话

    Returns:
        ExcelAnalysisResponse: 分析结果
    """
    try:
        ensure_latest_revenue_column(db)

        record = db.query(ExcelAnalysisRecord).filter(ExcelAnalysisRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分析记录 {record_id} 不存在",
            )

        # 获取该记录的所有链接历史
        link_histories = (
            db.query(ExcelLinkHistory)
            .filter(ExcelLinkHistory.analysis_record_id == record_id)
            .all()
        )

        links = []
        for link_history in link_histories:
            links.append(
                LinkData(
                    link=link_history.link,
                    ctr=float(link_history.ctr) if link_history.ctr else None,
                    revenue=float(link_history.revenue) if link_history.revenue else None,
                    latest_revenue=float(link_history.latest_revenue)
                    if link_history.latest_revenue
                    else None,
                    data=link_history.data or {},
                    matched_groups=link_history.matched_groups or [],
                    matched_rules=link_history.matched_rules or [],
                )
            )

        columns = record.columns or []
        if "最新收入" not in columns:
            columns = columns + ["最新收入"]

        return ExcelAnalysisResponse(
            total_rows=record.total_rows,
            matched_count=record.matched_count,
            links=links,
            columns=columns,
            rule_fields=record.rule_fields or [],
            record_id=record.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析记录详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析记录详情失败: {str(e)}",
        )


@router.get("/history/link/{link:path}", response_model=LinkChangeTrend)
async def get_link_change_trend(
    link: str,
    db: Session = Depends(get_db),
) -> LinkChangeTrend:
    """
    获取指定链接的变化趋势.

    Args:
        link: 链接地址
        db: 数据库会话

    Returns:
        LinkChangeTrend: 链接变化趋势
    """
    try:
        ensure_latest_revenue_column(db)

        # 获取该链接的所有历史记录
        link_histories = (
            db.query(ExcelLinkHistory, ExcelAnalysisRecord)
            .join(
                ExcelAnalysisRecord, ExcelLinkHistory.analysis_record_id == ExcelAnalysisRecord.id
            )
            .filter(ExcelLinkHistory.link == link)
            .order_by(ExcelLinkHistory.created_at.asc())
            .all()
        )

        if not link_histories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"链接 '{link}' 没有历史记录",
            )

        # 转换为 LinkHistoryItem
        history_items = []
        ctr_changes = []
        revenue_changes = []

        for link_history, analysis_record in link_histories:
            ctr = float(link_history.ctr) if link_history.ctr else None
            revenue = float(link_history.revenue) if link_history.revenue else None
            latest_revenue = (
                float(link_history.latest_revenue) if link_history.latest_revenue else None
            )

            history_items.append(
                LinkHistoryItem(
                    id=link_history.id,
                    analysis_record_id=link_history.analysis_record_id,
                    link=link_history.link,
                    ctr=ctr,
                    revenue=revenue,
                    latest_revenue=latest_revenue,
                    data=link_history.data or {},
                    matched_groups=link_history.matched_groups or [],
                    matched_rules=link_history.matched_rules or [],
                    created_at=link_history.created_at.isoformat(),
                    file_name=analysis_record.file_name,
                )
            )
            ctr_changes.append(ctr)
            revenue_changes.append(revenue)

        first_seen = history_items[0].created_at
        last_seen = history_items[-1].created_at

        return LinkChangeTrend(
            link=link,
            records=history_items,
            ctr_changes=ctr_changes,
            revenue_changes=revenue_changes,
            first_seen=first_seen,
            last_seen=last_seen,
            appearance_count=len(history_items),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取链接变化趋势失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取链接变化趋势失败: {str(e)}",
        )


@router.get("/history/links", response_model=List[str])
async def get_all_links(
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[str]:
    """
    获取所有出现过的链接列表.

    Args:
        limit: 返回链接数，默认 100
        db: 数据库会话

    Returns:
        List[str]: 链接列表
    """
    try:
        links = db.query(ExcelLinkHistory.link).distinct().limit(limit).all()
        return [link[0] for link in links]
    except Exception as e:
        logger.error(f"获取链接列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取链接列表失败: {str(e)}",
        )
