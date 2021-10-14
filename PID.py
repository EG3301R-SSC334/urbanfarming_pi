#!/usr/bin/env python3

import time

class PID:

    def __init__(self, k_p, k_i, k_d, setpoint):
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.setpoint = setpoint

        self.p = 0
        self.i = 0
        self.d = 0

        self.prev_error = 0
        self.prev_time = time.time()

    def update(self, data, time):
        error = data - self.setpoint
        d_error = error - self.prev_error
        d_time = time - self.prev_time

        # P term
        self.p = error

        # I term
        self.i += self.k_i * d_time

        # D term
        if d_time > 0:
            self.d = d_error / d_time
        else:
            self.d = 0

        # Return
        return (self.k_p * self.p) + (self.k_i * self.i) + (self.k_d * self.d)