"""
Adapted from moderngl examples (compute_shader)
"""

import time
import glfw
import shader
import random
import OpenGL.GL as gl
from PIL import Image
from ctypes import c_float, sizeof, c_uint8

SCR_WIDTH = 1024
SCR_HEIGHT = 768

W = 512
H = 256
X = W
Y = 1
Z = 1

FRAMES = 50

RES = lambda filename : f"shaders/median5x5/{filename}"


def main():
    random.seed(time.time())

    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.VISIBLE, False)
    window = glfw.create_window(SCR_WIDTH, SCR_HEIGHT, "hidden window", None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)

    compute_program = shader.ComputeShader(RES("median5x5.glsl"))

    buffer_size = H * W * 4
    in_buffer = [random.uniform(0.0, 1.0) for _ in range(buffer_size)]
    in_buffer = (c_float * buffer_size)(*in_buffer)
    in_ssbo = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, in_ssbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, sizeof(in_buffer), in_buffer, gl.GL_STATIC_DRAW)

    out_buffer = [0.0 for _ in range(buffer_size)]
    out_buffer = (c_float * buffer_size)(*out_buffer)
    out_ssbo = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, out_ssbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, sizeof(out_buffer), out_buffer, gl.GL_STATIC_DRAW)

    images = []
    for i in range(FRAMES):
        print(f"Computing Frame {i}")

        toggle = True if i % 2 else False
        bind_storage_buffer(in_ssbo, 1 if toggle else 0)
        bind_storage_buffer(out_ssbo, 0 if toggle else 1)

        compute_program.use()
        gl.glDispatchCompute(H, 1, 1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, in_ssbo if toggle else out_ssbo)
        data = gl.glMapBufferRange(gl.GL_ARRAY_BUFFER, 0, sizeof(in_buffer), gl.GL_MAP_READ_BIT)
        gl.glUnmapBuffer(gl.GL_ARRAY_BUFFER)

        out = (c_float * buffer_size).from_address(data)
        store_buffer_as_int(out, images)

    write_gif(images)


def bind_storage_buffer(ssbo, location):
    gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, ssbo)
    gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, location, ssbo)


def store_buffer_as_int(buf, storage_list):
    copy = (c_uint8 * len(buf))(*[int(item*255) for item in buf])
    storage_list.append(copy)


def write_gif(images):
    print(f"Writing GIF ...")
    im = Image.frombytes("RGBA", (W, H), bytes(images[0]))
    others = [Image.frombytes("RGBA", (W, H),  bytes(data)) for data in images[1:]]
    im.save("out.gif", save_all=True, append_images=others, duration=150)


if __name__ == '__main__':
    main()
