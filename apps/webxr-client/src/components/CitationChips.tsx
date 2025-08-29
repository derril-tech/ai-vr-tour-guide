import React, { useState, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Vector3, Color } from 'three';

interface Citation {
  id: string;
  position: { x: number; y: number; z: number };
  source_title: string;
  source_type: string;
  credibility_score: number;
  relevance_score: number;
  preview_text: string;
  full_citation: string;
  visual_style: {
    color: string;
    opacity: number;
    glow_intensity: number;
    border_style: string;
  };
  display_duration: number;
}

interface CitationChipsProps {
  citations: Citation[];
  onCitationClick: (citation: Citation) => void;
}

export const CitationChips: React.FC<CitationChipsProps> = ({ 
  citations, 
  onCitationClick 
}) => {
  const [hoveredChip, setHoveredChip] = useState<string | null>(null);
  const [expandedChip, setExpandedChip] = useState<string | null>(null);
  const chipRefs = useRef<{ [key: string]: any }>({});

  // Animate chips floating
  useFrame((state) => {
    citations.forEach((citation) => {
      const chipRef = chipRefs.current[citation.id];
      if (chipRef) {
        // Gentle floating animation
        const time = state.clock.elapsedTime;
        const floatOffset = Math.sin(time * 2 + citation.id.length) * 0.02;
        chipRef.position.y = citation.position.y + floatOffset;
        
        // Gentle rotation
        chipRef.rotation.y = Math.sin(time * 0.5) * 0.1;
      }
    });
  });

  const getCredibilityColor = (score: number): string => {
    if (score >= 0.8) return '#4CAF50'; // Green
    if (score >= 0.6) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };

  const getCredibilityLabel = (score: number): string => {
    if (score >= 0.8) return 'High Credibility';
    if (score >= 0.6) return 'Medium Credibility';
    return 'Low Credibility';
  };

  return (
    <>
      {citations.map((citation) => (
        <group key={citation.id}>
          {/* Main Citation Chip */}
          <mesh
            ref={(ref) => (chipRefs.current[citation.id] = ref)}
            position={[citation.position.x, citation.position.y, citation.position.z]}
            onClick={() => onCitationClick(citation)}
            onPointerEnter={() => setHoveredChip(citation.id)}
            onPointerLeave={() => setHoveredChip(null)}
          >
            <boxGeometry args={[0.3, 0.15, 0.02]} />
            <meshStandardMaterial
              color={citation.visual_style.color}
              transparent
              opacity={hoveredChip === citation.id ? 0.9 : citation.visual_style.opacity}
              emissive={citation.visual_style.color}
              emissiveIntensity={hoveredChip === citation.id ? 0.3 : 0.1}
            />
          </mesh>

          {/* Citation Number */}
          <Html
            position={[citation.position.x, citation.position.y, citation.position.z + 0.02]}
            center
            distanceFactor={10}
          >
            <div className="citation-number">
              {citations.indexOf(citation) + 1}
            </div>
          </Html>

          {/* Expanded Citation Info */}
          {(hoveredChip === citation.id || expandedChip === citation.id) && (
            <Html
              position={[
                citation.position.x + 0.4, 
                citation.position.y, 
                citation.position.z
              ]}
              center
              distanceFactor={8}
            >
              <div className="citation-popup">
                <div className="citation-header">
                  <div className="source-title">{citation.source_title}</div>
                  <div 
                    className="credibility-badge"
                    style={{ 
                      backgroundColor: getCredibilityColor(citation.credibility_score),
                      color: 'white'
                    }}
                  >
                    {getCredibilityLabel(citation.credibility_score)}
                  </div>
                </div>
                
                <div className="citation-content">
                  <div className="preview-text">
                    "{citation.preview_text}"
                  </div>
                  
                  <div className="citation-meta">
                    <div className="source-type">
                      Type: {citation.source_type}
                    </div>
                    <div className="relevance-score">
                      Relevance: {(citation.relevance_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div className="full-citation">
                    {citation.full_citation}
                  </div>
                </div>

                <div className="citation-actions">
                  <button
                    onClick={() => setExpandedChip(
                      expandedChip === citation.id ? null : citation.id
                    )}
                    className="expand-button"
                  >
                    {expandedChip === citation.id ? 'Collapse' : 'Expand'}
                  </button>
                  
                  <button
                    onClick={() => onCitationClick(citation)}
                    className="view-source-button"
                  >
                    View Source
                  </button>
                </div>
              </div>
            </Html>
          )}

          {/* Glow Effect */}
          {hoveredChip === citation.id && (
            <mesh
              position={[citation.position.x, citation.position.y, citation.position.z - 0.01]}
            >
              <boxGeometry args={[0.35, 0.2, 0.01]} />
              <meshBasicMaterial
                color={citation.visual_style.color}
                transparent
                opacity={0.3}
              />
            </mesh>
          )}
        </group>
      ))}

      <style jsx>{`
        .citation-number {
          background: rgba(255, 255, 255, 0.9);
          color: #333;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 12px;
          font-family: 'Inter', sans-serif;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        .citation-popup {
          background: rgba(0, 0, 0, 0.95);
          border-radius: 12px;
          padding: 16px;
          min-width: 280px;
          max-width: 400px;
          color: white;
          font-family: 'Inter', sans-serif;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }

        .citation-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          gap: 12px;
        }

        .source-title {
          font-weight: 600;
          font-size: 14px;
          line-height: 1.3;
          flex: 1;
        }

        .credibility-badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 10px;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          white-space: nowrap;
        }

        .citation-content {
          margin-bottom: 12px;
        }

        .preview-text {
          font-style: italic;
          color: rgba(255, 255, 255, 0.9);
          font-size: 13px;
          line-height: 1.4;
          margin-bottom: 10px;
          padding: 8px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 6px;
          border-left: 3px solid rgba(255, 255, 255, 0.3);
        }

        .citation-meta {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.7);
        }

        .full-citation {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
          line-height: 1.3;
          padding-top: 8px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .citation-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }

        .expand-button, .view-source-button {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 500;
        }

        .expand-button {
          background: rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .expand-button:hover {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }

        .view-source-button {
          background: #6c5ce7;
          color: white;
        }

        .view-source-button:hover {
          background: #5f3dc4;
        }
      `}</style>
    </>
  );
};
