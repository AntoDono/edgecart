import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'
import Experience from './Experience'
import { Canvas } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div style={{ width: '100vw', height: '100vh', position: 'fixed', top: 0, left: 0 }}>
      <Canvas
        gl={{
          antialias: true,
          toneMapping: 3, // ACESFilmicToneMapping
          outputEncoding: 3, // sRGBEncoding
        }}
        dpr={[1, 2]}
        camera={{
          fov: 45,
          near: 0.1,
          far: 200,
          position: [0, 0, 6]
        }}
      >
        <color attach="background" args={['#000000']} />
        <Experience />
        <EffectComposer multisampling={8}>
          <Bloom
            intensity={2.0}
            luminanceThreshold={0.2}
            luminanceSmoothing={0.9}
            mipmapBlur
          />
        </EffectComposer>
      </Canvas>
    </div>
  </StrictMode>
)
