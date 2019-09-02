#version 420
#extension GL_ARB_gpu_shader5 : require


layout(location = 0) out vec4 Color;
layout(binding=0) uniform sampler2D Whatever;
void main ()
{
	vec2 UV = gl_FragCoord.xy/vec2(1024,768);
	Color = texture(Whatever, UV);
}
