import glfw
import shader
import OpenGL.GL as gl
from camera import Camera, CameraMovement
from pyrr import Vector3, Matrix44
from ctypes import c_byte, c_void_p, sizeof

SCR_WIDTH = 1024
SCR_HEIGHT = 720

camera = Camera(Vector3([1.0, 2.0, 7.0]))
last_x = SCR_WIDTH / 2
last_y = SCR_HEIGHT / 2
first_mouse = True
delta_time = 0.0
last_frame = 0.0
frames = 0

RES = lambda filename : f"shaders/pathtracer/{filename}"


def main():
    global delta_time, last_frame, frames

    if not glfw.init():
        raise ValueError("Failed to initialize glfw")

    glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.NATIVE_CONTEXT_API)
    glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.DOUBLEBUFFER, True)
    glfw.window_hint(glfw.DEPTH_BITS, 24)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(
        SCR_WIDTH, SCR_HEIGHT, "Python Compute Shader Demo: Pathtracer", None, None
    )
    if not window:
        glfw.terminate()
        raise ValueError("Failed to create window")

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    # -- setup shaders
    compute_program = shader.ComputeShader(RES(f"tracer_cs.glsl"))
    quad_program = shader.Shader(RES("tracer_vs.glsl"), RES("tracer_fs.glsl"))

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

    trace_tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, trace_tex)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, SCR_WIDTH, SCR_HEIGHT, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # -- initialize quad program uniforms
    quad_program.use()
    quad_program.set_int("trace_tex", 0)

    while not glfw.window_should_close(window):
        projection = Matrix44.perspective_projection(camera.zoom, SCR_WIDTH / SCR_HEIGHT, 1.0, 2.0)

        # -- time logic
        current_frame = glfw.get_time()
        delta_time = current_frame - last_frame
        last_frame = current_frame

        # -- input
        process_input(window)

        compute_program.use()
        compute_program.set_int("u_NumFrames", frames)
        compute_program.set_float("u_Accum", frames / (frames+1))
        compute_program.set_mat4("u_InvProjectionMat", projection.inverse)
        compute_program.set_mat4("u_InvViewMat", camera.get_view_matrix().inverse)

        gl.glBindImageTexture(0, trace_tex, 0, gl.GL_FALSE, 0, gl.GL_WRITE_ONLY, gl.GL_RGBA32F)
        gl.glDispatchCompute(SCR_WIDTH // 8, SCR_HEIGHT // 8, 1)

        gl.glBindImageTexture(0, 0, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
        gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        frames += 1

        quad_program.use()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glBindVertexArray(vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, trace_tex)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


def process_input(window):
    global last_x, last_y, frames
    if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        camera.process_keyboard(CameraMovement.FORWARD, delta_time)
        frames = 0
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        camera.process_keyboard(CameraMovement.BACKWARD, delta_time)
        frames = 0

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        camera.process_keyboard(CameraMovement.LEFT, delta_time)
        frames = 0
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        camera.process_keyboard(CameraMovement.RIGHT, delta_time)
        frames = 0


def framebuffer_size_callback(window, width, height):
    gl.glViewport(0, 0, width, height)


def mouse_callback(window, xpos, ypos):
    global first_mouse, last_x, last_y, frames

    if first_mouse:
        last_x, last_y = xpos, ypos
        first_mouse = False

    xoffset = xpos - last_x
    yoffset = last_y - ypos  # XXX Note Reversed (y-coordinates go from bottom to top)
    last_x = xpos
    last_y = ypos

    camera.process_mouse_movement(xoffset, yoffset)
    frames = 0


def scroll_callback(window, xoffset, yoffset):
    global frames
    camera.process_mouse_scroll(yoffset)
    frames = 0


if __name__ == '__main__':
    main()
