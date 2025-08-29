import { Canvas } from '@react-three/fiber'
import { XR, VRButton, ARButton, Controllers, Hands } from '@react-three/xr'
import { OrbitControls, Environment, Sky } from '@react-three/drei'
import { Suspense } from 'react'
import { Scene } from './components/Scene'
import { UI } from './components/UI'
import { useStore } from './store/useStore'
import './App.css'

function App() {
  const { isVRSupported, isARSupported } = useStore()

  return (
    <div className="app">
      {/* VR/AR Entry Buttons */}
      <div className="xr-buttons">
        {isVRSupported && <VRButton />}
        {isARSupported && <ARButton />}
      </div>

      {/* Main 3D Canvas */}
      <Canvas
        camera={{ position: [0, 1.6, 3], fov: 60 }}
        gl={{ antialias: true }}
      >
        <XR>
          <Suspense fallback={null}>
            {/* Environment */}
            <Environment preset="sunset" />
            <Sky />
            
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 10, 5]} intensity={1} />
            
            {/* XR Controllers */}
            <Controllers />
            <Hands />
            
            {/* Main Scene */}
            <Scene />
            
            {/* Fallback Controls for Non-XR */}
            <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
          </Suspense>
        </XR>
      </Canvas>

      {/* 2D UI Overlay */}
      <UI />
    </div>
  )
}

export default App
