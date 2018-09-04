# Copyright 2018 Michael J Simms

import SensorAnalyzer
import StraenKeys

class CadenceAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on bicycle cadence."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, StraenKeys.APP_CADENCE_KEY, "RPM")
