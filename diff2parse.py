#!/bin/env python

import argparse
import os
from subprocess import call, check_output
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--parse-thalamus', action='store_true')
parser.add_argument('--parse-cortex', action='store_true')
parser.add_argument('--reset', action='store_true')
parser.add_argument('--verbose', '-v', action='store_true')
parser.add_argument('--pairs', '-p', nargs='+')
parser.add_argument('--options')
args = parser.parse_args()

def _run(command):
    """Run a command in shell"""
    if args.verbose:
        print(command)
    if not args.dry_run:
        call(command, shell=True)

def _get_options():
    """Get options in local order of preference"""
    if args.options:
        fp = os.path.abspath(args.options)
    else:
        working_directory = 'options'
        home_directory = os.path.join(os.getenv('HOME'), 'options')
        var_directory = '/var/project_delta/options'
        if os.path.isfile(working_directory):
            fp = os.path.abspath(working_directory)
        elif os.path.isfile(home_directory):
            fp = home_directory
        elif os.path.isfile(var_directory):
            fp = var_directory
        else:
            raise OSError("Options file not found")
    if args.verbose:
        print(': '.join(['Reading options from', fp]))
    with open('options', 'r') as f:
        options = yaml.load(f)
    return options

def _set_base(options):
    """Create base probtrackx2 call"""
    base = [
    'probtrackx2',
    '-l',
    '--onewaycondition',
    '-c',
    options['c'],
    '-S',
    options['steps'],
    '='.join(['--steplength', str(options['steplength'])]),
    '-P',
    options['P'],
    '='.join(['--xfm', os.path.join(options['base_directory'], options['bedpostX_directory'], 'xfms', options['xfm'])]),
    '='.join(['--fibthresh', str(options['fibthresh'])]),
    '='.join(['--distthresh', str(options['distthresh'])]),
    '--forcedir',
    '--opd',
    '--os2t',
    '-s',
    os.path.join(options['bedpostX_directory'], 'merged'),
    '-m',
    os.path.join(options['bedpostX_directory'], 'nodif_brain_mask')
    ]
    if options['euler']:
        base.append('--modeuler')
    if options['verbose']:
        base.append('-V 1')
    return base

def _parcellate(seed_location, output):
    """ Wraps FSL function 'find_the_biggest' """
    command = ' '.join([str(item) for item in [
    'find_the_biggest',
    os.path.join(seed_location, 'seeds_to_*'),
    output
    ]])
    _run(command)

def _split_parcels(parcel, options):
    """Split parcel image into seed masks"""
    FSLDIR = os.getenv('FSLDIR')
    maximum = check_output([
    os.path.join(FSLDIR, 'bin', 'fslstats'),
    parcel,
    '-R'
    ]).split()[1]
    maximum = int(float(maximum))
    seed_list = []
    for i in range(1, maximum):
        seed_name = os.path.join(os.path.join(options['base_directory'], options['masks_directory'], 'seed_' + str(i) + '.nii.gz'))
        seed_list.append(seed_name)
        command = ' '.join([str(item) for item in [
        'fslmaths',
        parcel,
        '-thr',
        i,
        '-uthr',
        i,
        '-bin',
        seed_name
        ]])
        _run(command)
    return seed_list

def _set_output(options, structure, side):
    """Set output based on structure, side, and options"""
    if options['output_modifier']:
        output = os.path.join(options['base_directory'], '_'.join([
        options['output_modifier'], '_'.join([side, structure, 'parcellated'])]))
    else:
        output = os.path.join(options['base_directory'], '_'.join([side, structure, 'parcellated']))
    if args.verbose:
        print('Output set to: ' + output)
    if not os.path.isdir(output):
        os.makedirs(output)
    return output

def parce_thalamus():
    """
    Run probtrakx2 in classification mode from thalamus to eight user defined
    seed masks
    """
    options = _get_options()
    base = _set_base(options=options)
    for side in options['sides']:
        output = _set_output(options=options, side=side, structure='thalamus')
        with open(os.path.join(output, side), 'w') as f:
            f.write('\n'.join([os.path.join(options['base_directory'], options['masks_directory'], '_'.join([side, item])) for item in [
            options['mammillothalamic_tract'],
            options['amygdala'],
            options['globus_pallidus'],
            options['putamen'],
            options['medial_lemniscus'],
            # options['sensory_trigeminal'],
            options['inferior_colliculus'],
            options['optic_tract'],
            options['superior_colliculus']
            ]]))
        command = ' '.join([str(item) for item in base + [
        '-x',
        os.path.join(options['base_directory'], options['masks_directory'], '_'.join([side, options['thalamus']])),
        '='.join(['--targetmasks', os.path.join(output, side)]),
        '='.join(['--dir', output])
        ]])
        _run(command)
        _parcellate(seed_location=output, output=os.path.join(output, options['parcels_name']))

def parse_cortex():
    """
    Run probtrakx2 in classification mode from cortex to eight thalamic seed masks
    """
    options = _get_options()
    base = _set_base(options=options)
    for side in options['sides']:
        prior_output = _set_output(options=options, side=side, structure='thalamus')
        prior_parcel = os.path.join(prior_output, options['parcels_name'])
        if not os.path.isfile(prior_parcel):
            raise OSError("Expected thalamic parcel at: " + prior_parcel)
        seed_list = _split_parcels(parcel=prior_parcel, options=options)
        output = _set_output(side=side, structure='cortex', options=options)
        with open(os.path.join(output, side), 'w') as f:
            f.write('\n'.join(seed_list))
        command = ' '.join([str(item) for item in base + [
        '-x',
        os.path.join(options['base_directory'], options['masks_directory'], '_'.join([side, options['cortex']])),
        '='.join(['--targetmasks', os.path.join(output, side)]),
        '='.join(['--dir', output])
        ]])
        _run(command)
        _parcellate(seed_location=output, output=os.path.join(output, options['parcels_name']))

def reset(pairs):
    """
    CLI tool for resetting key-value pairs in options file
    """
    keys = pairs[0:len(pairs):2]
    values = pairs[1:len(pairs):2]
    with open('options', 'r+') as f:
        options = yaml.load(f)
        for key in keys:
            if key not in options:
                f.close()
                raise KeyError("One of the supplied keys is not valid")
        for key, value in zip(keys, values):
            options.update({key : value})
        yaml.dump(options, f)
    return True

if __name__ == '__main__':
    if args.reset:
        if len(args.pairs) % 2:
            raise IndexError('Odd number of key-value pairs')
        else:
            reset(args.pairs)
    if args.parse_thalamus:
        parse_thalamus()
    if args.parse_cortex:
        parse_cortex()
    else:
        print("It looks like you haven't called any functions!")
