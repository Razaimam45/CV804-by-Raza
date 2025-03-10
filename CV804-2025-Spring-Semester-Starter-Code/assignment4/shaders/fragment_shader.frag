//=============================================================================
//                                                
//   Code framework for the lecture
//
//   "CV804: 3D Geometry Processing"
//
//   Lecturer: Hao Li
//   TAs: Phong Tran, Long Nhat Ho, Ekaterina Radionova
//
//   Copyright (C) 2025 Metaverse Lab
//                                                                         
//-----------------------------------------------------------------------------
//                                                                            
//                                License                                     
//                                                                            
//   This program is free software; you can redistribute it and/or
//   modify it under the terms of the GNU General Public License
//   as published by the Free Software Foundation; either version 2
//   of the License, or (at your option) any later version.
//   
//   This program is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU General Public License for more details.
//   
//   You should have received a copy of the GNU General Public License
//   along with this program; if not, write to the Free Software
//   Foundation, Inc., 51 Franklin Street, Fifth Floor, 
//   Boston, MA  02110-1301, USA.
//                                                                            
//=============================================================================
//=============================================================================

#version 330 core
out vec4 FragColor;
in vec2 uv;

uniform vec3 camera_pos;
uniform float aspect_ratio;
uniform float fov_tan;

// Quality settings
const int MAX_REFLECTION_BOUNCES = 3;
const int ANTIALIASING_SAMPLES = 16; // 16x16 = 256
const int SOFT_SHADOW_SAMPLES = 16;
const float SOFT_SHADOW_RADIUS = 0.2;

struct Light {
    vec3 pos;
    vec3 color;
    float radius; // For soft shadows
};
uniform Light ambient_light;
uniform Light lights[32];
uniform int num_lights;

struct Sphere {
    vec3 pos;
    float radius;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    float reflectivity; // 0.0 - 1.0
};
uniform Sphere spheres[32];
uniform int num_spheres;

struct Triangle {
    vec3 v0, v1, v2;
    vec3 n0, n1, n2;
    vec3 diffuse0, diffuse1, diffuse2;
    vec3 specular0, specular1, specular2;
    float shininess0, shininess1, shininess2;
    float reflectivity0, reflectivity1, reflectivity2; // 0.0 - 1.0
};
uniform Triangle triangles[32];
uniform int num_triangles;

const float EPS = 1e-6;
const vec3 BACKGROUND_COLOR = vec3(1.0, 1.0, 1.0);

// Generate a pseudo-random float between 0 and 1
float random(vec2 st) {
    return fract(sin(dot(st, vec2(12.9898, 78.233))) * 43758.5453123);
}

// Generate a random point in a unit disk
vec2 random_in_unit_disk(vec2 seed) {
    float angle = random(seed) * 2.0 * 3.14159265359;
    float radius = sqrt(random(seed + vec2(0.1, 0.1)));
    return vec2(radius * cos(angle), radius * sin(angle));
}

float sphere_intersect(vec3 ro, vec3 rd, vec3 center, float radius) {
    vec3 L = center - ro;
    float tca = dot(L, rd);
    if (tca < 0.0) return -1.0;
    
    float d2 = dot(L, L) - tca * tca;
    float radius2 = radius * radius;
    if (d2 > radius2) return -1.0;
    
    float thc = sqrt(radius2 - d2);
    float t0 = tca - thc;
    float t1 = tca + thc;
    
    if (t0 < EPS && t1 < EPS) return -1.0;
    if (t0 < EPS) return t1;
    if (t1 < EPS) return t0;
    
    return min(t0, t1);
}

vec3 barycentric(vec3 p, vec3 a, vec3 b, vec3 c) {
    vec3 v0 = b - a, v1 = c - a, v2 = p - a;
    float d00 = dot(v0, v0);
    float d01 = dot(v0, v1);
    float d11 = dot(v1, v1);
    float d20 = dot(v2, v0);
    float d21 = dot(v2, v1);
    
    float denom = d00 * d11 - d01 * d01;
    float v = (d11 * d20 - d01 * d21) / denom;
    float w = (d00 * d21 - d01 * d20) / denom;
    float u = 1.0 - v - w;
    
    return vec3(u, v, w);
}

