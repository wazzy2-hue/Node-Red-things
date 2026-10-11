"""Photo-style renders of the board: flat top/bottom views and 3D views.

Board artwork comes from KiCad's own layer plots (so it is exactly the
designed copper, mask and silk); component bodies come from the KiCad 3D
library models (plus our own TDA7294 model).
"""
import math
import os
import subprocess
import sys

import cairosvg
import numpy as np
from PIL import Image
import pcbnew
import vtk
from vtk.util import numpy_support as nps

PCB = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
TMP = "/tmp/claude-0/render"
os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

OX, OY, W, H, R = 50.0, 40.0, 130.0, 80.0, 2.0
PAGE_W, PAGE_H = 297.0, 210.0      # A4 sheet the board sits on
S = 16                              # px per mm for textures
T = 1.6                             # board thickness

MASK = np.array([18, 20, 24])       # matte black solder mask over bare laminate
MASK_CU = np.array([40, 43, 50])    # mask over copper
GOLD = np.array([214, 178, 96])     # ENIG
HOLE = np.array([12, 12, 12])
SILK = np.array([236, 236, 232])


def layer_mask(layer, mirror=False):
    svg = f"{TMP}/{layer}.svg"
    args = ["kicad-cli", "pcb", "export", "svg", "-l", layer, "--black-and-white",
            "--page-size-mode", "1", "--exclude-drawing-sheet", "--drill-shape-opt", "2",
            "-o", svg, PCB]
    subprocess.run(args, check=True, capture_output=True)
    png = svg[:-4] + ".png"
    cairosvg.svg2png(url=svg, write_to=png, output_width=int(PAGE_W * S),
                     output_height=int(PAGE_H * S), background_color="white")
    im = np.asarray(Image.open(png).convert("L"))
    im = im[int(OY * S):int((OY + H) * S), int(OX * S):int((OX + W) * S)]
    m = im < 128
    return m[:, ::-1] if mirror else m


def board_alpha():
    h, w = int(H * S), int(W * S)
    yy, xx = np.mgrid[0:h, 0:w] / S
    cx = np.clip(xx, R, W - R)
    cy = np.clip(yy, R, H - R)
    return ((xx - cx) ** 2 + (yy - cy) ** 2) <= R * R


