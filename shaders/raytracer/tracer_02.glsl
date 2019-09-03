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
uniform float seed;


#define MAX_SCENE_BOUNCES 100.0
#define NUM_BOXES 2
#define EPSILON 0.001f

float _seed = seed;
const float infinity = 1. / 0.;

struct ray {
  vec3 origin;
  vec3 direction;
};


struct material {
  vec4 albedo;
};

struct box {
  vec3 min;
  vec3 max;

  material mat;
};

struct hitinfo {
  vec2 lambda ;
  vec3 p; // hit position
  vec3 n; // hit normal

  material mat;
};

const box boxes[] = {
  // ground box
  {vec3(-5.0, -0.1, -5.0), vec3(5.0, 0.0, 5.0), {vec4(1.0, 0.25, 0.25, 1.0)}},

  // middle box
  {vec3(-0.5, 0.0, -0.5), vec3(0.5, 1.0, 0.5), {vec4(0.2, 0.2, 0.3, 1.0)}}
};


vec3 box_normal_at_point(box b, vec3 p) {
  if (p.z == b.min.z) {
    return vec3(0.0, 0.0, -1.0);
  } else if (p.z == b.max.z) {
    return vec3(0.0, 0.0, 1.0);
  } else if (p.x == b.min.x) {
    return vec3(-1.0, 0.0, 0.0);
  } else if (p.x == b.max.x) {
    return vec3(1.0, 0.0, 0.0);
  } else if (p.y == b.min.y) {
    return vec3(0.0, -1.0, 0.0);
  } else if (p.y == b.max.y) {
    return vec3(0.0, 1.0, 0.0);
  }
  return vec3(0.0);
}

float rand(){
    vec2 pixel = gl_GlobalInvocationID.xy;
    float res = fract(sin(_seed / 100.0 * dot(pixel ,vec2(12.9898,78.233))) * 43758.5453);
    _seed += 1.0;
    return res;
}

vec3 random_in_unit_sphere() {
  vec3 p;
  do {
      p = 2.0 * vec3(rand(), rand(), rand()) - vec3(1.0, 1.0, 1.0);
  } while (length(p) >= 1.0);
  return p;
}

mat3 GetTangentSpace(vec3 normal)
{
    // Choose a helper vector for the cross product
    vec3 helper = vec3(1, 0, 0);
    if (abs(normal.x) > 0.99f)
        helper = vec3(0, 0, 1);
    // Generate vectors
    vec3 tangent = normalize(cross(normal, helper));
    vec3 binormal = normalize(cross(normal, tangent));
    return mat3(tangent, binormal, normal);
}

vec3 SampleHemisphere(vec3 normal)
{
    // Uniformly sample hemisphere direction
    float PI = 3.141592653589793;
    float cosTheta = rand();
    float sinTheta = sqrt(max(0.0f, 1.0f - cosTheta * cosTheta));
    float phi = 2 * PI * rand();
    vec3 tangentSpaceDir = vec3(cos(phi) * sinTheta, sin(phi) * sinTheta, cosTheta);
    // Transform direction to world space

    return tangentSpaceDir * GetTangentSpace(normal);
}


bool scatter_lambertian(hitinfo info, out vec4 attenuation, out ray scattered) {
  vec3 target = info.p + info.n;
  scattered.origin = info.p;
  scattered.direction =  SampleHemisphere(info.n);
  attenuation = info.mat.albedo;
  return true;
}


hitinfo intersect_box(ray r, const box b) {
  vec3 tMin = (b.min - r.origin) / r.direction;
  vec3 tMax = (b.max - r.origin) / r.direction;
  vec3 t1 = min(tMin, tMax);
  vec3 t2 = max(tMin, tMax);
  float tNear = max(max(t1.x, t1.y), t1.z);
  float tFar = min(min(t2.x, t2.y), t2.z);

  vec3 position = r.origin + (tNear * r.direction);
  vec3 normal = box_normal_at_point(b, position);
  return hitinfo(vec2(tNear, tFar), position, normal, b.mat);
}

bool intersect_scene(ray r, out hitinfo info) {
  float smallest = MAX_SCENE_BOUNCES;
  bool found = false;

  for (int i = 0; i < NUM_BOXES; i++) {
    hitinfo hi = intersect_box(r, boxes[i]);

    if (hi.lambda.x > 0.0 && hi.lambda.x < hi.lambda.y && hi.lambda.x < smallest) {
      info.lambda = hi.lambda;
      info.p = hi.p;
      info.n = hi.n;
      info.mat = hi.mat;

      smallest = hi.lambda.x;
      found = true;
    }
  }
  return found;
}

vec4 trace(ray r, int depth) {
  hitinfo hit;
  vec4 color = vec4(1.0);

  if (intersect_scene(r, hit)) {
    ray scattered;
    vec4 attenuation;
    if (scatter_lambertian(hit, attenuation, scattered)) {
      color *= attenuation;

      while(depth < 50 && intersect_scene(scattered, hit)) {
        if (scatter_lambertian(hit, attenuation, scattered)) {
          color *= attenuation;
        } else {
          color  = vec4(0.0, 0.0, 0.0, 1.0);
        }
        depth++;
      }

    }

  } else {
    // -- gradient background
    vec3 unit = normalize(r.direction);
    float t = 0.5 * (unit.y + 1.0);
    vec3 background = (1.0-t) * vec3(1.0, 1.0, 1.0) + t*vec3(0.5, 0.7, 1.0);
    color = vec4(background, 1.0);
  }
  return color;
}

layout (local_size_x = 16, local_size_y = 8) in;
void main(void) {
  ivec2 pix = ivec2(gl_GlobalInvocationID.xy);
  ivec2 size = imageSize(framebuffer);

  if (pix.x >= size.x || pix.y >= size.y) {
    return;
  }

  int samples = 16;
  vec4 color = vec4(0.0);
  for (int i = 0; i < samples; i++) {
    float y = float(pix.y + rand()) / size.y;
    float x = float(pix.x + rand()) / size.x;
    vec3 dir = mix(mix(ray00, ray01, y), mix(ray10, ray11, y), x);
    color += trace(ray(eye, dir), 0);
  }
  color /= float(samples);

  imageStore(framebuffer, pix, color);
}