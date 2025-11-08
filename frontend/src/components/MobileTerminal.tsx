import React from 'react';
import { FaGithub } from 'react-icons/fa';
import { SiDevpost } from 'react-icons/si';
import { Canvas } from '@react-three/fiber';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import Experience from '../Experience';
import CustomerLogin from './CustomerLogin';
import './MobileTerminal.css';

const MobileTerminal = () => {
  const asciiArt = `....................
.....+++++++*+*+:...
:*##-:+********:....
...+##==*****+-##=:.
...:*##==***==##*-..
....=###+-*=+###+...
.....####+:=*++=:...
.....-#++++++++-....
.......::.:::::.....
......-#*:..=**.....
....................`;

  return (
    <div className="mobile-terminal">
      {/* ORB Background */}
      <div className="mobile-background">
        <Canvas
          style={{ width: '100%', height: '100%', pointerEvents: 'auto' }}
          gl={{
            antialias: true,
            toneMapping: 3,
            outputEncoding: 3,
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

      {/* Top Header */}
      <div className="mobile-top-header">
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="mobile-header-icon"
        >
          <FaGithub />
        </a>

        <span className="mobile-header-spacer">✦</span>

        <div className="mobile-mlh-logo">
          <img src="/mlh.png" alt="MLH" />
        </div>

        <span className="mobile-header-spacer">✦</span>

        <a
          href="https://devpost.com"
          target="_blank"
          rel="noopener noreferrer"
          className="mobile-header-icon"
        >
          <SiDevpost />
        </a>
      </div>

      {/* Mobile Login Container */}
      <div className="mobile-login-container">
        {/* Login Component */}
        <div className="mobile-login">
          <CustomerLogin />
        </div>

        {/* Footer - ASCII Art */}
        <div className="mobile-footer">
          <pre className="mobile-ascii-art">{asciiArt}</pre>
          <p className="mobile-footer-text">made with ♥︎ at hackprinceton</p>
        </div>
      </div>
    </div>
  );
};

export default MobileTerminal;
