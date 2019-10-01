#version 420 core

in vec2 texcoord;
out vec4 color;

uniform sampler2D tex;

void main() {
    vec3 res = texture(tex, texcoord).rgb;
    // res = pow(res, vec3(1.0/2.2));
    color = vec4(res, 1.0);
}