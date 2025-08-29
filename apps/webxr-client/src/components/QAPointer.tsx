import React, { useState, useRef, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Vector3, Raycaster } from 'three';
import { Html } from '@react-three/drei';
import { useStore } from '../store/useStore';

interface QAPointerProps {
  onQuestionAsked: (question: string, position: Vector3) => void;
}

export const QAPointer: React.FC<QAPointerProps> = ({ onQuestionAsked }) => {
  const [isActive, setIsActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [question, setQuestion] = useState('');
  const [pointerPosition, setPointerPosition] = useState<Vector3 | null>(null);
  
  const { camera, scene } = useThree();
  const raycaster = useRef(new Raycaster());
  const { qaMode, setQAMode } = useStore();

  // Voice recognition setup
  const startVoiceRecognition = useCallback(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
      };
      
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(transcript);
        setIsListening(false);
      };
      
      recognition.onerror = () => {
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      recognition.start();
    }
  }, []);

  // Handle pointer interaction
  const handlePointerClick = useCallback((event: any) => {
    if (!qaMode) return;
    
    const pointer = event.pointer || { x: 0, y: 0 };
    raycaster.current.setFromCamera(pointer, camera);
    
    const intersects = raycaster.current.intersectObjects(scene.children, true);
    
    if (intersects.length > 0) {
      const position = intersects[0].point;
      setPointerPosition(position);
      setIsActive(true);
      
      // Start voice recognition automatically
      startVoiceRecognition();
    }
  }, [qaMode, camera, scene, startVoiceRecognition]);

  // Submit question
  const handleSubmitQuestion = useCallback(() => {
    if (question.trim() && pointerPosition) {
      onQuestionAsked(question, pointerPosition);
      setQuestion('');
      setIsActive(false);
      setPointerPosition(null);
      setQAMode(false);
    }
  }, [question, pointerPosition, onQuestionAsked, setQAMode]);

  useFrame(() => {
    // Update pointer visual feedback
  });

  return (
    <>
      {/* Pointer Visual */}
      {qaMode && (
        <mesh
          position={[0, 0, -2]}
          onClick={handlePointerClick}
        >
          <sphereGeometry args={[0.02, 16, 16]} />
          <meshBasicMaterial 
            color={isActive ? "#ff6b6b" : "#4ecdc4"} 
            transparent 
            opacity={0.8} 
          />
        </mesh>
      )}

      {/* Question Input UI */}
      {isActive && pointerPosition && (
        <Html
          position={[pointerPosition.x, pointerPosition.y + 0.5, pointerPosition.z]}
          center
        >
          <div className="qa-input-panel">
            <div className="qa-header">
              <h3>Ask a Question</h3>
              {isListening && (
                <div className="listening-indicator">
                  🎤 Listening...
                </div>
              )}
            </div>
            
            <div className="qa-input-section">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What would you like to know about this?"
                className="qa-textarea"
                rows={3}
              />
              
              <div className="qa-buttons">
                <button
                  onClick={startVoiceRecognition}
                  className="voice-button"
                  disabled={isListening}
                >
                  🎤 {isListening ? 'Listening...' : 'Voice'}
                </button>
                
                <button
                  onClick={handleSubmitQuestion}
                  className="submit-button"
                  disabled={!question.trim()}
                >
                  Ask
                </button>
                
                <button
                  onClick={() => {
                    setIsActive(false);
                    setQuestion('');
                    setQAMode(false);
                  }}
                  className="cancel-button"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </Html>
      )}

      <style jsx>{`
        .qa-input-panel {
          background: rgba(0, 0, 0, 0.9);
          border-radius: 12px;
          padding: 20px;
          min-width: 300px;
          max-width: 400px;
          color: white;
          font-family: 'Inter', sans-serif;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .qa-header {
          margin-bottom: 15px;
        }

        .qa-header h3 {
          margin: 0 0 10px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .listening-indicator {
          color: #ff6b6b;
          font-size: 14px;
          animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .qa-textarea {
          width: 100%;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          padding: 12px;
          color: white;
          font-size: 14px;
          resize: vertical;
          margin-bottom: 15px;
        }

        .qa-textarea::placeholder {
          color: rgba(255, 255, 255, 0.6);
        }

        .qa-buttons {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
        }

        .voice-button, .submit-button, .cancel-button {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .voice-button {
          background: #4ecdc4;
          color: white;
        }

        .voice-button:hover:not(:disabled) {
          background: #45b7b8;
        }

        .voice-button:disabled {
          background: #666;
          cursor: not-allowed;
        }

        .submit-button {
          background: #6c5ce7;
          color: white;
        }

        .submit-button:hover:not(:disabled) {
          background: #5f3dc4;
        }

        .submit-button:disabled {
          background: #666;
          cursor: not-allowed;
        }

        .cancel-button {
          background: transparent;
          color: rgba(255, 255, 255, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .cancel-button:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
      `}</style>
    </>
  );
};
