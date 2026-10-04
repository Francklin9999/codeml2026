"""Check an STL like a slicer would: python validate_stl.py file.stl. One line per check, exit 1 on any failure."""
import sys

import numpy as np
import trimesh


def _bodies(faces: np.ndarray) -> int:
    """Connected components of faces sharing a vertex (union-find, no scipy/networkx needed)."""
    parent = list(range(int(faces.max()) + 1)) if len(faces) else []

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in faces:
        ra, rb, rc = find(int(a)), find(int(b)), find(int(c))
        parent[rb] = ra
        parent[rc] = ra
    return len({find(int(v)) for v in np.unique(faces)})


def validate(path: str) -> list[tuple[str, bool, str]]:
    try:
        mesh = trimesh.load(path, force='mesh', process=True)
    except Exception as e:  # unreadable file is a failed check, not a crash
        return [('readable', False, str(e))]
    if len(mesh.faces) == 0:
        return [('readable', False, 'no triangles')]
    ext = mesh.bounds[1] - mesh.bounds[0]
    return [
        ('watertight', bool(mesh.is_watertight), f'{len(mesh.faces)} triangles'),
        ('winding consistent', bool(mesh.is_winding_consistent), ''),
        ('single body', _bodies(mesh.faces) == 1, f'{_bodies(mesh.faces)} body(ies)'),
        ('positive volume', bool(mesh.volume > 0), f'{mesh.volume:.2f} mm3'),
        ('bounding box', bool(np.all(np.isfinite(ext)) and np.all(ext > 0)),
         f'{ext[0]:.2f} x {ext[1]:.2f} x {ext[2]:.2f} mm'),
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print('usage: validate_stl.py file.stl', file=sys.stderr)
        return 2
    checks = validate(argv[1])
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f': {detail}' if detail else ''))
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
