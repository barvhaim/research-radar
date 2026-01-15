import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

const AVAILABLE_KEYWORDS = [
  // Core Concepts
  "Large Language Models (LLMs)",
  "Transformers",
  "Attention Mechanisms",
  "Neural Networks",
  // Training Methods
  "Fine-tuning",
  "Reinforcement Learning",
  "Direct Preference Optimization (DPO)",
  "Supervised Learning",
  "Transfer Learning",
  // Reasoning & Prompting
  "Chain-of-Thought",
  "Reasoning",
  "Prompting",
  "In-Context Learning",
  "Few-Shot Learning",
  // Retrieval & Knowledge
  "RAG (Retrieval-Augmented Generation)",
  "Knowledge Retrieval",
  "Semantic Search",
  // Instructions & Evaluation
  "Instruction Following",
  "Benchmarks",
  "Evaluation",
  "Human Feedback",
  // Memory & Context
  "Long Context",
  "Memory",
  "Context Window",
  // Information Theory
  "Entropy",
  "KL-divergence",
  "Uncertainty",
  // Tasks & Applications
  "Code Generation",
  "Question Answering",
  "Summarization",
  "Translation",
  // Multimodal
  "Multimodal",
  "Vision-Language",
  // Safety & Alignment
  "Alignment",
  "Safety",
]

function App() {
  const [paperId, setPaperId] = useState('')
  const [selectedKeywords, setSelectedKeywords] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [summary, setSummary] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState('')

  const handleKeywordToggle = (keyword) => {
    setSelectedKeywords(prev => 
      prev.includes(keyword)
        ? prev.filter(k => k !== keyword)
        : [...prev, keyword]
    )
  }

  const formatAnalysis = (analysisData) => {
    if (!analysisData || Object.keys(analysisData).length === 0) {
      return '*No analysis available*'
    }

    return Object.entries(analysisData).map(([question, answer], index) => (
      `#### ${index + 1}. ${question}\n\n${answer}`
    )).join('\n\n---\n\n')
  }

  const handleAnalyze = async () => {
    if (!paperId.trim()) {
      setError('Please enter a valid ID')
      return
    }

    setLoading(true)
    setError('')
    setStatus('Analyzing...')
    setSummary('')
    setAnalysis(null)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paper_id: paperId.trim(),
          keywords: selectedKeywords.length > 0 ? selectedKeywords : [],
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()
      setStatus(`Analysis completed successfully for: ${result.paper_id}`)
      setSummary(result.summary || 'No summary available')
      setAnalysis(result.analysis)
    } catch (err) {
      setError(err.message)
      setStatus('Error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleAnalyze()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Research Radar</h1>
        <p className="subtitle">Extract insights from papers and videos with AI-powered analysis</p>
      </header>

      <main className="main-content">
        <div className="input-section">
          <div className="input-group">
            <input
              type="text"
              className="paper-input"
              placeholder="ArXiv ID (2510.24081) or YouTube URL"
              value={paperId}
              onChange={(e) => setPaperId(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={loading || !paperId.trim()}
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>

          <div className="keywords-section">
            <label className="keywords-label">
              Filter by Keywords (optional - leave empty to analyze all content)
            </label>
            <div className="keywords-grid">
              {AVAILABLE_KEYWORDS.map((keyword) => (
                <button
                  key={keyword}
                  className={`keyword-chip ${selectedKeywords.includes(keyword) ? 'selected' : ''}`}
                  onClick={() => handleKeywordToggle(keyword)}
                  disabled={loading}
                >
                  {keyword}
                </button>
              ))}
            </div>
          </div>
        </div>

        {status && (
          <div className={`status ${error ? 'error' : 'success'}`}>
            {error || status}
          </div>
        )}

        {summary && (
          <section className="results-section">
            <h2 className="section-title">Summary</h2>
            <div className="content-box">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          </section>
        )}

        {analysis && Object.keys(analysis).length > 0 && (
          <section className="results-section">
            <h2 className="section-title">Detailed Analysis</h2>
            <div className="content-box">
              <ReactMarkdown>{formatAnalysis(analysis)}</ReactMarkdown>
            </div>
          </section>
        )}

        {!summary && !loading && (
          <div className="placeholder">
            <p>Enter a paper ID or YouTube URL above to start analysis</p>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Processing may take a few moments depending on content size.</p>
      </footer>
    </div>
  )
}

export default App
