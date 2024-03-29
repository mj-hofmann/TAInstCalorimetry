import pathlib

import pytest

from TAInstCalorimetry import tacalorimetry


@pytest.mark.parametrize(
    "file, expected",
    [
        ("opc_3.csv", 322461),
        ("c3a.csv", 173873),
        (
            "TEST_CALO_Gen1+2.csv",
            None,
        ),  # multiples samples in one file?  --> do nothing / return 0
        ("TEST_CALO_Gen3.csv", 172799),
        ("calorimetry_data_1.csv", 296830),  # comma sep
        ("calorimetry_data_2.csv", 277199),
        ("calorimetry_data_3.csv", 296820),  # comma sep
        ("calorimetry_data_4.csv", 277199),
        ("calorimetry_data_5.csv", 277199),
        ("1stgen.csv", 264470),  # in-situ first gen file
        ("1stgen_2.csv", 263750),  # in-situ first gen file
        ("MOD_myexp1.csv", 259040),  # comma sep ("corrupt" due to 2 missing values)
    ],
)
def test_last_time_entry(file, expected):

    # path
    path = pathlib.Path().cwd() / "TAInstCalorimetry" / "DATA"

    # get data
    data = tacalorimetry.Measurement(auto_clean=False)._read_calo_data_csv(path / file)

    # checks
    if data is None:
        # test
        assert data is None
    else:
        # discard NaN values
        data = data.dropna()
        # actual test
        assert int(data.tail(1)["time_s"].values[0]) == expected
