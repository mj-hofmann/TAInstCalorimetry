import numpy as np
import pandas as pd
from scipy.interpolate import InterpolatedUnivariateSpline, UnivariateSpline
from scipy.signal import convolve, gaussian


#
# conversion of DataFrame to float
#
def convert_df_to_float(df: pd.DataFrame) -> pd.DataFrame:
    """
    convert

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """

    # type conversion
    for c in df.columns:
        try:
            df[c] = df[c].astype(float)
        except Exception:
            pass

    # return modified DataFrame
    return df


def fit_univariate_spline(df, target_col, s=1e-6):
    """
    fit_univariate_spline

    Parameters
    ----------
    df : pandas dataframe
        DESCRIPTION.

    target_col : str
        DESCRIPTION.

    s : float, optional
        DESCRIPTION. The default is 1e-6.

    """
    df[target_col].fillna(0, inplace=True)
    spl = UnivariateSpline(df["time_s"], df[target_col], s=s)
    df["interpolated"] = spl(df["time_s"])
    # cut off last 100 points to avoid large gradient detection due to potential interpolation artifacts at the end of the data
    df = df.iloc[:-100, :]
    return df


def calculate_smoothed_heatflow_derivatives(
    df: pd.DataFrame, window: int = 11, polynom: int = 3, spline_smoothing: float = 1e-9
) -> tuple[pd.Series, pd.Series]:
    """
    calculate first and second derivative of heat flow

    Parameters
    ----------
    df : pandas DataFrame
        A dataframe containing the calorimetry data.

    window : int, optional
        Window size for Savitzky-Golay filter. The default is 11.

    polynom : int, optional
        Polynom order for Savitzky-Golay filter. The default is 3.

    spline_smoothing : float, optional
        Smoothing factor for spline interpolation. The default is 1e-9.

    Returns
    -------
    df["first_derivative"] : pandas Series
        First derivative of the heat flow.

    df["second_derivative"] : pandas Series
        Second derivative of the heat flow.

    """

    #
    df["norm_hf_smoothed"] = non_uniform_savgol(
        df["time_s"].values,
        df["normalized_heat_flow_w_g"].values,
        window=window,
        polynom=polynom,
    )
    df["first_derivative"] = np.gradient(df["norm_hf_smoothed"], df["time_s"])
    df["first_derivative"] = df["first_derivative"].fillna(value=0)
    # interpolate first derivative for better smoothing
    f = UnivariateSpline(df["time_s"], df["first_derivative"], k=3, s=spline_smoothing)
    df["interpolated_first_derivative"] = f(df["time_s"])
    df["second_derivative"] = np.gradient(
        df["interpolated_first_derivative"], df["time_s"]
    )

    return df["first_derivative"], df["second_derivative"]


# https://dsp.stackexchange.com/questions/1676/savitzky-golay-smoothing-filter-for-not-equally-spaced-data
def non_uniform_savgol(x, y, window, polynom):
    """
    Applies a Savitzky-Golay filter to y with non-uniform spacing
    as defined in x

    This is based on https://dsp.stackexchange.com/questions/1676/savitzky-golay-smoothing-filter-for-not-equally-spaced-data
    The borders are interpolated like scipy.signal.savgol_filter would do

    Parameters
    ----------
    x : array_like
        List of floats representing the x values of the data
    y : array_like
        List of floats representing the y values. Must have same length
        as x
    window : int (odd)
        Window length of datapoints. Must be odd and smaller than x
    polynom : int
        The order of polynom used. Must be smaller than the window size

    Returns
    -------
    np.array of float
        The smoothed y values
    """
    if len(x) != len(y):
        raise ValueError('"x" and "y" must be of the same size')

    if len(x) < window:
        raise ValueError("The data size must be larger than the window size")

    if type(window) is not int:
        raise TypeError('"window" must be an integer')

    if window % 2 == 0:
        raise ValueError('The "window" must be an odd integer')

    if type(polynom) is not int:
        raise TypeError('"polynom" must be an integer')

    if polynom >= window:
        raise ValueError('"polynom" must be less than "window"')

    half_window = window // 2
    polynom += 1

    # Initialize variables
    A = np.empty((window, polynom))  # Matrix
    tA = np.empty((polynom, window))  # Transposed matrix
    t = np.empty(window)  # Local x variables
    y_smoothed = np.full(len(y), np.nan)

    # Start smoothing
    for i in range(half_window, len(x) - half_window, 1):
        # Center a window of x values on x[i]
        for j in range(0, window, 1):
            t[j] = x[i + j - half_window] - x[i]

        # Create the initial matrix A and its transposed form tA
        for j in range(0, window, 1):
            r = 1.0
            for k in range(0, polynom, 1):
                A[j, k] = r
                tA[k, j] = r
                r *= t[j]

        # Multiply the two matrices
        tAA = np.matmul(tA, A)

        # Invert the product of the matrices
        tAA = np.linalg.inv(tAA)

        # Calculate the pseudoinverse of the design matrix
        coeffs = np.matmul(tAA, tA)

        # Calculate c0 which is also the y value for y[i]
        y_smoothed[i] = 0
        for j in range(0, window, 1):
            y_smoothed[i] += coeffs[0, j] * y[i + j - half_window]

        # If at the end or beginning, store all coefficients for the polynom
        if i == half_window:
            first_coeffs = np.zeros(polynom)
            for j in range(0, window, 1):
                for k in range(polynom):
                    first_coeffs[k] += coeffs[k, j] * y[j]
        elif i == len(x) - half_window - 1:
            last_coeffs = np.zeros(polynom)
            for j in range(0, window, 1):
                for k in range(polynom):
                    last_coeffs[k] += coeffs[k, j] * y[len(y) - window + j]

    # Interpolate the result at the left border
    for i in range(0, half_window, 1):
        y_smoothed[i] = 0
        x_i = 1
        for j in range(0, polynom, 1):
            y_smoothed[i] += first_coeffs[j] * x_i
            x_i *= x[i] - x[half_window]

    # Interpolate the result at the right border
    for i in range(len(x) - half_window, len(x), 1):
        y_smoothed[i] = 0
        x_i = 1
        for j in range(0, polynom, 1):
            y_smoothed[i] += last_coeffs[j] * x_i
            x_i *= x[i] - x[-half_window - 1]

    return y_smoothed
