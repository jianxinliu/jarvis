"""Excel 文件处理服务."""

import logging
from typing import Any, Optional

import pandas as pd
from fastapi import UploadFile

from app.apps.excel.schemas import FilterRule, LinkData, RuleCondition, RuleGroup

logger = logging.getLogger(__name__)


class ExcelService:
    """Excel 处理服务类."""

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
                    # 先移除可能的百分号和逗号
                    if df[col].dtype == "object":
                        # 尝试直接转换
                        converted = pd.to_numeric(df[col], errors="coerce")
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
                # 先尝试直接转换
                converted = pd.to_numeric(df_processed[col], errors="coerce")
                # 如果转换成功（非空值比例 > 50%），使用转换后的值
                if converted.notna().sum() / len(df_processed) > 0.5:
                    df_processed[col] = converted
                else:
                    # 尝试处理百分比格式（如 "4.5%"）
                    if df_processed[col].dtype == "object":
                        # 移除百分号并转换为数值
                        df_processed[col] = (
                            df_processed[col]
                            .astype(str)
                            .str.replace("%", "", regex=False)
                            .str.replace(",", "", regex=False)
                            .str.strip()
                        )
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
                # 如果是字符串类型，先尝试清理（移除百分号、逗号等）
                if column.dtype == "object":
                    # 移除百分号和逗号
                    column_clean = (
                        column.astype(str)
                        .str.replace("%", "", regex=False)
                        .str.replace(",", "", regex=False)
                        .str.strip()
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
    def convert_to_link_data(
        df: pd.DataFrame,
        matched_info: Optional[pd.DataFrame] = None,
        filter_rule: Optional[FilterRule] = None,
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
                                val_clean = str(val).replace("%", "").replace(",", "").strip()
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

                if "收入" in col_str or "revenue" in col_lower or "收益" in col_str:
                    val = data.get(col)
                    if val is not None and pd.notna(val):
                        try:
                            # 尝试转换为数值
                            if isinstance(val, str):
                                # 处理字符串格式（如 "300.5", "300,000"）
                                val_clean = str(val).replace(",", "").strip()
                                revenue = float(val_clean)
                            else:
                                revenue = float(val)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"无法转换收入值 {val} (列: {col}): {e}")
                            revenue = None

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
                                    val_clean = str(val).replace("%", "").replace(",", "").strip()
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

            # 将规则字段值添加到 data 中
            data_with_rule_fields = {**data, **rule_field_values}

            result.append(
                LinkData(
                    link=link,
                    ctr=float(ctr) if ctr is not None and pd.notna(ctr) else None,
                    revenue=float(revenue) if revenue is not None and pd.notna(revenue) else None,
                    data={k: float(v) if pd.api.types.is_number(v) else str(v) for k, v in data_with_rule_fields.items() if pd.notna(v)},
                    matched_groups=matched_groups,
                    matched_rules=matched_rules,
                )
            )

        return result