def compose(side):
    mirror = side == "B"
    cu = layer_mask(f"{side}.Cu", mirror)
    op = layer_mask(f"{side}.Mask", mirror)
    sk = layer_mask(f"{side}.SilkS", mirror)
    img = np.zeros(cu.shape + (3,), np.uint8)
    img[:] = MASK
    img[cu] = MASK_CU
    img[op & cu] = GOLD
    img[op & ~cu] = HOLE
    img[sk & ~op] = SILK
    a = board_alpha()
    if mirror:
        a = a[:, ::-1]
    rgba = np.dstack([img, (a * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(f"{TMP}/{side}_tex.png")
    return rgba


# ------------------------------------------------------------------ 3D scene
def rounded_rect_pts(n=8):
    pts = []
    for cx, cy, a0 in [(W - R, R, -90), (W - R, H - R, 0), (R, H - R, 90), (R, R, 180)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    return pts


def face(z, tex_path, flip):
    pts = rounded_rect_pts()
    vp = vtk.vtkPoints()
    tc = vtk.vtkFloatArray()
    tc.SetNumberOfComponents(2)
    for x, y in pts:
        vp.InsertNextPoint(x, -y, z)
        u = x / W
        tc.InsertNextTuple2(1 - u if flip else u, 1 - y / H)
    poly = vtk.vtkCellArray()
    poly.InsertNextCell(len(pts))
    for i in range(len(pts)):
        poly.InsertCellPoint(i)
    pd = vtk.vtkPolyData()
    pd.SetPoints(vp)
    pd.SetPolys(poly)
    pd.GetPointData().SetTCoords(tc)
    tri = vtk.vtkTriangleFilter()
    tri.SetInputData(pd)
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(tri.GetOutputPort())
    rd = vtk.vtkPNGReader()
    rd.SetFileName(tex_path)
    tex = vtk.vtkTexture()
    tex.SetInputConnection(rd.GetOutputPort())
    tex.InterpolateOn()
    tex.MipmapOn()
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.SetTexture(tex)
    p = a.GetProperty()
    p.SetSpecular(0.25)
    p.SetSpecularPower(30)
    p.SetAmbient(0.25)
    p.SetDiffuse(0.85)
    return a


def edge_actor():
    pts = rounded_rect_pts()
    vp = vtk.vtkPoints()
    for x, y in pts:
        vp.InsertNextPoint(x, -y, 0.0)
    cells = vtk.vtkCellArray()
    cells.InsertNextCell(len(pts))
    for i in range(len(pts)):
        cells.InsertCellPoint(i)
    pd = vtk.vtkPolyData()
    pd.SetPoints(vp)
    pd.SetPolys(cells)
    ex = vtk.vtkLinearExtrusionFilter()
    ex.SetInputData(pd)
    ex.SetScaleFactor(T)
    ex.SetVector(0, 0, 1)
    ex.CappingOff()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(ex.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(0.42, 0.40, 0.30)
    return a


_keep = []


def model_actors():
    env = {"KICAD6_3DMODEL_DIR": "/usr/share/kicad/3dmodels",
           "KICAD7_3DMODEL_DIR": "/usr/share/kicad/3dmodels",
           "KIPRJMOD": os.path.dirname(PCB)}
    board = pcbnew.LoadBoard(PCB)
    actors = []
    cache = {}
    for fp in board.GetFootprints():
        pos = fp.GetPosition()
        x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
        rot = fp.GetOrientationDegrees()
        if fp.GetReference() == "C12":   # not fitted
            continue
        is_res = fp.GetReference().startswith("R")
        for md in fp.Models():
            fn = md.m_Filename
            for k, v in env.items():
                fn = fn.replace("${%s}" % k, v)
            if not os.path.exists(fn):
                continue
            if fn not in cache:
                # VTK's VRML reader chokes on '-' in DEF/USE names (KiCad uses them)
                import re
                txt = open(fn, errors="replace").read()
                # ...and does not apply USE'd materials: inline every material
                mats = dict(re.findall(r"DEF\s+([A-Za-z0-9_\-]+)\s+Material\s*(\{[^}]*\})", txt))
                txt = re.sub(r"DEF\s+[A-Za-z0-9_\-]+\s+Material", "Material", txt)
                txt = re.sub(r"material\s+USE\s+([A-Za-z0-9_\-]+)",
                             lambda m: "material Material " + mats.get(m.group(1), "{}"), txt)
                txt = re.sub(r"\b(DEF|USE)\s+([A-Za-z0-9_\-]+)",
                             lambda m: m.group(1) + " " + m.group(2).replace("-", "_"), txt)
                safe = os.path.join(TMP, "m_" + os.path.basename(fn))
                open(safe, "w").write(txt)
                imp = vtk.vtkVRMLImporter()
                imp.SetFileName(safe)
                rwi = vtk.vtkRenderWindow()
                rwi.SetOffScreenRendering(1)
                imp.SetRenderWindow(rwi)
                imp.Update()
                _keep.append((imp, rwi))
                ren = imp.GetRenderer()
                parts = []
                acts = ren.GetActors()
                acts.InitTraversal()
                for _ in range(acts.GetNumberOfItems()):
                    a = acts.GetNextActor()
                    mat = vtk.vtkMatrix4x4()
                    a.GetMatrix(mat)
                    parts.append((a, mat))
                cache[fn] = parts
            for src, mat in cache[fn]:
                t = vtk.vtkTransform()
                t.PostMultiply()
                t.Concatenate(mat)
                t.Scale(2.54, 2.54, 2.54)
                o = md.m_Offset
                t.Translate(o.x, o.y, o.z)
                t.RotateZ(rot)
                t.Translate(x, -y, T)
                a = vtk.vtkActor()
                a.SetMapper(src.GetMapper())
                prop = src.GetProperty()
                c = prop.GetDiffuseColor()
                if is_res and c[0] > 0.7 and c[1] > 0.55 and c[2] < 0.65:
                    prop = vtk.vtkProperty()
                    prop.DeepCopy(src.GetProperty())
                    prop.SetDiffuseColor(0.30, 0.52, 0.80)   # blue metal-film body
                    prop.SetColor(0.30, 0.52, 0.80)
                a.SetProperty(prop)
                a.SetUserTransform(t)
                actors.append(a)
    return actors


def render(name, cam_pos, focal, view_angle=30, size=(2400, 1500), parallel=False):
    ren = vtk.vtkRenderer()
    ren.GradientBackgroundOn()
    ren.SetBackground(0.86, 0.87, 0.89)
    ren.SetBackground2(0.98, 0.98, 0.99)
    ren.AddActor(face(T + 0.005, f"{TMP}/F_tex.png", False))
    ren.AddActor(face(-0.005, f"{TMP}/B_tex.png", True))
    ren.AddActor(edge_actor())
    for a in MODELS:
        ren.AddActor(a)
    lk = vtk.vtkLightKit()
    lk.SetKeyLightIntensity(0.9)
    lk.AddLightsToRenderer(ren)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.SetMultiSamples(8)
    rw.AddRenderer(ren)
    rw.SetSize(*size)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focal)
    cam.SetPosition(*cam_pos)
    cam.SetViewUp(0, 0, 1) if not parallel else cam.SetViewUp(0, 1, 0)
    cam.SetViewAngle(view_angle)
    if parallel:
        cam.ParallelProjectionOn()
        cam.SetParallelScale(H / 2 + 4)
    ren.ResetCameraClippingRange()
    ssao = False
    if hasattr(ren, "SetUseSSAO"):
        ren.SetUseSSAO(True)
        ren.SetSSAORadius(3.0)
        ren.SetSSAOKernelSize(128)
        ssao = True
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(f"{OUT}/{name}.png")
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()
    print("rendered", name, "ssao" if ssao else "")


if __name__ == "__main__":
    top = compose("F")
    bot = compose("B")
    Image.fromarray(top[..., :3]).save(f"{OUT}/board_top_flat.png")
    Image.fromarray(bot[..., :3]).save(f"{OUT}/board_bottom_flat.png")
    MODELS = model_actors()
    cx, cy = W / 2, -H / 2
    render("render_3d_front", (cx - 40, cy - 135, 115), (cx, cy + 4, 4), 30)
    render("render_3d_heatsink_side", (cx + 70, cy + 120, 95), (cx, cy, 6), 30)
    render("render_top", (cx, cy, 300), (cx, cy, 0), parallel=True, size=(2400, 1500))
