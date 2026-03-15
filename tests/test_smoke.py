from kortana.utils import timestamp_utils


def test_smoke():
    print("SMOKE TEST:", timestamp_utils.get_iso_timestamp())


if __name__ == "__main__":
    test_smoke()
