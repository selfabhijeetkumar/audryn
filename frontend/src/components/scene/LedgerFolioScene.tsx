import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';

export interface LedgerFolioSceneProps {
  scrollProgress: number; // Continuous 0.0 to 1.0
  onStageChange?: (stage: number) => void;
  className?: string;
}

// Camera coordinates from Section 6.1 (folio width W = 1.0)
const CAMERA_POSITIONS = [
  new THREE.Vector3(0, 2.4, 0.2),     // S0: Fragmented (0-10%)
  new THREE.Vector3(0, 1.9, 0.9),     // S1: Extracted (15-25%)
  new THREE.Vector3(0, 1.6, 1.2),     // S2: Reconciled (30-40%)
  new THREE.Vector3(-0.8, 0.9, 1.0),  // S3: Related (45-55%)
  new THREE.Vector3(0.1, 0.35, 0.45), // S4: Challenged (60-70%)
  new THREE.Vector3(0, 0.9, 1.3),     // S5: Reviewed (75-85%)
  new THREE.Vector3(0.5, 0.7, 1.4),   // S6: Reported (90-100%)
];

const CAMERA_TARGETS = [
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(0.05, 0, 0),
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(0, 0.1, 0),
];

/**
 * Maps continuous scroll progress (0.0 to 1.0) to exact 7 holds and 6 transitions:
 * S0: 0–10%
 * Trans 0->1: 10–15%
 * S1: 15–25%
 * Trans 1->2: 25–30%
 * S2: 30–40%
 * Trans 2->3: 40–45%
 * S3: 45–55%
 * Trans 3->4: 55–60%
 * S4: 60–70%
 * Trans 4->5: 70–75%
 * S5: 75–85%
 * Trans 5->6: 85–90%
 * S6: 90–100%
 */
export function calculateStageAndInterpolation(p: number): {
  fromStage: number;
  toStage: number;
  t: number;
  activeStage: number;
} {
  const clamped = Math.max(0, Math.min(1, p));

  if (clamped <= 0.10) {
    return { fromStage: 0, toStage: 0, t: 0, activeStage: 0 };
  } else if (clamped < 0.15) {
    const t = (clamped - 0.10) / 0.05;
    return { fromStage: 0, toStage: 1, t, activeStage: t < 0.5 ? 0 : 1 };
  } else if (clamped <= 0.25) {
    return { fromStage: 1, toStage: 1, t: 0, activeStage: 1 };
  } else if (clamped < 0.30) {
    const t = (clamped - 0.25) / 0.05;
    return { fromStage: 1, toStage: 2, t, activeStage: t < 0.5 ? 1 : 2 };
  } else if (clamped <= 0.40) {
    return { fromStage: 2, toStage: 2, t: 0, activeStage: 2 };
  } else if (clamped < 0.45) {
    const t = (clamped - 0.40) / 0.05;
    return { fromStage: 2, toStage: 3, t, activeStage: t < 0.5 ? 2 : 3 };
  } else if (clamped <= 0.55) {
    return { fromStage: 3, toStage: 3, t: 0, activeStage: 3 };
  } else if (clamped < 0.60) {
    const t = (clamped - 0.55) / 0.05;
    return { fromStage: 3, toStage: 4, t, activeStage: t < 0.5 ? 3 : 4 };
  } else if (clamped <= 0.70) {
    return { fromStage: 4, toStage: 4, t: 0, activeStage: 4 };
  } else if (clamped < 0.75) {
    const t = (clamped - 0.70) / 0.05;
    return { fromStage: 4, toStage: 5, t, activeStage: t < 0.5 ? 4 : 5 };
  } else if (clamped <= 0.85) {
    return { fromStage: 5, toStage: 5, t: 0, activeStage: 5 };
  } else if (clamped < 0.90) {
    const t = (clamped - 0.85) / 0.05;
    return { fromStage: 5, toStage: 6, t, activeStage: t < 0.5 ? 5 : 6 };
  } else {
    return { fromStage: 6, toStage: 6, t: 0, activeStage: 6 };
  }
}

