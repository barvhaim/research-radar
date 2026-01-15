import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Header,
  HeaderName,
  Content,
  Grid,
  Column,
  TextInput,
  Button,
  MultiSelect,
  InlineNotification,
  Loading,
  Tile,
  Theme,
} from '@carbon/react'
import { Analytics, Search } from '@carbon/icons-react'

const KEYWORDS = [
  { id: 'llm', label: 'Large Language Models (LLMs)' },
  { id: 'transformers', label: 'Transformers' },
  { id: 'attention', label: 'Attention Mechanisms' },
  { id: 'neural', label: 'Neural Networks' },
  { id: 'finetuning', label: 'Fine-tuning' },
  { id: 'rl', label: 'Reinforcement Learning' },
  { id: 'dpo', label: 'Direct Preference Optimization (DPO)' },
  { id: 'supervised', label: 'Supervised Learning' },
  { id: 'transfer', label: 'Transfer Learning' },
  { id: 'cot', label: 'Chain-of-Thought' },
  { id: 'reasoning', label: 'Reasoning' },
  { id: 'prompting', label: 'Prompting' },
  { id: 'icl', label: 'In-Context Learning' },
  { id: 'fewshot', label: 'Few-Shot Learning' },
  { id: 'rag', label: 'RAG (Retrieval-Augmented Generation)' },
  { id: 'retrieval', label: 'Knowledge Retrieval' },
  { id: 'semantic', label: 'Semantic Search' },
  { id: 'instruction', label: 'Instruction Following' },
  { id: 'benchmarks', label: 'Benchmarks' },
  { id: 'evaluation', label: 'Evaluation' },
  { id: 'rlhf', label: 'Human Feedback' },
  { id: 'longcontext', label: 'Long Context' },
  { id: 'memory', label: 'Memory' },
  { id: 'context', label: 'Context Window' },
  { id: 'codegen', label: 'Code Generation' },
  { id: 'qa', label: 'Question Answering' },
  { id: 'summarization', label: 'Summarization' },
  { id: 'multimodal', label: 'Multimodal' },
  { id: 'visionlang', label: 'Vision-Language' },
  { id: 'alignment', label: 'Alignment' },
  { id: 'safety', label: 'Safety' },
]

// Extract YouTube video ID from various URL formats
const extractYouTubeId = (input) => {
  if (!input) return null

  // Already a video ID (11 characters)
  if (/^[a-zA-Z0-9_-]{11}$/.test(input)) {
    return input
  }

  // Various YouTube URL patterns
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
  ]

  for (const pattern of patterns) {
    const match = input.match(pattern)
    if (match) return match[1]
  }

  return null
}

function App() {
  const [paperId, setPaperId] = useState('')
  const [selectedKeywords, setSelectedKeywords] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [summary, setSummary] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState('')
  const [youtubeId, setYoutubeId] = useState(null)

  const formatAnalysis = (analysisData) => {
    if (!analysisData || Object.keys(analysisData).length === 0) {
      return '*No analysis available*'
    }
    return Object.entries(analysisData).map(([question, answer], index) => (
      `### ${index + 1}. ${question}\n\n${answer}`
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
    setYoutubeId(null)

    // Check if it's a YouTube URL and extract video ID
    const videoId = extractYouTubeId(paperId.trim())

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: paperId.trim(),
          keywords: selectedKeywords.map(k => k.label),
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()
      setStatus(`Analysis completed for: ${result.paper_id}`)
      setSummary(result.summary || 'No summary available')
      setAnalysis(result.analysis)
      if (videoId) setYoutubeId(videoId)
    } catch (err) {
      setError(err.message)
      setStatus('')
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
    <Theme theme="g100">
      <div className="app">
        <Header aria-label="Research Radar">
          <HeaderName href="/" prefix="">
            <Analytics size={20} style={{ marginRight: '0.5rem' }} />
            Research Radar
          </HeaderName>
        </Header>

        <Content>
          <Grid className="landing-grid">
            <Column lg={16} md={8} sm={4}>
              <h1 className="page-title">Analyze Research Papers & Videos</h1>
              <p className="page-subtitle">
                Extract insights from ArXiv papers and YouTube videos with AI-powered analysis
              </p>
            </Column>

            <Column lg={16} md={8} sm={4}>
              <Tile className="input-tile">
                <div className="input-row">
                  <div className="input-field">
                    <TextInput
                      id="paper-input"
                      labelText="Paper ID or URL"
                      placeholder="ArXiv ID (e.g., 2510.24081) or YouTube URL"
                      value={paperId}
                      onChange={(e) => setPaperId(e.target.value)}
                      onKeyPress={handleKeyPress}
                      disabled={loading}
                      size="lg"
                    />
                  </div>
                  <Button
                    kind="primary"
                    size="lg"
                    onClick={handleAnalyze}
                    disabled={loading || !paperId.trim()}
                    renderIcon={Search}
                    className="analyze-btn"
                  >
                    {loading ? 'Analyzing...' : 'Analyze'}
                  </Button>
                </div>

                <div className="keywords-field">
                  <MultiSelect
                    id="keywords-select"
                    titleText="Filter by Keywords (optional)"
                    label="Select keywords to focus analysis..."
                    items={KEYWORDS}
                    itemToString={(item) => item?.label || ''}
                    selectedItems={selectedKeywords}
                    onChange={({ selectedItems }) => setSelectedKeywords(selectedItems)}
                    disabled={loading}
                    size="lg"
                  />
                </div>
              </Tile>
            </Column>

            {loading && (
              <Column lg={16} md={8} sm={4}>
                <Tile className="loading-tile">
                  <Loading description="Analyzing..." withOverlay={false} />
                  <p>Processing your request. This may take a few moments...</p>
                </Tile>
              </Column>
            )}

            {error && (
              <Column lg={16} md={8} sm={4}>
                <InlineNotification
                  kind="error"
                  title="Error"
                  subtitle={error}
                  onClose={() => setError('')}
                />
              </Column>
            )}

            {status && !error && !loading && (
              <Column lg={16} md={8} sm={4}>
                <InlineNotification
                  kind="success"
                  title="Success"
                  subtitle={status}
                  onClose={() => setStatus('')}
                />
              </Column>
            )}

            {youtubeId && (
              <Column lg={16} md={8} sm={4}>
                <h2 className="section-title">Video</h2>
                <div className="video-container">
                  <iframe
                    src={`https://www.youtube.com/embed/${youtubeId}`}
                    title="YouTube video"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </Column>
            )}

            {summary && (
              <Column lg={16} md={8} sm={4}>
                <h2 className="section-title">Summary</h2>
                <Tile className="content-tile">
                  <ReactMarkdown>{summary}</ReactMarkdown>
                </Tile>
              </Column>
            )}

            {analysis && Object.keys(analysis).length > 0 && (
              <Column lg={16} md={8} sm={4}>
                <h2 className="section-title">Detailed Analysis</h2>
                <Tile className="content-tile">
                  <ReactMarkdown>{formatAnalysis(analysis)}</ReactMarkdown>
                </Tile>
              </Column>
            )}

            {!summary && !loading && (
              <Column lg={16} md={8} sm={4}>
                <Tile className="placeholder-tile">
                  <Analytics size={64} />
                  <p>Enter a paper ID or YouTube URL above to start analysis</p>
                </Tile>
              </Column>
            )}
          </Grid>
        </Content>

        <footer className="app-footer">
          <p>Processing may take a few moments depending on content size.</p>
        </footer>
      </div>
    </Theme>
  )
}

export default App
