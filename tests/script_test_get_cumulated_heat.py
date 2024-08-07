import pathlib

import pysnooper
import pytest

from CaloCem import tacalorimetry


#
# run "time check" on each sample file
# see https://www.youtube.com/watch?v=DhUpxWjOhME (~ at 12:20)
# to use the the test:
#       1) install the module locally with "pip install -e ."
#       2) run "pytest" from shell
#
# @pytest.mark.parametrize(
#     "test_input,expected",
#     [
#         ("OPC_1.xls", 499440),
#         ("OPC_2.xls", 336000),
#     ],
# )
# @pysnooper.snoop()
# def test_last_time_entry(test_input, expected):

# path
path = pathlib.Path().cwd().parent / "CaloCem" / "DATA"

# get data
tam = tacalorimetry.Measurement(
    path, regex="calorimetry_data_[245].*csv", show_info=True, cold_start=False
)
# %%
data = tam.get_data()

h = tam.get_cumulated_heat_at_hours(target_h=[1, 2, 3, 4, 8], cutoff_min=10)

# print(h)

import seaborn as sns

sns.barplot(data=h, hue="sample", y="cumulated_heat_at_hours", x="target_h")

# # get "last time for a file
# last_time = int(data.tail(1)["time_s"])

# # actual test
# assert last_time == int(expected)


# %%

# kk = tacalorimetry.Measurement()._read_calo_data_csv_comma_sep(r"C:\Users\LocalAdmin\Documents\GitHub\CaloCem\CaloCem\DATA\TEST_CALO_Gen1+2.csv")
# data = tacalorimetry.Measurement()._read_calo_data_csv_comma_sep(r"C:\Users\LocalAdmin\Documents\GitHub\CaloCem\CaloCem\DATA\TEST_CALO_Gen3.csv")
# data = tacalorimetry.Measurement()._read_calo_data_csv(r"C:\Users\LocalAdmin\Documents\GitHub\CaloCem\CaloCem\DATA\calorimetry_data_1.csv")

tam.plot(regex="calorimetry_data_.*")

tacalorimetry.plt.xlim(0, 20)


# # %% remove pickled files

# tam.remove_pickle_files()
