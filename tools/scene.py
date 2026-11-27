import bpy, bmesh, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, PFP = argv[0], argv[1]
ONLY = argv[2:] or ["cursor", "frame", "cloud"]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    except TypeError:
        continue
for d in prefs.devices:
    d.use = d.type != "CPU"
sc.cycles.device = "GPU"
sc.cycles.samples = 256
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 1000
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
bg = wn["Background"]
grad = wn.new("ShaderNodeTexGradient")
tc = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0])
wl.new(sep.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.10, 0.08, 0.065, 1)
ramp.color_ramp.elements[1].color = (0.55, 0.70, 0.95, 1)
wl.new(ramp.outputs[0], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.55

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 85
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
cam.location = (0, -11, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam


def area(name, loc, power, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size, d.color = power, size, color
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


area("key", (-5, -6, 5), 1400, 5, (1.0, 0.94, 0.86))
area("fill", (6, -5, -1), 260, 6, (0.75, 0.85, 1.0))
area("rim", (3, 4, 5), 600, 3, (0.85, 0.9, 1.0))


def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def sky_material():
    m, n, l = mat("sky")
    bsdf = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.5, 1.5, 1.5)
    l.new(tc.outputs["Object"], mp.inputs[0])
    warp = n.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 2.0
    warp.inputs["Detail"].default_value = 4
    mix = n.new("ShaderNodeMix")
    mix.data_type = "VECTOR"
    mix.inputs[0].default_value = 0.35
    l.new(mp.outputs[0], warp.inputs["Vector"])
    l.new(mp.outputs[0], mix.inputs[4])
    l.new(warp.outputs["Color"], mix.inputs[5])
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 12
    noise.inputs["Roughness"].default_value = 0.62
    l.new(mix.outputs[1], noise.inputs["Vector"])
    cr = n.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.42
    cr.color_ramp.elements[0].color = (0.04, 0.2, 0.66, 1)
    cr.color_ramp.elements[1].position = 0.66
    cr.color_ramp.elements[1].color = (0.97, 0.96, 0.93, 1)
    mid = cr.color_ramp.elements.new(0.53)
    mid.color = (0.3, 0.52, 0.9, 1)
    l.new(noise.outputs["Fac"], cr.inputs[0])
    l.new(cr.outputs[0], bsdf.inputs["Base Color"])
    l.new(cr.outputs[0], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.04
    return m


def catcher(y=0.9):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, y, 0), rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.name = "catcher"
    o.is_shadow_catcher = True
    return o


def cursor():
    pts = [(0, 0), (0, -16), (4, -12.2), (7.1, -18.8), (9.9, -17.6), (6.9, -11.2), (12.2, -11.2)]
    me = bpy.data.meshes.new("cursor")
    bm = bmesh.new()
    vs = [bm.verts.new((x / 10, 0, y / 10)) for x, y in pts]
    bm.faces.new(vs)
    bm.to_mesh(me)
    o = bpy.data.objects.new("cursor", me)
    sc.collection.objects.link(o)
    sol = o.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.34
    sol.offset = 0
    bev = o.modifiers.new("bev", "BEVEL")
    bev.width = 0.085
    bev.segments = 8
    bev.limit_method = "NONE"
    bev.harden_normals = False
    sub = o.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    o.data.materials.append(sky_material())
    for p in o.data.polygons:
        p.use_smooth = True
    o.location = (-0.55, 0, 0.95)
    o.rotation_euler = (math.radians(-10), math.radians(-22), math.radians(-10))
    cam_data.lens = 150
    return [o]


def frame():
    objs = []
    m, n, l = mat("pfp")
    bsdf = n["Principled BSDF"]
    img = n.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(PFP)
    l.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Coat Weight"].default_value = 0.25
    bsdf.inputs["Coat Roughness"].default_value = 0.2
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0.02, 0), rotation=(math.radians(90), 0, 0))
    canvas = bpy.context.object
    canvas.data.materials.append(m)
    objs.append(canvas)

    fm, fn, fl = mat("frame")
    fb = fn["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0.018, 0.014, 0.011, 1)
    fb.inputs["Roughness"].default_value = 0.38
    fb.inputs["Metallic"].default_value = 0.2
    fb.inputs["Coat Weight"].default_value = 0.6
    fb.inputs["Coat Roughness"].default_value = 0.12
    me = bpy.data.meshes.new("frame")
    bm = bmesh.new()
    def sq(r, y):
        return [bm.verts.new((sx * r, y, sz * r)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    o_f, i_f, o_b, i_b = sq(1.24, -0.12), sq(1.0, -0.12), sq(1.24, 0.06), sq(1.0, 0.06)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((o_f[i], o_f[j], i_f[j], i_f[i]))
        bm.faces.new((o_b[j], o_b[i], i_b[i], i_b[j]))
        bm.faces.new((o_f[j], o_f[i], o_b[i], o_b[j]))
        bm.faces.new((i_f[i], i_f[j], i_b[j], i_b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    fr = bpy.data.objects.new("frame", me)
    sc.collection.objects.link(fr)
    b = fr.modifiers.new("bev", "BEVEL")
    b.width, b.segments, b.limit_method = 0.035, 6, "NONE"
    fr.data.materials.append(fm)
    for p in fr.data.polygons:
        p.use_smooth = True
    objs.append(fr)
    gm, gn, gl = mat("gold")
    gb = gn["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.83, 0.62, 0.33, 1)
    gb.inputs["Metallic"].default_value = 1.0
    gb.inputs["Roughness"].default_value = 0.28
    bm2 = bmesh.new()
    def sq2(r, y):
        return [bm2.verts.new((sx * r, y, sz * r)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    a, c = sq2(1.045, -0.05), sq2(1.0, -0.05)
    a2, c2 = sq2(1.045, 0.02), sq2(1.0, 0.02)
    for i in range(4):
        j = (i + 1) % 4
        bm2.faces.new((a[i], a[j], c[j], c[i]))
        bm2.faces.new((c[i], c[j], c2[j], c2[i]))
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    me2 = bpy.data.meshes.new("lip")
    bm2.to_mesh(me2)
    lip = bpy.data.objects.new("lip", me2)
    sc.collection.objects.link(lip)
    lb = lip.modifiers.new("bev", "BEVEL")
    lb.width, lb.segments, lb.limit_method = 0.008, 3, "NONE"
    lip.data.materials.append(gm)
    objs.append(lip)
    pivot = bpy.data.objects.new("pivot", None)
    sc.collection.objects.link(pivot)
    for o in objs:
        o.parent = pivot
    pivot.rotation_euler = (math.radians(6), math.radians(-12), math.radians(3))
    cam_data.lens = 118
    pivot.scale = (0.98, 0.98, 0.98)
    return objs + [pivot]


def cloud():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object
    o.name = "cloud"
    o.scale = (4.4, 2.6, 2.6)
    cam_data.lens = 70
    m, n, l = mat("cloud")
    n.remove(n["Principled BSDF"])
    out = n["Material Output"]
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (1, 1, 1, 1)
    vol.inputs["Anisotropy"].default_value = 0.5
    l.new(vol.outputs[0], out.inputs["Volume"])
    tc = n.new("ShaderNodeTexCoord")
    geo = n.new("ShaderNodeNewGeometry")
    warp = n.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 1.4
    warp.inputs["Detail"].default_value = 3
    l.new(geo.outputs["Position"], warp.inputs["Vector"])
    vm = n.new("ShaderNodeVectorMath")
    vm.operation = "MULTIPLY_ADD"
    vm.inputs[1].default_value = (0.35, 0.35, 0.35)
    vm.inputs[2].default_value = (-0.175, -0.175, -0.175)
    l.new(warp.outputs["Color"], vm.inputs[0])
    pos = n.new("ShaderNodeVectorMath")
    pos.operation = "ADD"
    l.new(geo.outputs["Position"], pos.inputs[0])
    l.new(vm.outputs[0], pos.inputs[1])
    lobes = [((0, 0, 0.1), 0.95), ((-0.95, 0.05, -0.15), 0.7), ((0.95, -0.05, -0.1), 0.75),
             ((0.35, 0, 0.75), 0.62), ((-0.45, 0.1, 0.55), 0.58), ((-1.6, 0, -0.35), 0.45), ((1.65, 0, -0.35), 0.42)]
    acc = None
    for c, r in lobes:
        sub = n.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = c
        l.new(pos.outputs[0], sub.inputs[0])
        ln = n.new("ShaderNodeVectorMath")
        ln.operation = "LENGTH"
        l.new(sub.outputs[0], ln.inputs[0])
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = r
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        l.new(ln.outputs["Value"], mr.inputs["Value"])
        if acc is None:
            acc = mr.outputs["Result"]
        else:
            mx = n.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            l.new(acc, mx.inputs[0])
            l.new(mr.outputs["Result"], mx.inputs[1])
            acc = mx.outputs[0]
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(geo.outputs["Position"], sep.inputs[0])
    base = n.new("ShaderNodeMapRange")
    base.inputs["From Min"].default_value = -0.62
    base.inputs["From Max"].default_value = -0.42
    l.new(sep.outputs["Z"], base.inputs["Value"])
    mb = n.new("ShaderNodeMath")
    mb.operation = "MULTIPLY"
    l.new(acc, mb.inputs[0])
    l.new(base.outputs["Result"], mb.inputs[1])
    det = n.new("ShaderNodeTexNoise")
    det.inputs["Scale"].default_value = 4.5
    det.inputs["Detail"].default_value = 15
    det.inputs["Roughness"].default_value = 0.6
    l.new(pos.outputs[0], det.inputs["Vector"])
    ero = n.new("ShaderNodeMath")
    ero.operation = "MULTIPLY_ADD"
    ero.inputs[1].default_value = -0.45
    ero.inputs[2].default_value = 0.0
    l.new(det.outputs["Fac"], ero.inputs[0])
    sm = n.new("ShaderNodeMath")
    sm.operation = "ADD"
    l.new(mb.outputs[0], sm.inputs[0])
    l.new(ero.outputs[0], sm.inputs[1])
    cut = n.new("ShaderNodeMapRange")
    cut.inputs["From Min"].default_value = 0.0
    cut.inputs["From Max"].default_value = 0.08
    cut.inputs["To Min"].default_value = 0.0
    cut.inputs["To Max"].default_value = 60.0
    l.new(sm.outputs[0], cut.inputs["Value"])
    l.new(cut.outputs["Result"], vol.inputs["Density"])
    o.data.materials.append(m)
    sc.cycles.volume_bounces = 8
    sc.cycles.volume_step_rate = 0.4
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy, sun.color, sun.angle = 6.0, (1.0, 0.95, 0.86), math.radians(3)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(35), math.radians(-40), math.radians(-25))
    return [o, so]


builders = {"cursor": cursor, "frame": frame, "cloud": cloud}
for name in ONLY:
    keep = set(o.name for o in sc.objects)
    objs = builders[name]()
    c = catcher() if name != "cloud" else None
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    for o in list(objs) + ([c] if c else []):
        bpy.data.objects.remove(o, do_unlink=True)
    print("RENDERED", name)
