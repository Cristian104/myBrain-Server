import * as THREE from 'three';

// --- Configuration ---
const config = {
    viscosity: 0.98,    // How thick the fluid is
    baseColor: new THREE.Color(0x0f3d2e), // Dark green
    simResolution: 256  // Lower res for blurrier effect
};

let renderer, scene, camera;
let fluidMaterial, quad;
let currentRenderTarget, nextRenderTarget;
let mouse = new THREE.Vector2(0.5, 0.5);

const container = document.getElementById('fluid-container');

function init() {
    const width = container.offsetWidth;
    const height = container.offsetHeight;

    // --- Renderer Setup ---
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- Scene & Camera ---
    scene = new THREE.Scene();
    camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    // --- Render Targets for Simulation (Ping-Pong) ---
    const rtOptions = {
        format: THREE.RGBAFormat,
        type: THREE.FloatType,
        minFilter: THREE.LinearFilter,
        magFilter: THREE.LinearFilter,
        wrapS: THREE.ClampToEdgeWrapping,
        wrapT: THREE.ClampToEdgeWrapping,
        depthBuffer: false,
        stencilBuffer: false
    };
    currentRenderTarget = new THREE.WebGLRenderTarget(config.simResolution, config.simResolution, rtOptions);
    nextRenderTarget = new THREE.WebGLRenderTarget(config.simResolution, config.simResolution, rtOptions);

    // --- Load Shaders and Create Material ---
    Promise.all([
        fetch('/static/auth/shaders/fluid.vert').then(r => r.text()),
        fetch('/static/auth/shaders/fluid.frag').then(r => r.text())
    ]).then(([vert, frag]) => {
        fluidMaterial = new THREE.ShaderMaterial({
            vertexShader: vert,
            fragmentShader: frag,
            uniforms: {
                uTexture: { value: null },
                uResolution: { value: new THREE.Vector2(config.simResolution, config.simResolution) },
                uMouse: { value: mouse },
                uTime: { value: 0 },
                uViscosity: { value: config.viscosity },
                uBaseColor: { value: config.baseColor }
            }
        });

        quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), fluidMaterial);
        scene.add(quad);

        animate();
    });

    // --- Event Listeners ---
    window.addEventListener('resize', onResize);
    container.addEventListener('mousemove', onMouseMove);
}

function onMouseMove(e) {
    const rect = container.getBoundingClientRect();
    mouse.x = (e.clientX - rect.left) / rect.width;
    mouse.y = 1.0 - (e.clientY - rect.top) / rect.height; // Flip Y
}

function onResize() {
    const width = container.offsetWidth;
    const height = container.offsetHeight;
    renderer.setSize(width, height);
}

function animate(time) {
    requestAnimationFrame(animate);

    if (!fluidMaterial) return;

    // --- Simulation Step ---
    // 1. Set current fluid state as input texture
    fluidMaterial.uniforms.uTexture.value = currentRenderTarget.texture;
    fluidMaterial.uniforms.uMouse.value = mouse;
    fluidMaterial.uniforms.uTime.value = time * 0.001;

    // 2. Render new state to 'next' target
    renderer.setRenderTarget(nextRenderTarget);
    renderer.render(scene, camera);

    // 3. Render the 'next' state to the screen
    renderer.setRenderTarget(null);
    renderer.render(scene, camera);

    // 4. Swap buffers for the next frame
    const temp = currentRenderTarget;
    currentRenderTarget = nextRenderTarget;
    nextRenderTarget = temp;
}

// Start it up
if (container) {
    init();
}