#version 420 core

in vec2 vertex;

out vec2 texcoord;

void main() {
    gl_Position = vec4(vertex, 0.0, 1.0);

    // compute texcoords by mapping [-1, 1] to [0, 1]
    texcoord = vertex * 0.5 + vec2(0.5, 0.5);
}