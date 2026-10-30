# Three.js in React

TODO(team): decide between plain Three.js in a component and React Three Fiber (`@react-three/fiber` + `@react-three/drei`). For apps with many scenes or interactive 3D UI, React Three Fiber is usually easier to maintain.

## Plain Three.js component skeleton

```tsx
export function Scene({ data }: { data: Point[] }) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    // ... build meshes from data

    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    });
    ro.observe(mount);

    let frame = 0;
    const tick = () => { renderer.render(scene, camera); frame = requestAnimationFrame(tick); };
    tick();

    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
      scene.traverse(obj => {
        if ((obj as THREE.Mesh).isMesh) {
          const mesh = obj as THREE.Mesh;
          mesh.geometry.dispose();
          const m = mesh.material;
          (Array.isArray(m) ? m : [m]).forEach(mat => mat.dispose());
        }
      });
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [data]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} role="img" aria-label="..." />;
}
```

## Performance

- Many similar objects -> `InstancedMesh`, not thousands of meshes.
- Render on demand (only when something changes) for mostly static scenes instead of a constant loop.
- Cap pixel ratio at 2. Compress models (glTF + Draco/meshopt) and textures (KTX2).
- Dispose geometries, materials, and textures you replace, not only on unmount.

## Interaction and accessibility

- Picking with `Raycaster` on pointer events; throttle pointermove.
- Offer non-3D access to the same information (a list or table) and respect `prefers-reduced-motion`.
- Detect WebGL failure and render a fallback message.
