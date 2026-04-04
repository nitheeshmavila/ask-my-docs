import { useState, useRef, useEffect } from 'react'
import './App.css'

interface Message {
  question: string
  answer: string | null
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [asking, setAsking] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploadError, setUploadError] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeFile, setActiveFile] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [input])

  const handleUpload = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      setUploadStatus('Only PDF files are accepted.')
      setUploadError(true)
      return
    }

    setUploading(true)
    setUploadStatus(`Uploading ${file.name}...`)
    setUploadError(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/ingest', { method: 'POST', body: formData })
      const data = await res.json()
      if (data.error) {
        setUploadStatus(data.error)
        setUploadError(true)
      } else {
        setActiveFile(data.filename)
        setUploadStatus('')
        setUploadError(false)
      }
    } catch {
      setUploadStatus('Upload failed. Is the API running?')
      setUploadError(true)
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
    e.target.value = ''
  }

  const handleNewSession = () => {
    setActiveFile(null)
    setMessages([])
    setInput('')
    setUploadStatus('')
    setUploadError(false)
  }

  const handleAsk = async () => {
    const question = input.trim()
    if (!question || asking) return

    setInput('')
    setAsking(true)
    setMessages((prev) => [...prev, { question, answer: null }])

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await res.json()
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1 ? { ...m, answer: data.answer } : m
        )
      )
    } catch {
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1
            ? { ...m, answer: 'Failed to get answer. Is the API running?' }
            : m
        )
      )
    } finally {
      setAsking(false)
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const hasSession = activeFile !== null

  return (
    <div className="app">
      {/* Top bar - visible after file upload */}
      {hasSession && (
        <div className="top-bar">
          <div className="top-bar-inner">
            <div className="top-bar-left">
              <span className="top-bar-title">Ask My Docs</span>
              <span className="top-bar-sep">/</span>
              <span className="top-bar-file">
                <svg className="top-bar-file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                {activeFile}
              </span>
            </div>
            <button className="new-session-button" onClick={handleNewSession}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New document
            </button>
          </div>
        </div>
      )}

      {/* Upload status banner */}
      {uploadStatus && (
        <div className={`upload-banner${hasSession ? ' with-topbar' : ''}`}>
          <div className={`upload-banner-content${uploadError ? ' error' : ''}`}>
            {uploadStatus}
          </div>
        </div>
      )}

      <div className={`messages-wrapper${hasSession ? ' with-topbar' : ''}`}>
        <div className="messages-container">
          {!hasSession ? (
            <div className="welcome">
              <div className="welcome-title">Ask My Docs</div>
              <div className="welcome-sub">Upload a PDF to start asking questions</div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="upload-input"
                onChange={handleFileChange}
              />
              <button
                className="welcome-upload"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                {uploading ? 'Uploading...' : 'Upload PDF'}
              </button>
            </div>
          ) : messages.length === 0 ? (
            <div className="session-empty">
              Ask anything about this document
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className="message">
                <div className="message-user">
                  <div className="message-user-bubble">{m.question}</div>
                </div>
                <div className="message-assistant">
                  {m.answer === null ? (
                    <div className="message-loading">
                      <span className="loading-dot" />
                      <span className="loading-dot" />
                      <span className="loading-dot" />
                    </div>
                  ) : (
                    <div className="message-content">{m.answer}</div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input bar - only visible after upload */}
      {hasSession && (
        <div className="input-wrapper">
          <div className="input-container">
            <div className="input-box">
              <textarea
                ref={textareaRef}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question..."
                disabled={asking}
                rows={1}
              />
              <button
                className="send-button"
                onClick={handleAsk}
                disabled={asking || !input.trim()}
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
