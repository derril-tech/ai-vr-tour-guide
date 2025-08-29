import { useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Sphere } from '@react-three/drei'
import { Mesh } from 'three'
import { useStore } from '../store/useStore'

interface HotspotProps {
  hotspot: {
    id: string
    position: [number, number, number]
    title: string
    description: string
    type: 'info' | 'audio' | 'video' | 'quiz'
    content?: any
  }
  position: [number, number, number]
}

export function Hotspot({ hotspot, position }: HotspotProps) {
  const meshRef = useRef<Mesh>(null)
  const [hovered, setHovered] = useState(false)
  const { setCurrentHotspot, playAudio } = useStore()

  // Floating animation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.1
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.5
    }
  })

  const handleClick = () => {
    setCurrentHotspot(hotspot)
    
    // Play audio if available
    if (hotspot.type === 'audio' && hotspot.content?.audioUrl) {
      playAudio(hotspot.content.audioUrl)
    }
  }

  const getHotspotColor = () => {
    switch (hotspot.type) {
      case 'info': return '#4A90E2'
      case 'audio': return '#F5A623'
      case 'video': return '#D0021B'
      case 'quiz': return '#7ED321'
      default: return '#4A90E2'
    }
  }

  return (
    <group position={position}>
      {/* Main hotspot sphere */}
      <Sphere
        ref={meshRef}
        args={[0.2, 16, 16]}
        onClick={handleClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={getHotspotColor()}
          emissive={getHotspotColor()}
          emissiveIntensity={hovered ? 0.3 : 0.1}
          transparent
          opacity={hovered ? 0.9 : 0.7}
        />
      </Sphere>

      {/* Pulsing ring effect */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <ringGeometry args={[0.3, 0.4, 32]} />
        <meshBasicMaterial
          color={getHotspotColor()}
          transparent
          opacity={0.3}
        />
      </mesh>

      {/* Title text */}
      {hovered && (
        <Text
          position={[0, 0.5, 0]}
          fontSize={0.2}
          color="white"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.02}
          outlineColor="black"
        >
          {hotspot.title}
        </Text>
      )}
    </group>
  )
}
