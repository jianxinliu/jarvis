import { useState, useCallback } from 'react'

interface UseModalOptions {
  type?: 'info' | 'success' | 'warning' | 'error'
  showCancel?: boolean
  onConfirm?: () => void
  confirmText?: string
  cancelText?: string
}

export function useModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [title, setTitle] = useState<string | undefined>(undefined)
  const [message, setMessage] = useState('')
  const [options, setOptions] = useState<UseModalOptions>({})

  const show = useCallback((
    msg: string,
    modalTitle?: string,
    modalOptions?: UseModalOptions
  ) => {
    setMessage(msg)
    setTitle(modalTitle)
    setOptions(modalOptions || {})
    setIsOpen(true)
  }, [])

  const hide = useCallback(() => {
    setIsOpen(false)
  }, [])

  const showAlert = useCallback((
    msg: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    show(msg, undefined, { type })
  }, [show])

  const showConfirm = useCallback((
    msg: string,
    onConfirm: () => void,
    title?: string
  ) => {
    show(msg, title, {
      type: 'warning',
      showCancel: true,
      onConfirm,
    })
  }, [show])

  return {
    isOpen,
    title,
    message,
    options,
    show,
    hide,
    showAlert,
    showConfirm,
  }
}

