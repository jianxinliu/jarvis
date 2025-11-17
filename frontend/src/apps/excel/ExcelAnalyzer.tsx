import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import Modal from '../../components/Modal'
import { useModal } from '../../hooks/useModal'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import type {
  ExcelAnalysisResponse,
  FilterRule,
  RuleCondition,
  RuleGroup,
  AnalysisRecordSummary,
  LinkChangeTrend,
  LinkHistoryItem,
  LinkData,
} from '../../types'
import './ExcelAnalyzer.css'

function ExcelAnalyzer() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ExcelAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(7)
  const [selectedLink, setSelectedLink] = useState<string | null>(null)
  const [linkDetails, setLinkDetails] = useState<any[] | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const modal = useModal()
  const [groups, setGroups] = useState<RuleGroup[]>([
    {
      conditions: [
        { field: 'ctr', operator: '>', value: 4, priority: 0 },
        { field: '收入', operator: '>', value: 300, priority: 1 },
        { field: '收入', operator: '<', value: 100, priority: 2 },
      ],
      logic: 'or',
      priority: 0,
    },
  ])
  const [groupLogic, setGroupLogic] = useState<'and' | 'or'>('or')
  const [savedRules, setSavedRules] = useState<Array<{ name: string; rule: FilterRule }>>([])
  const [selectedRuleName, setSelectedRuleName] = useState<string>('')
  const [ruleNameInput, setRuleNameInput] = useState<string>('')
  const [saveToDb, setSaveToDb] = useState<boolean>(false)
  const [showHistory, setShowHistory] = useState<boolean>(false)
  const [historyRecords, setHistoryRecords] = useState<AnalysisRecordSummary[]>([])
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false)
  const [linkTrend, setLinkTrend] = useState<LinkChangeTrend | null>(null)
  
  // 表格排序和列宽状态
  const [sortConfig, setSortConfig] = useState<{
    key: string | null
    direction: 'asc' | 'desc'
  }>({ key: null, direction: 'asc' })
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({})
  const tableRef = useRef<HTMLTableElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleAddGroup = () => {
    setGroups([
      ...groups,
      { conditions: [{ field: '', operator: '>', value: 0 }], logic: 'or', priority: groups.length },
    ])
  }

  const handleRemoveGroup = (groupIndex: number) => {
    setGroups(groups.filter((_, i) => i !== groupIndex))
  }

  const handleAddCondition = (groupIndex: number) => {
    const newGroups = [...groups]
    const currentGroup = newGroups[groupIndex]
    const maxPriority = Math.max(
      ...currentGroup.conditions.map((c) => c.priority ?? 0),
      currentGroup.priority ?? 0,
      0
    )
    newGroups[groupIndex].conditions.push({
      field: '',
      operator: '>',
      value: 0,
      priority: maxPriority + 1,
    })
    setGroups(newGroups)
  }

  const handleRemoveCondition = (groupIndex: number, conditionIndex: number) => {
    const newGroups = [...groups]
    newGroups[groupIndex].conditions = newGroups[groupIndex].conditions.filter(
      (_, i) => i !== conditionIndex
    )
    setGroups(newGroups)
  }

  const handleConditionChange = (
    groupIndex: number,
    conditionIndex: number,
    field: keyof RuleCondition,
    value: any
  ) => {
    const newGroups = [...groups]
    newGroups[groupIndex].conditions[conditionIndex] = {
      ...newGroups[groupIndex].conditions[conditionIndex],
      [field]: value,
    }
    setGroups(newGroups)
  }

  const handleGroupLogicChange = (groupIndex: number, logic: 'and' | 'or') => {
    const newGroups = [...groups]
    newGroups[groupIndex].logic = logic
    setGroups(newGroups)
  }

  const handlePriorityChange = (groupIndex: number, priority: number) => {
    const newGroups = [...groups]
    newGroups[groupIndex].priority = priority
    setGroups(newGroups)
  }

  // 加载保存的规则列表
  useEffect(() => {
    loadSavedRules()
    // 尝试加载默认规则
    loadDefaultRule()
  }, [])

  const loadSavedRules = async () => {
    try {
      const response = await axios.get('/api/excel/rules/list')
      setSavedRules(response.data.rules || [])
    } catch (err) {
      console.error('加载规则列表失败:', err)
    }
  }

  const loadDefaultRule = async () => {
    try {
      const response = await axios.get('/api/excel/rules/default')
      if (response.data.rule && response.data.rule.groups) {
        setGroups(response.data.rule.groups)
        setGroupLogic(response.data.rule.logic || 'or')
      }
    } catch (err) {
      // 默认规则不存在，忽略错误
    }
  }

  const handleSaveRule = async () => {
    if (!ruleNameInput.trim()) {
      setError('请输入规则名称')
      return
    }

    try {
      const rule: FilterRule = {
        groups,
        logic: groupLogic,
      }

      const formData = new FormData()
      formData.append('name', ruleNameInput.trim())
      formData.append('rule', JSON.stringify(rule))

      await axios.post('/api/excel/rules/save', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setRuleNameInput('')
      await loadSavedRules()
      // 规则保存成功，界面已更新，无需弹框提示
    } catch (err: any) {
      setError(err.response?.data?.detail || '保存规则失败')
    }
  }

  const handleLoadRule = async (name: string) => {
    try {
      const response = await axios.get(`/api/excel/rules/${name}`)
      const rule = response.data.rule
      setGroups(rule.groups || [])
      setGroupLogic(rule.logic || 'or')
      setSelectedRuleName(name)
      // 规则已加载到界面，无需弹框提示
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载规则失败')
    }
  }

  const handleDeleteRule = async (name: string) => {
    modal.showConfirm(
      `确定要删除规则 "${name}" 吗？`,
      async () => {
        try {
          await axios.delete(`/api/excel/rules/${name}`)
          await loadSavedRules()
          if (selectedRuleName === name) {
            setSelectedRuleName('')
          }
          // 规则已删除，界面已更新，无需弹框提示
        } catch (err: any) {
          setError(err.response?.data?.detail || '删除规则失败')
        }
      },
      '确认删除'
    )
  }

  const handleLinkClick = async (link: string) => {
    setSelectedLink(link)
    setLoadingDetails(true)
    setLinkDetails(null)

    try {
      const formData = new FormData()
      
      // 如果有 record_id，使用 record_id 从数据库获取
      if (result?.record_id) {
        formData.append('record_id', result.record_id.toString())
        formData.append('link', link)
        formData.append('days', days.toString())
      } else if (file) {
        // 否则使用文件对象
        formData.append('file', file)
        formData.append('link', link)
        formData.append('days', days.toString())
      } else {
        // 既没有 record_id 也没有文件对象
        setError('无法查看详情：原始文件不可用。请重新上传文件进行分析，并勾选"保存分析结果到数据库"。')
        setLoadingDetails(false)
        return
      }

      const response = await axios.post('/api/excel/link-details', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setLinkDetails(response.data.data)
      setError(null) // 清除之前的错误
    } catch (err: any) {
      console.error('获取链接详情失败:', err)
      const errorMsg = err.response?.data?.detail || '获取链接详情失败'
      setError(errorMsg)
      // 即使出错也关闭加载状态，但保持弹框打开以显示错误信息
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('请先选择文件')
      return
    }

    if (groups.length === 0) {
      setError('请至少添加一个规则组')
      return
    }

    // 验证所有条件
    for (const group of groups) {
      if (group.conditions.length === 0) {
        setError('每个规则组至少需要一个条件')
        return
      }
      for (const condition of group.conditions) {
        if (!condition.field) {
          setError('请填写所有条件的字段名')
          return
        }
      }
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const rule: FilterRule = {
        groups,
        logic: groupLogic,
      }

      formData.append('rule', JSON.stringify(rule))
      formData.append('days', days.toString())
      formData.append('save_to_db', saveToDb.toString())

      const response = await axios.post('/api/excel/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setResult(response.data)
      if (response.data.record_id) {
        // 如果历史记录面板已打开，刷新历史记录
        if (showHistory) {
          loadHistoryRecords()
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '分析失败，请检查文件格式和规则')
    } finally {
      setLoading(false)
    }
  }

  const loadHistoryRecords = async () => {
    setLoadingHistory(true)
    try {
      const response = await axios.get('/api/excel/history/records', {
        params: { limit: 50, offset: 0 },
      })
      setHistoryRecords(response.data)
    } catch (err: any) {
      console.error('加载历史记录失败:', err)
      setError(err.response?.data?.detail || '加载历史记录失败')
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleViewHistory = async () => {
    setShowHistory(true)
    await loadHistoryRecords()
  }

  const handleViewRecord = async (recordId: number) => {
    try {
      const response = await axios.get(`/api/excel/history/records/${recordId}`)
      setResult(response.data)
      setShowHistory(false)
      // 历史记录已显示在结果区域，无需弹框提示
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载历史记录失败')
    }
  }

  const handleViewLinkTrend = async (link: string) => {
    setLinkTrend(null)
    try {
      const encodedLink = encodeURIComponent(link)
      const response = await axios.get(`/api/excel/history/link/${encodedLink}`)
      setLinkTrend(response.data)
      // 趋势模态框已打开并显示数据，无需弹框提示
    } catch (err: any) {
      console.error('获取链接变化趋势失败:', err)
      setError(err.response?.data?.detail || '获取链接变化趋势失败')
    }
  }

  // 准备图表数据
  const prepareChartData = (trend: LinkChangeTrend) => {
    return trend.records.map((record) => ({
      date: new Date(record.created_at).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
      }),
      fullDate: new Date(record.created_at).toLocaleString('zh-CN'),
      ctr: record.ctr ?? null,
      revenue: record.revenue ?? null,
      fileName: record.file_name,
    }))
  }

  // 提取主域名用于排序
  const extractDomain = (link: string): string => {
    try {
      if (!link) return ''
      let url = link
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'http://' + url
      }
      const urlObj = new URL(url)
      let hostname = urlObj.hostname
      if (hostname.startsWith('www.')) {
        hostname = hostname.substring(4)
      }
      const parts = hostname.split('.')
      if (parts.length >= 2) {
        return parts.slice(-2).join('.')
      }
      return hostname
    } catch {
      return ''
    }
  }

  // 排序处理
  const handleSort = (key: string) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        }
      }
      return { key, direction: 'asc' }
    })
  }

  // 获取排序后的数据
  const getSortedLinks = (links: LinkData[]): LinkData[] => {
    if (!sortConfig.key) return links

    const sorted = [...links].sort((a, b) => {
      let aValue: any
      let bValue: any

      switch (sortConfig.key) {
        case 'link':
          aValue = extractDomain(a.link)
          bValue = extractDomain(b.link)
          break
        case 'ctr':
          aValue = a.ctr ?? -Infinity
          bValue = b.ctr ?? -Infinity
          break
        case 'revenue':
          aValue = a.revenue ?? -Infinity
          bValue = b.revenue ?? -Infinity
          break
        default:
          // 处理规则字段
          if (sortConfig.key) {
            aValue = a.data?.[sortConfig.key] ?? ''
            bValue = b.data?.[sortConfig.key] ?? ''
          } else {
            return 0
          }
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return aValue.localeCompare(bValue)
      }
      if (aValue < bValue) return -1
      if (aValue > bValue) return 1
      return 0
    })

    return sortConfig.direction === 'desc' ? sorted.reverse() : sorted
  }

  // 列宽调整处理
  const handleMouseDown = useCallback((columnKey: string, e: React.MouseEvent) => {
    e.preventDefault()

    const startX = e.clientX
    const startWidth = columnWidths[columnKey] || 150

    const handleMouseMove = (e: MouseEvent) => {
      const diff = e.clientX - startX
      const newWidth = Math.max(80, startWidth + diff)
      setColumnWidths((prev) => ({
        ...prev,
        [columnKey]: newWidth,
      }))
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [columnWidths])

  // 获取列宽
  const getColumnWidth = (columnKey: string, defaultWidth: number = 150): number => {
    return columnWidths[columnKey] || defaultWidth
  }

  // 获取排序图标
  const getSortIcon = (columnKey: string) => {
    if (sortConfig.key !== columnKey) {
      return '↕️'
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓'
  }

  return (
    <div className="excel-analyzer">
      <h2>Excel 链接分析</h2>

      <div className="analyzer-section">
        <h3>上传文件</h3>
        <div className="file-upload">
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            className="file-input"
          />
          {file && <span className="file-name">{file.name}</span>}
        </div>
      </div>

      <div className="analyzer-section">
        <h3>筛选规则（支持原子化逻辑关系）</h3>
        
        {/* 规则保存/加载区域 */}
        <div className="rule-save-load">
          <div className="rule-save">
            <input
              type="text"
              placeholder="规则名称"
              value={ruleNameInput}
              onChange={(e) => setRuleNameInput(e.target.value)}
              className="rule-name-input"
            />
            <button type="button" onClick={handleSaveRule} className="btn-save-rule">
              保存规则
            </button>
          </div>
          <div className="rule-load">
            <label>加载规则：</label>
            <select
              value={selectedRuleName}
              onChange={(e) => {
                if (e.target.value) {
                  handleLoadRule(e.target.value)
                } else {
                  setSelectedRuleName('')
                }
              }}
              className="rule-select"
            >
              <option value="">-- 选择规则 --</option>
              {savedRules.map((rule) => (
                <option key={rule.name} value={rule.name}>
                  {rule.name}
                </option>
              ))}
            </select>
            {selectedRuleName && (
              <button
                type="button"
                onClick={() => handleDeleteRule(selectedRuleName)}
                className="btn-delete-rule"
              >
                删除
              </button>
            )}
          </div>
        </div>

        <div className="rule-config">
          <div className="group-logic-selector">
            <label>组间逻辑关系：</label>
            <select
              value={groupLogic}
              onChange={(e) => setGroupLogic(e.target.value as 'and' | 'or')}
            >
              <option value="or">或 (OR)</option>
              <option value="and">且 (AND)</option>
            </select>
            <span className="logic-hint">
              （规则组之间使用 {groupLogic === 'or' ? 'OR' : 'AND'} 连接）
            </span>
          </div>

          <div className="groups-list">
            {groups.map((group, groupIndex) => (
              <div key={groupIndex} className="rule-group">
                <div className="group-header">
                  <div className="group-title">
                    <span className="group-number">规则组 {groupIndex + 1}</span>
                    <span className="group-logic-badge">
                      {group.logic === 'or' ? 'OR' : 'AND'}
                    </span>
                  </div>
                  {groups.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveGroup(groupIndex)}
                      className="btn-remove-group"
                    >
                      删除组
                    </button>
                  )}
                </div>

                <div className="group-settings">
                  <div className="group-logic-selector-inline">
                    <label>组内逻辑：</label>
                    <select
                      value={group.logic}
                      onChange={(e) =>
                        handleGroupLogicChange(groupIndex, e.target.value as 'and' | 'or')
                      }
                    >
                      <option value="or">或 (OR)</option>
                      <option value="and">且 (AND)</option>
                    </select>
                  </div>
                  <div className="group-priority-selector">
                    <label>优先级：</label>
                    <input
                      type="number"
                      value={group.priority ?? 0}
                      onChange={(e) =>
                        handlePriorityChange(groupIndex, parseInt(e.target.value) || 0)
                      }
                      min={0}
                      className="priority-input"
                      title="数字越小优先级越高"
                    />
                    <span className="priority-hint">（越小越优先）</span>
                  </div>
                </div>

                <div className="conditions-list">
                  {group.conditions.map((condition, conditionIndex) => (
                    <div key={conditionIndex} className="condition-item">
                      <input
                        type="text"
                        placeholder="字段名（如：ctr, 收入）"
                        value={condition.field}
                        onChange={(e) =>
                          handleConditionChange(groupIndex, conditionIndex, 'field', e.target.value)
                        }
                        className="condition-field"
                      />
                      <select
                        value={condition.operator}
                        onChange={(e) =>
                          handleConditionChange(
                            groupIndex,
                            conditionIndex,
                            'operator',
                            e.target.value
                          )
                        }
                        className="condition-operator"
                      >
                        <option value=">">&gt;</option>
                        <option value=">=">&gt;=</option>
                        <option value="<">&lt;</option>
                        <option value="<=">&lt;=</option>
                        <option value="==">=</option>
                        <option value="!=">≠</option>
                      </select>
                      <input
                        type="number"
                        placeholder="值"
                        value={condition.value}
                        onChange={(e) =>
                          handleConditionChange(
                            groupIndex,
                            conditionIndex,
                            'value',
                            parseFloat(e.target.value) || 0
                          )
                        }
                        className="condition-value"
                        step="0.01"
                      />
                      <div className="condition-priority">
                        <label>优先级:</label>
                        <input
                          type="number"
                          value={condition.priority ?? 0}
                          onChange={(e) =>
                            handleConditionChange(
                              groupIndex,
                              conditionIndex,
                              'priority',
                              parseInt(e.target.value) || 0
                            )
                          }
                          min={0}
                          className="condition-priority-input"
                          title="数字越小优先级越高"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveCondition(groupIndex, conditionIndex)}
                        className="btn-remove"
                      >
                        删除
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => handleAddCondition(groupIndex)}
                    className="btn-add-condition"
                  >
                    + 添加条件
                  </button>
                </div>
              </div>
            ))}
            <button type="button" onClick={handleAddGroup} className="btn-add-group">
              + 添加规则组
            </button>
          </div>
        </div>
      </div>

      <div className="analyzer-section">
        <h3>分析设置</h3>
        <div className="days-setting">
          <label>查看近几日的均值：</label>
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value) || 7)}
            min={1}
            max={30}
            className="days-input"
          />
          <span>天</span>
        </div>
        <div className="save-db-setting">
          <label>
            <input
              type="checkbox"
              checked={saveToDb}
              onChange={(e) => setSaveToDb(e.target.checked)}
            />
            保存分析结果到数据库
          </label>
        </div>
      </div>

      <div className="analyzer-actions">
        <button
          onClick={handleAnalyze}
          disabled={loading || !file}
          className="btn btn-primary"
        >
          {loading ? '分析中...' : '开始分析'}
        </button>
        <button
          onClick={handleViewHistory}
          disabled={loadingHistory}
          className="btn btn-secondary"
        >
          {loadingHistory ? '加载中...' : '查看历史记录'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className="analyzer-results">
          <div className="results-header">
            <h3>分析结果</h3>
            {result.record_id && (
              <span className="saved-badge" title="已保存到数据库">
                ✓ 已保存 (ID: {result.record_id})
              </span>
            )}
          </div>
          <div className="result-summary">
            <div className="summary-item">
              <span className="summary-label">总行数：</span>
              <span className="summary-value">{result.total_rows}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">符合规则：</span>
              <span className="summary-value highlight">{result.matched_count}</span>
            </div>
          </div>

          {result.links.length > 0 ? (
            <>
              <div className="links-table">
                <table ref={tableRef}>
                  <thead>
                    <tr>
                      <th
                        style={{ width: getColumnWidth('link', 300), minWidth: 150 }}
                        className="sortable"
                        onClick={() => handleSort('link')}
                      >
                        <div className="th-content">
                          <span>链接</span>
                          <span className="sort-icon">{getSortIcon('link')}</span>
                        </div>
                        <div
                          className="resizer"
                          onMouseDown={(e) => handleMouseDown('link', e)}
                        />
                      </th>
                      <th
                        style={{ width: getColumnWidth('matched_rules', 400), minWidth: 200 }}
                        className="sortable"
                      >
                        <div className="th-content">
                          <span>满足的规则</span>
                        </div>
                        <div
                          className="resizer"
                          onMouseDown={(e) => handleMouseDown('matched_rules', e)}
                        />
                      </th>
                      <th
                        style={{ width: getColumnWidth('ctr', 120), minWidth: 100 }}
                        className="sortable"
                        onClick={() => handleSort('ctr')}
                      >
                        <div className="th-content">
                          <span>CTR 均值</span>
                          <span className="sort-icon">{getSortIcon('ctr')}</span>
                        </div>
                        <div
                          className="resizer"
                          onMouseDown={(e) => handleMouseDown('ctr', e)}
                        />
                      </th>
                      <th
                        style={{ width: getColumnWidth('revenue', 120), minWidth: 100 }}
                        className="sortable"
                        onClick={() => handleSort('revenue')}
                      >
                        <div className="th-content">
                          <span>收入均值</span>
                          <span className="sort-icon">{getSortIcon('revenue')}</span>
                        </div>
                        <div
                          className="resizer"
                          onMouseDown={(e) => handleMouseDown('revenue', e)}
                        />
                      </th>
                      <th
                        style={{ width: getColumnWidth('action', 120), minWidth: 100 }}
                      >
                        <div className="th-content">
                          <span>操作</span>
                        </div>
                        <div
                          className="resizer"
                          onMouseDown={(e) => handleMouseDown('action', e)}
                        />
                      </th>
                      {result.rule_fields &&
                        result.rule_fields
                          .filter((field) => {
                            // 排除已经在固定列中显示的字段
                            const fieldLower = field.toLowerCase()
                            return (
                              !fieldLower.includes('ctr') &&
                              !fieldLower.includes('点击率') &&
                              !fieldLower.includes('收入') &&
                              !fieldLower.includes('revenue')
                            )
                          })
                          .map((field) => (
                            <th
                              key={field}
                              style={{ width: getColumnWidth(field, 150), minWidth: 100 }}
                              className="sortable"
                              onClick={() => handleSort(field)}
                            >
                              <div className="th-content">
                                <span>{field}</span>
                                <span className="sort-icon">{getSortIcon(field)}</span>
                              </div>
                              <div
                                className="resizer"
                                onMouseDown={(e) => handleMouseDown(field, e)}
                              />
                            </th>
                          ))}
                    </tr>
                  </thead>
                  <tbody>
                    {getSortedLinks(result.links).map((link, index) => (
                      <tr key={index}>
                        <td className="link-cell">
                          <button
                            className="link-button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleLinkClick(link.link)
                            }}
                            title={link.link}
                          >
                            {link.link}
                          </button>
                        </td>
                        <td className="matched-groups-cell">
                          {link.matched_rules && link.matched_rules.length > 0
                            ? link.matched_rules.map((rule, idx) => (
                                <div key={idx} className="rule-text">
                                  {rule}
                                </div>
                              ))
                            : '-'}
                        </td>
                        <td className="ctr-cell">
                          {link.ctr !== null && link.ctr !== undefined
                            ? `${link.ctr.toFixed(2)}%`
                            : '-'}
                        </td>
                        <td className="revenue-cell">
                          {link.revenue !== null && link.revenue !== undefined
                            ? link.revenue.toFixed(2)
                            : '-'}
                        </td>
                        <td className="action-cell">
                          <button
                            className="btn-link-trend"
                            onClick={() => handleViewLinkTrend(link.link)}
                            title="查看链接变化趋势"
                          >
                            查看趋势
                          </button>
                        </td>
                        {result.rule_fields &&
                          result.rule_fields
                            .filter((field) => {
                              // 排除已经在固定列中显示的字段
                              const fieldLower = field.toLowerCase()
                              return (
                                !fieldLower.includes('ctr') &&
                                !fieldLower.includes('点击率') &&
                                !fieldLower.includes('收入') &&
                                !fieldLower.includes('revenue')
                              )
                            })
                            .map((field) => {
                              const value = link.data?.[field]
                              let displayValue = '-'
                              
                              if (value !== null && value !== undefined) {
                                if (typeof value === 'number') {
                                  // 如果是 CTR 相关字段，显示百分比
                                  if (field.toLowerCase().includes('ctr') || field.includes('点击率')) {
                                    displayValue = `${value.toFixed(2)}%`
                                  } else {
                                    displayValue = value.toFixed(2)
                                  }
                                } else {
                                  displayValue = String(value)
                                }
                              }
                              
                              return (
                                <td key={field} className="rule-field-cell">
                                  {displayValue}
                                </td>
                              )
                            })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedLink && (
                <div className="link-details-modal">
                  <div className="modal-overlay" onClick={() => setSelectedLink(null)}></div>
                  <div className="modal-content">
                    <div className="modal-header">
                      <h3>链接详情：{selectedLink}</h3>
                      <button className="modal-close" onClick={() => setSelectedLink(null)}>
                        ×
                      </button>
                    </div>
                    <div className="modal-body">
                      {loadingDetails ? (
                        <div className="loading">加载中...</div>
                      ) : linkDetails && linkDetails.length > 0 ? (
                        <div className="details-table">
                          <table>
                            <thead>
                              <tr>
                                {Object.keys(linkDetails[0]).map((col) => (
                                  <th key={col}>{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {linkDetails.map((row, idx) => (
                                <tr key={idx}>
                                  {Object.keys(linkDetails[0]).map((col) => {
                                    const value = row[col]
                                    let displayValue = '-'
                                    
                                    if (value !== null && value !== undefined) {
                                      if (typeof value === 'number') {
                                        // 如果是 CTR 相关字段，显示百分比
                                        if (col.toLowerCase().includes('ctr') || col.includes('点击率')) {
                                          displayValue = `${value.toFixed(2)}%`
                                        } else {
                                          displayValue = value.toFixed(2)
                                        }
                                      } else {
                                        displayValue = String(value)
                                      }
                                    }
                                    
                                    // 高亮显示日期和下游异常字段
                                    const isDateField = col.includes('日期') || col.toLowerCase().includes('date')
                                    const isDownstreamField = col.includes('下游') || col.toLowerCase().includes('downstream')
                                    const cellClass = isDateField || isDownstreamField ? 'highlight-cell' : ''
                                    
                                    return (
                                      <td key={col} className={cellClass}>
                                        {displayValue}
                                      </td>
                                    )
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="no-details">
                          {error && error.includes('无法查看详情') ? (
                            <div>
                              <p style={{ color: 'var(--color-danger)', marginBottom: '12px' }}>
                                {error}
                              </p>
                              <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                                提示：从历史记录加载的结果无法查看原始数据详情。如需查看详情，请重新上传文件进行分析。
                              </p>
                            </div>
                          ) : (
                            <div>暂无数据</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-results">未找到符合规则的链接</div>
          )}
        </div>
      )}

      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h3>历史分析记录</h3>
            <button className="btn-close" onClick={() => setShowHistory(false)}>
              ×
            </button>
          </div>
          <div className="history-content">
            {loadingHistory ? (
              <div className="loading">加载中...</div>
            ) : historyRecords.length === 0 ? (
              <div className="no-history">暂无历史记录</div>
            ) : (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>文件名</th>
                    <th>总行数</th>
                    <th>符合规则</th>
                    <th>天数</th>
                    <th>分析时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {historyRecords.map((record) => (
                    <tr key={record.id}>
                      <td>{record.id}</td>
                      <td>{record.file_name}</td>
                      <td>{record.total_rows}</td>
                      <td>{record.matched_count}</td>
                      <td>{record.days}</td>
                      <td>{new Date(record.created_at).toLocaleString()}</td>
                      <td>
                        <button
                          className="btn-view-record"
                          onClick={() => handleViewRecord(record.id)}
                        >
                          查看
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {linkTrend && (
        <div className="link-trend-modal">
          <div className="modal-overlay" onClick={() => setLinkTrend(null)}></div>
          <div className="modal-content">
            <div className="modal-header">
              <h3>链接变化趋势：{linkTrend.link}</h3>
              <button className="modal-close" onClick={() => setLinkTrend(null)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="trend-summary">
                <div className="summary-item">
                  <span className="summary-label">首次出现：</span>
                  <span className="summary-value">
                    {new Date(linkTrend.first_seen).toLocaleString()}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">最后出现：</span>
                  <span className="summary-value">
                    {new Date(linkTrend.last_seen).toLocaleString()}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">出现次数：</span>
                  <span className="summary-value">{linkTrend.appearance_count}</span>
                </div>
              </div>
              <div className="trend-chart">
                <h4>CTR 变化趋势</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={prepareChartData(linkTrend)}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="colorCtr" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                      dataKey="date"
                      stroke="#666"
                      style={{ fontSize: '12px' }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      stroke="#666"
                      style={{ fontSize: '12px' }}
                      label={{ value: 'CTR (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                      }}
                      formatter={(value: any) => {
                        const numValue = value as number | null
                        return numValue !== null ? `${numValue.toFixed(2)}%` : '无数据'
                      }}
                      labelFormatter={(label, payload) => {
                        if (payload && payload[0]) {
                          return payload[0].payload.fullDate
                        }
                        return label
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="ctr"
                      stroke="#8884d8"
                      fillOpacity={1}
                      fill="url(#colorCtr)"
                      connectNulls={false}
                      name="CTR"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="trend-chart">
                <h4>收入变化趋势</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={prepareChartData(linkTrend)}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#82ca9d" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                      dataKey="date"
                      stroke="#666"
                      style={{ fontSize: '12px' }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      stroke="#666"
                      style={{ fontSize: '12px' }}
                      label={{ value: '收入', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                      }}
                      formatter={(value: any) => {
                        const numValue = value as number | null
                        return numValue !== null ? numValue.toFixed(2) : '无数据'
                      }}
                      labelFormatter={(label, payload) => {
                        if (payload && payload[0]) {
                          return payload[0].payload.fullDate
                        }
                        return label
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#82ca9d"
                      fillOpacity={1}
                      fill="url(#colorRevenue)"
                      connectNulls={false}
                      name="收入"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="trend-chart">
                <h4>综合趋势对比</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart
                    data={prepareChartData(linkTrend)}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                      dataKey="date"
                      stroke="#666"
                      style={{ fontSize: '12px' }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      yAxisId="left"
                      stroke="#8884d8"
                      style={{ fontSize: '12px' }}
                      label={{ value: 'CTR (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      stroke="#82ca9d"
                      style={{ fontSize: '12px' }}
                      label={{ value: '收入', angle: 90, position: 'insideRight' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                      }}
                      formatter={(value: any, name: string) => {
                        const numValue = value as number | null
                        if (numValue === null) return '无数据'
                        if (name === 'CTR (%)') return `${numValue.toFixed(2)}%`
                        return numValue.toFixed(2)
                      }}
                      labelFormatter={(label, payload) => {
                        if (payload && payload[0]) {
                          return payload[0].payload.fullDate
                        }
                        return label
                      }}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="ctr"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                      name="CTR (%)"
                      connectNulls={false}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="revenue"
                      stroke="#82ca9d"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                      name="收入"
                      connectNulls={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="trend-records">
                <h4>历史记录详情</h4>
                <table className="trend-table">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>文件名</th>
                      <th>CTR</th>
                      <th>收入</th>
                      <th>满足的规则</th>
                    </tr>
                  </thead>
                  <tbody>
                    {linkTrend.records.map((record: LinkHistoryItem) => (
                      <tr key={record.id}>
                        <td>{new Date(record.created_at).toLocaleString()}</td>
                        <td>{record.file_name}</td>
                        <td>{record.ctr !== null && record.ctr !== undefined ? `${record.ctr.toFixed(2)}%` : '-'}</td>
                        <td>{record.revenue !== null && record.revenue !== undefined ? record.revenue.toFixed(2) : '-'}</td>
                        <td>
                          {record.matched_rules && record.matched_rules.length > 0
                            ? record.matched_rules.join(', ')
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      <Modal
        isOpen={modal.isOpen}
        onClose={modal.hide}
        title={modal.title}
        message={modal.message}
        type={modal.options.type}
        showCancel={modal.options.showCancel}
        onConfirm={modal.options.onConfirm}
        confirmText={modal.options.confirmText}
        cancelText={modal.options.cancelText}
      />
    </div>
  )
}

export default ExcelAnalyzer
