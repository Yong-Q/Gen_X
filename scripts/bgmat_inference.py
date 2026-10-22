#!/usr/bin/env python3
"""Actual pretrained bgmat sampling, separate from the synthetic smoke workflow.

Sampling calls the Apache-2.0 upstream constructors and _get_loss unchanged.
Only the pinned author's checkpoint is deserialized (pickle is executable input).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = '6e3db2b3453cb57eb16fdd2148c95ec35264faf4'
CHECKPOINT_SHA256 = '89d03c7ae3980421f313b0495b89d92a9f107804f4d936fcd99b34dd4cb294ba'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def validate_request(samples, particles, seed):
    if not 1 <= samples <= 256 or particles != 216 or not 0 <= seed < 2**31:
        raise ValueError('Require 1..256 samples, 216 mW particles, and seed in [0, 2**31)')


def reserve_output(path):
    path = Path(path).resolve()
    if ROOT not in path.parents:
        raise ValueError('Output must resolve inside the repository')
    path.mkdir(parents=True, exist_ok=False)
    return path


def verify_source(source, lock_path):
    lock=json.loads(Path(lock_path).read_text())
    if lock['upstream_commit'] != UPSTREAM_COMMIT:
        raise ValueError('Unexpected upstream source revision')
    source=Path(source).resolve()
    for relative, expected in lock['files'].items():
        path=(source/relative).resolve()
        if source not in path.parents or sha256(path) != expected:
            raise ValueError('Upstream source integrity failure: '+relative)
    return lock['upstream_commit']


def write_extxyz(path, frames, box, energies):
    with Path(path).open('x', encoding='utf-8') as handle:
        lattice = '{} 0 0 0 {} 0 0 0 {}'.format(*box)
        for i, positions in enumerate(frames):
            handle.write(str(len(positions))+'\n')
            handle.write('Lattice="'+lattice+'" Properties=species:S:1:pos:R:3 '
                         'pbc="T T T" representation=mW_single_bead '
                         'explicit_hydrogens=false sample='+str(i)+' '
                         'energy_kcal_per_mol='+str(float(energies[i]))+'\n')
            for xyz in positions:
                handle.write('O {:.10f} {:.10f} {:.10f}\n'.format(*xyz))


def infer(args, output, provenance):
    # Upstream's editable installation omits its PEP-420 namespace package.
    # This exact source tree has already passed the pinned file-hash checks.
    sys.path.insert(0, str(ROOT/'external/bgmat'))
    import importlib.metadata
    import pickle
    import numpy as np
    import jax
    import haiku as hk
    from bgmat.experiments import augmented_monatomic_water_config as mw
    from bgmat.experiments.train_augmented_nvt import create_base, create_flow, _get_loss

    if jax.default_backend() != 'cpu':
        raise RuntimeError('This integration run is restricted to CPU')
    config = mw.get_config(args.particles, 'cubic')
    # Exact pretrained architecture settings from the author's tutorial cells 18–22.
    conditioner = config.model.kwargs.bijector.kwargs.conditioner.kwargs.conditioner_kwargs
    conditioner.embedding_size = 96
    conditioner.n_local = 16
    config.model.kwargs.bijector.kwargs.num_layers = 10
    box = np.asarray(config.test_energy.kwargs.box_length, dtype=float)
    with Path(args.checkpoint).open('rb') as handle:
        params = pickle.load(handle)
    leaves = jax.tree_util.tree_leaves(params)
    parameter_count = sum(int(np.prod(x.shape)) for x in leaves)
    if parameter_count == 0:
        raise ValueError('Checkpoint contains no learned parameters')
    print(json.dumps({'stage':'checkpoint_loaded','parameter_count':parameter_count,
                      'devices':[str(x) for x in jax.devices()]}), flush=True)

    def sample_once():
        base = create_base(config)
        flow = create_flow(config)
        energy = config.test_energy.constructor(**config.test_energy.kwargs)
        _, stats, displacements, coordinates = _get_loss(base, flow, energy, 1, config.state)
        return coordinates, stats, displacements

    transformed = hk.transform(sample_once)
    apply = jax.jit(transformed.apply)
    keys = jax.random.split(jax.random.PRNGKey(args.seed), args.samples)
    coordinates, energies, model_log_prob, target_log_prob = [], [], [], []
    durations = []
    for i, key in enumerate(keys):
        start = time.monotonic()
        frame, stats, _ = jax.device_get(apply(params, key))
        durations.append(time.monotonic()-start)
        coordinates.append(frame[0])
        energies.append(float(stats['energy'][0]))
        model_log_prob.append(float(stats['model_log_prob'][0]))
        target_log_prob.append(float(stats['target_log_prob'][0]))
        print(json.dumps({'stage':'sample_generated','sample':i,'seconds':durations[-1],
                          'energy_kcal_per_mol':energies[-1]}), flush=True)

    coordinates = np.mod(np.asarray(coordinates), box)
    energies = np.asarray(energies)
    model_log_prob = np.asarray(model_log_prob)
    target_log_prob = np.asarray(target_log_prob)
    arrays = [coordinates, energies, model_log_prob, target_log_prob]
    if not all(np.isfinite(x).all() for x in arrays):
        raise ValueError('Nonfinite generated coordinates, energy or probability')
    if coordinates.shape != (args.samples, args.particles, 3):
        raise ValueError('Unexpected generated coordinate shape')
    log_weights = target_log_prob-model_log_prob
    weights = np.exp(log_weights-log_weights.max())
    weights /= weights.sum()
    minima=[]
    for frame in coordinates:
        delta = frame[:,None,:]-frame[None,:,:]
        delta -= box*np.round(delta/box)
        distances = np.linalg.norm(delta,axis=-1)
        np.fill_diagonal(distances, np.inf)
        minima.append(float(distances.min()))
    if min(minima) <= 1e-6:
        raise ValueError('Generated configuration contains coincident beads')
    distinct = len({hashlib.sha256(x.tobytes()).hexdigest() for x in coordinates})
    if args.samples > 1 and distinct < 2:
        raise ValueError('Different random keys produced identical configurations')

    # Keep raw generated samples: no optimization, selection, MD or reweight-resampling.
    with (output/'samples.npz').open('xb') as handle:
        np.savez_compressed(handle, positions_A=coordinates, box_A=box,
                            energies_kcal_per_mol=energies, model_log_prob_unnormalized=model_log_prob,
                            target_log_prob_unnormalized=target_log_prob, importance_weights=weights)
    write_extxyz(output/'samples.extxyz',coordinates,box,energies)
    with (output/'samples.csv').open('x') as handle:
        handle.write('sample,energy_kcal_per_mol,energy_per_bead,min_distance_A,importance_weight\n')
        for i in range(args.samples):
            handle.write('{},{},{},{},{}\n'.format(i,energies[i],energies[i]/args.particles,minima[i],weights[i]))

    reference_path = ROOT/'external/bgmat/tutorial/data_md/ene_md_mw_cubic_216.npy'
    reference = np.load(reference_path, allow_pickle=False)
    summary = dict(provenance)
    summary.update(status='completed',model_inference='passed',synthetic=False,
        scientific_validation='limited_small_sample_diagnostics',
        parameter_count=parameter_count,temperature_K=mw.QUIGLEY_TEMPERATURE,
        number_density_A_minus3=mw.QUIGLEY_DENSITY,box_A=box.tolist(),
        samples_generated=args.samples,particles_per_sample=args.particles,
        representation='mW_single_bead_per_water_no_explicit_H',phase='cubic_ice',
        coordinate_unit='angstrom',energy_unit='kcal/mol of systems',
        probability_scope='joint physical and auxiliary coordinates; both log scores use the upstream unnormalized Einstein-reference convention; constants cancel in normalized weights',
        normalized_importance_weights=weights.tolist(),ess_samples=float(1/np.sum(weights**2)),
        ess_percent=float(100/(args.samples*np.sum(weights**2))),
        min_pair_distance_A=minima,distinct_coordinate_arrays=distinct,
        energy_per_bead_mean=float(energies.mean()/args.particles),
        reference_MD_energy_per_bead_mean=float(reference.mean()/args.particles),
        reference_MD_samples=int(reference.size),reference_MD_sha256=sha256(reference_path),
        sample_wall_seconds=durations,first_sample_includes_JIT=True,
        optimization_or_MD=False,training=False,finished_utc=datetime.now(timezone.utc).isoformat(),
        software_versions={name:importlib.metadata.version(name) for name in
                           ['jax','jaxlib','numpy','scipy','dm-haiku','distrax','e3nn-jax']},
        output_sha256={name:sha256(output/name) for name in ['samples.npz','samples.extxyz','samples.csv']},
        interpretation='Real pretrained generation verified; eight samples do not establish converged distributions, free energies, or paper-level replication.')
    write_json(output/'manifest.json',summary)
    print(json.dumps({'stage':'completed','output':str(output),'ess_samples':summary['ess_samples']}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=8)
    parser.add_argument('--particles',type=int,default=216)
    parser.add_argument('--seed',type=int,default=20261022)
    parser.add_argument('--checkpoint',type=Path,default=ROOT/'external/bgmat/tutorial/params_trained/params-mw_cubic_216.pkl')
    args=parser.parse_args()
    validate_request(args.samples,args.particles,args.seed)
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Submit this inference through Slurm; do not compute on the login node')
    # Compute nodes need only the source snapshot; git itself is not required there.
    actual_commit=verify_source(ROOT/'external/bgmat',ROOT/'configs/bgmat_source_lock.json')
    if actual_commit != UPSTREAM_COMMIT or sha256(args.checkpoint) != CHECKPOINT_SHA256:
        raise ValueError('Upstream revision or checkpoint hash differs from the reviewed source')
    output=reserve_output(args.output)
    provenance={'started_utc':datetime.now(timezone.utc).isoformat(),'upstream':'https://github.com/maxschebek/bgmat',
                'upstream_commit':actual_commit,'checkpoint_sha256':CHECKPOINT_SHA256,
                'script_sha256':sha256(__file__),'command':sys.argv,'seed':args.seed,
                'slurm_job_id':os.environ['SLURM_JOB_ID'],'hostname':os.uname().nodename,
                'slurm_cpus_per_task':os.environ.get('SLURM_CPUS_PER_TASK'),'backend':'cpu'}
    write_json(output/'launch.json',provenance)
    try:
        infer(args,output,provenance)
    except Exception as error:
        write_json(output/'failure.json',dict(provenance,status='failed',error=repr(error)))
        raise


if __name__=='__main__':
    main()