export const LedgerFolioScene: React.FC<LedgerFolioSceneProps> = ({
  scrollProgress,
  onStageChange,
  className = '',
}) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [tier, setTier] = useState<2 | 1 | 0>(2);
  const [isSupported, setIsSupported] = useState(true);

  const scrollRef = useRef(scrollProgress);
  scrollRef.current = scrollProgress;

  const lastReportedStage = useRef<number>(-1);

  // Check stage change and trigger callback
  useEffect(() => {
    const { activeStage } = calculateStageAndInterpolation(scrollProgress);
    if (activeStage !== lastReportedStage.current) {
      lastReportedStage.current = activeStage;
      onStageChange?.(activeStage);
    }
  }, [scrollProgress, onStageChange]);

  useEffect(() => {
    // 1. Eligibility Checks: Reduced motion, save-data, coarse pointer
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isExplicitlyReduced = document.documentElement.classList.contains('reduce-effects');
    const isSaveData = (navigator as unknown as { connection?: { saveData?: boolean } }).connection?.saveData === true;

    if (prefersReducedMotion || isExplicitlyReduced || isSaveData) {
      setTier(1); // Downgrade to CSS Tier 1
      return;
    }

    // 2. WebGL2 Context Health Probe
    try {
      const testCanvas = document.createElement('canvas');
      const gl = testCanvas.getContext('webgl2');
      if (!gl) {
        setTier(1);
        setIsSupported(false);
        return;
      }
    } catch {
      setTier(0);
      setIsSupported(false);
      return;
    }

    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 640;
    const height = container.clientHeight || 520;

    // 3. Single Shared WebGL2 Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x121110); // Charcoal Stage `#121110`

    const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
    const initialCalc = calculateStageAndInterpolation(scrollRef.current);
    camera.position.copy(CAMERA_POSITIONS[initialCalc.activeStage]);
    camera.lookAt(CAMERA_TARGETS[initialCalc.activeStage]);

    // Single WebGL Renderer instance
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.NeutralToneMapping || THREE.NoToneMapping;
    container.appendChild(renderer.domElement);

    // --- SCENE OBJECTS ---

    // A. Desk Plane
    const deskGeo = new THREE.PlaneGeometry(8, 8);
    const deskMat = new THREE.MeshStandardMaterial({
      color: 0x121110,
      roughness: 0.95,
      metalness: 0.05,
    });
    const desk = new THREE.Mesh(deskGeo, deskMat);
    desk.rotation.x = -Math.PI / 2;
    desk.position.y = -0.01;
    scene.add(desk);

    // B. The Columnar Ledger Folio (Double Page)
    const folioGroup = new THREE.Group();
    const folioGeo = new THREE.PlaneGeometry(1.2, 0.8);
    const folioMat = new THREE.MeshStandardMaterial({
      color: 0xF6F3EB, // Paper `#F6F3EB`
      roughness: 0.9,
      metalness: 0.0,
    });
    const folio = new THREE.Mesh(folioGeo, folioMat);
    folio.rotation.x = -Math.PI / 2;
    folioGroup.add(folio);

    // Center spine fold line
    const spineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0.001, -0.4),
      new THREE.Vector3(0, 0.001, 0.4),
    ]);
    const spineMat = new THREE.LineBasicMaterial({ color: 0xD8D4CC });
    const spine = new THREE.Line(spineGeo, spineMat);
    folioGroup.add(spine);

    // Etched Column Lines (Date, Particulars, Ref, Debit, Credit, Balance)
    const colXPositions = [-0.45, -0.15, -0.05, 0.15, 0.35];
    colXPositions.forEach((xPos) => {
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(xPos, 0.001, -0.38),
        new THREE.Vector3(xPos, 0.001, 0.38),
      ]);
      const lineMat = new THREE.LineBasicMaterial({ color: 0xE8E4DC });
      folioGroup.add(new THREE.Line(lineGeo, lineMat));
    });
    scene.add(folioGroup);

    // C. 36 Disordered Source Fragments
    const fragments: THREE.Mesh[] = [];
    const fragmentCount = 36;
    const fragGeo = new THREE.PlaneGeometry(0.12, 0.07);

    // Initial scatter positions
    const scatterPos: { pos: THREE.Vector3; rotZ: number }[] = [];
    for (let i = 0; i < fragmentCount; i++) {
      const fragMat = new THREE.MeshStandardMaterial({
        color: 0xFAF8F2,
        roughness: 0.85,
      });
      const frag = new THREE.Mesh(fragGeo, fragMat);
      frag.rotation.x = -Math.PI / 2;
      const angle = (i / fragmentCount) * Math.PI * 2 + (Math.sin(i) * 0.2);
      const dist = 0.55 + (i % 5) * 0.08;
      const p = new THREE.Vector3(Math.cos(angle) * dist, 0.002, Math.sin(angle) * dist);
      const rz = (i * 0.4) % Math.PI;
      frag.position.copy(p);
      frag.rotation.z = rz;
      scatterPos.push({ pos: p, rotZ: rz });
      scene.add(frag);
      fragments.push(frag);
    }

    // D. Translucent Acetate Counter-Evidence Sheet (S4)
    const acetateGeo = new THREE.PlaneGeometry(0.55, 0.12);
    const acetateMat = new THREE.MeshStandardMaterial({
      color: 0xB77F0A, // Amber tint
      transparent: true,
      opacity: 0.18,
      roughness: 0.1,
    });
    const acetate = new THREE.Mesh(acetateGeo, acetateMat);
    acetate.rotation.x = -Math.PI / 2;
    acetate.position.set(0.1, 0.005, 0.02);
    acetate.visible = false;
    scene.add(acetate);

    // E. Brass Sign-Off Stamp (S5 & S6)
    const brassGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.005, 32);
    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xB08D4F, // Brass Light
      metalness: 0.92,
      roughness: 0.38,
    });
    const brassStamp = new THREE.Mesh(brassGeo, brassMat);
    brassStamp.position.set(0.42, 0.006, 0.02);
    brassStamp.visible = false;
    scene.add(brassStamp);

    // F. Lighting
    const keyLight = new THREE.DirectionalLight(0xFFF7EB, 1.8);
    keyLight.position.set(-1.5, 3.0, 1.5);
    scene.add(keyLight);

    const hemiLight = new THREE.HemisphereLight(0xFDFBF7, 0x121110, 0.6);
    scene.add(hemiLight);

    // --- CURSOR TRAIL INSIDE SHARED WEBGL CONTEXT (Task 2 Requirement) ---
    // Single shared context, 14 Catmull-Rom spline points, 400ms decay, 120px max length, 2x2 terminal
    let isFinePointer = window.matchMedia('(pointer: fine) and (hover: hover)').matches;
    let cursorPaused = false;

    const maxTrailPoints = 14;
    const trailDecayMs = 400;
    const trailPositions: { x: number; y: number; time: number }[] = [];

    // Orthographic overlay camera for 2D cursor trail inside same WebGL renderer
    const orthoCam = new THREE.OrthographicCamera(0, width, height, 0, -1, 1);
    const trailScene = new THREE.Scene();

    const maxLinePoints = 32;
    const linePositions = new Float32Array(maxLinePoints * 3);
    const trailGeo = new THREE.BufferGeometry();
    trailGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));

    const trailMat = new THREE.LineBasicMaterial({
      color: 0xF6F3EB,
      transparent: true,
      opacity: 0.40, // 40% opacity on Stage
      linewidth: 1,
    });
    const trailLine = new THREE.Line(trailGeo, trailMat);
    trailScene.add(trailLine);

    // Terminal 2x2 square marker
    const termGeo = new THREE.PlaneGeometry(3, 3);
    const termMat = new THREE.MeshBasicMaterial({ color: 0xF6F3EB, transparent: true, opacity: 0.5 });
    const termMesh = new THREE.Mesh(termGeo, termMat);
    termMesh.visible = false;
    trailScene.add(termMesh);

    const onPointerMove = (e: PointerEvent) => {
      if (!isFinePointer) return;

      // Check if hovering over interactive UI (input, select, textarea, button, a)
      const target = e.target as HTMLElement | null;
      if (target && target.closest('button, input, select, textarea, a, [role="button"], [role="tab"]')) {
        cursorPaused = true;
        return;
      }
      cursorPaused = false;

      const rect = renderer.domElement.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
        trailPositions.push({ x, y, time: performance.now() });
        if (trailPositions.length > maxTrailPoints) {
          trailPositions.shift();
        }
      }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });

    // --- ANIMATION & CONTINUOUS CAMERA SCRIPT ---
    let animId: number;
    let slowFrames = 0;

    const animate = () => {
      const now = performance.now();
      const p = scrollRef.current;
      const { fromStage, toStage, t } = calculateStageAndInterpolation(p);

      // Smooth step easing for transition intervals
      const smoothT = t * t * (3 - 2 * t);

      // Interpolate camera position and target
      const camPosA = CAMERA_POSITIONS[fromStage];
      const camPosB = CAMERA_POSITIONS[toStage];
      camera.position.lerpVectors(camPosA, camPosB, smoothT);

      const camTargetA = CAMERA_TARGETS[fromStage];
      const camTargetB = CAMERA_TARGETS[toStage];
      const currentTarget = new THREE.Vector3().lerpVectors(camTargetA, camTargetB, smoothT);
      camera.lookAt(currentTarget);

      // Interpolate Fragment Positions
      fragments.forEach((frag, idx) => {
        const scatter = scatterPos[idx];
        if (p <= 0.10) {
          // S0: Scattered
          frag.position.copy(scatter.pos);
          frag.rotation.z = scatter.rotZ;
          frag.scale.set(1, 1, 1);
        } else if (p < 0.25) {
          // S0 -> S1 -> S1 hold: rotate square and align
          const progress = Math.min(1, Math.max(0, (p - 0.10) / 0.10));
          const targetX = -0.45 + (idx % 4) * 0.28;
          const targetZ = -0.3 + Math.floor(idx / 4) * 0.08;
          frag.rotation.z = THREE.MathUtils.lerp(scatter.rotZ, 0, progress);
          frag.position.x = THREE.MathUtils.lerp(scatter.pos.x, targetX, progress);
          frag.position.z = THREE.MathUtils.lerp(scatter.pos.z, targetZ, progress);
          frag.scale.set(1, 1, 1);
        } else {
          // S2 onwards: Reconciled into ledger rows
          const progress = Math.min(1, Math.max(0, (p - 0.25) / 0.10));
          const targetX = 0.2;
          const targetZ = -0.28 + (idx % 8) * 0.07;
          frag.position.x = THREE.MathUtils.lerp(frag.position.x, targetX, progress);
          frag.position.z = THREE.MathUtils.lerp(frag.position.z, targetZ, progress);
          frag.scale.set(0.7, 0.7, 0.7);
        }
      });

      // Acetate Sheet (S4: 60-70%)
      if (p >= 0.55 && p <= 0.75) {
        acetate.visible = true;
        const opacityT = p < 0.60 ? (p - 0.55) / 0.05 : p > 0.70 ? (0.75 - p) / 0.05 : 1;
        acetateMat.opacity = 0.18 * opacityT;
      } else {
        acetate.visible = false;
      }

      // Brass Sign-Off Stamp (S5 & S6: 75%+)
      if (p >= 0.70) {
        brassStamp.visible = true;
        const scaleT = Math.min(1, (p - 0.70) / 0.05);
        brassStamp.scale.set(scaleT, scaleT, scaleT);
      } else {
        brassStamp.visible = false;
      }

      // --- RENDER 3D SCENE ---
      renderer.autoClear = true;
      renderer.render(scene, camera);

      // --- RENDER CURSOR TRAIL ON TOP IN SAME CONTEXT ---
      while (trailPositions.length > 0 && now - trailPositions[0].time > trailDecayMs) {
        trailPositions.shift();
      }

      if (!cursorPaused && trailPositions.length >= 2) {
        const points2D = trailPositions.map((pt) => new THREE.Vector2(pt.x, height - pt.y));
        const curve = new THREE.SplineCurve(points2D);
        const curvePoints = curve.getPoints(maxLinePoints - 1);

        for (let i = 0; i < curvePoints.length; i++) {
          linePositions[i * 3] = curvePoints[i].x;
          linePositions[i * 3 + 1] = curvePoints[i].y;
          linePositions[i * 3 + 2] = 0;
        }
        trailGeo.attributes.position.needsUpdate = true;
        trailGeo.setDrawRange(0, curvePoints.length);

        termMesh.visible = true;
        termMesh.position.set(points2D[0].x, points2D[0].y, 0);

        renderer.autoClear = false;
        renderer.render(trailScene, orthoCam);
      } else {
        trailGeo.setDrawRange(0, 0);
        termMesh.visible = false;
      }

      // Performance monitoring: 30 consecutive frames > 22ms -> automatic demotion
      const frameDuration = performance.now() - now;
      if (frameDuration > 22) {
        slowFrames++;
        if (slowFrames > 30) {
          setTier(1); // Demote to Tier 1
          return;
        }
      } else {
        slowFrames = 0;
      }

      animId = requestAnimationFrame(animate);
    };

    animId = requestAnimationFrame(animate);

    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      orthoCam.right = newWidth;
      orthoCam.top = newHeight;
      orthoCam.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize, { passive: true });

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', onPointerMove);
      renderer.dispose();
      deskGeo.dispose();
      deskMat.dispose();
      folioGeo.dispose();
      folioMat.dispose();
      fragGeo.dispose();
      acetateGeo.dispose();
      acetateMat.dispose();
      brassGeo.dispose();
      brassMat.dispose();
      trailGeo.dispose();
      trailMat.dispose();
      termGeo.dispose();
      termMat.dispose();
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // --- TIER 1 & TIER 0 FALLBACKS ---
  if (tier < 2 || !isSupported) {
    const { activeStage } = calculateStageAndInterpolation(scrollProgress);
    return (
      <div
        className={`relative w-full h-[520px] bg-[#121110] border border-[#2A2724] p-6 flex flex-col items-center justify-center text-center overflow-hidden ${className}`}
        aria-hidden="true"
      >
        <div className="max-w-md space-y-4">
          <div className="w-16 h-12 mx-auto border border-[#B08D4F] bg-[#1A1816] flex items-center justify-center text-[#B08D4F] font-mono text-xs">
            S{activeStage}
          </div>
          <h4 className="font-serif text-lg text-[#F6F3EB]">
            The Indexed Ledger Folio (Tier {tier} Mode)
          </h4>
          <p className="text-xs text-[#9C968F] font-sans leading-relaxed">
            {activeStage === 0 && 'S0: Disordered physical source fragments arrive around an empty ledger.'}
            {activeStage === 1 && 'S1: Deterministic extraction aligns records with SHA-256 provenance integrity.'}
            {activeStage === 2 && 'S2: Reconciled ledger rows calculate exact balances without float distortion.'}
            {activeStage === 3 && 'S3: Multi-agent intelligence maps cross-year dependencies and tax rules.'}
            {activeStage === 4 && 'S4: Counter-evidence agent challenges preliminary findings with contradictory proofs.'}
            {activeStage === 5 && 'S5: Human auditor stamps statutory approval with licensed CA sign-off in brass.'}
            {activeStage === 6 && 'S6: Reproducible audit working papers bound into indexed report manifest.'}
          </p>
          <div className="font-mono text-[10px] text-[#7A746A] uppercase tracking-wider">
            SYNTHETIC DATA · REAL DOM PARITY AVAILABLE BELOW
          </div>
        </div>
      </div>
    );
  }

  const { activeStage } = calculateStageAndInterpolation(scrollProgress);

  return (
    <div className={`relative w-full h-full min-h-[480px] ${className}`}>
      {/* Single Shared WebGL Canvas Container */}
      <div
        ref={mountRef}
        className="w-full h-full min-h-[480px]"
        aria-hidden="true"
      />

      {/* Synchronized Status Pill */}
      <div className="absolute bottom-3 left-4 px-2.5 py-1 bg-[#121110]/85 backdrop-blur-sm border border-[#2A2724] font-mono text-[10px] text-[#9C968F] select-none flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[#B08D4F]" />
        <span>
          STAGE S{activeStage}:{' '}
          <strong className="text-[#F6F3EB]">
            {['FRAGMENTED', 'EXTRACTED', 'RECONCILED', 'RELATED', 'CHALLENGED', 'REVIEWED', 'REPORTED'][activeStage]}
          </strong>{' '}
          ({Math.round(scrollProgress * 100)}% SCROLL)
        </span>
      </div>
    </div>
  );
};
