"""Excel 分析相关的 API 路由."""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.apps.excel.schemas import ExcelAnalysisRequest, ExcelAnalysisResponse, FilterRule, LinkData
from app.apps.excel.service import ExcelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/excel", tags=["excel"])

# Excel 规则配置文件目录
RULES_DIR = Path("data/excel_rules")
RULES_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze", response_model=ExcelAnalysisResponse)
async def analyze_excel(
    file: UploadFile = File(...),
    rule: str = Form('{"conditions": [], "logic": "or"}'),
    days: int = Form(7),
) -> ExcelAnalysisResponse:
    """
    分析 Excel 文件，根据规则筛选链接.

    Args:
        file: 上传的 Excel 文件
        rule: 筛选规则 JSON 字符串
        days: 查看近几日的均值，默认 7 天

    Returns:
        ExcelAnalysisResponse: 分析结果

    Raises:
        HTTPException: 如果文件格式不正确或处理失败
    """
    try:
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

        # 计算近几日均值
        df_avg = ExcelService.calculate_recent_days_average(df, days=days)

        # 应用筛选规则
        df_filtered, matched_info = ExcelService.apply_filter_rule(df_avg, filter_rule)

        # 转换为链接数据
        links = ExcelService.convert_to_link_data(df_filtered, matched_info, filter_rule)

        # 对结果进行排序：优先按 CTR 降序，如果 CTR 为空则按收入降序
        # 使用负无穷大作为空值的排序键，确保空值排在最后
        links.sort(
            key=lambda x: (
                x.ctr if x.ctr is not None else float('-inf'),
                x.revenue if x.revenue is not None else float('-inf'),
            ),
            reverse=True,
        )

        # 获取列名
        columns = ExcelService.get_column_names(df)
        
        # 收集所有规则中使用的字段（用于前端显示）
        rule_fields = set()
        for group in filter_rule.groups:
            for condition in group.conditions:
                rule_fields.add(condition.field)
        rule_fields_list = sorted(list(rule_fields))

        return ExcelAnalysisResponse(
            total_rows=len(df),
            matched_count=len(df_filtered),
            links=links,
            columns=columns,
            rule_fields=rule_fields_list,
        )
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
    file: UploadFile = File(...),
    link: str = Form(...),
    days: int = Form(7),
) -> JSONResponse:
    """
    获取链接的详细数据.

    Args:
        file: 上传的 Excel 文件
        link: 链接地址
        days: 查看近几日的均值，默认 7 天

    Returns:
        JSONResponse: 链接的详细数据
    """
    try:
        # 重置文件指针（如果可能）
        if hasattr(file.file, 'seek'):
            try:
                file.file.seek(0)
            except Exception:
                pass
        
        df = ExcelService.parse_excel(file)

        # 查找链接列（使用原始数据，不是均值数据）
        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            raise ValueError("未找到链接列")

        # 筛选出该链接的所有原始数据（不计算均值，显示详细数据）
        link_data = df[df[link_column] == link]

        if len(link_data) == 0:
            raise ValueError(f"未找到链接 {link} 的数据")

        # 转换为字典列表
        data = link_data.to_dict(orient="records")

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

