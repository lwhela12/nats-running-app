from app.domain.projection import riegel_predict


def test_riegel_monotonic_with_distance():
    t5k = 25 * 60
    t10k = riegel_predict(t5k, 5000, 10000)
    t_half = riegel_predict(t5k, 5000, 21097)
    assert t10k > t5k
    assert t_half > t10k


def test_riegel_exponent_variants():
    t1 = riegel_predict(3600, 10000, 21097, k=1.02)
    t2 = riegel_predict(3600, 10000, 21097, k=1.10)
    assert t2 > t1


def test_riegel_invalid_distance_raises():
    try:
        riegel_predict(1000, 0, 5000)
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"

