"""Validation and export tests; real inference is verified in a separate Slurm job."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InferenceIOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('bgmat_inference', ROOT / 'scripts/bgmat_inference.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_invalid_counts_and_seed_rejected(self):
        for values in [(0, 216, 1), (1, 215, 1), (1, 216, -1)]:
            with self.assertRaises(ValueError):
                self.module.validate_request(*values)

    def test_run_directory_cannot_be_reused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            with self.assertRaises(FileExistsError):
                self.module.reserve_output(Path(directory))

    def test_output_must_be_inside_repo(self):
        with self.assertRaises(ValueError):
            self.module.reserve_output(Path('/tmp/genx-disallowed-output'))

    def test_source_integrity_does_not_require_compute_node_git(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            directory=Path(directory)
            source=directory/'source';source.mkdir()
            code=source/'model.py';code.write_text('x = 1\n')
            lock=directory/'source.json'
            lock.write_text(json.dumps({'upstream_commit':self.module.UPSTREAM_COMMIT,
                'files':{'model.py':self.module.sha256(code)}}))
            self.assertEqual(self.module.verify_source(source,lock),self.module.UPSTREAM_COMMIT)
            code.write_text('x = 2\n')
            with self.assertRaises(ValueError):self.module.verify_source(source,lock)

    def test_xyz_has_cell_particles_and_coarse_grained_label(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            target = Path(directory)/'sample.extxyz'
            self.module.write_extxyz(target, [[[0, 0, 0], [2, 2, 2]]], [5, 5, 5], [-10])
            lines=target.read_text().splitlines()
            self.assertEqual(lines[0], '2')
            self.assertIn('mW_single_bead', lines[1])
            self.assertIn('pbc="T T T"', lines[1])
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[2].split()[0], 'O')

    def test_slurm_spooled_script_uses_submit_directory_and_exports_runtime(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            directory=Path(directory)
            spooled=directory/'slurm_script'
            shutil.copyfile(ROOT/'scripts/run_bgmat_cpu.sh',spooled)
            fake=directory/'srun'
            fake.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            fake.chmod(0o755)
            env=dict(os.environ,SLURM_JOB_ID='test-only',SLURM_SUBMIT_DIR=str(ROOT),
                     PATH=str(directory)+':'+os.environ['PATH'])
            result=subprocess.run(['bash',str(spooled),'--output','runs/example'],
                                  env=env,capture_output=True,text=True,check=True)
            self.assertIn(str(ROOT/'.venv-bgmat/bin/python'),result.stdout)
            self.assertIn('--export=ALL',result.stdout)


if __name__=='__main__':
    unittest.main()
