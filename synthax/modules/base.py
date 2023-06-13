# Copyright (c) 2023
# Manuel Cherep <mcherep@mit.edu>
# Nikhil Singh <nsingh1@mit.edu>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import jax
import chex
from flax import linen as nn
from synthax.config import SynthConfig
from synthax.parameter import ModuleParameter
from synthax.functional import fix_length
from synthax.types import Signal


class SynthModule(nn.Module):
    """
    A base class for synthesis modules. A :class:`~.SynthModule`
    optionally takes input from other :class:`~.SynthModule` instances.
    The :class:`~.SynthModule` uses its (optional) input and its
    set of :class:`~synthax.parameter.ModuleParameter` to generate
    output.

    All :class:`~.SynthModule` objects should be atomic, i.e., they
    should not contain other :class:`~.SynthModule` objects. This
    design choice is in the spirit of modular synthesis.

    Args:
        config (SynthConfig): An object containing synthesis settings
            that are shared across all modules.
    """

    config: SynthConfig
    PRNG_key: jax.random.PRNGKey

    @property
    def batch_size(self):
        """ Size of the batch to be generated. """
        return self.config.batch_size

    @property
    def sample_rate(self):
        """ Sample rate frequency in Hz. """
        return self.config.sample_rate

    @property
    def nyquist(self):
        """ Convenience property for the highest frequency that can be
        represented at :attr:`~.sample_rate` (as per Shannon-Nyquist). """
        return self.sample_rate / 2.0

    @property
    def eps(self):
        """ A very small value used to avoid computational errors. """
        return self.config.eps

    @property
    def buffer_size(self):
        """ Size of the module output in samples. """
        return self.config.buffer_size

    def to_buffer_size(self, signal: Signal) -> Signal:
        """
        Fixes the length of a signal to the default buffer size of this module,
        as specified by :attr:`~.SynthModule.buffer_size`. Longer signals are
        truncated to length; shorter signals are zero-padded.

        Args:
            signal (TODO): A signal to pad or truncate.
        """
        return fix_length(signal, self.buffer_size)

    def seconds_to_samples(self, seconds: float):
        """
        Convenience function to calculate the number of samples corresponding to
        given a time value and :attr:`~.sample_rate`. Returns a possibly
        fractional value.

        Args:
            seconds (float): Time value in seconds.
        """
        return seconds * self.sample_rate

    def set_parameter(self, parameter: ModuleParameter, value: chex.Array):
        """
        Updates a parameter value in a parameter-specific non-normalized range.

        Args:
            parameter_id: Id of the parameter to update.
            value:  Value to assign to the parameter.
        """
        parameter.to_0to1(value)


class ControlRateModule(SynthModule):
    """
    An abstract base class for non-audio modules that adapts the functions of
    :class:`.~SynthModule` to run at :attr:`~.ControlRateModule.control_rate`.

    Args:
        config (SynthConfig): An object containing synthesis settings
            that are shared across all modules.
    """

    @property
    def sample_rate(self):
        raise NotImplementedError("This module operates at control rate")

    @property
    def buffer_size(self):
        raise NotImplementedError("This module uses control buffer size")

    @property
    def control_rate(self):
        """ Control rate frequency in Hz. """
        return self.config.control_rate

    @property
    def control_buffer_size(self):
        """ Size of the module output in samples. """
        return self.config.control_buffer_size

    def to_buffer_size(self, signal: Signal) -> Signal:
        """
        Fixes the length of a signal to the control buffer size of this module,
        as specified by :attr:`~.ControlRateModule.control_buffer_size`. Longer
        signals are truncated to length; shorter signals are zero-padded.

        Args:
            signal: A signal to pad or truncate.
        """
        return fix_length(signal, self.control_buffer_size)

    def seconds_to_samples(self, seconds: float):
        """
        Convenience function to calculate the number of samples corresponding to
        given a time value and :attr:`~.control_rate`. Returns a possibly
        fractional value.

        Args:
            seconds (float): Time value in seconds.
        """
        return seconds * self.control_rate

    def __call__(self) -> Signal:
        """
        Each :class:`~.ControlRateModule` should override this.
        """
        raise NotImplementedError("Must override the __call__ method")