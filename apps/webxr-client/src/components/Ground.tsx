import { Plane } from '@react-three/drei'

export function Ground() {
  return (
    <Plane
      args={[50, 50]}
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, 0, 0]}
      receiveShadow
    >
      <meshStandardMaterial
        color="#2d5a27"
        roughness={0.8}
        metalness={0.1}
      />
    </Plane>
  )
}
