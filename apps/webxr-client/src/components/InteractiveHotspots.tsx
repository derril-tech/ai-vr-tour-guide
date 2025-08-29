import React, { useState, useRef, useCallback } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Vector3, Color } from 'three';
import { useStore } from '../store/useStore';

interface Hotspot {
  id: string;
  position: [number, number, number];
  title: string;
  description: string;
  narratives: {
    id: string;
    title: string;
    content: string;
    duration: number;
    branches?: { id: string; title: string; condition?: string }[];
  }[];
  interactionType: 'click' | 'proximity' | 'gaze';
  visualStyle: {
    color: string;
    size: number;
    animation: 'pulse' | 'rotate' | 'float' | 'static';
  };
  unlocked: boolean;
  visited: boolean;
}

interface InteractiveHotspotsProps {
  hotspots: Hotspot[];
  onHotspotActivated: (hotspot: Hotspot, narrativeId?: string) => void;
  userPosition: Vector3;
}

export const InteractiveHotspots: React.FC<InteractiveHotspotsProps> = ({
  hotspots,
  onHotspotActivated,
  userPosition
}) => {
  const [activeHotspot, setActiveHotspot] = useState<string | null>(null);
  const [hoveredHotspot, setHoveredHotspot] = useState<string | null>(null);
  const [selectedNarrative, setSelectedNarrative] = useState<string | null>(null);
  const hotspotRefs = useRef<{ [key: string]: any }>({});
  
  const { currentNarrative, setCurrentNarrative } = useStore();

  // Animation loop
  useFrame((state) => {
    const time = state.clock.elapsedTime;
    
    hotspots.forEach((hotspot) => {
      const ref = hotspotRefs.current[hotspot.id];
      if (!ref) return;

      switch (hotspot.visualStyle.animation) {
        case 'pulse':
          const pulseScale = 1 + Math.sin(time * 3) * 0.2;
          ref.scale.setScalar(pulseScale);
          break;
          
        case 'rotate':
          ref.rotation.y = time * 0.5;
          break;
          
        case 'float':
          ref.position.y = hotspot.position[1] + Math.sin(time * 2) * 0.1;
          break;
          
        default:
          break;
      }

      // Proximity detection
      if (hotspot.interactionType === 'proximity') {
        const distance = new Vector3(...hotspot.position).distanceTo(userPosition);
        if (distance < 2 && !hotspot.visited) {
          handleHotspotActivation(hotspot);
        }
      }
    });
  });

  const handleHotspotActivation = useCallback((hotspot: Hotspot, narrativeId?: string) => {
    if (!hotspot.unlocked) return;
    
    setActiveHotspot(hotspot.id);
    
    if (narrativeId) {
      setSelectedNarrative(narrativeId);
      onHotspotActivated(hotspot, narrativeId);
    } else if (hotspot.narratives.length === 1) {
      // Auto-select single narrative
      onHotspotActivated(hotspot, hotspot.narratives[0].id);
    }
    // Otherwise, show narrative selection
  }, [onHotspotActivated]);

  const handleNarrativeSelection = useCallback((hotspot: Hotspot, narrativeId: string) => {
    setSelectedNarrative(narrativeId);
    setActiveHotspot(null);
    onHotspotActivated(hotspot, narrativeId);
  }, [onHotspotActivated]);

  const getHotspotColor = (hotspot: Hotspot): string => {
    if (!hotspot.unlocked) return '#666666';
    if (hotspot.visited) return '#4CAF50';
    if (hoveredHotspot === hotspot.id) return '#FF6B6B';
    return hotspot.visualStyle.color;
  };

  const getHotspotOpacity = (hotspot: Hotspot): number => {
    if (!hotspot.unlocked) return 0.3;
    if (activeHotspot === hotspot.id) return 1.0;
    if (hoveredHotspot === hotspot.id) return 0.9;
    return 0.7;
  };

  return (
    <>
      {hotspots.map((hotspot) => (
        <group key={hotspot.id}>
          {/* Main Hotspot Sphere */}
          <mesh
            ref={(ref) => (hotspotRefs.current[hotspot.id] = ref)}
            position={hotspot.position}
            onClick={() => hotspot.interactionType === 'click' && handleHotspotActivation(hotspot)}
            onPointerEnter={() => setHoveredHotspot(hotspot.id)}
            onPointerLeave={() => setHoveredHotspot(null)}
          >
            <sphereGeometry args={[hotspot.visualStyle.size, 16, 16]} />
            <meshStandardMaterial
              color={getHotspotColor(hotspot)}
              transparent
              opacity={getHotspotOpacity(hotspot)}
              emissive={getHotspotColor(hotspot)}
              emissiveIntensity={hotspot.unlocked ? 0.2 : 0.05}
            />
          </mesh>

          {/* Hotspot Ring Effect */}
          {hotspot.unlocked && !hotspot.visited && (
            <mesh position={hotspot.position}>
              <ringGeometry args={[hotspot.visualStyle.size * 1.2, hotspot.visualStyle.size * 1.5, 32]} />
              <meshBasicMaterial
                color={hotspot.visualStyle.color}
                transparent
                opacity={0.3}
                side={2}
              />
            </mesh>
          )}

          {/* Hotspot Label */}
          {(hoveredHotspot === hotspot.id || activeHotspot === hotspot.id) && (
            <Html
              position={[
                hotspot.position[0],
                hotspot.position[1] + hotspot.visualStyle.size + 0.5,
                hotspot.position[2]
              ]}
              center
              distanceFactor={10}
            >
              <div className="hotspot-label">
                <div className="hotspot-title">{hotspot.title}</div>
                {hotspot.unlocked ? (
                  <div className="hotspot-description">{hotspot.description}</div>
                ) : (
                  <div className="hotspot-locked">🔒 Locked</div>
                )}
              </div>
            </Html>
          )}

          {/* Narrative Selection Panel */}
          {activeHotspot === hotspot.id && hotspot.narratives.length > 1 && (
            <Html
              position={[
                hotspot.position[0] + 1,
                hotspot.position[1],
                hotspot.position[2]
              ]}
              center
              distanceFactor={8}
            >
              <div className="narrative-selection-panel">
                <div className="panel-header">
                  <h3>Choose Your Path</h3>
                  <button
                    onClick={() => setActiveHotspot(null)}
                    className="close-button"
                  >
                    ×
                  </button>
                </div>
                
                <div className="narrative-options">
                  {hotspot.narratives.map((narrative) => (
                    <div
                      key={narrative.id}
                      className="narrative-option"
                      onClick={() => handleNarrativeSelection(hotspot, narrative.id)}
                    >
                      <div className="narrative-title">{narrative.title}</div>
                      <div className="narrative-duration">
                        ~{narrative.duration} min
                      </div>
                      <div className="narrative-preview">
                        {narrative.content.substring(0, 100)}...
                      </div>
                      
                      {narrative.branches && (
                        <div className="narrative-branches">
                          <small>Leads to: {narrative.branches.length} more paths</small>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </Html>
          )}

          {/* Progress Indicator */}
          {hotspot.visited && (
            <Html
              position={[
                hotspot.position[0] + hotspot.visualStyle.size + 0.2,
                hotspot.position[1] + hotspot.visualStyle.size + 0.2,
                hotspot.position[2]
              ]}
              center
              distanceFactor={15}
            >
              <div className="progress-indicator">✓</div>
            </Html>
          )}
        </group>
      ))}

      <style jsx>{`
        .hotspot-label {
          background: rgba(0, 0, 0, 0.8);
          border-radius: 8px;
          padding: 12px;
          color: white;
          font-family: 'Inter', sans-serif;
          text-align: center;
          min-width: 150px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .hotspot-title {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 6px;
        }

        .hotspot-description {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.3;
        }

        .hotspot-locked {
          font-size: 12px;
          color: #ff6b6b;
          font-weight: 500;
        }

        .narrative-selection-panel {
          background: rgba(0, 0, 0, 0.95);
          border-radius: 12px;
          padding: 20px;
          color: white;
          font-family: 'Inter', sans-serif;
          min-width: 320px;
          max-width: 400px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
          backdrop-filter: blur(15px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .panel-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .close-button {
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.6);
          font-size: 24px;
          cursor: pointer;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          transition: all 0.2s;
        }

        .close-button:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }

        .narrative-options {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .narrative-option {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .narrative-option:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
        }

        .narrative-title {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 6px;
        }

        .narrative-duration {
          font-size: 11px;
          color: #4ecdc4;
          margin-bottom: 8px;
          font-weight: 500;
        }

        .narrative-preview {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.7);
          line-height: 1.4;
          margin-bottom: 8px;
        }

        .narrative-branches {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.5);
          font-style: italic;
        }

        .progress-indicator {
          background: #4CAF50;
          color: white;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: bold;
          box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
        }
      `}</style>
    </>
  );
};
