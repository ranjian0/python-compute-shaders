"""
Adapted from:
https://github.com/LWJGL/lwjgl3-wiki
2.6.1. Ray tracing with OpenGL Compute Shaders (Part I)
"""

import glfw
import shader
import OpenGL.GL as gl
from pyrr import Vector3, Vector4, Matrix44
from ctypes import c_byte, c_void_p, sizeof

SCR_WIDTH = 1024
SCR_HEIGHT = 768

RES = lambda filename : f"shaders/raytracer/{filename}"


def main():
    if not glfw.init():
        raise ValueError("Failed to initialize glfw")

    glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.NATIVE_CONTEXT_API)
    glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.RESIZABLE, True)
    glfw.window_hint(glfw.DOUBLEBUFFER, True)
    glfw.window_hint(glfw.DEPTH_BITS, 24)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(SCR_WIDTH, SCR_HEIGHT, "Python Compute Shader Demo", None, None)
    if not window:
        glfw.terminate()
        raise ValueError("Failed to create window")

    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_event_callback)
    glfw.set_cursor_pos_callback(window, mouse_event_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_window_size_callback(window, window_resize_callback)

    # -- setup shaders
    compute_program = shader.ComputeShader(RES(f"tracer_01.glsl"))
    quad_program = shader.Shader(RES("tracer.vert"), RES("tracer.frag"))

    # -- create vao with full screen quad
    quad_verts = [
        -1, -1,
         1, -1,
         1,  1,
         1,  1,
        -1,  1,
        -1, -1,
    ]
    quad_verts = (c_byte * len(quad_verts))(*quad_verts)

    vao = gl.glGenVertexArrays(1)
    vbo = gl.glGenBuffers(1)

    gl.glBindVertexArray(vao)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, sizeof(quad_verts), quad_verts, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(0, 2, gl.GL_BYTE, gl.GL_FALSE, 2 * sizeof(c_byte), c_void_p(0))
    gl.glEnableVertexAttribArray(0)
    gl.glBindVertexArray(0)

    tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, SCR_WIDTH, SCR_HEIGHT, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # -- initialize quad program uniforms
    quad_program.use()
    quad_program.set_int("tex", 0)

    # -- initialize compute program uniforms
    # compute_program.use()
    work_group_size_x = 8
    work_group_size_y = 8

    # -- camera
    cam_pos = Vector3([3.0, 2.0, 7.0])
    view = Matrix44.look_at(cam_pos, Vector3([0.0, 0.5, 0.0]), Vector3([0.0, 1.0, 0.0]))
    projection = Matrix44.perspective_projection(60.0, SCR_WIDTH / SCR_HEIGHT, 1.0, 2.0)
    inverse_projection_view = (projection * view).inverse

    def get_eye_ray(x, y):
        tmp3 = Vector4([x, y, 0.0, 1.0])
        tmp3 = inverse_projection_view * tmp3
        tmp3 *= (1.0 / tmp3.w)
        return Vector3([tmp3.x, tmp3.y, tmp3.z]) - cam_pos

    while not glfw.window_should_close(window):
        compute_program.use()
        compute_program.set_vec3("eye", cam_pos)
        compute_program.set_vec3("ray00", get_eye_ray(-1, -1))
        compute_program.set_vec3("ray01", get_eye_ray(-1, 1))
        compute_program.set_vec3("ray10", get_eye_ray(1, -1))
        compute_program.set_vec3("ray11", get_eye_ray(1, 1))

        gl.glBindImageTexture(0, tex, 0, gl.GL_FALSE, 0, gl.GL_WRITE_ONLY, gl.GL_RGBA32F)
        gl.glDispatchCompute(SCR_WIDTH // work_group_size_x, SCR_HEIGHT // work_group_size_y, 1)

        gl.glBindImageTexture(0, 0, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
        gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        quad_program.use()
        gl.glBindVertexArray(vao)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glBindVertexArray(0)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


def key_event_callback(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)


def mouse_event_callback(window, xpos, ypos):
    pass


def mouse_button_callback(window, button, action, mods):
    pass


def window_resize_callback(window, width, height):
    gl.glViewport(0, width, 0, height)


if __name__ == '__main__':
    main()
