#!/usr/bin/env python

from clip2frame import utils
import numpy as np
import theano
import theano.tensor as T
from lasagne import layers


if __name__ == '__main__':
    # Search options
    search_range = (0, 1)
    step_size = 1e-4
    measure_type = 'f1'

    # Files and directories
    data_dir = '../data/data.magnatagatune/sample_exp_data'
    param_fp = '../data/models/sample_model.npz'
    threshold_fp = '../data/models/sample_threshold.magnatagatune.npy'

    # Default setting
    scale_list = [
        "scale0",
        "scale1",
        "scale2",
    ]

    # Load data
    n_scales = len(scale_list)
    X_va_list, y_va = \
        utils.load_data_multiscale_va(
            data_dir, scale_list
        )
    X_list = X_va_list
    y = y_va

    # Network options
    network_type = 'fcn_gaussian_multiscale'
    n_early_conv = 2
    early_pool_size = 4
    network_options = {
        'early_conv_dict_list': [
            {'conv_filter_list': [(32, 8) for ii in range(n_early_conv)],
             'pool_filter_list': [early_pool_size
                                  for ii in range(n_early_conv)],
             'pool_stride_list': [None for ii in range(n_early_conv)]}
            for ii in range(n_scales)
        ],
        'late_conv_dict': {
            'conv_filter_list': [(512, 1), (512, 1)],
            'pool_filter_list': [None, None],
            'pool_stride_list': [None, None]
        },
        'dense_filter_size': 1,
        'scan_dict': {
            'scan_filter_list': [256],
            'scan_std_list': [256/early_pool_size**n_early_conv],
            'scan_stride_list': [1],
        },
        'final_pool_function': T.mean,  # T.max
        'input_size_list': [128 for nn in range(n_scales)],
        'output_size': 188,
        'p_dropout': 0.5
    }
    network, input_var_list, pr_func = utils.make_network_multiscale_test(
        network_type, n_scales, network_options
    )

    # Load params
    utils.load_model(param_fp, network)

    # Make predicting function
    sym_song_prediction = layers.get_output(network, deterministic=True)
    clip_func = theano.function(input_var_list, [sym_song_prediction])

    # Predict
    clip_prediction = np.vstack(
        [term[0] for term in utils.predict_multiscale(X_list, clip_func)])

    print('Searching for thresholds...')
    thresholds, measures = utils.get_thresholds(clip_prediction, y,
                                                search_range, step_size,
                                                measure_func=measure_type,
                                                n_processes=20)
    np.save(threshold_fp, thresholds)
