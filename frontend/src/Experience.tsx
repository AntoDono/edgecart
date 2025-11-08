import { OrbitControls } from '@react-three/drei'
import { SparklingSphereR3F } from './components/SparklingSphereR3F'

export default function Experience() {
  return (
    <>
      <OrbitControls makeDefault />

      <directionalLight position={ [ 1, 2, 3 ] } intensity={ 1.5 } />
      <ambientLight intensity={ 0.5 } />
      <SparklingSphereR3F />
    </>
  )
}
