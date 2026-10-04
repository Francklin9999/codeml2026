import type { FrameResult } from '../contracts';

export interface Preview {
  update(frame: FrameResult): void;
  dispose(): void;
}

/**
 * 3D preview of the frame. three.js is loaded on demand (frame screen only).
 * Resolves with null where WebGL is not available: the screen then shows its own note and everything else still works.
 */
export async function createPreview(host: HTMLElement): Promise<Preview | null> {
  try {
    const THREE = await import('three');
    const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls.js');
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    const canvas = renderer.domElement;
    canvas.style.touchAction = 'none'; // one finger orbits, two pinch: the page must not scroll under it
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    host.append(canvas);

    const scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x888888, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.4);
    sun.position.set(0.5, 1, 1.5);
    scene.add(sun);
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 2000);
    const controls = new OrbitControls(camera, canvas);
    controls.enablePan = false;
    let mesh: import('three').Mesh | null = null;

    const render = () => renderer.render(scene, camera);
    controls.addEventListener('change', render);
    const resize = () => {
      const w = Math.max(1, host.clientWidth), h = Math.max(1, host.clientHeight);
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      render();
    };
    const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
    observer?.observe(host);

    return {
      update(frame) {
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.BufferAttribute(frame.positions, 3));
        g.setIndex(new THREE.BufferAttribute(frame.indices, 1));
        g.computeVertexNormals();
        g.computeBoundingSphere();
        const first = !mesh;
        if (mesh) { scene.remove(mesh); mesh.geometry.dispose(); }
        mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0xd9dde3, roughness: 0.7, metalness: 0, flatShading: true }));
        scene.add(mesh);
        const s = g.boundingSphere!;
        controls.target.copy(s.center);
        if (first) {
          // Front view with a slight tilt, far enough for the whole frame to fit in the field of view.
          const d = (s.radius / Math.sin((camera.fov * Math.PI) / 360)) * 1.15;
          camera.position.set(s.center.x, s.center.y - d * 0.3, s.center.z + d * 0.95);
          camera.near = d / 50;
          camera.far = d * 10;
          camera.updateProjectionMatrix();
        }
        controls.update();
        render();
      },
      dispose() {
        observer?.disconnect();
        controls.dispose();
        mesh?.geometry.dispose();
        renderer.dispose();
        canvas.remove();
      },
    };
  } catch {
    return null;
  }
}
