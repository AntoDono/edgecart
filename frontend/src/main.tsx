import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'
import Experience from './Experience'
import { Canvas } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import Balatro from './components/Balatro'
import SimpleGlass from './components/SimpleGlass'
import LogoLoop from './components/LogoLoop'
import AdminLogin from './components/AdminLogin'
import { RiAnthropicFill } from "react-icons/ri"

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div style={{ width: '100vw', height: '100vh', position: 'fixed', top: 0, left: 0, backgroundColor: '#000000' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0 }}>
        <Balatro
          isRotate={false}
          mouseInteraction={true}
          pixelFilter={6969}
          color1="#101111ff"
          color2="#2a382aff"
          color3="#000000ff"
          spinRotation={-2.0}
          spinSpeed={7.0}
          contrast={1.5}
          lighting={0.4}
          spinAmount={0.25}
          spinEase={1.0}
        />
      </div>

      {/* Title Loop - Top Center */}
      <div style={{
        position: 'fixed',
        top: 'calc(50% - 325px)',
        left: 'calc(4rem + 450px)',
        right: 'calc(4rem + 450px)',
        zIndex: 3,
      }}>
        <LogoLoop
          logos={[
            { node: <img src="/edgecart.png" alt="edgecart" style={{ filter: 'brightness(0) invert(1)', transform: 'translateY(3px)' }} /> },
            { node: <span style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, color: '#ffffff' }}>✦</span> },
            { node: <img src="/edgecart.png" alt="edgecart" style={{ filter: 'brightness(0) invert(1)', transform: 'translateY(3px)' }} /> },
            { node: <span style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, color: '#ffffff' }}>✦</span> },
          ]}
          speed={50}
          direction="left"
          logoHeight={40}
          gap={48}
          pauseOnHover={false}
          fadeOut={true}
        />
      </div>

      {/* Subtitle - Below Title */}
      <div style={{
        position: 'fixed',
        top: 'calc(50% - 325px + 50px)',
        left: 'calc(4rem + 450px)',
        right: 'calc(4rem + 450px)',
        zIndex: 3,
        display: 'flex',
        justifyContent: 'center',
      }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, fontSize: '1rem', color: '#ffffff', textTransform: 'lowercase', margin: 0, opacity: 0.7 }}>
          finding alpha in grocery arbitrage
        </p>
      </div>

      {/* Glass Surface - Left Side */}
      <div style={{
        position: 'fixed',
        left: '4rem',
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 2,
      }}>
        <SimpleGlass width={450} height={650} borderRadius={0}>
          <AdminLogin />
        </SimpleGlass>
      </div>

      {/* Glass Surface - Right Side */}
      <div style={{
        position: 'fixed',
        right: '4rem',
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 2,
      }}>
        <SimpleGlass width={450} height={650} borderRadius={0}>
          <h2 style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, fontSize: '2rem', color: '#ffffff', textTransform: 'lowercase' }}>
            suscart
          </h2>
        </SimpleGlass>
      </div>

      {/* Made With - Above Logo Loop */}
      <div style={{
        position: 'fixed',
        bottom: 'calc(50% - 325px + 50px)',
        left: 'calc(4rem + 450px)',
        right: 'calc(4rem + 450px)',
        zIndex: 3,
        display: 'flex',
        justifyContent: 'center',
      }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, fontSize: '1rem', color: '#ffffff', textTransform: 'lowercase', margin: 0, opacity: 0.7 }}>
          made at hackprinceton with ♥︎ using
        </p>
      </div>

      {/* LogoLoop - Bottom Center */}
      <div style={{
        position: 'fixed',
        bottom: 'calc(50% - 325px)',
        left: 'calc(4rem + 450px)',
        right: 'calc(4rem + 450px)',
        zIndex: 3,
      }}>
        <LogoLoop
          logos={[
            { node: <RiAnthropicFill style={{ color: '#ffffff' }} /> },
            { node: <span style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, color: '#ffffff' }}>✦</span> },
            { node: <RiAnthropicFill style={{ color: '#ffffff' }} /> },
            { node: <span style={{ fontFamily: '"Geist Mono", monospace', fontWeight: 100, color: '#ffffff' }}>✦</span> },
          ]}
          speed={50}
          direction="right"
          logoHeight={40}
          gap={48}
          pauseOnHover={false}
          fadeOut={true}
        />
      </div>

      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1 }}>
        <Canvas
          style={{ width: '100%', height: '100%', pointerEvents: 'auto' }}
          gl={{
            antialias: true,
            toneMapping: 3, // ACESFilmicToneMapping
            outputEncoding: 3, // sRGBEncoding
            alpha: true,
          }}
          dpr={[1, 2]}
          camera={{
            fov: 45,
            near: 0.1,
            far: 200,
            position: [0, 0, 6]
          }}
        >
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
    </div>
  </StrictMode>
)
