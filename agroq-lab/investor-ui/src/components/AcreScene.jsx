import { Html, OrbitControls, RoundedBox } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";

function SensorNode({ position, active = true, label }) {
  const pulse = useRef();

  useFrame(({ clock }) => {
    if (pulse.current) {
      const scale = 1 + Math.sin(clock.elapsedTime * 2.2) * 0.08;
      pulse.current.scale.setScalar(scale);
    }
  });

  return (
    <group position={position}>
      <mesh position={[0, 0.35, 0]}>
        <cylinderGeometry args={[0.08, 0.11, 0.7, 12]} />
        <meshStandardMaterial color="#364c42" metalness={0.55} roughness={0.4} />
      </mesh>
      <mesh ref={pulse} position={[0, 0.77, 0]}>
        <sphereGeometry args={[0.12, 20, 20]} />
        <meshStandardMaterial
          color={active ? "#58ef9b" : "#f0b35c"}
          emissive={active ? "#58ef9b" : "#f0b35c"}
          emissiveIntensity={1.2}
        />
      </mesh>
      <Html position={[0, 1.05, 0]} center distanceFactor={12}>
        <div className="sensor-label">{label}</div>
      </Html>
    </group>
  );
}

function FieldZone({ zone, selected, onSelect }) {
  const [hovered, setHovered] = useState(false);
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: zone.color,
        roughness: 0.82,
        metalness: 0.02,
        emissive: selected ? zone.color : "#000000",
        emissiveIntensity: selected ? 0.28 : hovered ? 0.1 : 0,
      }),
    [zone.color, selected, hovered],
  );

  return (
    <group position={zone.position}>
      <RoundedBox
        args={zone.size}
        radius={0.16}
        smoothness={4}
        material={material}
        onClick={(event) => {
          event.stopPropagation();
          onSelect(zone);
        }}
        onPointerEnter={(event) => {
          event.stopPropagation();
          setHovered(true);
          document.body.style.cursor = "pointer";
        }}
        onPointerLeave={() => {
          setHovered(false);
          document.body.style.cursor = "default";
        }}
      />
      <mesh position={[0, 0.17, 0]}>
        <boxGeometry args={[zone.size[0] * 0.9, 0.04, zone.size[2] * 0.8]} />
        <meshStandardMaterial color="#183d2a" roughness={1} />
      </mesh>
      {Array.from({ length: 8 }).map((_, row) => (
        <mesh
          key={row}
          position={[
            -zone.size[0] * 0.38 + row * (zone.size[0] * 0.108),
            0.23,
            0,
          ]}
        >
          <boxGeometry args={[0.035, 0.08, zone.size[2] * 0.7]} />
          <meshStandardMaterial color="#83c765" roughness={0.86} />
        </mesh>
      ))}
      {(hovered || selected) && (
        <Html position={[0, 0.78, 0]} center distanceFactor={9}>
          <div className="scene-label">
            <strong>{zone.name}</strong>
            <span>
              {zone.status} · {zone.moisture}% moisture
            </span>
          </div>
        </Html>
      )}
    </group>
  );
}

function Greenhouse() {
  return (
    <group position={[4.15, 0.62, -2.35]}>
      <RoundedBox args={[2.55, 1.25, 2.2]} radius={0.24} smoothness={4}>
        <meshPhysicalMaterial
          color="#c7f7e2"
          transparent
          opacity={0.28}
          roughness={0.15}
          transmission={0.2}
          thickness={0.4}
        />
      </RoundedBox>
      <mesh position={[0, 1.31, 0]} rotation={[0, 0, Math.PI / 4]}>
        <boxGeometry args={[1.8, 0.08, 2.25]} />
        <meshStandardMaterial color="#d9fbeb" metalness={0.45} roughness={0.3} />
      </mesh>
      <mesh position={[0, 0.11, 0]}>
        <boxGeometry args={[2.2, 0.12, 1.8]} />
        <meshStandardMaterial color="#31543f" roughness={0.9} />
      </mesh>
    </group>
  );
}

function GatewayTower({ offline }) {
  return (
    <group position={[4.25, 0.25, 0.65]}>
      <RoundedBox args={[1.15, 0.45, 1.05]} radius={0.12} smoothness={4}>
        <meshStandardMaterial color="#1b2b25" metalness={0.7} roughness={0.35} />
      </RoundedBox>
      <mesh position={[0, 1.15, 0]}>
        <cylinderGeometry args={[0.05, 0.07, 1.8, 10]} />
        <meshStandardMaterial color="#70897c" metalness={0.65} roughness={0.28} />
      </mesh>
      {[0.52, 0.82, 1.12].map((height) => (
        <mesh key={height} position={[0, height, 0]}>
          <torusGeometry args={[0.28, 0.015, 8, 32]} />
          <meshStandardMaterial
            color={offline ? "#efb464" : "#5ff3a2"}
            emissive={offline ? "#efb464" : "#5ff3a2"}
            emissiveIntensity={0.75}
          />
        </mesh>
      ))}
      <Html position={[0, 1.8, 0]} center distanceFactor={10}>
        <div className="gateway-label">
          Gateway · {offline ? "local-only" : "connected"}
        </div>
      </Html>
    </group>
  );
}

function Scene({ zones, selectedZone, onSelect, offline }) {
  return (
    <>
      <color attach="background" args={["#07110d"]} />
      <fog attach="fog" args={["#07110d", 13, 28]} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[8, 12, 5]} intensity={1.45} color="#e8fff0" />
      <pointLight position={[-6, 4, -4]} intensity={0.55} color="#63f3a3" />

      <mesh position={[0.45, -0.03, -0.9]}>
        <boxGeometry args={[12.5, 0.22, 8.5]} />
        <meshStandardMaterial color="#10271c" roughness={1} />
      </mesh>

      <mesh position={[0.45, 0.09, -0.9]}>
        <boxGeometry args={[11.9, 0.04, 7.9]} />
        <meshStandardMaterial color="#173624" roughness={1} />
      </mesh>

      {zones.map((zone) => (
        <FieldZone
          key={zone.id}
          zone={zone}
          selected={selectedZone?.id === zone.id}
          onSelect={onSelect}
        />
      ))}

      <Greenhouse />
      <GatewayTower offline={offline} />

      <SensorNode position={[-4.8, 0.14, -3.25]} label="S-01" />
      <SensorNode position={[-1.15, 0.14, -3.25]} label="S-02" />
      <SensorNode position={[-4.8, 0.14, 1.2]} label="S-03" />
      <SensorNode
        position={[-1.15, 0.14, 1.2]}
        label="S-04"
        active={!offline}
      />

      <OrbitControls
        enablePan
        enableZoom
        minDistance={8}
        maxDistance={19}
        minPolarAngle={0.65}
        maxPolarAngle={1.35}
        target={[0.3, 0, -0.8]}
      />
    </>
  );
}

export default function AcreScene({
  zones,
  selectedZone,
  onSelect,
  offline,
}) {
  return (
    <div className="acre-scene">
      <Canvas
        camera={{ position: [9.7, 9.4, 11.5], fov: 42 }}
        dpr={[1, 1.7]}
        shadows
      >
        <Scene
          zones={zones}
          selectedZone={selectedZone}
          onSelect={onSelect}
          offline={offline}
        />
      </Canvas>
      <div className="scene-hint">Drag to orbit · Scroll to zoom · Select a plot</div>
    </div>
  );
}
