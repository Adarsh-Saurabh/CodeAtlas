import React, { useState, useRef, useEffect } from 'react';
import CNNCanvas from './components/CNNCanvas';
import { UploadCloud, Loader2, Play, Pause, SkipForward, RotateCcw, Sparkles, ChevronRight } from 'lucide-react';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [activeNodeIndex, setActiveNodeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(2000);
  const [packetProgress, setPacketProgress] = useState(0);

  const fileInputRef = useRef(null);
  const playRef = useRef(null);
  const packetRef = useRef(null);

  const handleUpload = async (file) => {
    if (!file || !file.name.endsWith('.zip')) {
      setError("Please upload a .zip file containing your project.");
      return;
    }
    setIsLoading(true); setError(null); setGraphData(null);
    setIsPlaying(false); setActiveNodeIndex(0); setPacketProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
      setGraphData(await res.json());
    } catch (e) { setError(e.message); }
    finally { setIsLoading(false); }
  };

  const totalNodes = graphData ? graphData.nodes.length : 0;

  // Packet animation loop (smooth)
  useEffect(() => {
    if (isPlaying) {
      let start = null;
      const duration = speed * 0.6; // packet travels during 60% of the step time
      const animate = (ts) => {
        if (!start) start = ts;
        const elapsed = ts - start;
        const progress = Math.min(elapsed / duration, 1);
        setPacketProgress(progress);
        if (progress < 1) {
          packetRef.current = requestAnimationFrame(animate);
        }
      };
      packetRef.current = requestAnimationFrame(animate);
      return () => cancelAnimationFrame(packetRef.current);
    }
  }, [isPlaying, activeNodeIndex, speed]);

  // Step timer
  useEffect(() => {
    if (isPlaying) {
      playRef.current = setInterval(() => {
        setActiveNodeIndex(prev => {
          if (prev >= totalNodes - 1) { setIsPlaying(false); return prev; }
          setPacketProgress(0);
          return prev + 1;
        });
      }, speed);
    } else { clearInterval(playRef.current); }
    return () => clearInterval(playRef.current);
  }, [isPlaying, totalNodes, speed]);

  const handlePlayPause = () => {
    if (activeNodeIndex >= totalNodes - 1) { setActiveNodeIndex(0); setPacketProgress(0); }
    setIsPlaying(!isPlaying);
  };
  const handleStep = () => {
    setIsPlaying(false);
    if (activeNodeIndex < totalNodes - 1) {
      setPacketProgress(0);
      setActiveNodeIndex(p => p + 1);
      // Animate packet for manual step
      let start = null;
      const dur = 600;
      const anim = (ts) => {
        if (!start) start = ts;
        const p = Math.min((ts - start) / dur, 1);
        setPacketProgress(p);
        if (p < 1) requestAnimationFrame(anim);
      };
      requestAnimationFrame(anim);
    }
  };
  const handleReset = () => { setIsPlaying(false); setActiveNodeIndex(0); setPacketProgress(0); };
  const handleNew = () => { setGraphData(null); setIsPlaying(false); setActiveNodeIndex(0); setError(null); };

  const activeNode = graphData && activeNodeIndex < totalNodes ? graphData.nodes[activeNodeIndex] : null;
  const progress = totalNodes > 0 ? ((activeNodeIndex + 1) / totalNodes) * 100 : 0;

  return (
    <div className="app-container">
      <header className="glass-header">
        <div className="logo">
          <Sparkles className="logo-icon" size={22} />
          <h1>CodeAtlas Visualizer</h1>
        </div>
        {graphData && (
          <div className="header-controls">
            <div className="speed-control">
              <label>Speed:</label>
              <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>
                <option value={3500}>Slow</option>
                <option value={2000}>Normal</option>
                <option value={1200}>Fast</option>
                <option value={600}>Very Fast</option>
              </select>
            </div>
            <div className="playback-controls">
              <button className="btn-ctrl" onClick={handleReset}><RotateCcw size={16} /></button>
              <button className="btn-ctrl play" onClick={handlePlayPause}>
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button className="btn-ctrl" onClick={handleStep}><SkipForward size={16} /></button>
            </div>
            <button className="btn-upload-new" onClick={handleNew}>Upload New</button>
          </div>
        )}
      </header>

      {graphData && <div className="progress-bar-wrap"><div className="progress-bar" style={{ width: `${progress}%` }} /></div>}

      <main className="main-content">
        {!graphData && !isLoading && (
          <div className="upload-screen">
            <div
              className={`dropzone glass-panel ${isDragActive ? 'active' : ''}`}
              onDragOver={e => { e.preventDefault(); setIsDragActive(true); }}
              onDragLeave={() => setIsDragActive(false)}
              onDrop={e => { e.preventDefault(); setIsDragActive(false); if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]); }}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={56} className="upload-icon" />
              <h2>Upload Any Project</h2>
              <p>Drag & drop a .zip file — CNN, Web App, Data Pipeline, or any Python project.</p>
              <p className="upload-sub">We'll auto-detect the architecture and animate how it works.</p>
              <button className="btn-primary">Browse Files</button>
              <input type="file" ref={fileInputRef} accept=".zip" style={{ display: 'none' }} onChange={e => handleUpload(e.target.files[0])} />
            </div>
            {error && <div className="error-msg">{error}</div>}
          </div>
        )}

        {isLoading && (
          <div className="loading-screen glass-panel">
            <Loader2 className="spinner" size={52} />
            <h2>Analyzing Architecture...</h2>
            <p>Computing tensor shapes and detecting patterns.</p>
          </div>
        )}

        {graphData && !isLoading && (
          <div className="visualizer-layout">
            <div className="canvas-pane">
              <CNNCanvas nodes={graphData.nodes} activeNodeIndex={activeNodeIndex} packetProgress={packetProgress} />
            </div>
            <div className="side-panel glass-panel">
              <h3>Layer Details</h3>
              {activeNode ? (
                <div className="side-content" key={activeNodeIndex}>
                  <div className="side-badge" style={{ background: activeNode.color || '#5352ed' }}>
                    Step {activeNodeIndex + 1} / {totalNodes}
                  </div>
                  <h4>{activeNode.title}</h4>
                  <p className="side-type">{activeNode.type}</p>

                  {activeNode.shape_label && (
                    <div className="side-shape">
                      <span className="shape-label">Output Shape</span>
                      <span className="shape-value">{activeNode.shape_label}</span>
                    </div>
                  )}
                  {activeNode.input_shape_label && (
                    <div className="side-shape">
                      <span className="shape-label">Input Shape</span>
                      <span className="shape-value">{activeNode.input_shape_label}</span>
                    </div>
                  )}

                  {activeNode.math && (
                    <div className="side-math">
                      <span className="math-label">Formula</span>
                      <code>{activeNode.math}</code>
                    </div>
                  )}

                  {activeNode.params_label && (
                    <div className="side-params">
                      <span className="params-label">Parameters</span>
                      <code>{activeNode.params_label}</code>
                    </div>
                  )}

                  <p className="side-desc">{activeNode.description}</p>
                </div>
              ) : (
                <p className="side-empty">Press Play or Step to begin.</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