float triangle_intersect(vec3 ro, vec3 rd, Triangle tri) {
    vec3 edge1 = tri.v1 - tri.v0;
    vec3 edge2 = tri.v2 - tri.v0;
    vec3 h = cross(rd, edge2);
    float det = dot(edge1, h);
    
    if (abs(det) < EPS) return -1.0;
    
    float inv_det = 1.0 / det;
    vec3 s = ro - tri.v0;
    float u = dot(s, h) * inv_det;
    if (u < 0.0 || u > 1.0) return -1.0;
    
    vec3 q = cross(s, edge1);
    float v = dot(rd, q) * inv_det;
    if (v < 0.0 || u + v > 1.0) return -1.0;
    
    float t = dot(edge2, q) * inv_det;
    return (t > EPS) ? t : -1.0;
}

vec3 phong_shading(vec3 pos, vec3 normal, vec3 diffuse, vec3 specular, float shininess, vec3 view_dir, Light light) {
    vec3 light_dir = normalize(light.pos - pos);
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse_component = light.color * diffuse * diff;
    
    vec3 reflect_dir = reflect(-light_dir, normal);
    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), shininess);
    vec3 specular_component = light.color * specular * spec;
    
    return diffuse_component + specular_component;
}

struct HitInfo {
    bool hit;
    float t;
    vec3 pos;
    vec3 normal;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    float reflectivity;
};

HitInfo raytrace(vec3 ray_origin, vec3 ray_dir) {
    HitInfo info;
    info.hit = false;
    info.t = -1.0;
    info.reflectivity = 0.0;

    // Trace against spheres
    for (int i = 0; i < num_spheres; i++) {
        float t = sphere_intersect(ray_origin, ray_dir, spheres[i].pos, spheres[i].radius);
        if (t > 0.0 && (info.t < 0.0 || t < info.t)) {
            info.hit = true;
            info.t = t;
            info.pos = ray_origin + ray_dir * t;
            info.normal = normalize(info.pos - spheres[i].pos);
            info.diffuse = spheres[i].diffuse;
            info.specular = spheres[i].specular;
            info.shininess = spheres[i].shininess;
            info.reflectivity = spheres[i].reflectivity;
        }
    }

    // Trace against triangles
    for (int i = 0; i < num_triangles; i++) {
        float t = triangle_intersect(ray_origin, ray_dir, triangles[i]);
        if (t > 0.0 && (info.t < 0.0 || t < info.t)) {
            info.hit = true;
            info.t = t;
            info.pos = ray_origin + ray_dir * t;
            vec3 b = barycentric(info.pos, triangles[i].v0, triangles[i].v1, triangles[i].v2);
            info.normal = normalize(triangles[i].n0 * b.x + triangles[i].n1 * b.y + triangles[i].n2 * b.z);
            info.diffuse = triangles[i].diffuse0 * b.x + triangles[i].diffuse1 * b.y + triangles[i].diffuse2 * b.z;
            info.specular = triangles[i].specular0 * b.x + triangles[i].specular1 * b.y + triangles[i].specular2 * b.z;
            info.shininess = triangles[i].shininess0 * b.x + triangles[i].shininess1 * b.y + triangles[i].shininess2 * b.z;
            info.reflectivity = triangles[i].reflectivity0 * b.x + triangles[i].reflectivity1 * b.y + triangles[i].reflectivity2 * b.z;
        }
    }

    return info;
}

bool is_in_shadow(vec3 shadow_origin, vec3 shadow_dir, float max_dist) {
    for (int j = 0; j < num_spheres; j++) {
        float t = sphere_intersect(shadow_origin, shadow_dir, spheres[j].pos, spheres[j].radius);
        if (t > 0.0 && t < max_dist) return true;
    }
    
    for (int j = 0; j < num_triangles; j++) {
        float t = triangle_intersect(shadow_origin, shadow_dir, triangles[j]);
        if (t > 0.0 && t < max_dist) return true;
    }
    
    return false;
}

