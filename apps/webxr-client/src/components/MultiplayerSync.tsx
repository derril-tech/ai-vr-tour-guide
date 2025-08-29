import React, { useState, useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Vector3, Color } from 'three';
import { useStore } from '../store/useStore';

interface MultiplayerUser {
  id: string;
  name: string;
  position: [number, number, number];
  rotation: [number, number, number, number];
  avatar_color: string;
  is_guide: boolean;
  current_waypoint: string;
  status: 'active' | 'idle' | 'disconnected';
}

interface GuidePointer {
  position: [number, number, number];
  target: [number, number, number];
  message: string;
  timestamp: number;
}

interface MultiplayerSyncProps {
  sessionId: string;
  userId: string;
  onUserJoined: (user: MultiplayerUser) => void;
  onUserLeft: (userId: string) => void;
  onGuidePointer: (pointer: GuidePointer) => void;
}

export const MultiplayerSync: React.FC<MultiplayerSyncProps> = ({
  sessionId,
  userId,
  onUserJoined,
  onUserLeft,
  onGuidePointer
}) => {
  const [connectedUsers, setConnectedUsers] = useState<MultiplayerUser[]>([]);
  const [guidePointer, setGuidePointer] = useState<GuidePointer | null>(null);
  const [isGuide, setIsGuide] = useState(false);
  const [showUserList, setShowUserList] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const userAvatarRefs = useRef<{ [key: string]: any }>({});
  const guidePointerRef = useRef<any>();
  
  const { userPosition, currentWaypoint } = useStore();

  // WebSocket connection for real-time sync
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8010/multiplayer/${sessionId}`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Connected to multiplayer session');
        
        // Send join message
        wsRef.current?.send(JSON.stringify({
          type: 'user_join',
          user_id: userId,
          session_id: sessionId,
          position: userPosition || [0, 1.7, 0],
          timestamp: Date.now()
        }));
      };
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };
      
      wsRef.current.onclose = () => {
        console.log('Disconnected from multiplayer session');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId, userId]);

  // Send position updates
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && userPosition) {
      const updateMessage = {
        type: 'position_update',
        user_id: userId,
        position: userPosition,
        waypoint: currentWaypoint,
        timestamp: Date.now()
      };
      
      wsRef.current.send(JSON.stringify(updateMessage));
    }
  }, [userPosition, currentWaypoint, userId]);

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'user_joined':
        const newUser: MultiplayerUser = message.user;
        setConnectedUsers(prev => [...prev.filter(u => u.id !== newUser.id), newUser]);
        onUserJoined(newUser);
        break;
        
      case 'user_left':
        setConnectedUsers(prev => prev.filter(u => u.id !== message.user_id));
        onUserLeft(message.user_id);
        break;
        
      case 'position_update':
        setConnectedUsers(prev => prev.map(user => 
          user.id === message.user_id 
            ? { ...user, position: message.position, current_waypoint: message.waypoint }
            : user
        ));
        break;
        
      case 'guide_pointer':
        const pointer: GuidePointer = message.pointer;
        setGuidePointer(pointer);
        onGuidePointer(pointer);
        
        // Auto-hide pointer after 10 seconds
        setTimeout(() => {
          setGuidePointer(null);
        }, 10000);
        break;
        
      case 'role_update':
        if (message.user_id === userId) {
          setIsGuide(message.is_guide);
        }
        setConnectedUsers(prev => prev.map(user =>
          user.id === message.user_id
            ? { ...user, is_guide: message.is_guide }
            : user
        ));
        break;
        
      case 'sync_waypoint':
        // Sync all users to the same waypoint
        useStore.getState().setCurrentWaypoint(message.waypoint_id);
        break;
    }
  };

  const sendGuidePointer = (targetPosition: [number, number, number], message: string) => {
    if (!isGuide || !wsRef.current) return;
    
    const pointer: GuidePointer = {
      position: userPosition || [0, 1.7, 0],
      target: targetPosition,
      message,
      timestamp: Date.now()
    };
    
    wsRef.current.send(JSON.stringify({
      type: 'guide_pointer',
      pointer,
      session_id: sessionId
    }));
  };

  const syncAllToWaypoint = (waypointId: string) => {
    if (!isGuide || !wsRef.current) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'sync_waypoint',
      waypoint_id: waypointId,
      session_id: sessionId
    }));
  };

  // Animate user avatars
  useFrame((state) => {
    const time = state.clock.elapsedTime;
    
    // Animate guide pointer
    if (guidePointerRef.current && guidePointer) {
      // Pulsing animation
      const scale = 1 + Math.sin(time * 4) * 0.2;
      guidePointerRef.current.scale.setScalar(scale);
      
      // Floating animation
      guidePointerRef.current.position.y = guidePointer.target[1] + Math.sin(time * 2) * 0.1;
    }
    
    // Animate user avatars
    Object.entries(userAvatarRefs.current).forEach(([userId, ref]) => {
      if (ref) {
        // Gentle bobbing animation
        const offset = userId.length * 0.5; // Unique offset per user
        ref.position.y += Math.sin(time * 2 + offset) * 0.005;
      }
    });
  });

  return (
    <>
      {/* Other User Avatars */}
      {connectedUsers.filter(user => user.id !== userId).map((user) => (
        <group key={user.id}>
          {/* User Avatar */}
          <mesh
            ref={(ref) => (userAvatarRefs.current[user.id] = ref)}
            position={user.position}
          >
            <capsuleGeometry args={[0.3, 1.4]} />
            <meshStandardMaterial
              color={user.avatar_color}
              transparent
              opacity={user.status === 'active' ? 0.8 : 0.4}
              emissive={user.is_guide ? '#FFD700' : user.avatar_color}
              emissiveIntensity={user.is_guide ? 0.2 : 0.05}
            />
          </mesh>

          {/* User Name Tag */}
          <Html
            position={[user.position[0], user.position[1] + 1, user.position[2]]}
            center
            distanceFactor={10}
          >
            <div className="user-nametag">
              <div className="user-name">
                {user.is_guide && '👑 '}
                {user.name}
              </div>
              <div className="user-status">
                {user.current_waypoint && (
                  <span className="waypoint-indicator">
                    📍 {user.current_waypoint}
                  </span>
                )}
              </div>
            </div>
          </Html>

          {/* Guide Crown Effect */}
          {user.is_guide && (
            <mesh position={[user.position[0], user.position[1] + 1.2, user.position[2]]}>
              <coneGeometry args={[0.1, 0.2, 6]} />
              <meshStandardMaterial
                color="#FFD700"
                emissive="#FFD700"
                emissiveIntensity={0.5}
              />
            </mesh>
          )}
        </group>
      ))}

      {/* Guide Pointer */}
      {guidePointer && (
        <group>
          {/* Pointer Beam */}
          <mesh
            position={[
              (guidePointer.position[0] + guidePointer.target[0]) / 2,
              (guidePointer.position[1] + guidePointer.target[1]) / 2,
              (guidePointer.position[2] + guidePointer.target[2]) / 2
            ]}
          >
            <cylinderGeometry args={[0.01, 0.01, 
              new Vector3(...guidePointer.position).distanceTo(new Vector3(...guidePointer.target))
            ]} />
            <meshBasicMaterial
              color="#FFD700"
              transparent
              opacity={0.6}
            />
          </mesh>

          {/* Target Indicator */}
          <mesh
            ref={guidePointerRef}
            position={guidePointer.target}
          >
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshStandardMaterial
              color="#FFD700"
              emissive="#FFD700"
              emissiveIntensity={0.5}
              transparent
              opacity={0.8}
            />
          </mesh>

          {/* Pointer Message */}
          <Html
            position={[
              guidePointer.target[0],
              guidePointer.target[1] + 0.5,
              guidePointer.target[2]
            ]}
            center
            distanceFactor={8}
          >
            <div className="guide-pointer-message">
              <div className="pointer-text">{guidePointer.message}</div>
              <div className="pointer-timestamp">
                {new Date(guidePointer.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </Html>
        </group>
      )}

      {/* Multiplayer UI */}
      <Html
        position={[2, 2, -3]}
        center
        distanceFactor={6}
      >
        <div className="multiplayer-ui">
          <div className="multiplayer-header">
            <button
              onClick={() => setShowUserList(!showUserList)}
              className="user-list-toggle"
            >
              👥 Users ({connectedUsers.length})
            </button>
            
            {isGuide && (
              <div className="guide-controls">
                <span className="guide-badge">👑 Guide</span>
              </div>
            )}
          </div>

          {showUserList && (
            <div className="user-list">
              {connectedUsers.map((user) => (
                <div key={user.id} className="user-item">
                  <div className="user-info">
                    <span className="user-avatar" style={{ backgroundColor: user.avatar_color }}></span>
                    <span className="user-name">
                      {user.is_guide && '👑 '}
                      {user.name}
                    </span>
                  </div>
                  <div className="user-status-indicator">
                    <span className={`status-dot ${user.status}`}></span>
                    {user.current_waypoint && (
                      <span className="current-waypoint">{user.current_waypoint}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {isGuide && (
            <div className="guide-actions">
              <button
                onClick={() => syncAllToWaypoint(currentWaypoint || 'entrance')}
                className="sync-button"
              >
                🔄 Sync All to Current
              </button>
            </div>
          )}
        </div>
      </Html>

      <style jsx>{`
        .user-nametag {
          background: rgba(0, 0, 0, 0.8);
          border-radius: 8px;
          padding: 8px 12px;
          color: white;
          font-family: 'Inter', sans-serif;
          text-align: center;
          min-width: 80px;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .user-name {
          font-weight: 600;
          font-size: 12px;
          margin-bottom: 4px;
        }

        .user-status {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.7);
        }

        .waypoint-indicator {
          background: rgba(76, 175, 80, 0.2);
          padding: 2px 6px;
          border-radius: 10px;
          border: 1px solid rgba(76, 175, 80, 0.4);
        }

        .guide-pointer-message {
          background: rgba(255, 215, 0, 0.95);
          color: #333;
          border-radius: 12px;
          padding: 12px 16px;
          font-family: 'Inter', sans-serif;
          text-align: center;
          min-width: 150px;
          box-shadow: 0 4px 16px rgba(255, 215, 0, 0.3);
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }

        .pointer-text {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 4px;
        }

        .pointer-timestamp {
          font-size: 10px;
          opacity: 0.7;
        }

        .multiplayer-ui {
          background: rgba(0, 0, 0, 0.9);
          border-radius: 12px;
          padding: 16px;
          color: white;
          font-family: 'Inter', sans-serif;
          min-width: 250px;
          backdrop-filter: blur(15px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .multiplayer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .user-list-toggle {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .user-list-toggle:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .guide-badge {
          background: linear-gradient(45deg, #FFD700, #FFA500);
          color: #333;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 10px;
          font-weight: 600;
        }

        .user-list {
          margin-bottom: 12px;
          max-height: 200px;
          overflow-y: auto;
        }

        .user-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          margin-bottom: 4px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .user-avatar {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .user-name {
          font-size: 12px;
          font-weight: 500;
        }

        .user-status-indicator {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .status-dot.active {
          background: #4CAF50;
          box-shadow: 0 0 4px rgba(76, 175, 80, 0.5);
        }

        .status-dot.idle {
          background: #FF9800;
        }

        .status-dot.disconnected {
          background: #F44336;
        }

        .current-waypoint {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.6);
        }

        .guide-actions {
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          padding-top: 12px;
        }

        .sync-button {
          width: 100%;
          background: #6c5ce7;
          border: none;
          color: white;
          padding: 10px;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 500;
        }

        .sync-button:hover {
          background: #5f3dc4;
          transform: translateY(-1px);
        }
      `}</style>
    </>
  );
};
