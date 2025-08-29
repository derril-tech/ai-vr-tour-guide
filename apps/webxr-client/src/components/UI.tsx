import { useStore } from '../store/useStore'
import './UI.css'

export function UI() {
  const {
    currentHotspot,
    isNarrating,
    showUI,
    isXRActive,
    stopAudio,
    setCurrentHotspot
  } = useStore()

  if (!showUI || isXRActive) return null

  return (
    <div className="ui-overlay">
      {/* Loading indicator */}
      {useStore.getState().isLoading && (
        <div className="loading-indicator">
          <div className="spinner" />
          <p>Loading tour...</p>
        </div>
      )}

      {/* Hotspot details panel */}
      {currentHotspot && (
        <div className="hotspot-panel">
          <div className="hotspot-header">
            <h3>{currentHotspot.title}</h3>
            <button
              className="close-button"
              onClick={() => setCurrentHotspot(null)}
            >
              ×
            </button>
          </div>
          
          <div className="hotspot-content">
            <p>{currentHotspot.description}</p>
            
            {currentHotspot.type === 'audio' && (
              <div className="audio-controls">
                {isNarrating ? (
                  <button onClick={stopAudio} className="audio-button stop">
                    Stop Audio
                  </button>
                ) : (
                  <button
                    onClick={() => currentHotspot.content?.audioUrl && 
                      useStore.getState().playAudio(currentHotspot.content.audioUrl)}
                    className="audio-button play"
                  >
                    Play Audio
                  </button>
                )}
              </div>
            )}
            
            {currentHotspot.type === 'quiz' && (
              <div className="quiz-content">
                <p>Interactive quiz content would go here</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation controls */}
      <div className="nav-controls">
        <button className="nav-button">
          Sites
        </button>
        <button className="nav-button">
          Settings
        </button>
      </div>

      {/* Audio indicator */}
      {isNarrating && (
        <div className="audio-indicator">
          <div className="audio-wave" />
          <span>Playing narration...</span>
        </div>
      )}
    </div>
  )
}
