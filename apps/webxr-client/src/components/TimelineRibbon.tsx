import React, { useState, useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Vector3, CatmullRomCurve3, BufferGeometry, Float32BufferAttribute } from 'three';

interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  description: string;
  position: [number, number, number];
  era: string;
  importance: number; // 1-5 scale
  mediaUrl?: string;
  relatedEvents?: string[];
}

interface TimelineRibbonProps {
  events: TimelineEvent[];
  onEventSelected: (event: TimelineEvent) => void;
  onTimeTravel: (targetDate: string) => void;
  currentTime?: string;
}

export const TimelineRibbon: React.FC<TimelineRibbonProps> = ({
  events,
  onEventSelected,
  onTimeTravel,
  currentTime
}) => {
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<string | null>(null);
  const [isTimeScrubbingMode, setIsTimeScrubbingMode] = useState(false);
  const ribbonRef = useRef<any>();
  const timeMarkerRef = useRef<any>();

  // Sort events chronologically
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [events]);

  // Create ribbon curve
  const ribbonCurve = useMemo(() => {
    if (sortedEvents.length < 2) return null;
    
    const points = sortedEvents.map(event => new Vector3(...event.position));
    return new CatmullRomCurve3(points);
  }, [sortedEvents]);

  // Create ribbon geometry
  const ribbonGeometry = useMemo(() => {
    if (!ribbonCurve) return null;
    
    const points = ribbonCurve.getPoints(100);
    const geometry = new BufferGeometry();
    
    const vertices = [];
    const colors = [];
    const ribbonWidth = 0.1;
    
    for (let i = 0; i < points.length - 1; i++) {
      const current = points[i];
      const next = points[i + 1];
      
      // Calculate perpendicular vector for ribbon width
      const direction = next.clone().sub(current).normalize();
      const perpendicular = new Vector3(-direction.z, 0, direction.x).normalize();
      
      // Create ribbon quad
      const p1 = current.clone().add(perpendicular.clone().multiplyScalar(ribbonWidth));
      const p2 = current.clone().sub(perpendicular.clone().multiplyScalar(ribbonWidth));
      const p3 = next.clone().add(perpendicular.clone().multiplyScalar(ribbonWidth));
      const p4 = next.clone().sub(perpendicular.clone().multiplyScalar(ribbonWidth));
      
      // Add vertices for two triangles
      vertices.push(
        p1.x, p1.y, p1.z,
        p2.x, p2.y, p2.z,
        p3.x, p3.y, p3.z,
        
        p2.x, p2.y, p2.z,
        p4.x, p4.y, p4.z,
        p3.x, p3.y, p3.z
      );
      
      // Add colors (gradient based on time)
      const progress = i / (points.length - 1);
      const r = 0.2 + progress * 0.6;
      const g = 0.4 + Math.sin(progress * Math.PI) * 0.4;
      const b = 0.8 - progress * 0.4;
      
      for (let j = 0; j < 6; j++) {
        colors.push(r, g, b);
      }
    }
    
    geometry.setAttribute('position', new Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('color', new Float32BufferAttribute(colors, 3));
    
    return geometry;
  }, [ribbonCurve]);

  // Animation
  useFrame((state) => {
    if (ribbonRef.current) {
      // Gentle floating animation
      ribbonRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
    }
    
    if (timeMarkerRef.current && currentTime) {
      // Animate time marker position
      const progress = getTimeProgress(currentTime);
      if (ribbonCurve) {
        const position = ribbonCurve.getPoint(progress);
        timeMarkerRef.current.position.copy(position);
        timeMarkerRef.current.position.y += 0.2;
      }
    }
  });

  const getTimeProgress = (dateString: string): number => {
    if (sortedEvents.length === 0) return 0;
    
    const targetDate = new Date(dateString).getTime();
    const startDate = new Date(sortedEvents[0].date).getTime();
    const endDate = new Date(sortedEvents[sortedEvents.length - 1].date).getTime();
    
    return Math.max(0, Math.min(1, (targetDate - startDate) / (endDate - startDate)));
  };

  const getEventColor = (event: TimelineEvent): string => {
    const importanceColors = {
      5: '#FF6B6B', // Critical events
      4: '#4ECDC4', // Major events
      3: '#45B7D1', // Important events
      2: '#96CEB4', // Notable events
      1: '#FFEAA7'  // Minor events
    };
    return importanceColors[event.importance as keyof typeof importanceColors] || '#FFEAA7';
  };

  const handleEventClick = (event: TimelineEvent) => {
    setSelectedEvent(event.id);
    onEventSelected(event);
    
    if (isTimeScrubbingMode) {
      onTimeTravel(event.date);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <group>
      {/* Timeline Ribbon */}
      {ribbonGeometry && (
        <mesh ref={ribbonRef} geometry={ribbonGeometry}>
          <meshStandardMaterial
            vertexColors
            transparent
            opacity={0.8}
            emissiveIntensity={0.1}
          />
        </mesh>
      )}

      {/* Current Time Marker */}
      {currentTime && (
        <mesh ref={timeMarkerRef}>
          <coneGeometry args={[0.05, 0.2, 8]} />
          <meshStandardMaterial
            color="#FFD700"
            emissive="#FFD700"
            emissiveIntensity={0.3}
          />
        </mesh>
      )}

      {/* Event Markers */}
      {sortedEvents.map((event, index) => (
        <group key={event.id}>
          {/* Event Sphere */}
          <mesh
            position={event.position}
            onClick={() => handleEventClick(event)}
            onPointerEnter={() => setHoveredEvent(event.id)}
            onPointerLeave={() => setHoveredEvent(null)}
          >
            <sphereGeometry args={[0.08 + event.importance * 0.02, 16, 16]} />
            <meshStandardMaterial
              color={getEventColor(event)}
              emissive={getEventColor(event)}
              emissiveIntensity={hoveredEvent === event.id ? 0.4 : 0.1}
              transparent
              opacity={selectedEvent === event.id ? 1.0 : 0.8}
            />
          </mesh>

          {/* Event Info Panel */}
          {(hoveredEvent === event.id || selectedEvent === event.id) && (
            <Html
              position={[
                event.position[0],
                event.position[1] + 0.3,
                event.position[2]
              ]}
              center
              distanceFactor={8}
            >
              <div className="timeline-event-panel">
                <div className="event-header">
                  <div className="event-date">{formatDate(event.date)}</div>
                  <div className="event-era">{event.era}</div>
                </div>
                
                <div className="event-title">{event.title}</div>
                <div className="event-description">{event.description}</div>
                
                <div className="event-actions">
                  <button
                    onClick={() => onTimeTravel(event.date)}
                    className="time-travel-button"
                  >
                    🕰️ Travel Here
                  </button>
                  
                  {event.relatedEvents && event.relatedEvents.length > 0 && (
                    <button className="related-events-button">
                      🔗 Related ({event.relatedEvents.length})
                    </button>
                  )}
                </div>
              </div>
            </Html>
          )}

          {/* Importance Indicator */}
          {event.importance >= 4 && (
            <Html
              position={[
                event.position[0] + 0.1,
                event.position[1] + 0.1,
                event.position[2]
              ]}
              center
              distanceFactor={12}
            >
              <div className="importance-indicator">
                {'★'.repeat(event.importance)}
              </div>
            </Html>
          )}
        </group>
      ))}

      {/* Timeline Controls */}
      <Html
        position={[0, 3, -2]}
        center
        distanceFactor={6}
      >
        <div className="timeline-controls">
          <div className="control-header">
            <h3>Timeline Navigation</h3>
            <button
              onClick={() => setIsTimeScrubbingMode(!isTimeScrubbingMode)}
              className={`scrub-mode-button ${isTimeScrubbingMode ? 'active' : ''}`}
            >
              {isTimeScrubbingMode ? '🎬 Exit Scrub Mode' : '🎬 Time Scrub Mode'}
            </button>
          </div>
          
          <div className="timeline-info">
            <div className="era-legend">
              {Array.from(new Set(events.map(e => e.era))).map(era => (
                <div key={era} className="era-item">
                  <span className="era-dot"></span>
                  {era}
                </div>
              ))}
            </div>
            
            {currentTime && (
              <div className="current-time">
                Current: {formatDate(currentTime)}
              </div>
            )}
          </div>
        </div>
      </Html>

      <style jsx>{`
        .timeline-event-panel {
          background: rgba(0, 0, 0, 0.9);
          border-radius: 12px;
          padding: 16px;
          min-width: 250px;
          max-width: 350px;
          color: white;
          font-family: 'Inter', sans-serif;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
          backdrop-filter: blur(15px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          animation: fadeInUp 0.3s ease-out;
        }

        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .event-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .event-date {
          font-weight: 600;
          font-size: 12px;
          color: #4ECDC4;
        }

        .event-era {
          font-size: 10px;
          background: rgba(255, 255, 255, 0.1);
          padding: 2px 8px;
          border-radius: 12px;
          color: rgba(255, 255, 255, 0.8);
        }

        .event-title {
          font-weight: 600;
          font-size: 16px;
          margin-bottom: 8px;
          line-height: 1.3;
        }

        .event-description {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.4;
          margin-bottom: 12px;
        }

        .event-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .time-travel-button, .related-events-button {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 500;
        }

        .time-travel-button {
          background: #6c5ce7;
          color: white;
        }

        .time-travel-button:hover {
          background: #5f3dc4;
          transform: translateY(-1px);
        }

        .related-events-button {
          background: rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .related-events-button:hover {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }

        .importance-indicator {
          color: #FFD700;
          font-size: 12px;
          text-shadow: 0 0 4px rgba(255, 215, 0, 0.5);
        }

        .timeline-controls {
          background: rgba(0, 0, 0, 0.8);
          border-radius: 12px;
          padding: 20px;
          color: white;
          font-family: 'Inter', sans-serif;
          min-width: 300px;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .control-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .control-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .scrub-mode-button {
          padding: 8px 12px;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
          background: rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .scrub-mode-button.active {
          background: #4ECDC4;
          color: white;
          border-color: #4ECDC4;
        }

        .scrub-mode-button:hover {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }

        .scrub-mode-button.active:hover {
          background: #45b7b8;
        }

        .timeline-info {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .era-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }

        .era-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.7);
        }

        .era-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4ECDC4;
        }

        .current-time {
          font-size: 12px;
          color: #FFD700;
          font-weight: 500;
          text-align: center;
          padding: 8px;
          background: rgba(255, 215, 0, 0.1);
          border-radius: 6px;
          border: 1px solid rgba(255, 215, 0, 0.3);
        }
      `}</style>
    </group>
  );
};
