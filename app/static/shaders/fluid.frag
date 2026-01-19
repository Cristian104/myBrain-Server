uniform sampler2D uTexture; // The previous frame's fluid state
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uTime;
uniform float uViscosity;
uniform vec3 uBaseColor;

varying vec2 vUv;

void main() {
    vec2 st = vUv;
    vec2 pixel = 1.0 / uResolution;

    // Sample neighboring pixels for fluid simulation
    vec4 left = texture2D(uTexture, st + vec2(-pixel.x, 0.0));
    vec4 right = texture2D(uTexture, st + vec2(pixel.x, 0.0));
    vec4 up = texture2D(uTexture, st + vec2(0.0, pixel.y));
    vec4 down = texture2D(uTexture, st + vec2(0.0, -pixel.y));
    vec4 center = texture2D(uTexture, st);

    // Simple diffusion/viscosity calculation
    vec4 diffusion = (left + right + up + down) * 0.25;
    vec4 fluid = mix(center, diffusion, uViscosity);

    // Add interaction from mouse
    float dist = distance(st, uMouse);
    float mouseInfluence = smoothstep(0.1, 0.0, dist);
    
    // Add a dark green "splat" where the mouse is
    fluid.rgb += uBaseColor * mouseInfluence * 2.0;
    fluid.a += mouseInfluence;

    // Decay the fluid over time to make it dissipate
    fluid *= 0.99;

    gl_FragColor = fluid;
}