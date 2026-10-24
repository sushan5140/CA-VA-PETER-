import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const host = document.querySelector('#viewport');
const status = document.querySelector('#status');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
host.append(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color('#30343c');
const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
camera.position.set(2.4, 1.5, 3.5);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x596078, 2));
for (const [position, intensity] of [
  [[-3, 4, 4], 3], [[3, 2, -3], 2],
]) {
  const light = new THREE.DirectionalLight(0xffffff, intensity);
  light.position.set(...position);
  scene.add(light);
}
const grid = new THREE.GridHelper(4, 20, 0x777777, 0x555555);
scene.add(grid);

let model;
function resize() {
  const { width, height } = host.getBoundingClientRect();
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(host);
resize();

document.querySelector('#file').addEventListener('change', async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  status.textContent = `Loading ${file.name}…`;
  try {
    const data = await file.arrayBuffer();
    const gltf = await new GLTFLoader().parseAsync(data, '');
    if (model) scene.remove(model);
    model = gltf.scene;
    scene.add(model);
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z) * 1.8;
    if (!Number.isFinite(radius) || radius <= 0) throw new Error('Mesh has invalid bounds');
    controls.target.copy(center);
    camera.position.copy(center).add(new THREE.Vector3(radius, radius * 0.45, radius));
    camera.near = Math.max(radius / 1000, 0.001);
    camera.far = radius * 100;
    camera.updateProjectionMatrix();
    controls.update();
    let triangles = 0;
    let meshes = 0;
    let materials = 0;
    model.traverse(node => {
      if (!node.isMesh) return;
      meshes += 1;
      triangles += node.geometry.index ? node.geometry.index.count / 3 : node.geometry.attributes.position.count / 3;
      materials += Array.isArray(node.material) ? node.material.length : 1;
    });
    status.textContent = `${file.name} · ${meshes} meshes · ${Math.round(triangles).toLocaleString()} triangles · ${materials} material slots · ${size.y.toFixed(2)} world units high`;
  } catch (error) {
    status.textContent = `Could not load GLB: ${error.message}`;
  }
});

function frame() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
frame();
