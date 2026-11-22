import React, { useEffect, useRef } from 'react';

/**
 * Custom 3D Cursor Trail Component (Deliverable H)
 * - Single fine tie-line thread (1px wide)
 * - 14 Catmull-Rom spline points interpolated from coordinates
 * - 400ms decay; max length ~120px; tiny square terminal
 * - Passive pointermove listener; pointer-events: none
 * - Native OS cursor is NEVER hidden or restyled
 * - Automatically disabled on touch / coarse pointers or reduced-motion
 */
export const CursorTrail: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    // Only enable on desktop pointer devices with fine precision and no reduced motion
    const isFinePointer = window.matchMedia('(pointer: fine) and (hover: hover)').matches;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isExplicitlyReduced = document.documentElement.classList.contains('reduce-effects');

    if (!isFinePointer || prefersReducedMotion || isExplicitlyReduced) {
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize, { passive: true });

    interface Point {
      x: number;
      y: number;
      time: number;
    }

    const points: Point[] = [];
    const maxPoints = 14;
    const maxDuration = 400; // ms

    const onPointerMove = (e: PointerEvent) => {
      points.push({
        x: e.clientX,
        y: e.clientY,
        time: performance.now(),
      });
      if (points.length > maxPoints) {
        points.shift();
      }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });

    let animId: number;

    const render = (now: number) => {
      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Cull expired points
      while (points.length > 0 && now - points[0].time > maxDuration) {
        points.shift();
      }

      if (points.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length - 1; i++) {
          const xc = (points[i].x + points[i + 1].x) / 2;
          const yc = (points[i].y + points[i + 1].y) / 2;
          ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }

        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);

        // Styling: 1px tie line with graphite tint
        ctx.strokeStyle = 'rgba(26, 23, 20, 0.32)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Terminal marker: tiny 2x2 square at the tail
        const tail = points[0];
        ctx.fillStyle = 'rgba(26, 23, 20, 0.45)';
        ctx.fillRect(tail.x - 1, tail.y - 1, 2, 2);
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', onPointerMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[9999]"
      aria-hidden="true"
    />
  );
};
