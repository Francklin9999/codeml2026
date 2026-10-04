import trimesh

import validate_stl


def _write(tmp_path, mesh, name='m.stl'):
    p = tmp_path / name
    mesh.export(str(p))
    return str(p)


def test_cube_passes(tmp_path, capsys):
    path = _write(tmp_path, trimesh.creation.box(extents=(10, 20, 30)))
    assert validate_stl.main(['validate_stl.py', path]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 5 and all(l.startswith('PASS') for l in out)
    assert '10.00 x 20.00 x 30.00 mm' in out[-1]


def test_cube_missing_one_triangle_fails(tmp_path, capsys):
    box = trimesh.creation.box(extents=(10, 10, 10))
    broken = trimesh.Trimesh(vertices=box.vertices, faces=box.faces[1:], process=False)
    path = _write(tmp_path, broken)
    assert validate_stl.main(['validate_stl.py', path]) == 1
    assert 'FAIL watertight' in capsys.readouterr().out


def test_two_bodies_and_inverted_fail(tmp_path):
    a = trimesh.creation.box(extents=(5, 5, 5))
    b = trimesh.creation.box(extents=(5, 5, 5))
    b.apply_translation((20, 0, 0))
    two = trimesh.util.concatenate([a, b])
    res = {n: ok for n, ok, _ in validate_stl.validate(_write(tmp_path, two, 'two.stl'))}
    assert res['watertight'] and not res['single body']
    inv = trimesh.Trimesh(vertices=a.vertices, faces=a.faces[:, ::-1], process=False)
    res = {n: ok for n, ok, _ in validate_stl.validate(_write(tmp_path, inv, 'inv.stl'))}
    assert not res['positive volume']


def test_unreadable_file_fails(tmp_path):
    p = tmp_path / 'x.stl'
    p.write_text('not an stl')
    assert validate_stl.main(['validate_stl.py', str(p)]) == 1
