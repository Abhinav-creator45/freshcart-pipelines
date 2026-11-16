import pytest
from sklearn.datasets import load_iris
from iris_project.transformers.verify_iris import test_input_quality as check_quality

@pytest.mark.parametrize('fault', ['missing', 'class'])
def test_input_quality_rejects_faults(fault):
    df = load_iris(as_frame=True).frame
    if fault == 'missing':
        df.iloc[0, 0] = float('nan')
    else:
        df.loc[df['target'] == 2, 'target'] = 3
    with pytest.raises(AssertionError):
        check_quality(df)
