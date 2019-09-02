#version 420 core

in vec2 texcoord;

out vec4 color;

uniform sampler2D tex;

void main() {
    color = texture(tex, texcoord);
}