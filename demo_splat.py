import glfw
import shader
import OpenGL.GL as gl

SCR_WIDTH = 1024
SCR_HEIGHT = 768

RES = lambda filename : f"shaders/splat/{filename}"


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

    CSG = shader.ComputeShader(RES("splat.glsl"))
    SplatProgram = shader.Shader(RES("splat.vert"), RES("splat.frag"))

    some_UAV = gl.glGenTextures(1)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_2D, some_UAV)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, SCR_WIDTH, SCR_HEIGHT, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
    gl.glBindImageTexture(0, some_UAV, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)

    vao = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(vao)

    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_DEPTH_TEST)

    while not glfw.window_should_close(window):
        CSG.use()
        gl.glDispatchCompute(SCR_WIDTH // 8, SCR_HEIGHT // 8, 1)
        gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        SplatProgram.use()
        SplatProgram.set_int("Whatever", 0)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

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
