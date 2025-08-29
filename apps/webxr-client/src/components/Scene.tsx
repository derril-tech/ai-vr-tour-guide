import { useRef, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { useXR } from '@react-three/xr'
import { Group } from 'three'
import { Hotspot } from './Hotspot'
import { Ground } from './Ground'
import { useStore } from '../store/useStore'

export function Scene() {
  const groupRef = useRef<Group>(null)
  const { isPresenting } = useXR()
  const { currentSite, setXRActive } = useStore()

  // Update XR state
  useEffect(() => {
    setXRActive(isPresenting)
  }, [isPresenting, setXRActive])

  // Animation loop
  useFrame((state) => {
    if (groupRef.current) {
      // Subtle floating animation for the scene
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.02
    }
  })

  return (
    <group ref={groupRef}>
      {/* Ground/Environment */}
      <Ground />
      
      {/* Site Content */}
      {currentSite && (
        <group position={currentSite.position}>
          {/* Site Hotspots */}
          {currentSite.hotspots.map((hotspot) => (
            <Hotspot
              key={hotspot.id}
              hotspot={hotspot}
              position={hotspot.position}
            />
          ))}
          
          {/* Site-specific 3D content would go here */}
          <mesh position={[0, 1, 0]}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="orange" />
          </mesh>
        </group>
      )}
      
      {/* Default scene when no site is loaded */}
      {!currentSite && (
        <group>
          <mesh position={[0, 1, 0]}>
            <sphereGeometry args={[0.5, 32, 32]} />
            <meshStandardMaterial color="lightblue" />
          </mesh>
          
          <mesh position={[2, 0.5, 0]}>
            <cylinderGeometry args={[0.3, 0.3, 1]} />
            <meshStandardMaterial color="green" />
          </mesh>
          
          <mesh position={[-2, 0.5, 0]}>
            <coneGeometry args={[0.4, 1]} />
            <meshStandardMaterial color="red" />
          </mesh>
        </group>
      )}
    </group>
  )
}
