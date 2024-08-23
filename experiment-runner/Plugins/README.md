
# Plugins

A description and usage for each provided plugin can be found here.

---

## CodecarbonWrapper.py

### Overview

This plugin is a wrapper for the [mlco2/codecarbon](https://github.com/mlco2/codecarbon) project. It will estimate and track carbon emissions for your experiment.

### Requirements

```bash
pip install codecarbon
```

### Usage

To simply measure CO2 emissions (kg) and total energy consumed (kWh) and append them as data columns, use the following snippet:

```python
from Plugins.Profilers import CodecarbonWrapper
from Plugins.Profilers.CodecarbonWrapper import DataColumns as CCDataCols

@CodecarbonWrapper.emission_tracker(
    data_columns=[CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED],
    country_iso_code="NLD" # your country code
)
class RunnerConfig:
    ...
```

This will add `codecarbon__emissions` and `codecarbon__energy_consumed` data columns in the generated run_table.csv.

For a more fine-grained approach, the above snippet is equivalent to the following:

```python
from Plugins.Profilers import CodecarbonWrapper
from Plugins.Profilers.CodecarbonWrapper import DataColumns as CCDataCols

class RunnerConfig:

    @CodecarbonWrapper.add_data_columns([CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED])
    def create_run_table_model(self):
        ...
    
    @CodecarbonWrapper.start_emission_tracker(
        country_iso_code="NLD" # your country code
    )
    def start_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.stop_emission_tracker
    def stop_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.populate_data_columns
    def populate_run_data(self, context: RunnerContext):
        ...
```

* For the description of the "emissions.csv" that is generated per variation, check [codecarbon documentation](https://mlco2.github.io/codecarbon/output.html#output).

### Known issues

* If you encounter the error "AttributeError: Jumbotron was deprecated in dash-bootstrap-components version 1.0.0.", check [issue#319](https://github.com/mlco2/codecarbon/issues/319)
* If you encounter the error "Unable to read Intel RAPL files for CPU power : Permission denied", check [issue#244](https://github.com/mlco2/codecarbon/issues/244)

### Side notes

* To find country codes, use the ISO 3166-1 Alpha-3 code from [wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes)

---

## WattsUpPro.py

### Overview

This plugin is a port of the [Watts up? Pro](https://github.com/isaaclino/wattsup) project. It logs data from a "Watts Up Pro" power meter.

### Requirements

* (Hardware) A [Watts Up Pro power meter](https://www.vernier.com/files/manuals/wu-pro.pdf)

```bash
pip install pyserial
```

### Usage

```python
from Plugins.Profilers.WattsUpPro import WattsUpPro

class RunnerConfig:
    def start_measurement(self, context: RunnerContext) -> None:
        meter = WattsUpPro('/dev/ttyUSB0', 1.0)
        meter.log(5, str(context.run_dir.resolve() / 'sample.log'))

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        log_data = {}
        with open(context.run_dir.resolve() / 'sample.log') as f:
            lines = f.readlines()
        # prase lines and populate `log_data`
        return log_data
```

---

## PicoCM3.py

### Overview 
This plugin implements a python wrapper for the C driver and interface for the PicoLog CM3 device. It facilitates power measurements from up to three different inputs using clamps that physically attach to wires to measure the current passing through them.

### Requirements
* (Hardware) [PicoLog CM3 device](https://www.picotech.com/download/manuals/PicoLogCM3CurrentDataLoggerUsersGuide.pdf)

* Requires the picosdk drivers to be installed. Instructions found [here](https://www.picotech.com/downloads/linux)) see the section on "installing drivers only".

* The LD_LIBRARY_PATH environment variable MUST be set in your environment to the location of the CM3 driver (/opt/picoscope/lib on linux by default)

* The python numpy package

```bash
pip install numpy
```

### Usage

```python
from Plugins.Profilers.PicoCM3 import PicoCM3, CM3DataTypes, CM3Channels

class RunnerConfig:
    def create_run_table_model(self) -> RunTableModel:
        self.run_table_model = RunTableModel(
            data_columns=['timestamp', 'channel_1(A)', 'channel_2(off)', 'channel_3(off)']) # Channel 1 is in Amps

        return self.run_table_model

    def before_experiment(self) -> None:
        # Setup the picolog cm3 here (the parameters passed are also the default)
        self.meter = PicoCM3(sample_frequency   = 1000, # Sample the CM3 every second
                             mains_setting      = 0,    # Account for 50hz mains frequency
                             channel_settings   = {     # Which channels are enabled in what mode
                                CM3Channels.PLCM3_CHANNEL_1.value: CM3DataTypes.PLCM3_1_MILLIVOLT.value,
                                CM3Channels.PLCM3_CHANNEL_2.value: CM3DataTypes.PLCM3_OFF.value,
                                CM3Channels.PLCM3_CHANNEL_3.value: CM3DataTypes.PLCM3_OFF.value})
        # Open the device
        self.meter.open_device()

    def start_measurement(self, context: RunnerContext) -> None:
        # Start the picologs measurements here, create a unique log file for each (or pass the values through a variable)
        self.latest_log = str(context.run_dir.resolve() / f'picocm3.log')
        self.meter.log(timeout=60, self.latest_log)

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:       
        if self.latest_log == None:
            return {}

        log_data = self.meter.parse_log(self.latest_log)
        
        run_data = {k: None for k in self.run_table_model.get_data_columns()}
        # Parse the log_data dict here, and populate run_data as required by your experiment
        return run_data

    # Ensure that the PicoLog is closed properly
    def after_experiment(self) -> None:
        self.meter.close_device()
```

---

### Known issues
* After the device has been opened, changing a set channels settings (via the plcm3.PLCM3SetChannel api call) for a second time will result in some systems freezing, requiring a restart. Ensure that you only set these settings once for the entire experiment to avoid this.

### Side Notes
* The libpswrappers package does not provide a python API for the CM3, we provide this

* The linux drivers are by default available only for Ubuntu or openSUSE, after the repository has been added.

* The PicoLog CM3 does support connection over ethernet, this can be facilitated using the plcm3 python api we provide.

* Be aware that you must call device_open() and device_closed() on the PicoCM3 for the device to operate as intended, not closing will result in the bug described earlier.
