"""
This module contains the General class and related functions for WAD-QC.

The General class provides a set of general functions and parameters for WAD-QC. It is designed to work in conjunction with the Data class to process DICOM images and perform various operations.

Classes:
- General: A class that defines parameters and provides general functions.

Functions:
- None

Example Usage:
---------------
import pydicom as dcm
from data import Data

# Create a Data object
data = Data()

# Create a General object
general = General(data)

# Convert Acquisition DateTime string to datetime format
converted_datetime = general.convert_date_time()

# Print the converted datetime
print(converted_datetime)

"""

import datetime as dt
import pydicom as dcm
import numpy as np


class Config:
    """
    Getting config parameters from json.
    """

    def __init__(self, config_parameters) -> None:
        self.config_paramseters = config_parameters

    @property
    def get_config_params(self) -> dict:
        """
        Returns a dictonary with the parameters given in the config json
        """
        return self.config_paramseters["actions"].get("qc_series").get("params")


class General:
    """
    A class that defines parameters and provides general functions.

    Attributes:
        data (object): The data object containing series filelist.
        images (list): A list of DICOM images.

    Methods:
        __init__(self, data): Initializes the General class.
        convert_date_time: Converts Acquisition DateTime string to datetime format.

    Example usage:
        data = Data()
        general = General(data)
        converted_datetime = general.convert_date_time()
    """

    def __init__(self, data) -> None:
        self.headers = [
            dcm.dcmread(file, stop_before_pixels=True)
            for file in data.series_filelist[0]
        ]
        self.data = data

    # @property
    def convert_date_time(self, acquisitiondatetime):
        """
        Convert Acquisition DateTime string to datetime format. Not all labs report
        microseconds, so they are removed beforehand for those that do.
        """

        convertedacquistiondatetime = dt.datetime.strptime(
            acquisitiondatetime, "%Y%m%d%H%M%S"
        )
        return convertedacquistiondatetime

    def outside_tolerance_check(self, values, instances, alarm_limit) -> np.ndarray:
        """
        Function to check if any values differ from the center value with a
        given value. Will return an array with indecies and values if outside6
        the tolerance, if not it will return False.
        """
        center = values[int(len(values) / 2)]
        if (1 in np.shape(values)) or len(np.shape(values)) == 1:
            if np.any(np.abs(values) > np.abs(center * alarm_limit)):
                indecies = np.where(np.abs(values) > np.abs(center * alarm_limit))
                number_of_indecies = len(indecies[0])
                values_outside = np.zeros((number_of_indecies, 2))

                for counter, index in enumerate(indecies[0]):
                    values_outside[counter] = [instances[index], float(values[index])]
            else:
                values_outside = False

        else:
            highest_diff = np.max(np.abs(center))

            if np.any(np.abs(values) > np.abs(highest_diff * alarm_limit)):
                indecies = np.where(np.abs(values) > np.abs(highest_diff * alarm_limit))
                values_outside = np.zeros((len(indecies[0]), 3))

                for counter, index in enumerate(indecies[0]):
                    values_outside[counter] = (
                        instances[index],
                        indecies[1][counter],
                        values[indecies[0][counter], indecies[1][counter]],
                    )

            else:
                values_outside = False

        return values_outside

    def read_and_write_dcm_info(self, results: object, dicom_tag: list):
        """
        Reads the specified dicom tag and writes it to results. Dicom tags can be
        given as a list of dictionary. If more than one instance, the middle instance dicom tag(s)
        will be saved to results.

        :param results: object contating the results.json file.
        :param dicom_tag: list of dictionaries to determine dicom tags to be saved.
        Dictonaries have the form {"dicom_name": "name of dicom tag", "results_name":
        "name that will show up in results", "type": "value type (float, str, etc.)",
        "factor": float to muliply result value with (optional)}
        """

        for tag in dicom_tag:
            if len(self.headers) > 1:
                header = self.headers[int(len(self.headers) / 2)]
            else:
                header = self.headers[0]

            value = getattr(header, tag.get("dicom_name"))

            if tag.get("factor"):
                value *= tag.get("factor")

            if tag.get("type") == "float":
                results.addFloat(tag.get("results_name"), value)

            elif tag.get("type") == "str":
                results.addString(tag.get("results_name"), value)

            elif tag.get("type") == "datetime":
                date_tag = tag.get("dicom_name")
                time_tag = date_tag.replace("Date", "Time")
                time_value = getattr(header, time_tag)
                time_value = time_value[0:6]
                date_time = value + time_value
                value = self.convert_date_time(date_time)
                results.addDateTime(tag.get("results_name"), value)

        return results