float calculate_soft_shadow(vec3 pos, Light light, vec3 normal) {
    vec3 light_dir = normalize(light.pos - pos);
    float shadow_factor = 0.0;
    
    // Early exit for backfaces
    if (dot(normal, light_dir) <= 0.0) return 0.0;
    
    // Offset origin slightly along normal to prevent self-intersection
    vec3 shadow_origin = pos + normal * EPS;
    float max_dist = length(light.pos - pos);
    
    // Sample random points on the light
    for (int i = 0; i < SOFT_SHADOW_SAMPLES; i++) {
        vec2 disk_sample = random_in_unit_disk(vec2(float(i), float(i) * 2.0));
        vec3 offset = vec3(disk_sample.x, disk_sample.y, 0.0);
        
        // Create orthonormal basis around light_dir
        vec3 up = abs(light_dir.y) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
        vec3 right = normalize(cross(up, light_dir));
        up = normalize(cross(light_dir, right));
        
        // Apply offset in light's local space
        vec3 sample_pos = light.pos + right * offset.x * light.radius + up * offset.y * light.radius;
        vec3 sample_dir = normalize(sample_pos - shadow_origin);
        
        if (!is_in_shadow(shadow_origin, sample_dir, max_dist)) {
            shadow_factor += 1.0;
        }
    }
    
    return shadow_factor / float(SOFT_SHADOW_SAMPLES);
}

vec3 direct_lighting(HitInfo hit, vec3 view_dir) {
    vec3 color = ambient_light.color * hit.diffuse;
    
    // Direct lighting with soft shadows
    for (int i = 0; i < num_lights; i++) {
        float shadow_factor = calculate_soft_shadow(hit.pos, lights[i], hit.normal);
        if (shadow_factor > 0.0) {
            color += shadow_factor * phong_shading(hit.pos, hit.normal, hit.diffuse, hit.specular, hit.shininess, view_dir, lights[i]);
        }
    }
    
    return color;
}

void main() {
    vec3 final_color = vec3(0.0);
    
    // Antialiasing
    for (int i = 0; i < ANTIALIASING_SAMPLES; i++) {
        for (int j = 0; j < ANTIALIASING_SAMPLES; j++) {
            float si = float(i) / float(ANTIALIASING_SAMPLES);
            float sj = float(j) / float(ANTIALIASING_SAMPLES);
            
            // Apply sub-pixel jitter
            vec2 jitter = vec2(si, sj) / float(ANTIALIASING_SAMPLES);
            vec2 offset = vec2(1.0) / float(ANTIALIASING_SAMPLES);
            vec2 aa_uv = uv + (jitter - 0.5) * offset;
            
            // Set up ray direction with antialiasing
            vec2 ndc = aa_uv * 2.0 - 1.0;
            ndc.y *= aspect_ratio;
            vec3 ray_dir = normalize(vec3(ndc * fov_tan, -1.0));
            vec3 ray_origin = camera_pos;
            
            // ITERATIVE approach for reflections (instead of recursion)
            vec3 sample_color = vec3(0.0);
            vec3 ray_contribution = vec3(1.0);
            vec3 current_ray_origin = ray_origin;
            vec3 current_ray_dir = ray_dir;
            
            // Loop for reflection bounces
            for (int bounce = 0; bounce <= MAX_REFLECTION_BOUNCES; bounce++) {
                HitInfo hit = raytrace(current_ray_origin, current_ray_dir);
                
                if (!hit.hit) {
                    sample_color += ray_contribution * BACKGROUND_COLOR;
                    break;
                }
                
                // Direct lighting at this bounce
                vec3 direct_color = direct_lighting(hit, -current_ray_dir);
                sample_color += ray_contribution * (1.0 - hit.reflectivity) * direct_color;
                
                // If not reflective or last bounce, exit
                if (hit.reflectivity <= 0.0 || bounce == MAX_REFLECTION_BOUNCES) {
                    break;
                }
                
                // Setup for next bounce
                ray_contribution *= hit.reflectivity;
                current_ray_dir = reflect(current_ray_dir, hit.normal);
                current_ray_origin = hit.pos + hit.normal * EPS;
            }
            
            // Accumulate color
            final_color += sample_color;
        }
    }
    
    // Average all samples
    final_color /= float(ANTIALIASING_SAMPLES * ANTIALIASING_SAMPLES);
    
    // Output final color
    FragColor = vec4(clamp(final_color, 0.0, 1.0), 1.0);
}