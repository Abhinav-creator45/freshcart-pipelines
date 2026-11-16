"""C4 extension: validate the input measurements before splitting."""
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def verify(df, *args, **kwargs):
    return df.copy()

@test
def test_input_quality(output, *args):
    assert not output.isna().any().any(), 'Iris data contains missing values'
    assert set(output['target']) == {0, 1, 2}, 'Expected exactly three Iris classes'
