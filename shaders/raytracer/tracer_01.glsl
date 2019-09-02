#version 420
#extension GL_ARB_compute_shader : require
#extension GL_ARB_shader_storage_buffer_object : require
#extension GL_ARB_shader_image_load_store : require
#extension GL_ARB_shader_image_size : require
#extension GL_ARB_gpu_shader5 : require

layout(binding = 0, rgba32f) uniform image2D framebuffer;

uniform vec3 eye;
uniform vec3 ray00;
uniform vec3 ray01;
uniform vec3 ray10;
uniform vec3 ray11;

struct box {
  vec3 min;
  vec3 max;
};

#define MAX_SCENE_BOUNCES 100.0
#define NUM_BOXES 2

const box boxes[] = {
  // ground box
  {vec3(-5.0, -0.1, -5.0), vec3(5.0, 0.0, 5.0)},

  // middle box
  {vec3(-0.5, 0.0, -0.5), vec3(0.5, 1.0, 0.5)}
};

struct hitinfo {
  vec2 lambda;
  int bi;
};


vec2 intersect_box(vec3 origin, vec3 dir, const box b) {
  vec3 tMin = (b.min - origin) / dir;
  vec3 tMax = (b.max - origin) / dir;
  vec3 t1 = min(tMin, tMax);
  vec3 t2 = max(tMin, tMax);
  float tNear = max(max(t1.x, t1.y), t1.z);
  float tFar = min(min(t2.x, t2.y), t2.z);
  return vec2(tNear, tFar);
}

bool intersect_boxes(vec3 origin, vec3 dir, out hitinfo info) {
  float smallest = MAX_SCENE_BOUNCES;
  bool found = false;

  for (int i = 0; i < NUM_BOXES; i++) {
    vec2 lambda = intersect_box(origin, dir, boxes[i]);

    if (lambda.x > 0.0 && lambda.x < lambda.y && lambda.x < smallest) {
      info.lambda = lambda;
      info.bi = i;

      smallest = lambda.x;
      found = true;
    }
  }
  return found;
}

vec4 trace(vec3 origin, vec3 dir) {
  hitinfo i;

  if (intersect_boxes(origin, dir, i)) {
    vec4 gray = vec4(i.bi / 10.0 + 0.8);
    return vec4(gray.rgb, 1.0);
  }
  return vec4(0.0, 0.0, 0.0, 1.0);
}

layout (local_size_x = 8, local_size_y = 8) in;
void main(void) {
  ivec2 pix = ivec2(gl_GlobalInvocationID.xy);
  ivec2 size = imageSize(framebuffer);

  if (pix.x >= size.x || pix.y >= size.y) {
    return;
  }

vec2 pos = vec2(pix) / vec2(size.x - 1, size.y - 1);
vec3 dir = mix(mix(ray00, ray01, pos.y), mix(ray10, ray11, pos.y), pos.x);
vec4 color = trace(eye, dir);
imageStore(framebuffer, pix, color);
}