#version 420
#extension GL_ARB_compute_shader : require
#extension GL_ARB_shader_storage_buffer_object : require
#extension GL_ARB_shader_image_load_store : require
#extension GL_ARB_gpu_shader5 : require


layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
layout(rgba32f, binding = 0) uniform image2D img_output;
void main()
{
  	const vec2 DrawingArea = vec2(gl_NumWorkGroups.xy) * vec2(gl_WorkGroupSize.xy);
	const vec2 AspectRatio = vec2(DrawingArea.x / DrawingArea.y, 1);
	const vec2 ScreenUV = vec2(gl_GlobalInvocationID.xy) / DrawingArea;
	const vec2 DemoSpace = (ScreenUV * 2 - 1) * AspectRatio;

	const float DistanceFromCenter = distance(DemoSpace, vec2(0.0));

	const bool bChecker = gl_WorkGroupID.x % 2 ==  gl_WorkGroupID.y % 2;
	const vec4 Color1 = vec4(bChecker, 0.0, 0.5, 1.0);
	const vec4 Color2 = vec4(0.5, bChecker, 0.0, 1.0);
	const vec4 PixelColor = mix(Color1, Color2, float(int(DistanceFromCenter*10.0) % 2));

	imageStore(img_output, ivec2(gl_GlobalInvocationID.xy), PixelColor);
}
