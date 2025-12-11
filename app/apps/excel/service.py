"""Excel 文件处理服务."""

import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

import pandas as pd
from fastapi import UploadFile

from app.apps.excel.schemas import FilterRule, LinkData, RuleCondition, RuleGroup

logger = logging.getLogger(__name__)


class ExcelService:
    """Excel 处理服务类."""

    @staticmethod
    def _clean_thousands_separator(value: Any) -> str:
        """
        清理千位标记法中的分隔符（支持逗号和点号）.
        
        支持的格式：
        - 英文格式：1,000,000 或 1,000,000.50
        - 欧洲格式：1.000.000 或 1.000.000,50（点号作为千位分隔符，逗号作为小数分隔符）
        
        Args:
            value: 需要清理的值
            
        Returns:
            str: 清理后的字符串
        """
        if pd.isna(value) or value is None:
            return ""
        
        value_str = str(value).strip()
        
        # 如果为空，直接返回
        if not value_str:
            return value_str
        
        # 处理逗号分隔符（如 1,000,000 或 1,000,000.50）
        if "," in value_str:
            # 检查是否符合千位分隔符模式：逗号后面是3位数字
            # 匹配模式：数字，逗号，3位数字（可能重复），可选的小数部分
            if re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', value_str):
                value_str = value_str.replace(",", "")
        
        # 处理点号分隔符（如 1.000.000 或 1.000.000,50）
        # 需要小心处理，因为点号也可能是小数分隔符
        if "." in value_str:
            parts = value_str.split(".")
            if len(parts) > 2:
                # 有多个点号，检查是否符合千位分隔符模式
                # 除了最后一部分，其他部分都应该是3位数字
                is_thousands = True
                for part in parts[:-1]:
                    if len(part) != 3 or not part.isdigit():
                        is_thousands = False
                        break
                
                if is_thousands:
                    # 是千位分隔符，移除所有点号（除了最后一个，如果最后一部分是小数）
                    # 如果最后一部分也是3位数字，则所有点号都是千位分隔符
                    if len(parts[-1]) == 3 and parts[-1].isdigit():
                        # 所有点号都是千位分隔符
                        value_str = value_str.replace(".", "")
                    else:
                        # 最后一个点号可能是小数分隔符，只移除前面的点号
                        value_str = "".join(parts[:-1]) + "." + parts[-1]
        
        return value_str

    @staticmethod
    def parse_excel(file: UploadFile) -> pd.DataFrame:
        """
        解析 Excel 文件.

        Args:
            file: 上传的文件

        Returns:
            pd.DataFrame: 解析后的数据框

        Raises:
            ValueError: 如果文件格式不正确
        """
        try:
            # 读取 Excel 文件
            # 需要将文件内容读取到内存
            # 重置文件指针（如果可能）
            if hasattr(file.file, 'seek'):
                try:
                    file.file.seek(0)
                except Exception:
                    pass
            contents = file.file.read()
            import io

            # 读取 Excel，先全部读为字符串，后续再转换
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl", dtype=str)

            # 尝试将数值列转换为数值类型
            for col in df.columns:
                # 跳过明显是文本的列（包含链接、日期等）
                col_lower = str(col).lower()
                col_str = str(col)
                if "链接" in col_str or "url" in col_lower or "link" in col_lower:
                    continue

                # 尝试转换为数值
                try:
                    if df[col].dtype == "object":
                        # 先清理千位标记和百分号
                        cleaned = df[col].astype(str).apply(
                            lambda x: ExcelService._clean_thousands_separator(x).replace("%", "").strip()
                        )
                        # 尝试转换为数值
                        converted = pd.to_numeric(cleaned, errors="coerce")
                        # 如果转换成功（非空值比例 > 50%），使用转换后的值
                        if len(df) > 0 and converted.notna().sum() / len(df) > 0.5:
                            df[col] = converted
                except Exception:
                    # 转换失败，保持字符串类型
                    pass

            logger.info(f"成功解析 Excel 文件，共 {len(df)} 行，{len(df.columns)} 列")
            return df
        except Exception as e:
            logger.error(f"解析 Excel 文件失败: {e}", exc_info=True)
            raise ValueError(f"解析 Excel 文件失败: {str(e)}")

    @staticmethod
    def get_column_names(df: pd.DataFrame) -> list[str]:
        """
        获取列名列表.

        Args:
            df: 数据框

        Returns:
            list[str]: 列名列表
        """
        return df.columns.tolist()

    @staticmethod
    def check_link_data_status(
        df: pd.DataFrame, date_column: Optional[str] = None
    ) -> tuple[list[str], list[str], pd.DataFrame]:
        """
        检查链接的数据状态：昨天无数据、昨天和今天都无数据（下线）.

        Args:
            df: 数据框
            date_column: 日期列名，如果为 None 则尝试自动识别

        Returns:
            tuple[list[str], list[str], pd.DataFrame]: (昨天无数据的链接列表, 下线的链接列表, 正常数据框)
        """
        # 尝试自动识别日期列
        if date_column is None:
            date_columns = df.select_dtypes(include=["datetime64"]).columns.tolist()
            if date_columns:
                date_column = date_columns[0]
            else:
                for col in df.columns:
                    if "日期" in str(col) or "date" in str(col).lower():
                        date_column = col
                        try:
                            df[date_column] = pd.to_datetime(df[date_column])
                        except Exception:
                            pass
                        break

        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            return [], [], df

        if not date_column or date_column not in df.columns:
            # 没有日期列，无法判断，返回所有数据
            return [], [], df

        # 转换日期列
        df[date_column] = pd.to_datetime(df[date_column])
        
        # 获取所有唯一链接
        all_links = df[link_column].unique()
        
        # 获取最新日期和昨天日期（只保留日期部分，忽略时间）
        latest_date = df[date_column].max()
        if pd.isna(latest_date):
            # 如果没有有效日期，返回所有数据
            return [], [], df
        
        # 转换为日期（只保留年月日）
        if hasattr(latest_date, 'date'):
            latest_date_only = latest_date.date()
        elif hasattr(latest_date, 'normalize'):
            latest_date_only = latest_date.normalize().date()
        else:
            latest_date_only = pd.Timestamp(latest_date).date()
        
        yesterday_date_only = (pd.Timestamp(latest_date_only) - pd.Timedelta(days=1)).date()
        
        # 转换数据框中的日期为日期部分
        df['_date_only'] = df[date_column].apply(
            lambda x: x.date() if hasattr(x, 'date') and pd.notna(x) 
            else (x.normalize().date() if hasattr(x, 'normalize') and pd.notna(x) 
                  else pd.Timestamp(x).date() if pd.notna(x) else None)
        )
        
        # 检查每个链接的数据状态
        no_yesterday_links = []
        offline_links = []
        normal_links = []
        
        for link in all_links:
            link_data = df[df[link_column] == link]
            # 过滤掉 None 值
            link_dates = [d for d in link_data['_date_only'].unique() if d is not None]
            
            has_yesterday = yesterday_date_only in link_dates
            has_today = latest_date_only in link_dates
            
            if not has_yesterday and not has_today:
                # 昨天和今天都没有数据，标记为下线
                offline_links.append(link)
            elif not has_yesterday:
                # 只有昨天没有数据
                no_yesterday_links.append(link)
            else:
                # 正常数据
                normal_links.append(link)
        
        # 清理临时列
        df = df.drop(columns=['_date_only'])
        
        # 返回正常数据（排除昨天无数据和下线的链接）
        normal_df = df[df[link_column].isin(normal_links)].copy()
        
        return no_yesterday_links, offline_links, normal_df

    @staticmethod
    def get_latest_day_data(
        df: pd.DataFrame, date_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取最新一天的数据（按链接分组，每个链接只保留最新一天的数据）.

        Args:
            df: 数据框
            date_column: 日期列名，如果为 None 则尝试自动识别

        Returns:
            pd.DataFrame: 最新一天的数据框
        """
        # 尝试自动识别日期列
        if date_column is None:
            date_columns = df.select_dtypes(include=["datetime64"]).columns.tolist()
            if date_columns:
                date_column = date_columns[0]
            else:
                for col in df.columns:
                    if "日期" in str(col) or "date" in str(col).lower():
                        date_column = col
                        try:
                            df[date_column] = pd.to_datetime(df[date_column])
                        except Exception:
                            pass
                        break

        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            return df

        if not date_column or date_column not in df.columns:
            # 没有日期列，返回所有数据
            return df

        # 转换日期列
        df[date_column] = pd.to_datetime(df[date_column])
        
        # 按链接分组，获取每个链接的最新一天数据
        latest_data = df.loc[df.groupby(link_column)[date_column].idxmax()].copy()
        
        return latest_data

    @staticmethod
    def calculate_recent_days_average(
        df: pd.DataFrame, days: int = 7, date_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        计算近几日的均值.

        Args:
            df: 数据框
            days: 近几日，默认 7 天
            date_column: 日期列名，如果为 None 则尝试自动识别

        Returns:
            pd.DataFrame: 包含均值的聚合数据框
        """
        # 尝试自动识别日期列
        if date_column is None:
            date_columns = df.select_dtypes(include=["datetime64"]).columns.tolist()
            if date_columns:
                date_column = date_columns[0]
            else:
                # 尝试识别包含"日期"或"date"的列
                for col in df.columns:
                    if "日期" in str(col) or "date" in str(col).lower():
                        date_column = col
                        # 尝试转换为日期类型
                        try:
                            df[date_column] = pd.to_datetime(df[date_column])
                        except Exception:
                            pass
                        break

        if date_column and date_column in df.columns:
            # 按日期筛选最近 N 天
            df[date_column] = pd.to_datetime(df[date_column])
            latest_date = df[date_column].max()
            cutoff_date = latest_date - pd.Timedelta(days=days)
            df_filtered = df[df[date_column] >= cutoff_date].copy()
        else:
            # 如果没有日期列，使用所有数据
            df_filtered = df.copy()
            logger.warning("未找到日期列，使用所有数据进行计算")

        # 按链接分组，计算数值列的均值
        link_column = ExcelService._find_link_column(df_filtered)
        if link_column is None:
            raise ValueError("未找到链接列，请确保 Excel 中包含链接信息")

        # 创建数据框副本用于处理
        df_processed = df_filtered.copy()

        # 尝试将可能的数值列转换为数值类型
        for col in df_processed.columns:
            if col == link_column or (date_column and col == date_column):
                continue

            # 如果已经是数值类型，跳过
            if pd.api.types.is_numeric_dtype(df_processed[col]):
                continue

            # 尝试转换为数值类型
            try:
                if df_processed[col].dtype == "object":
                    # 先清理千位标记和百分号
                    cleaned = df_processed[col].astype(str).apply(
                        lambda x: ExcelService._clean_thousands_separator(x).replace("%", "").strip()
                    )
                    # 尝试转换为数值
                    converted = pd.to_numeric(cleaned, errors="coerce")
                    # 如果转换成功（非空值比例 > 50%），使用转换后的值
                    if converted.notna().sum() / len(df_processed) > 0.5:
                        df_processed[col] = converted
                else:
                    # 已经是数值类型，直接转换
                    converted = pd.to_numeric(df_processed[col], errors="coerce")
                    if converted.notna().sum() / len(df_processed) > 0.5:
                        df_processed[col] = converted
            except Exception:
                # 转换失败，保持原样
                logger.debug(f"无法将列 {col} 转换为数值类型")
                pass

        # 数值列（排除链接列和日期列）
        numeric_columns = df_processed.select_dtypes(include=["number"]).columns.tolist()
        if date_column and date_column in numeric_columns:
            numeric_columns.remove(date_column)
        if link_column in numeric_columns:
            numeric_columns.remove(link_column)

        # 按链接分组并计算均值
        group_columns = [link_column]
        agg_dict = {col: "mean" for col in numeric_columns}

        if numeric_columns:
            result = df_processed.groupby(group_columns, as_index=False).agg(agg_dict)
        else:
            # 如果没有数值列，只返回链接
            result = df_processed[[link_column]].drop_duplicates()

        return result

    @staticmethod
    def _find_link_column(df: pd.DataFrame) -> Optional[str]:
        """
        查找链接列.

        Args:
            df: 数据框

        Returns:
            Optional[str]: 链接列名，如果未找到返回 None
        """
        # 尝试识别包含"链接"、"url"、"link"的列
        for col in df.columns:
            col_lower = str(col).lower()
            if "链接" in str(col) or "url" in col_lower or "link" in col_lower:
                return col

        # 如果没找到，返回第一列
        if len(df.columns) > 0:
            return df.columns[0]

        return None

    @staticmethod
    def extract_domain(link: str) -> str:
        """
        从链接中提取主域名.

        Args:
            link: 链接地址

        Returns:
            str: 主域名，如果解析失败返回空字符串
        """
        try:
            # 如果没有协议，添加 http:// 以便解析
            if not link.startswith(('http://', 'https://')):
                link = 'http://' + link
            
            parsed = urlparse(link)
            hostname = parsed.hostname or ''
            
            # 提取主域名（去掉 www. 前缀，取最后两部分）
            if not hostname:
                return link
            
            # 去掉 www. 前缀
            if hostname.startswith('www.'):
                hostname = hostname[4:]
            
            # 分割域名部分
            parts = hostname.split('.')
            if len(parts) >= 2:
                # 返回最后两部分（主域名）
                return '.'.join(parts[-2:])
            else:
                return hostname
        except Exception as e:
            logger.debug(f"提取域名失败: {link}, 错误: {e}")
            return link

    @staticmethod
    def apply_filter_rule(
        df: pd.DataFrame, rule: FilterRule
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        应用筛选规则（支持原子化逻辑关系）.

        Args:
            df: 数据框
            rule: 筛选规则

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: (符合规则的数据框, 每个链接满足的规则组信息)
        """
        if len(rule.groups) == 0:
            # 返回空的结果和空的匹配信息
            matched_info = pd.DataFrame(index=df.index)
            return df, matched_info

        # 为每个规则组计算布尔掩码
        group_masks = []
        for group in rule.groups:
            if len(group.conditions) == 0:
                continue

            # 为组内每个条件创建布尔掩码
            condition_masks = []
            for condition in group.conditions:
                mask = ExcelService._evaluate_condition(df, condition)
                condition_masks.append(mask)

            # 根据组内逻辑关系组合掩码
            if len(condition_masks) == 0:
                continue

            if group.logic.lower() == "and":
                group_mask = condition_masks[0]
                for mask in condition_masks[1:]:
                    group_mask = group_mask & mask
            else:  # or
                group_mask = condition_masks[0]
                for mask in condition_masks[1:]:
                    group_mask = group_mask | mask

            group_masks.append(group_mask)

        if len(group_masks) == 0:
            matched_info = pd.DataFrame(index=df.index)
            return df, matched_info

        # 创建匹配信息数据框：记录每行满足哪些规则组和具体条件
        matched_info = pd.DataFrame(index=df.index)
        for i, group_mask in enumerate(group_masks):
            matched_info[f"group_{i}"] = group_mask
            
            # 记录每个条件是否满足（用于生成具体规则描述）
            group = rule.groups[i]
            for j, condition in enumerate(group.conditions):
                condition_mask = ExcelService._evaluate_condition(df, condition)
                matched_info[f"group_{i}_condition_{j}"] = condition_mask

        # 根据组间逻辑关系组合掩码
        if rule.logic.lower() == "and":
            final_mask = group_masks[0]
            for mask in group_masks[1:]:
                final_mask = final_mask & mask
        else:  # or
            final_mask = group_masks[0]
            for mask in group_masks[1:]:
                final_mask = final_mask | mask

        return df[final_mask].copy(), matched_info[final_mask].copy()

    @staticmethod
    def _evaluate_condition(df: pd.DataFrame, condition: RuleCondition) -> pd.Series:
        """
        评估单个条件.

        Args:
            df: 数据框
            condition: 规则条件

        Returns:
            pd.Series: 布尔掩码
        """
        if condition.field not in df.columns:
            logger.warning(f"字段 {condition.field} 不存在于数据中")
            return pd.Series([False] * len(df), index=df.index)

        column = df[condition.field]

        # 确保是数值类型
        if not pd.api.types.is_numeric_dtype(column):
            try:
                # 如果是字符串类型，先尝试清理（移除百分号、千位标记等）
                if column.dtype == "object":
                    # 清理千位标记和百分号
                    column_clean = column.astype(str).apply(
                        lambda x: ExcelService._clean_thousands_separator(x).replace("%", "").strip()
                    )
                    column = pd.to_numeric(column_clean, errors="coerce")
                else:
                    column = pd.to_numeric(column, errors="coerce")
            except Exception as e:
                logger.warning(f"无法将字段 {condition.field} 转换为数值类型: {e}")
                return pd.Series([False] * len(df), index=df.index)

        # 处理百分比字段（如 CTR）
        # CTR 通常以百分比形式存储（如 4.5 表示 4.5%）
        # 如果字段名包含 ctr 或点击率，直接使用原值
        condition_value = condition.value

        # 应用操作符
        operator = condition.operator.lower()
        if operator == ">":
            return column > condition_value
        elif operator == ">=":
            return column >= condition_value
        elif operator == "<":
            return column < condition_value
        elif operator == "<=":
            return column <= condition_value
        elif operator == "==" or operator == "=":
            return column == condition_value
        elif operator == "!=" or operator == "<>":
            return column != condition_value
        else:
            logger.warning(f"不支持的操作符: {operator}")
            return pd.Series([False] * len(df), index=df.index)

    @staticmethod
    def _extract_revenue_value(row: pd.Series, columns: list[str]) -> Optional[float]:
        """从一行数据中提取收入值."""
        for col in columns:
            col_lower = str(col).lower()
            col_str = str(col)
            if "收入" in col_str or "revenue" in col_lower or "收益" in col_str:
                val = row.get(col)
                if val is not None and pd.notna(val):
                    try:
                        if isinstance(val, str):
                            val_clean = ExcelService._clean_thousands_separator(val).strip()
                            return float(val_clean)
                        return float(val)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"无法转换收入值 {val} (列: {col}): {e}")
                        return None
        return None

    @staticmethod
    def build_latest_revenue_map(df: pd.DataFrame) -> dict[str, float]:
        """构建链接 -> 最新收入的映射."""
        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            return {}

        revenue_map: dict[str, float] = {}
        for _, row in df.iterrows():
            link = str(row[link_column])
            revenue = ExcelService._extract_revenue_value(row, df.columns.tolist())
            if revenue is not None:
                revenue_map[link] = revenue
        return revenue_map

    @staticmethod
    def convert_to_link_data(
        df: pd.DataFrame,
        matched_info: Optional[pd.DataFrame] = None,
        filter_rule: Optional[FilterRule] = None,
        is_latest_data_match: bool = False,
        latest_revenue_map: Optional[dict[str, float]] = None,
    ) -> list[LinkData]:
        """
        将数据框转换为链接数据列表.

        Args:
            df: 数据框

        Returns:
            list[LinkData]: 链接数据列表
        """
        link_column = ExcelService._find_link_column(df)
        if link_column is None:
            return []

        latest_revenue_map = latest_revenue_map or {}

        # 收集所有规则中使用的字段（用于在结果中显示）
        rule_fields = set()
        if filter_rule:
            for group in filter_rule.groups:
                for condition in group.conditions:
                    rule_fields.add(condition.field)

        result = []
        for idx, row in df.iterrows():
            link = str(row[link_column])
            data = row.to_dict()

            # 获取该链接满足的规则组和具体满足的条件（带优先级）
            matched_groups = []
            satisfied_conditions_with_priority = []  # 收集所有满足的条件及其优先级
            if matched_info is not None and idx in matched_info.index and filter_rule:
                # 遍历所有规则组
                for group_idx in range(len(filter_rule.groups)):
                    group_col = f"group_{group_idx}"
                    if group_col in matched_info.columns and matched_info.loc[idx, group_col]:
                        matched_groups.append(group_idx)
                        
                        # 收集该规则组中满足的条件
                        if group_idx < len(filter_rule.groups):
                            group = filter_rule.groups[group_idx]
                            group_priority = getattr(group, "priority", 0)
                            
                            # 检查每个条件是否满足
                            for cond_idx, condition in enumerate(group.conditions):
                                condition_col = f"group_{group_idx}_condition_{cond_idx}"
                                if condition_col in matched_info.columns:
                                    if matched_info.loc[idx, condition_col]:
                                        operator_symbol = {
                                            ">": ">",
                                            ">=": "≥",
                                            "<": "<",
                                            "<=": "≤",
                                            "==": "=",
                                            "=": "=",
                                            "!=": "≠",
                                        }.get(condition.operator, condition.operator)
                                        
                                        # 格式化值显示
                                        value_str = str(condition.value)
                                        if condition.field.lower() in ["ctr", "点击率"]:
                                            value_str = f"{condition.value}%"
                                        
                                        condition_desc = f"{condition.field} {operator_symbol} {value_str}"
                                        
                                        # 获取条件的优先级（优先使用条件优先级，否则使用规则组优先级）
                                        condition_priority = getattr(condition, "priority", group_priority)
                                        
                                        # 检查是否已存在相同的条件描述
                                        existing = next(
                                            (item for item in satisfied_conditions_with_priority if item["desc"] == condition_desc),
                                            None,
                                        )
                                        if not existing:
                                            satisfied_conditions_with_priority.append(
                                                {
                                                    "desc": condition_desc,
                                                    "priority": condition_priority,
                                                    "group_idx": group_idx,
                                                    "cond_idx": cond_idx,
                                                }
                                            )
            
            # 按优先级排序（数字越小优先级越高），优先级相同时按规则组和条件索引排序
            satisfied_conditions_with_priority.sort(key=lambda x: (x["priority"], x["group_idx"], x["cond_idx"]))
            
            # 生成规则描述：合并所有满足的条件，使用 & 连接
            matched_rules = []
            if satisfied_conditions_with_priority:
                # 提取条件描述并按优先级排序后的顺序连接
                all_satisfied_conditions = [item["desc"] for item in satisfied_conditions_with_priority]
                # 使用 " & " 连接所有满足的条件
                rule_desc = " & ".join(all_satisfied_conditions)
                matched_rules.append(rule_desc)

            # 提取 CTR 和收入
            ctr = None
            revenue = None
            latest_revenue = latest_revenue_map.get(link)

            for col in df.columns:
                col_lower = str(col).lower()
                col_str = str(col)
                if "ctr" in col_lower or "点击率" in col_str:
                    val = data.get(col)
                    if val is not None and pd.notna(val):
                        try:
                            # 尝试转换为数值
                            if isinstance(val, str):
                                # 处理字符串格式（如 "4.5%", "4.5", "0.045"）
                                val_clean = ExcelService._clean_thousands_separator(val).replace("%", "").strip()
                                ctr_val = float(val_clean)
                            else:
                                ctr_val = float(val)

                            # CTR 可能是小数形式（0.045）或百分比形式（4.5）
                            # 如果值小于 1，认为是小数形式，需要转换为百分比
                            if ctr_val < 1:
                                ctr = ctr_val * 100
                            else:
                                ctr = ctr_val
                        except (ValueError, TypeError) as e:
                            logger.warning(f"无法转换 CTR 值 {val} (列: {col}): {e}")
                            ctr = None

                if revenue is None:
                    revenue = ExcelService._extract_revenue_value(row, [col])

            # 提取规则中使用的所有字段的值
            rule_field_values = {}
            for field in rule_fields:
                # 在数据中查找匹配的列
                found = False
                for col in df.columns:
                    col_str = str(col)
                    # 精确匹配字段名，或字段名包含在列名中
                    if field == col_str or field.lower() in col_str.lower() or col_str.lower() in field.lower():
                        val = data.get(col)
                        if val is not None and pd.notna(val):
                            try:
                                # 尝试转换为数值
                                if isinstance(val, str):
                                    val_clean = ExcelService._clean_thousands_separator(val).replace("%", "").strip()
                                    num_val = float(val_clean)
                                else:
                                    num_val = float(val)
                                
                                # 如果是 CTR 相关字段，处理百分比
                                if "ctr" in field.lower() or "点击率" in field or "ctr" in col_str.lower():
                                    if num_val < 1:
                                        num_val = num_val * 100
                                
                                rule_field_values[field] = num_val
                                found = True
                                break
                            except (ValueError, TypeError):
                                # 如果转换失败，使用原始值
                                rule_field_values[field] = val
                                found = True
                                break
                if not found:
                    # 如果找不到匹配的列，设置为 None
                    rule_field_values[field] = None

            # 移除链接列从 data 中
            if link_column in data:
                del data[link_column]

            # 将规则字段值添加到 data 中，并附加最新收入方便前端展示
            data_with_rule_fields = {**data, **rule_field_values}
            if latest_revenue is not None:
                # 同时提供中英文键，避免前端列名不一致
                data_with_rule_fields.setdefault("最新收入", latest_revenue)
                data_with_rule_fields.setdefault("latest_revenue", latest_revenue)

            result.append(
                LinkData(
                    link=link,
                    ctr=float(ctr) if ctr is not None and pd.notna(ctr) else None,
                    revenue=float(revenue) if revenue is not None and pd.notna(revenue) else None,
                    latest_revenue=float(latest_revenue) if latest_revenue is not None and pd.notna(latest_revenue) else None,
                    data={k: float(v) if pd.api.types.is_number(v) else str(v) for k, v in data_with_rule_fields.items() if pd.notna(v)},
                    matched_groups=matched_groups,
                    matched_rules=matched_rules,
                    is_latest_data_match=is_latest_data_match,
                )
            )

        return result

