# Copyright 2017--2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License
# is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import pytest

import mxnet as mx
import numpy as np

import sockeye.constants as C
import sockeye.encoder
import sockeye.transformer


@pytest.mark.parametrize('dropout, factor_configs', [
    (0., None),
    (0.1, [sockeye.encoder.FactorConfig(vocab_size=5,
                                        num_embed=5,
                                        combine=C.FACTORS_COMBINE_SUM,
                                        share_embedding=False)]),
])
def test_embedding_encoder(dropout, factor_configs):
    config = sockeye.encoder.EmbeddingConfig(vocab_size=20, num_embed=10, dropout=dropout, factor_configs=factor_configs)
    embedding = sockeye.encoder.Embedding(config, prefix='embedding')
    assert type(embedding) == sockeye.encoder.Embedding


@pytest.mark.parametrize('lhuc', [
    (False,),
    (True,)
])
def test_get_transformer_encoder(lhuc):
    prefix = "test_"
    config = sockeye.transformer.TransformerConfig(model_size=20,
                                                   attention_heads=10,
                                                   feed_forward_num_hidden=30,
                                                   act_type='test_act',
                                                   num_layers=40,
                                                   dropout_attention=1.0,
                                                   dropout_act=2.0,
                                                   dropout_prepost=3.0,
                                                   positional_embedding_type=C.LEARNED_POSITIONAL_EMBEDDING,
                                                   preprocess_sequence='test_pre',
                                                   postprocess_sequence='test_post',
                                                   max_seq_len_source=50,
                                                   max_seq_len_target=60,
                                                   use_lhuc=lhuc)
    encoder = sockeye.encoder.get_transformer_encoder(config, prefix=prefix, dtype = C.DTYPE_FP32)
    encoder.initialize()
    encoder.hybridize(static_alloc=True)

    assert type(encoder) == sockeye.encoder.TransformerEncoder
    assert encoder.prefix == prefix + C.TRANSFORMER_ENCODER_PREFIX


def test_concat_encoder_reps():
    # In this artificial data, encoded content has positive values and encoded
    # padding has negative values.
    layer_reps = [mx.nd.array([[[1, 2], [3, 4], [-1, -2], [-3, -4]],
                               [[1, 2], [3, 4], [5, 6], [-1, -2]]]),
                  mx.nd.array([[[5, 6], [7, 8], [-5, -6], [-7, -8]],
                               [[7, 8], [9, 10], [11, 12], [-3, -4]]])]
    valid_length = mx.nd.array([2, 3])

    expected_concat_reps = mx.nd.array([[[1, 2], [3, 4], [5, 6], [7, 8], [-1, -2], [-3, -4], [-5, -6], [-7, -8]],
                                        [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [-1, -2], [-3, -4]]])
    expected_concat_valid_length = mx.nd.array([4, 6])

    concat_reps, concat_valid_length = sockeye.encoder.concat_encoder_reps(layer_reps, valid_length)

    assert np.array_equal(concat_reps.asnumpy(), expected_concat_reps.asnumpy())
    assert np.array_equal(concat_valid_length.asnumpy(), expected_concat_valid_length.asnumpy())
