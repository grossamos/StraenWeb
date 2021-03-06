# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Computes training paces based on previous efforts."""

import Keys
import VO2MaxCalculator

class TrainingPaceCalculator(object):
    """Computes training paces based on previous efforts"""

    def __init__(self):
        super(TrainingPaceCalculator, self).__init__()

    def convert_vo2max_to_speed(self, vo2):
    	return 29.54 + 5.000663 * vo2 - 0.007546 * vo2 * vo2

    def calc_from_vo2max(self, vo2max):
        """Give the athlete's VO2Max, returns the suggested long run, easy run, tempo run, and speed run paces."""
        long_run_pace = vo2max * 0.6
        easy_pace = vo2max * 0.7
        tempo_pace = vo2max * 0.88
        speed_pace = vo2max * 1.1
        long_run_pace = self.convert_vo2max_to_speed(long_run_pace)
        easy_pace = self.convert_vo2max_to_speed(easy_pace)
        tempo_pace = self.convert_vo2max_to_speed(tempo_pace)
        speed_pace = self.convert_vo2max_to_speed(speed_pace)
        paces = {}
        paces[Keys.LONG_RUN_PACE] = long_run_pace
        paces[Keys.EASY_RUN_PACE] = easy_pace
        paces[Keys.TEMPO_RUN_PACE] = tempo_pace
        paces[Keys.SPEED_RUN_PACE] = speed_pace
        return paces

    def calc_from_hr(self, max_hr, resting_hr):
        """Give the athlete's maximum and resting heart rates, returns the suggested long run, easy run, tempo run, and speed run paces."""
        v02maxCalc = VO2MaxCalculator.VO2MaxCalculator()
        vo2max = v02maxCalc.estimate_vo2max_from_heart_rate(max_hr, resting_hr)
        return self.calc_from_vo2max(vo2max)

    def calc_from_race_distance_in_meters(self, race_distance_meters, race_time_minutes):
        """Give the an athlete's recent race result, returns the suggested long run, easy run, tempo run, and speed run paces."""
        v02maxCalc = VO2MaxCalculator.VO2MaxCalculator()
        vo2max = v02maxCalc.estimate_vo2max_from_race_distance_in_meters(race_distance_meters, race_time_minutes)
        return self.calc_from_vo2max(vo2max)
